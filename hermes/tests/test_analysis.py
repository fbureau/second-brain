"""Phase 3-4 conformance: recall evidence, agenda gathering, decision archaeology,
tend previews, backfill planning. Every mutation still commits through hooks/pre-commit."""
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

from second_brain.vault import Vault, agenda, backfill, decisions, frontmatter, recall, tend  # noqa: E402

P = ("Scratch note for the analysis conformance suite. It exists so the retrieval, planning and "
     "maintenance layers can be checked against the vault contract and the pre-commit hook.")


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True)


def days_ago(n):
    return (dt.date.today() - dt.timedelta(days=n)).isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-analysis-"))
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
        res = self.v.commit(msg)
        self.assertTrue(res["ok"], res)
        return res

    def person(self, name, **fields):
        f = {"relationship": "peer", "region": "WE"}
        f.update(fields)
        return self.v.create_note("person", f, P, {"Compiled truth": f"- {name} works here."}, name=name)

    def decision(self, slug, decision_text, rationale, status="committed", date=None, **fields):
        f = {"status": status, "reversibility": "one-way", "date": date or days_ago(60)}
        f.update(fields)
        return self.v.create_note("decision", f, P,
                                  {"Decision": decision_text, "Rationale": rationale,
                                   "Reversal conditions": "Revisit if churn rises above 5%."},
                                  slug=slug)


class RecallTests(Base):
    def seed(self):
        self.person("Alex Rivera")
        self.v.create_note("project", {"status": "active"}, P,
                           {"Goal": "Refresh the onboarding funnel for the EMEA region."},
                           slug="onboarding refresh")
        self.v.create_note("meeting", {"participants": ["[[02-people/Alex Rivera]]"], "meeting-type": "1-1",
                                       "date": days_ago(3)}, P,
                           {"Decisions": "We decided to centralize tier-1 support in Lisbon.",
                            "Context": "Alex Rivera raised the tier-1 backlog again."},
                           slug="alex 1-1")
        self.v.append_timeline("02-people/Alex Rivera.md", "1-1 on tier-1",
                               ["What: Alex pushed to centralize tier-1 support."], date=days_ago(3))

    def test_entities_resolve_people_and_projects(self):
        self.seed()
        ents = recall.entities(self.root, "What did Alex Rivera say about the Onboarding Refresh?")
        paths = [e["path"] for e in ents]
        self.assertIn("02-people/Alex Rivera.md", paths)
        self.assertIn("03-projects/onboarding-refresh.md", paths)

    def test_recall_cites_with_confidence(self):
        self.seed()
        res = self.v.recall("What did we decide about tier-1 support?")
        self.assertIn(res["confidence"], ("stated", "high", "medium"))
        cited = [c["path"] for c in res["citations"]]
        self.assertTrue(any(c.startswith("04-meetings/") for c in cited), cited)
        self.assertTrue(any(c["lines"] for c in res["citations"]))
        for c in res["citations"]:
            self.assertIn("date", c)
        self.assertIn("tier-1", res["text"].lower())

    def test_recall_admits_ignorance(self):
        self.seed()
        res = self.v.recall("What is our position on quantum key distribution?")
        self.assertEqual(res["confidence"], "unknown")
        self.assertTrue(any("does not know" in g for g in res["gaps"]), res["gaps"])
        self.assertEqual(res["text"], "- the vault has nothing on this")

    def test_system_notes_are_never_the_answer(self):
        self.seed()
        res = self.v.recall("What are the vault rules for a person note?")
        self.assertNotIn("_CLAUDE.md", [c["path"] for c in res["citations"]])

    def test_prefetch_block_is_bounded_and_silent_when_empty(self):
        self.seed()
        block, count = recall.prefetch_block(self.root, "tier-1 support", max_chars=300)
        self.assertLessEqual(len(block), 320)
        self.assertGreater(count, 0)
        empty, n = recall.prefetch_block(self.root, "quantum key distribution")
        self.assertEqual((empty, n), ("", 0))


