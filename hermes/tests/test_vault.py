"""Conformance tests: every note the plugin writes must pass the repo's pre-commit hook.

Run:  python3 -m unittest discover -s hermes/tests -v   (from the repo root)
Needs only Python 3.10+ and git. No Hermes required.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hermes" / "plugin"))

from second_brain.vault import Vault, VaultError, frontmatter  # noqa: E402

PREAMBLE = ("Test note created by the conformance suite on a scratch vault. It exists to prove that "
            "notes written through the plugin satisfy the AI-first contract enforced by the pre-commit hook.")


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


class VaultTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-vault-"))
        shutil.copytree(REPO / "vault-starter", self.tmp, dirs_exist_ok=True)
        git(self.tmp, "init", "-q")
        git(self.tmp, "config", "user.email", "test@example.com")
        git(self.tmp, "config", "user.name", "conformance")
        hook_dst = self.tmp / ".git" / "hooks" / "pre-commit"
        shutil.copy(REPO / "hooks" / "pre-commit", hook_dst)
        hook_dst.chmod(0o755)
        git(self.tmp, "add", "-A")
        res = git(self.tmp, "commit", "-q", "-m", "seed vault-starter")
        self.assertEqual(res.returncode, 0, f"starter must pass the hook:\n{res.stdout}{res.stderr}")
        os.environ["SECOND_BRAIN_VAULT"] = str(self.tmp)
        self.v = Vault.locate()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("SECOND_BRAIN_VAULT", None)

    # -- helpers -----------------------------------------------------------
    def hook_passes(self, msg: str = "test"):
        res = self.v.commit(msg)
        self.assertTrue(res.get("ok"), f"pre-commit rejected the change: {res}")
        return res

    def person(self, name="Alex Rivera", **extra):
        fields = {"tags": ["specialist", "region-we"], "role": "CS specialist", "relationship": "peer",
                  "region": "WE", **extra}
        return self.v.create_note("person", fields, PREAMBLE, {"Compiled truth": "- **Working style**: unknown"},
                                  name=name)

    # -- create ------------------------------------------------------------
    def test_braindump_is_contract_compliant(self):
        res = self.v.create_note("braindump", {"domain": "professional", "energy": "medium", "tags": ["training"]},
                                 PREAMBLE, {"Raw content": "Agents struggle with the new qualification script.",
                                            "Insight": "Rollout outpaced training."},
                                 slug="qualification script friction")
        p = self.tmp / res["path"]
        self.assertTrue(p.exists())
        self.assertRegex(res["path"], r"^00-inbox/\d{4}-\d{2}-\d{2}-\d{4}-qualification-script-friction\.md$")
        fm, body = frontmatter.read(p.read_text(encoding="utf-8"))
        self.assertEqual(fm["type"], "braindump")
        self.assertEqual(fm["tags"][0], "braindump")
        self.assertIs(fm["ai-first"], True)
        self.assertIn("## For future Claude", body)
        self.assertIn("## Raw content", body)
        self.assertNotIn("## Tension", body, "empty optional sections are not scaffolded")
        self.hook_passes("braindump")

    def test_enum_and_preamble_are_enforced(self):
        with self.assertRaises(VaultError):
            self.v.create_note("braindump", {"domain": "work", "energy": "medium"}, PREAMBLE)
        with self.assertRaises(VaultError):
            self.v.create_note("braindump", {"domain": "personal", "energy": "low"}, "too short")
        with self.assertRaises(VaultError):
            self.v.create_note("person", {"tags": []}, PREAMBLE, name="No Relationship")

    def test_missing_wikilinks_are_reported(self):
        res = self.v.create_note("braindump", {"domain": "mixed", "energy": "high"}, PREAMBLE,
                                 {"Links": "- People: [[02-people/Jordan Park]]\n- Concepts: [[06-knowledge/agentforce]]"},
                                 slug="links")
        self.assertEqual(sorted(res["missing_links"]), ["02-people/Jordan Park", "06-knowledge/agentforce"])

    # -- people ------------------------------------------------------------
    def test_person_fuzzy_match_and_no_duplicates(self):
        self.person()
        self.assertEqual(self.v.find_person("alex rivera")["match"], "exact")
        self.assertIn(self.v.find_person("Alex")["match"], ("likely", "exact"))
        self.assertEqual(self.v.find_person("Alex Riviera")["match"], "likely")
        self.assertEqual(self.v.find_person("Jordan Park")["match"], "none")
        with self.assertRaises(VaultError):
            self.person()  # same name again → refused, append instead
        self.hook_passes("person")

    def test_timeline_is_append_only_and_stamps_frontmatter(self):
        res = self.person(**{"staleness-flag": "stale-30d-since-2026-05-22", "last-interaction": "2026-05-22"})
        rel = res["path"]
        self.hook_passes("create person")
        self.v.append_timeline(rel, "Weekly 1-1", ["Source: [[04-meetings/2026-06-01-1to1]]",
                                                    "What: raised friction on the script"], date="2026-06-01")
        text1 = (self.tmp / rel).read_text(encoding="utf-8")
        self.assertIn("### 2026-06-01 — Weekly 1-1", text1)
        fm, _ = frontmatter.read(text1)
        self.assertEqual(fm["last-interaction"], "2026-06-01")
        self.assertEqual(fm["updated"], "2026-06-01")
        self.assertEqual(fm["staleness-flag"], "")
        self.hook_passes("append 1")
        self.v.append_timeline(rel, "Daily interactions", ["Calendar: 1-1 30min"], date="2026-06-02",
                               marker="(auto-logged)")
        text2 = (self.tmp / rel).read_text(encoding="utf-8")
        self.assertIn("### 2026-06-01 — Weekly 1-1", text2, "earlier entry untouched")
        self.assertIn("### 2026-06-02 — Daily interactions (auto-logged)", text2)
        self.assertLess(text2.index("2026-06-01 — Weekly"), text2.index("2026-06-02 — Daily"))
        self.hook_passes("append 2")

    def test_hook_blocks_history_destruction(self):
        rel = self.person()["path"]
        self.v.append_timeline(rel, "Weekly 1-1", ["What: x"], date="2026-06-01")
        self.hook_passes("seed")
        p = self.tmp / rel
        p.write_text(p.read_text(encoding="utf-8").replace("### 2026-06-01 — Weekly 1-1\n- What: x\n", ""),
                     encoding="utf-8")
        res = self.v.commit("gut history")
        self.assertFalse(res["ok"])
        self.assertIn("append-only", res.get("output", ""))
        git(self.tmp, "checkout", "--", rel)

    # -- daily -------------------------------------------------------------
    def test_daily_append_creates_and_appends(self):
        r1 = self.v.daily_append("Braindumps of the day", "- [[00-inbox/2026-06-01-0900-x]] — test", date="2026-06-01")
        self.assertEqual(r1["path"], "01-daily/2026-06-01.md")
        text = (self.tmp / r1["path"]).read_text(encoding="utf-8")
        self.assertIn("## Braindumps of the day\n\n- [[00-inbox/2026-06-01-0900-x]] — test", text)
        self.assertIn("## Meetings ingested today", text, "daily scaffold has all shared sections")
        self.v.daily_append("Braindumps of the day", "- second", date="2026-06-01")
        self.v.daily_append("People touched today", "- [[02-people/Alex Rivera]] — 1-1", date="2026-06-01")
        text = (self.tmp / r1["path"]).read_text(encoding="utf-8")
        self.assertIn("— test\n- second\n", text)
        self.assertEqual(text.count("## Braindumps of the day"), 1)
        self.hook_passes("daily")

    # -- knowledge / curator ---------------------------------------------
    def test_wiki_stub_and_curator_incremental(self):
        stub = self.v.create_note("wiki", {"domain": "cs-ops", "aliases": ["QS v2"],
                                           "created-from": "[[00-inbox/2026-06-01-0900-x]]"}, PREAMBLE,
                                  {"Summary": "*Stub — first mentioned in [[00-inbox/2026-06-01-0900-x]] on 2026-06-01.*",
                                   "Sources": "- [[00-inbox/2026-06-01-0900-x]] — 2026-06-01 (stub created)"},
                                  slug="qualification-script")
        res = self.v.curate(stub["path"])
        self.assertEqual(res["listed_under"], "_INDEX.md → Unsorted by domain")
        idx = (self.tmp / "06-knowledge/_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("- [[06-knowledge/qualification-script]] — `domain: cs-ops`", idx)
        self.assertIn("- 1 wiki pages · 1 lessons · 0 source docs · 0 hubs.", idx)
        # now a hub exists → listed inside it, sorted, with recent activity
        self.v.create_note("index", {"domain": "cs-ops", "tags": ["cs-ops"]}, PREAMBLE,
                           {"Summary": "CS operations.", "Wiki pages": "- [[06-knowledge/zeta-tool]] — later",
                            "Recent activity": "- 2026-05-01: created hub"}, slug="cs-ops")
        res = self.v.curate(stub["path"], action="stub created")
        self.assertEqual(res["listed_under"], "Wiki pages")
        hub = (self.tmp / "06-knowledge/cs-ops.md").read_text(encoding="utf-8")
        self.assertLess(hub.index("qualification-script"), hub.index("zeta-tool"), "alphabetical listing")
        self.assertIn("stub created [[06-knowledge/qualification-script]]", hub)
        self.assertLess(hub.index("stub created [[06-knowledge/qualification"), hub.index("2026-05-01: created hub"))
        self.hook_passes("knowledge")

    # -- search / tasks ----------------------------------------------------
    def test_search_and_actions(self):
        self.v.create_note("braindump", {"domain": "professional", "energy": "low", "tags": ["onboarding"]}, PREAMBLE,
                           {"Raw content": "The onboarding team struggles with the qualification script."},
                           slug="onboarding friction")
        hits = self.v.search("qualification script")
        self.assertTrue(hits and hits[0]["path"].startswith("00-inbox/"), hits)
        line = self.v.new_action("Send the QA plan", owner="me", due="2026-06-10", source_tag="braindump")
        self.assertRegex(line, r"^- \[ \] Send the QA plan — owner: me — due: 2026-06-10 — #from/braindump \^t-[a-z0-9]{6}$")
        self.assertNotEqual(self.v.new_action("a"), self.v.new_action("a"))

    def test_brief_is_compact(self):
        b = self.v.brief()
        self.assertEqual(b["working_language"], "en")
        self.assertIn("02-people", b["note_counts"])
        self.assertLess(len(str(b)), 4000)

    def test_frontmatter_roundtrip_with_wikilink_lists(self):
        fm = {"date": "2026-06-01", "type": "meeting", "tags": ["meeting", "x"],
              "participants": ["[[02-people/Alex Rivera]]", "[[02-people/Sam Lee]]"], "duration": "30",
              "source": "https://docs.google.com/d/abc", "ai-first": True}
        text = frontmatter.write(fm, "## For future Claude\n\nx\n")
        back, _ = frontmatter.read(text)
        self.assertEqual(back["participants"], fm["participants"])
        self.assertEqual(back["source"], fm["source"])
        self.assertIs(back["ai-first"], True)


if __name__ == "__main__":
    unittest.main()
