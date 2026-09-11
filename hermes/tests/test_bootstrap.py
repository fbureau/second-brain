"""The zero-configuration install path: `sb_setup` creates a vault, and the plugin ships
everything it needs to do so.

These tests exist to protect a promise made to someone installing from Hermes Desktop's
plugin window: paste a URL, and it works. That promise breaks silently if the bundled
starter drifts from `vault-starter/`, or if the skills stop travelling with the package,
so both are asserted here rather than trusted.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "hermes" / "plugin" / "second_brain"
sys.path.insert(0, str(REPO / "hermes" / "plugin"))

from second_brain import schemas, tools  # noqa: E402
from second_brain.vault import Vault, bootstrap  # noqa: E402


def digest(root: Path) -> dict[str, str]:
    """Content fingerprint of a tree, so drift is reported per file rather than as a boolean."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            for p in sorted(root.rglob("*"))
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts}


class PackagingTests(unittest.TestCase):
    """What a Git-URL install actually receives."""

    def test_the_bundled_starter_matches_vault_starter_exactly(self):
        bundled, source = digest(PLUGIN / "starter"), digest(REPO / "vault-starter")
        missing = sorted(set(source) - set(bundled))
        extra = sorted(set(bundled) - set(source))
        changed = sorted(f for f in set(source) & set(bundled) if source[f] != bundled[f])
        self.assertEqual((missing, extra, changed), ([], [], []),
                         "hermes/plugin/second_brain/starter/ has drifted from vault-starter/ — "
                         "re-copy it so a plugin installed from a URL scaffolds the current contract")

    def test_the_skills_travel_inside_the_plugin(self):
        skills = sorted(p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 13, skills)
        self.assertIn("braindump", skills)
        self.assertIn("recall", skills)

    def test_the_plugin_declares_what_a_desktop_install_detects(self):
        """Hermes Desktop detects an agent plugin as plugin.yaml AND __init__.py."""
        self.assertTrue((PLUGIN / "plugin.yaml").exists())
        self.assertTrue((PLUGIN / "__init__.py").exists())

    def test_sb_setup_is_declared_and_handled(self):
        self.assertEqual([s["name"] for s in schemas.ALL_SETUP], ["sb_setup"])
        self.assertEqual({s["name"] for s in schemas.ALL}, set(tools.HANDLERS))


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-boot-"))
        self.home = self.tmp / "hermes-home"
        self.home.mkdir()
        self._env = {k: os.environ.get(k) for k in ("SECOND_BRAIN_VAULT", "HERMES_HOME")}
        os.environ["HERMES_HOME"] = str(self.home)
        os.environ.pop("SECOND_BRAIN_VAULT", None)
        tools.configure(lambda: None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in self._env.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def call(self, name, args):
        return json.loads(tools.HANDLERS[name](args))

    def test_setup_creates_a_working_vault(self):
        target = self.tmp / "my-brain"
        res = self.call("sb_setup", {"path": str(target)})
        self.assertTrue(res.get("created"), res)
        self.assertTrue((target / "_CLAUDE.md").exists())
        self.assertIn("02-people", res["folders"])
        self.assertIn("05-decisions", res["folders"])
        self.assertEqual(res["git"], "initialised")
        # the vault the plugin just made must satisfy the plugin's own contract
        v = Vault.locate(str(target))
        self.assertEqual(v.root, target.resolve())
        self.assertTrue(v.brief()["rules"])

    def test_the_created_vault_can_immediately_take_a_note(self):
        target = self.tmp / "usable"
        self.call("sb_setup", {"path": str(target)})
        tools.configure(lambda: str(target))
        res = self.call("sb_create_note", {
            "type": "braindump", "fields": {"domain": "professional", "energy": "medium"},
            "preamble": "First capture in a freshly scaffolded vault. It exists to prove the "
                        "zero-configuration install produces a vault the tools can write to.",
            "sections": {"Raw content": "The install worked."}, "slug": "first capture"})
        self.assertIn("path", res)
        self.assertTrue((target / res["path"]).exists())
        self.assertTrue(self.call("sb_commit", {"message": "first note"})["ok"])

    def test_setup_remembers_the_path_for_the_next_session(self):
        target = self.tmp / "remembered"
        res = self.call("sb_setup", {"path": str(target)})
        self.assertTrue(res["remembered"], res)
        self.assertIn(f"SECOND_BRAIN_VAULT={target}", (self.home / ".env").read_text(encoding="utf-8"))
        self.assertEqual(os.environ["SECOND_BRAIN_VAULT"], str(target))   # effective now, not next time

    def test_the_two_merged_reports_never_share_a_key(self):
        """sb_setup merges create() and remember(); a shared key silently ate a message once."""
        created = {"path", "created", "note", "next", "git", "folders", "hook", "profile"}
        self.assertFalse(set(bootstrap.REMEMBER_KEYS) & created)

    def test_remembering_twice_does_not_duplicate_the_line(self):
        target = self.tmp / "twice"
        self.call("sb_setup", {"path": str(target)})
        bootstrap.remember(target, self.home)
        bootstrap.remember(self.tmp / "other", self.home)
        lines = [l for l in (self.home / ".env").read_text(encoding="utf-8").splitlines()
                 if l.startswith("SECOND_BRAIN_VAULT=")]
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].endswith("other"))

    def test_setup_refuses_to_write_into_a_folder_that_holds_files(self):
        occupied = self.tmp / "my-obsidian"
        occupied.mkdir()
        (occupied / "Important note.md").write_text("years of work", encoding="utf-8")
        res = self.call("sb_setup", {"path": str(occupied)})
        self.assertIn("error", res)
        self.assertIn("already contains files", res["error"])
        self.assertEqual((occupied / "Important note.md").read_text(encoding="utf-8"), "years of work")
        self.assertEqual(sorted(p.name for p in occupied.iterdir()), ["Important note.md"])

    def test_setup_adopts_an_existing_vault_instead_of_clobbering_it(self):
        target = self.tmp / "existing"
        self.call("sb_setup", {"path": str(target)})
        marker = target / "02-people" / "Alex Rivera.md"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("---\ntype: person\n---\n\nkeep me\n", encoding="utf-8")
        res = self.call("sb_setup", {"path": str(target)})
        self.assertFalse(res["created"])
        self.assertIn("already there", res["note"])
        self.assertEqual(marker.read_text(encoding="utf-8"), "---\ntype: person\n---\n\nkeep me\n")

    def test_setup_defaults_to_the_home_directory_without_touching_it_here(self):
        self.assertEqual(bootstrap.default_path().name, "second-brain")
        self.assertEqual(bootstrap.default_path().parent, Path.home())

    def test_the_starter_ships_with_the_package(self):
        self.assertTrue(bootstrap.starter_available())