class AgendaTests(Base):
    def seed(self):
        self.person("Gone Quiet", **{"last-interaction": days_ago(90), "staleness-flag": "stale-60d"})
        self.v.create_note("project", {"status": "active", "date": days_ago(40),
                                       "updated": days_ago(40)}, P,
                           {"Goal": "Ship the billing migration.",
                            "Risks & dependencies": "- Blocked on legal sign-off."},
                           slug="billing migration")
        self.v.create_note("meeting", {"participants": ["[[02-people/Gone Quiet]]"], "meeting-type": "team-sync",
                                       "date": days_ago(2)}, P,
                           {"Action items": "- [ ] Send the QA plan — owner: me — due: " + days_ago(4) + " — #from/meeting\n"
                                            "- [ ] Book the review — owner: me — due: " + dt.date.today().isoformat() + " — #from/meeting\n"
                                            "- [ ] Chase the vendor — owner: [[02-people/Gone Quiet]] ⏳ — #from/meeting"},
                           slug="sync")

    def test_agenda_gathers_without_ranking(self):
        self.seed()
        out = self.v.agenda()
        self.assertEqual(out["counts"]["overdue"], 1)
        self.assertEqual(out["counts"]["today"], 1)
        self.assertEqual(out["counts"]["waiting"], 1)
        self.assertEqual([p["name"] for p in out["projects"]], ["billing-migration"])
        self.assertTrue(out["projects"][0]["quiet"])
        self.assertTrue(out["projects"][0]["blocked_notes"])
        self.assertEqual([p["name"] for p in out["cooling_people"]], ["Gone Quiet"])
        self.assertTrue(any("past their due date" in s for s in out["signals"]))
        self.assertIn("Rank these yourself", out["next"])

    def test_agenda_is_read_only(self):
        self.seed()
        self.commit_ok("seed")
        self.v.agenda()
        self.assertEqual(git(self.root, "status", "--porcelain").stdout.strip(), "")

    def test_empty_vault_says_so_instead_of_claiming_nothing_to_do(self):
        out = self.v.agenda()
        self.assertEqual(out["counts"]["open_total"], 0)
        self.assertTrue(any("TODO.md is in sync" in s for s in out["signals"]))


class DecisionTests(Base):
    def seed(self):
        self.person("Alex Rivera")
        self.decision("centralize support", "Centralize tier-1 support in Lisbon.",
                      "Cheaper per ticket and easier to staff. [[02-people/Alex Rivera]] agreed.",
                      status="reversed", date=days_ago(200))
        self.decision("centralize billing", "Centralize billing operations in Lisbon.",
                      "Same logic as support: cheaper per ticket, easier to staff.",
                      status="committed", date=days_ago(90))
        self.v.create_note("knowledge", {"domain": "operations"}, P,
                           {"What we know": "Centralizing support in one site raised handover cost."},
                           slug="centralizing support cost")

    def test_context_puts_reversals_first(self):
        self.seed()
        out = self.v.decision_context("Should we centralize tier-1 support in one site?")
        self.assertTrue(out["similar_decisions"])
        self.assertEqual(out["similar_decisions"][0]["status"], "reversed")
        self.assertTrue(out["reversed_precedents"])
        self.assertTrue(any(q.startswith("A comparable decision was reversed") for q in out["questions"]))
        self.assertTrue(any(s["path"] == "02-people/Alex Rivera.md" for s in out["stakeholders"]))

    def test_context_admits_no_prior_art(self):
        out = self.v.decision_context("Should we adopt a four-day working week in the Reykjavik office?")
        self.assertEqual(out["similar_decisions"], [])
        self.assertTrue(any("no comparable decision" in q for q in out["questions"]))

    def test_unchecked_reversal_conditions_are_surfaced(self):
        self.seed()
        out = self.v.decision_context("centralize")
        paths = [d["path"] for d in out["unchecked_reversal_conditions"]]
        self.assertIn("05-decisions/" + days_ago(90) + "-centralize-billing.md", paths)

    def test_postmortem_finds_notes_on_the_same_hypothesis(self):
        self.seed()
        rev = "05-decisions/" + days_ago(200) + "-centralize-support.md"
        out = self.v.decision_postmortem(rev)
        self.assertEqual(out["status"], "reversed")
        self.assertIn("Lisbon", out["decision_text"])
        resting = [n["path"] for n in out["notes_resting_on_the_same_hypothesis"]]
        self.assertIn("05-decisions/" + days_ago(90) + "-centralize-billing.md", resting)
        self.assertIn("02-people/Alex Rivera", out["stakeholders"])
        self.assertIn("append-only", out["next"])

    def test_postmortem_refuses_a_non_decision(self):
        self.person("Alex Rivera")
        out = self.v.decision_postmortem("02-people/Alex Rivera.md")
        self.assertIn("not a decision", out["error"])


