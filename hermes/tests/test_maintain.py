"""Maintenance conformance: task sync both ways, curator sweep convergence, staleness, health.
Every mutation is committed through hooks/pre-commit."""
from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hermes" / "plugin"))

from second_brain.vault import Vault, frontmatter, maintain  # noqa: E402

P = ("Scratch note for the maintenance conformance suite. It exists so the deterministic bookkeeping "
     "can be checked against the vault contract and the pre-commit hook.")


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True)


def days_ago(n):
    return (dt.date.today() - dt.timedelta(days=n)).isoformat()


class MaintainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-maint-"))
        shutil.copytree(REPO / "vault-starter", self.tmp, dirs_exist_ok=True)
        git(self.tmp, "init", "-q"); git(self.tmp, "config", "user.email", "t@t"); git(self.tmp, "config", "user.name", "t")
        hook = self.tmp / ".git/hooks/pre-commit"; shutil.copy(REPO / "hooks/pre-commit", hook); hook.chmod(0o755)
        git(self.tmp, "add", "-A"); self.assertEqual(git(self.tmp, "commit", "-qm", "seed").returncode, 0)
        os.environ["SECOND_BRAIN_VAULT"] = str(self.tmp)
        self.v = Vault.locate()
        self.root = self.tmp

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("SECOND_BRAIN_VAULT", None)

    def commit_ok(self, msg="m"):
        res = self.v.commit(msg); self.assertTrue(res["ok"], res); return res

    # ------------------------------------------------------------------ tasks
    def seed_tasks(self):
        self.v.create_note("meeting", {"participants": ["[[02-people/Alex Rivera]]"], "meeting-type": "team-sync",
                                       "date": days_ago(2)}, P,
                           {"Action items": "- [ ] Send the QA plan — owner: me — due: " + days_ago(1) + " — #from/meeting\n"
                                            "- [ ] Draft the rollout memo — owner: me — due: " + (dt.date.today() + dt.timedelta(days=3)).isoformat() + " — #from/meeting\n"
                                            "- [ ] Review the vendor contract — owner: [[02-people/Alex Rivera]] ⏳ — #from/meeting\n"
                                            "- [ ] Alex's own homework — owner: [[02-people/Alex Rivera]] — #from/meeting"},
                           slug="team sync")
        self.v.create_note("decision", {"status": "committed", "reversibility": "one-way", "date": days_ago(30)}, P,
                           {"Decision": "Centralize tier-1.", "Execution plan": "- [ ] Announce to regions — owner: me — #from/decision"},
                           slug="centralize tier1")
        self.v.create_note("project", {"status": "active", "date": days_ago(40), "updated": days_ago(40)}, P,
                           {"Goal": "x", "Success criteria": "- [ ] 90% CSAT", "Timeline": "- [ ] Book the kickoff — owner: me"},
                           slug="onboarding refresh")

    def test_sync_assigns_anchors_buckets_and_reconciles_both_ways(self):
        self.seed_tasks()
        rep = maintain.sync_tasks(self.root)
        self.assertEqual(rep["tasks"], 5, rep)            # 4 mine + 1 waiting; Alex's own homework ignored; success criterion excluded
        self.assertEqual(rep["new_anchors"], 5)
        todo = (self.root / "TODO.md").read_text(encoding="utf-8")
        self.assertIn("## ⏰ Overdue\n\n- [ ] 🔴 Send the QA plan — [[04-meetings/", todo)
        self.assertIn("## 🔜 Upcoming (next 7 days)\n\n- [ ] Draft the rollout memo", todo)
        self.assertIn("- [ ] (owner: [[02-people/Alex Rivera]]) Review the vendor contract", todo)
        self.assertIn("🔴 Announce to regions", todo, "one-way decision → high priority")
        self.assertIn("🟡 Book the kickoff", todo, "active project → medium")
        self.assertIn("⏳ stale", todo, "no due date + note older than 21 days → stale flag")
        self.assertTrue(any(j["kind"] == "zombie-task" for j in rep["needs_judgment"]))
        self.assertNotIn("90% CSAT", todo); self.assertNotIn("own homework", todo)
        self.commit_ok("roundup")
        # idempotent
        rep2 = maintain.sync_tasks(self.root)
        self.assertEqual(rep2["new_anchors"], 0)
        # TODO → source: tick "Send the QA plan" in TODO.md
        lines = todo.split("\n")
        i = next(k for k, l in enumerate(lines) if "Send the QA plan" in l)
        anchor = lines[i].split("#^t-")[1][:6]
        lines[i] = lines[i].replace("- [ ]", "- [x]", 1)
        (self.root / "TODO.md").write_text("\n".join(lines), encoding="utf-8")
        rep3 = maintain.sync_tasks(self.root)
        self.assertEqual(rep3["reconciled"]["todo_to_source"], 1)
        meeting = next(self.root.glob("04-meetings/*.md")).read_text(encoding="utf-8")
        self.assertRegex(meeting, r"- \[x\] Send the QA plan ✅ \d{4}-\d{2}-\d{2} — owner: me — due: .* \^t-" + anchor)
        self.assertIn(f"## ✅ Done (last 14 days)\n\n- [x] Send the QA plan", (self.root / "TODO.md").read_text(encoding="utf-8"))
        self.commit_ok("tick in todo")
        # source → TODO via set_task_state
        a2 = maintain.set_task_state(self.root, self.root.joinpath("TODO.md").read_text(encoding="utf-8").split("Draft the rollout memo")[1].split("#^t-")[1][:6], True)
        self.assertTrue(a2.get("done"), a2)
        rep4 = maintain.sync_tasks(self.root)
        self.assertEqual(rep4["reconciled"]["source_to_todo"], 1)
        self.assertEqual(rep4["buckets"]["✅ Done (last 14 days)"], 2)
        self.commit_ok("tick in source")

    def test_mirror_lines_never_get_anchors_and_complete_the_source(self):
        self.seed_tasks()
        maintain.sync_tasks(self.root)
        todo = (self.root / "TODO.md").read_text(encoding="utf-8")
        anchor = todo.split("Draft the rollout memo")[1].split("#^t-")[1][:6]
        self.v.daily_append("Pending follow-ups", f"- [x] Draft the rollout memo — [[TODO]] → [[04-meetings/x#^t-{anchor}]] — due soon")
        rep = maintain.sync_tasks(self.root)
        self.assertEqual(rep["new_anchors"], 0, "mirror line must not receive its own anchor")
        self.assertEqual(rep["reconciled"]["todo_to_source"], 1, "ticked mirror completes the source")
        self.commit_ok("mirror")

    def test_source_removed_is_flagged_not_dropped(self):
        self.seed_tasks(); maintain.sync_tasks(self.root)
        m = next(self.root.glob("04-meetings/*.md"))
        m.write_text("\n".join(l for l in m.read_text(encoding="utf-8").split("\n") if "rollout memo" not in l), encoding="utf-8")
        rep = maintain.sync_tasks(self.root)
        self.assertTrue(any(f["kind"] == "source-removed" for f in rep["flags"]))
        self.assertIn("⚠️ (source removed — confirm)", (self.root / "TODO.md").read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ curator
    def test_curator_sweep_rebuilds_hubs_converges_and_reports_health(self):
        self.v.create_note("index", {"domain": "cs-ops", "tags": ["cs-ops"]}, P, {"Summary": "CS ops.", "Wiki pages": "- [[06-knowledge/gone]] — deleted long ago"}, slug="cs-ops")
        for slug, d in (("qualification-script", days_ago(20)), ("qualif-script", days_ago(1)), ("agentforce", days_ago(100))):
            self.v.create_note("wiki", {"domain": "cs-ops", "date": d, "updated": d}, P, {"Summary": f"About {slug}."}, slug=slug)
        for slug in ("boost", "zowie", "chargebee"):
            self.v.create_note("wiki", {"domain": "vendor-stack", "needs-review": False}, P, {"Summary": f"{slug} vendor."}, slug=slug)
        self.v.create_note("doc", {"domain": "cs-ops", "doc-type": "analysis", "source": "https://x"}, P, {"Thesis": "T."}, slug="market")
        self.v.append_section("06-knowledge/qualification-script.md", "Related", ["- [[06-knowledge/agentforce]]"])
        rep = maintain.curator_sweep(self.root)
        self.assertLessEqual(rep["passes"], 2); self.assertTrue(rep["stable"])
        hub = (self.root / "06-knowledge/cs-ops.md").read_text(encoding="utf-8")
        self.assertNotIn("[[06-knowledge/gone]]", hub, "listings rebuilt from scratch")
        self.assertIn("- [[06-knowledge/agentforce]]", hub); self.assertIn("## Source documents\n\n- [[06-knowledge/_sources/", hub)
        self.assertIn("curator sweep rebuilt listings (3 wikis · 0 lessons · 1 docs)", hub)
        idx = (self.root / "06-knowledge/_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("- [[06-knowledge/cs-ops]] (3 wikis · 0 lessons · 1 source docs", idx)
        self.assertIn("- [[06-knowledge/boost]] — `domain: vendor-stack`", idx)
        self.assertIn("### Near-duplicates\n- 06-knowledge/qualif-script ↔ 06-knowledge/qualification-script", idx)
        self.assertIn("### Stale wikis\n- [[06-knowledge/agentforce]]", idx)
        stubs_block = idx.split("### Stubs to enrich")[1].split("###")[0]
        self.assertIn("- [[06-knowledge/qualification-script]]", stubs_block)   # needs-review default + 20 days old
        self.assertNotIn("qualif-script]]", stubs_block, "a 1-day-old stub is not flagged")
        self.assertTrue(any(j["kind"] == "new-hub" and j["domain"] == "vendor-stack" for j in rep["needs_judgment"]))
        self.assertTrue(any(j["kind"] == "near-duplicate" for j in rep["needs_judgment"]))
        h = rep["health"]
        self.assertIn("06-knowledge/boost", h["orphans"]); self.assertNotIn("06-knowledge/agentforce", h["orphans"])
        self.commit_ok("sweep")
        rep2 = maintain.curator_sweep(self.root)
        self.assertEqual(rep2["hubs_rebuilt"], [], "second sweep is a no-op")

    # ------------------------------------------------------------------ staleness / health
    def test_staleness_flags_by_relationship(self):
        mk = lambda name, rel, last: self.v.create_note("person", {"relationship": rel, "last-interaction": last, "tags": ["x"]}, P, {"Compiled truth": "-"}, name=name)
        mk("Fresh Peer", "peer", days_ago(5)); mk("Stale Peer", "peer", days_ago(45)); mk("Gone Report", "direct-report", days_ago(70)); mk("Old Vendor", "external", days_ago(200))
        rep = maintain.staleness(self.root)
        self.assertEqual([x["path"] for x in rep["stale"]], ["02-people/Stale Peer.md"])
        self.assertEqual([x["path"] for x in rep["critical"]], ["02-people/Gone Report.md"])
        self.assertEqual(rep["skipped"], 1)
        fm, _ = frontmatter.read((self.root / "02-people/Gone Report.md").read_text(encoding="utf-8"))
        self.assertRegex(fm["staleness-flag"], r"^stale-60d-since-\d{4}-\d{2}-\d{2}$")
        self.commit_ok("staleness")
        rep2 = maintain.staleness(self.root)
        fm2, _ = frontmatter.read((self.root / "02-people/Gone Report.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["staleness-flag"], fm2["staleness-flag"], "since-date kept on re-run")
        self.v.append_timeline("02-people/Gone Report.md", "Back in touch", ["What: coffee"])
        rep3 = maintain.staleness(self.root)
        self.assertEqual([x["path"] for x in rep3["cleared"]], [])  # append_timeline already cleared it
        fm3, _ = frontmatter.read((self.root / "02-people/Gone Report.md").read_text(encoding="utf-8"))
        self.assertEqual(fm3["staleness-flag"], "")

    def test_run_all_and_health(self):
        self.seed_tasks()
        out = maintain.run(self.root, "all")
        self.assertEqual(set(out) - {"needs_judgment"}, {"scope", "applied", "tasks", "curator", "staleness", "health"})
        self.assertIn("03-projects", out["health"]["counts"])
        self.assertEqual(out["health"]["zombie_projects"], ["03-projects/onboarding-refresh.md"])
        self.assertTrue(out["needs_judgment"])
        dry = maintain.run(self.root, "tasks", apply=False)
        self.assertFalse(dry["applied"])
        self.commit_ok("all")


    # --------------------------------------------------------------- activity
    def test_activity_reports_recent_notes(self):
        self.seed_tasks()
        rep = self.v.activity(since_hours=24)
        self.assertEqual(rep["source"], "vault")
        paths = [i["path"] for i in rep["items"]]
        self.assertIn("04-meetings/" + days_ago(2) + "-team-sync.md", paths)
        self.assertEqual(rep["count"], len(rep["items"]))
        self.assertIn("04-meetings", rep["by_folder"])
        # the meeting is dated 2 days ago -> not "new" in a 24h window; the daily note is
        meeting = next(i for i in rep["items"] if i["path"].startswith("04-meetings/"))
        self.assertFalse(meeting["new"])
        self.v.daily_append("Journal", "- Wrote the plan.")
        rep2 = self.v.activity(since_hours=24)
        today = next(i for i in rep2["items"] if i["path"].startswith("01-daily/"))
        self.assertTrue(today["new"])
        self.assertIn("[[01-daily/", rep2["text"])
        self.commit_ok("activity")

    def test_activity_window_excludes_old_notes(self):
        self.seed_tasks()
        self.commit_ok("seed for activity window")
        old = self.root / "07-archive/ancient.md"
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text("---\ndate: " + days_ago(400) + "\ntype: knowledge\ntags: []\nai-first: true\n---\n\n" + P + "\n",
                       encoding="utf-8")
        past = dt.datetime.now() - dt.timedelta(days=400)
        os.utime(old, (past.timestamp(), past.timestamp()))
        rep = self.v.activity(since_hours=1)
        self.assertNotIn("07-archive/ancient.md", [i["path"] for i in rep["items"]])


if __name__ == "__main__":
    unittest.main()