class GatingTests(unittest.TestCase):
    """With no vault, exactly one tool is offered — the one that fixes that."""

    class Ctx:
        def __init__(self):
            self.tools, self.skills, self.hooks = {}, [], {}

        def register_tool(self, name=None, toolset=None, schema=None, handler=None, check_fn=None, **kw):
            self.tools[name] = (toolset, check_fn)

        def register_skill(self, name, path, description="", frontmatter=None):
            self.skills.append(name)

        def register_hook(self, ev, cb):
            self.hooks[ev] = cb

        def get_config(self, key, default=None):
            return default

        def visible(self):
            return {n for n, (_, cf) in self.tools.items() if (cf() if cf else True)}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-gate-"))
        self._prev = os.environ.get("SECOND_BRAIN_VAULT")
        self._home = os.environ.get("HERMES_HOME")
        os.environ.pop("SECOND_BRAIN_VAULT", None)
        os.environ["HERMES_HOME"] = str(self.tmp / "hermes-home")
        self._cwd = os.getcwd()
        os.chdir(self.tmp)          # no _CLAUDE.md above this, so no vault resolves

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k, v in (("SECOND_BRAIN_VAULT", self._prev), ("HERMES_HOME", self._home)):
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def test_a_fresh_install_offers_only_sb_setup(self):
        import second_brain
        ctx = self.Ctx()
        second_brain.register(ctx)
        self.assertEqual(ctx.visible(), {"sb_setup"})

    def test_once_a_vault_exists_sb_setup_steps_aside(self):
        import second_brain
        vault = self.tmp / "v"
        bootstrap.create(str(vault))
        os.environ["SECOND_BRAIN_VAULT"] = str(vault)
        ctx = self.Ctx()
        second_brain.register(ctx)
        visible = ctx.visible()
        self.assertNotIn("sb_setup", visible)
        self.assertIn("sb_brief", visible)
        self.assertIn("sb_recall", visible)
        self.assertEqual(len(visible), len(schemas.ALL_VAULT))

    def test_the_plugin_registers_its_own_skills(self):
        import second_brain
        ctx = self.Ctx()
        second_brain.register(ctx)
        self.assertEqual(len(ctx.skills), 13, ctx.skills)
        self.assertIn("braindump", ctx.skills)

    def test_registration_never_raises_without_a_vault(self):
        import second_brain
        ctx = self.Ctx()
        second_brain.register(ctx)
        ctx.hooks["on_session_start"](session_id="s")      # must log, not explode


if __name__ == "__main__":
    unittest.main()