class TendTests(Base):
    def test_safe_fixes_are_previewed_then_applied(self):
        rel = "06-knowledge/loose-note.md"
        (self.root / rel).write_text("---\ndate: " + days_ago(2) + "\ntype: knowledge\ntags: []\n---\n\n"
                                     "## For future Claude\n\n" + P + "\n", encoding="utf-8")
        preview = self.v.tend(scope="frontmatter")
        fix = next(f for f in preview["safe_fixes"] if f["path"] == rel)
        self.assertEqual(fix["fixes"]["ai-first"], True)
        self.assertEqual(fix["fixes"]["tags"], ["knowledge"])
        self.assertFalse(fix["written"])
        fm, _ = frontmatter.read((self.root / rel).read_text(encoding="utf-8"))
        self.assertNotIn("ai-first", fm)          # preview wrote nothing

        applied = self.v.tend(scope="frontmatter", apply_safe=True)
        self.assertTrue(all(f["written"] for f in applied["safe_fixes"]))
        fm2, _ = frontmatter.read((self.root / rel).read_text(encoding="utf-8"))
        self.assertIs(fm2["ai-first"], True)
        self.assertEqual(fm2["tags"], ["knowledge"])
        self.commit_ok("tend safe fixes")

    def test_proposals_are_never_applied(self):
        rel = "06-knowledge/sans-preambule.md"
        (self.root / rel).write_text("---\ndate: " + days_ago(2) + "\ntype: knowledge\ntags: [knowledge]\n"
                                     "ai-first: true\n---\n\n## Ce que nous savons\n\n"
                                     "Nous avons decide que les equipes doivent etre reunies dans une "
                                     "seule region pour les operations.\n", encoding="utf-8")
        out = self.v.tend(scope="language")
        kinds = {p["kind"] for p in out["proposals"] if p.get("path") == rel}
        self.assertIn("missing-preamble", kinds)
        self.assertEqual(out["safe_fixes"], [])
        self.assertEqual((self.root / rel).read_text(encoding="utf-8").count("For future Claude"), 0)
        self.assertIn("has been applied", out["next"])

    def test_duplicate_people_are_flagged_not_merged(self):
        self.person("Alex Rivera")
        self.person("Alex")
        out = self.v.tend(scope="duplicates")
        dup = [p for p in out["proposals"] if p["kind"] == "duplicate-people"]
        self.assertTrue(dup)
        self.assertEqual(sorted(dup[0]["paths"]), ["02-people/Alex Rivera.md", "02-people/Alex.md"])
        self.assertTrue((self.root / "02-people/Alex.md").exists())

    def test_broken_links_are_reported(self):
        self.v.create_note("braindump", {"domain": "professional", "energy": "medium"}, P,
                           {"Raw content": "Talked to [[02-people/Nobody Here]] about it."},
                           slug="dangling")
        out = self.v.tend(scope="links")
        broken = [p for p in out["proposals"] if p["kind"] == "broken-links"]
        self.assertTrue(broken)
        self.assertIn("02-people/Nobody Here", broken[0]["targets"])

    def test_target_language_flags_drift_only_when_asked(self):
        rel = "06-knowledge/note-fr.md"
        (self.root / rel).write_text("---\ndate: " + days_ago(1) + "\ntype: knowledge\ntags: [knowledge]\n"
                                     "ai-first: true\n---\n\n## For future Claude\n\n" + P + "\n\n"
                                     "## Ce que nous savons\n\nNous avons decide que la migration des "
                                     "equipes vers la nouvelle region est une priorite pour les clients.\n",
                                     encoding="utf-8")
        neutral = self.v.tend(scope="language")
        self.assertFalse([p for p in neutral["proposals"] if p["kind"] == "body-language"])
        asked = self.v.tend(scope="language", target_language="en")
        drift = [p for p in asked["proposals"] if p["kind"] == "body-language" and p["path"] == rel]
        self.assertTrue(drift)
        self.assertEqual(drift[0]["detected"], "fr")


class BackfillTests(Base):
    def test_plan_orders_entities_first_and_windows_the_rest(self):
        since = days_ago(60)
        out = self.v.backfill_plan(since=since, batch_days=14)
        phases = [b["phase"] for b in out["batches"]]
        self.assertEqual(phases[0], "people")
        self.assertEqual(phases[1], "projects")
        self.assertLess(phases.index("people"), phases.index("meetings"))
        self.assertEqual(sum(1 for b in out["batches"] if b["phase"] == "people"), 1)
        meetings = [b for b in out["batches"] if b["phase"] == "meetings"]
        self.assertGreaterEqual(len(meetings), 4)
        self.assertEqual(meetings[0]["until"], dt.date.today().isoformat())   # newest first
        self.assertTrue(all(b["since"] >= since for b in meetings))
        self.assertTrue((self.root / backfill.STATE_FILE).exists())
        self.commit_ok("backfill plan")

    def test_plan_rejects_an_absurd_range(self):
        self.assertIn("error", self.v.backfill_plan(since="2019-01-01"))
        self.assertIn("error", self.v.backfill_plan(since="not-a-date"))
        self.assertIn("error", self.v.backfill_plan(since=dt.date.today().isoformat(), until=days_ago(30)))

    def test_plan_lists_known_entities_so_the_model_dedupes(self):
        self.person("Alex Rivera")
        out = self.v.backfill_plan(since=days_ago(30))
        self.assertIn("Alex Rivera", out["known_people"])
        self.assertEqual(out["existing_entities"]["people"], 1)

    def test_marking_a_batch_makes_the_next_run_resume(self):
        out = self.v.backfill_plan(since=days_ago(30))
        first = out["batches"][0]["id"]
        done = self.v.backfill_done(first)
        self.assertEqual(done["marked"], "done")
        self.assertEqual(self.v.backfill_done(first).get("batch"), first)   # already ticked -> error
        self.assertIn("error", self.v.backfill_done(first))
        again = self.v.backfill_plan(since=days_ago(30))
        self.assertTrue(again["resuming"])
        self.assertEqual(again["done_count"], 1)
        self.assertNotIn(first, [b["id"] for b in again["remaining"]])
        self.commit_ok("backfill progress")


if __name__ == "__main__":
    unittest.main()
