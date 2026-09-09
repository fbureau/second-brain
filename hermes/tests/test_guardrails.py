"""Adversarial suite: what happens when the model gets it wrong.

The premise of the Hermes edition is that a small local model can run a second brain because
the *tools* hold the contract, not the prompt. That premise is only worth anything if it holds
when the model misbehaves — and small models misbehave in predictable ways: they invent an enum
value, they skip the preamble, they answer in the wrong language, they try to overwrite a note
instead of appending, they hallucinate a person, they pass a path with `..` in it.

Every test here is a call a confused model would plausibly make. Each one must be **refused by
the code**, not by a prompt, and refused with a message that says what to do instead. Anything
that gets through here is a hole a 12B model will find on a Tuesday.

`hermes/bench/guardrails.py` runs the same cases and prints a scorecard.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hermes" / "plugin"))

from second_brain import tools  # noqa: E402
from second_brain.vault import Vault, VaultError, frontmatter  # noqa: E402

P = ("Scratch note for the adversarial suite. It exists so the guardrails can be checked against "
     "the kind of malformed call a small model makes when it loses the thread.")


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True)


class Guardrails(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-guard-"))
        shutil.copytree(REPO / "vault-starter", self.tmp, dirs_exist_ok=True)
        git(self.tmp, "init", "-q"); git(self.tmp, "config", "user.email", "t@t"); git(self.tmp, "config", "user.name", "t")
        hook = self.tmp / ".git/hooks/pre-commit"; shutil.copy(REPO / "hooks/pre-commit", hook); hook.chmod(0o755)
        git(self.tmp, "add", "-A"); git(self.tmp, "commit", "-qm", "seed")
        os.environ["SECOND_BRAIN_VAULT"] = str(self.tmp)
        tools.configure(lambda: str(self.tmp))
        self.v = Vault.locate()
        self.root = self.tmp

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("SECOND_BRAIN_VAULT", None)

    def call(self, name: str, args: dict) -> dict:
        """Invoke a tool exactly as Hermes would, and parse the JSON it returns."""
        return json.loads(tools.HANDLERS[name](args))

    def assert_refused(self, res: dict, *expect: str):
        self.assertIn("error", res, f"expected a refusal, got: {res}")
        for e in expect:
            self.assertIn(e.lower(), res["error"].lower(), res["error"])

    # ------------------------------------------------------------ frontmatter
    def test_invented_enum_value_is_refused_with_the_allowed_list(self):
        res = self.call("sb_create_note", {"type": "braindump", "preamble": P,
                                           "fields": {"domain": "work-stuff", "energy": "medium"}, "slug": "x"})
        self.assert_refused(res, "not allowed")
        self.assertIn("project-specific", res["error"])   # the fix is in the message

    def test_unknown_note_type_is_refused_with_the_known_types(self):
        res = self.call("sb_create_note", {"type": "journal", "preamble": P, "fields": {}, "slug": "x"})
        self.assert_refused(res, "unknown note type")
        self.assertIn("braindump", res["error"])

    def test_missing_required_field_is_refused_by_name(self):
        res = self.call("sb_create_note", {"type": "decision", "preamble": P,
                                           "fields": {"status": "committed"}, "slug": "x"})
        self.assert_refused(res, "requires fields", "reversibility")

    def test_a_note_cannot_be_written_without_a_preamble(self):
        for bad in ("", "   ", "Note.", "Quick note about the thing."):
            res = self.call("sb_create_note", {"type": "braindump", "preamble": bad,
                                               "fields": {"domain": "professional", "energy": "low"}, "slug": "x"})
            self.assert_refused(res, "preamble too short")

    def test_ai_first_and_base_tag_are_stamped_even_when_the_model_forgets(self):
        res = self.call("sb_create_note", {"type": "braindump", "preamble": P,
                                           "fields": {"domain": "professional", "energy": "low", "tags": ["ideas"]},
                                           "slug": "stamped"})
        fm, _ = frontmatter.read((self.root / res["path"]).read_text(encoding="utf-8"))
        self.assertIs(fm["ai-first"], True)
        self.assertEqual(fm["tags"][0], "braindump")
        self.assertIn("date", fm)

    # ------------------------------------------------------------ append-only
    def test_creating_over_an_existing_note_is_refused_and_points_at_append(self):
        first = self.call("sb_create_note", {"type": "person", "preamble": P,
                                             "fields": {"relationship": "peer"}, "name": "Alex Rivera"})
        self.assertIn("path", first)
        again = self.call("sb_create_note", {"type": "person", "preamble": P,
                                             "fields": {"relationship": "peer"}, "name": "Alex Rivera"})
        self.assert_refused(again, "already exists", "append")

    def test_appending_never_rewrites_what_is_already_there(self):
        self.call("sb_create_note", {"type": "person", "preamble": P,
                                     "fields": {"relationship": "peer"}, "name": "Alex Rivera"})
        rel = "02-people/Alex Rivera.md"
        self.call("sb_append_timeline", {"path": rel, "title": "First", "lines": ["What: first entry."]})
        before = (self.root / rel).read_text(encoding="utf-8")
        self.call("sb_append_timeline", {"path": rel, "title": "Second", "lines": ["What: second entry."]})
        after = (self.root / rel).read_text(encoding="utf-8")
        self.assertIn("First", after)
        self.assertIn("Second", after)
        self.assertIn("What: first entry.", after)
        self.assertGreater(len(after), len(before))
        # every original body line survives, in order
        kept = [l for l in before.split("\n") if l.strip() and not l.startswith("updated:")
                and not l.startswith("last-interaction:")]
        self.assertTrue(all(l in after for l in kept))

    def test_the_hook_rejects_a_destructive_edit_to_an_append_only_note(self):
        self.call("sb_create_note", {"type": "person", "preamble": P,
                                     "fields": {"relationship": "peer"}, "name": "Alex Rivera"})
        rel = "02-people/Alex Rivera.md"
        self.call("sb_append_timeline", {"path": rel, "title": "First", "lines": ["What: first entry."]})
        self.assertTrue(self.call("sb_commit", {"message": "person"})["ok"])
        # a model that "tidies" the note by rewriting it must not get past the hook
        (self.root / rel).write_text("---\ndate: 2026-01-01\ntype: person\ntags: [person]\nai-first: true\n"
                                     "relationship: peer\n---\n\n## For future Claude\n\n" + P + "\n",
                                     encoding="utf-8")
        res = self.call("sb_commit", {"message": "tidy"})
        self.assertFalse(res["ok"], res)
        self.assertIn("append-only", (res.get("output") or "").lower() + (res.get("error") or "").lower())

    def test_deleting_a_note_never_reaches_a_commit(self):
        self.call("sb_create_note", {"type": "decision", "preamble": P,
                                     "fields": {"status": "committed", "reversibility": "one-way"},
                                     "slug": "keep this"})
        self.assertTrue(self.call("sb_commit", {"message": "decision"})["ok"])
        rel = next(p for p in (self.root / "05-decisions").glob("*keep-this.md")).relative_to(self.root)
        (self.root / rel).unlink()
        res = self.call("sb_commit", {"message": "delete"})
        self.assertFalse(res["ok"], res)

    # ------------------------------------------------------------ path safety
    def test_paths_escaping_the_vault_are_refused(self):
        for bad in ("../outside.md", "/etc/passwd", "02-people/../../escape.md"):
            res = self.call("sb_read", {"path": bad})
            self.assertIn("error", res, f"{bad} was not refused")
        self.assertFalse((self.root.parent / "outside.md").exists())

    def test_reading_a_missing_note_says_so_instead_of_inventing(self):
        self.assert_refused(self.call("sb_read", {"path": "02-people/Ghost.md"}), "not found")

    def test_appending_to_a_missing_note_does_not_create_it(self):
        res = self.call("sb_append_section", {"path": "03-projects/nope.md", "heading": "Links",
                                              "lines": ["- [[x]]"]})
        self.assert_refused(res, "not found")
        self.assertFalse((self.root / "03-projects/nope.md").exists())

    # ------------------------------------------------------------ people
    def test_a_typo_is_never_reported_as_an_exact_match(self):
        self.call("sb_create_note", {"type": "person", "preamble": P,
                                     "fields": {"relationship": "peer"}, "name": "Alex Rivera"})
        self.assertEqual(self.call("sb_find_person", {"name": "Alex Rivera"})["match"], "exact")
        self.assertNotEqual(self.call("sb_find_person", {"name": "Alexx Riveraa"})["match"], "exact")
        self.assertEqual(self.call("sb_find_person", {"name": "Someone Else Entirely"})["match"], "none")

    def test_an_ambiguous_first_name_is_flagged_not_guessed(self):
        for n in ("Alex Rivera", "Alex Moreau"):
            self.call("sb_create_note", {"type": "person", "preamble": P,
                                         "fields": {"relationship": "peer"}, "name": n})
        res = self.call("sb_find_person", {"name": "Alex"})
        self.assertEqual(res["match"], "ambiguous")
        self.assertGreaterEqual(len(res["candidates"]), 2)

    # ------------------------------------------------------------ retrieval honesty
    def test_recall_refuses_to_answer_what_the_vault_does_not_hold(self):
        res = self.call("sb_recall", {"question": "What is our position on quantum key distribution?"})
        self.assertEqual(res["confidence"], "unknown")
        self.assertEqual(res["citations"], [])
        self.assertIn("does not know", res["next"])

    def test_search_never_answers_with_the_system_files(self):
        res = self.call("sb_search", {"query": "vault rules append-only frontmatter"})
        paths = [r["path"] for r in res["results"]]
        for system in ("_CLAUDE.md", "AGENTS.md", "00-inbox/MY-PROFILE.md", "TODO.md"):
            self.assertNotIn(system, paths)

    # ------------------------------------------------------------ maintenance
    def test_preview_mode_writes_nothing(self):
        self.call("sb_create_note", {"type": "meeting", "preamble": P,
                                     "fields": {"participants": ["[[02-people/Alex Rivera]]"],
                                                "meeting-type": "team-sync"},
                                     "sections": {"Action items": "- [ ] Do the thing — owner: me — #from/meeting"},
                                     "slug": "sync"})
        self.assertTrue(self.call("sb_commit", {"message": "seed"})["ok"])
        self.call("sb_maintain", {"scope": "tasks", "apply": False})
        self.call("sb_tend", {"scope": "all"})
        self.call("sb_agenda", {})
        self.call("sb_recall", {"question": "the thing"})
        self.assertEqual(git(self.root, "status", "--porcelain").stdout.strip(), "")

    def test_toggling_an_unknown_anchor_is_refused(self):
        res = self.call("sb_toggle_task", {"anchor": "t-zzzzzz", "done": True})
        self.assertIn("error", res)

    def test_a_handler_never_raises_into_the_agent_loop(self):
        """Whatever the model sends, the tool answers with JSON — a traceback ends the session."""
        junk = [{}, {"path": None}, {"query": 12}, {"question": ["not", "a", "string"]},
                {"type": "braindump", "fields": "not-a-dict", "preamble": P},
                {"since": "yesterday"}, {"anchor": {"nested": True}}, {"scope": "nonsense"}]
        for name in tools.VAULT_HANDLERS:
            for args in junk:
                out = tools.HANDLERS[name](args)
                self.assertIsInstance(out, str)
                parsed = json.loads(out)          # must always be valid JSON
                self.assertIsInstance(parsed, dict)

    def test_a_source_tool_is_hidden_rather_than_failing_without_credentials(self):
        for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN",
                  "SLACK_BOT_TOKEN", "JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
            os.environ.pop(k, None)
        for kind in ("google", "slack", "jira"):
            self.assertFalse(tools.source_available(kind))
        os.environ["SLACK_BOT_TOKEN"] = "xoxb-test"
        try:
            self.assertTrue(tools.source_available("slack"))
            self.assertFalse(tools.source_available("google"))
        finally:
            os.environ.pop("SLACK_BOT_TOKEN", None)

    # ------------------------------------------------------------ contract drift
    def test_every_schema_has_a_handler_and_every_handler_has_a_schema(self):
        from second_brain import schemas
        declared = {s["name"] for s in schemas.ALL}
        self.assertEqual(declared, set(tools.HANDLERS), "schemas and handlers have drifted apart")
        for s in schemas.ALL:
            self.assertTrue(s["description"].strip(), s["name"])
            self.assertIn("properties", s["parameters"], s["name"])
            for req in s["parameters"].get("required", []):
                self.assertIn(req, s["parameters"]["properties"], f"{s['name']}: required '{req}' is undeclared")

    def test_the_executable_schema_matches_the_written_contract(self):
        """`vault/schemas.py` mirrors `_CLAUDE.md` §4 — a type in one and not the other is a bug."""
        from second_brain.vault import schemas as vs
        brief = (REPO / "vault-starter" / "_CLAUDE.md").read_text(encoding="utf-8")
        for t, spec in vs.TYPES.items():
            self.assertIn(f"type: {t}", brief, f"type '{t}' is not documented in _CLAUDE.md")
            self.assertTrue((self.root / spec["folder"]).is_dir() or spec["folder"].startswith("06-knowledge"),
                            f"{t} -> {spec['folder']} does not exist in the starter vault")


if __name__ == "__main__":
    unittest.main()
