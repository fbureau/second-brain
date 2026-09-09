"""The `sb_vault` memory provider, against a stubbed Hermes runtime.

Hermes is not importable here, so `agent.memory_provider` is stubbed with the real contract's
shape (taken from hermes-agent's abstract base class). That is enough to check the two things
that actually matter and that a live session would only reveal late:

  1. the provider is **read-only** — a full turn cycle leaves the vault byte-identical;
  2. it never blocks or raises — a missing vault, a trivial prompt, or a broken contract
     import all degrade to an empty string rather than taking the session down.
"""
from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hermes" / "plugin"))

P = ("Scratch note for the memory-provider suite. It exists so passive recall can be checked "
     "for read-only behaviour and for graceful degradation when the vault is absent.")

TRIVIAL = re.compile(r"^(yes|no|ok|okay|sure|thanks|hi|hey|hello|continue|go ahead|done|k)[\s!?.:;,'\"]*$", re.I)


def _install_hermes_stub() -> None:
    """Minimal stand-in for `agent.memory_provider`, matching the upstream contract."""
    if "agent.memory_provider" in sys.modules:
        return
    agent = types.ModuleType("agent")
    mp = types.ModuleType("agent.memory_provider")

    class RecallStatus:
        def __init__(self, provider_label, count, glyph="🧠"):
            self.provider_label, self.count, self.glyph = provider_label, count, glyph

    class MemoryProvider:
        pre_compress_checkpoint_api_version = 1

        def is_available(self): return False
        def initialize(self, session_id, **kw): pass
        def system_prompt_block(self): return ""
        def prefetch(self, query, *, session_id=""): return ""
        def queue_prefetch(self, query, *, session_id=""): pass
        def recall_status(self): return None
        def sync_turn(self, u, a, **kw): pass
        def get_tool_schemas(self): return []
        def shutdown(self): pass

    def is_trivial_prompt(text):
        s = (text or "").strip()
        return not s or s.startswith("/") or bool(TRIVIAL.match(s))

    mp.MemoryProvider = MemoryProvider
    mp.RecallStatus = RecallStatus
    mp.is_trivial_prompt = is_trivial_prompt
    mp.INDICATOR_GLYPH = "🧠"
    mp.PRE_COMPRESS_CHECKPOINT_API_VERSION = 2
    agent.memory_provider = mp
    sys.modules["agent"], sys.modules["agent.memory_provider"] = agent, mp


_install_hermes_stub()
sys.path.insert(0, str(REPO / "hermes" / "memory"))
sb_vault = importlib.import_module("sb_vault")

from second_brain.vault import Vault  # noqa: E402


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True)


class Ctx:
    """The slice of Hermes' plugin context a memory provider touches."""

    def __init__(self, vault_path=None):
        self.provider = None
        self._vault_path = vault_path

    def get_config(self, key, default=None):
        return self._vault_path if key == "vault_path" else default

    def register_memory_provider(self, provider):
        self.provider = provider


class MemoryProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-mem-"))
        shutil.copytree(REPO / "vault-starter", self.tmp, dirs_exist_ok=True)
        git(self.tmp, "init", "-q"); git(self.tmp, "config", "user.email", "t@t"); git(self.tmp, "config", "user.name", "t")
        os.environ["SECOND_BRAIN_VAULT"] = str(self.tmp)
        v = Vault.locate()
        v.create_note("person", {"relationship": "peer"}, P,
                      {"Compiled truth": "- Alex Rivera runs the tier-1 support team."}, name="Alex Rivera")
        v.create_note("meeting", {"participants": ["[[02-people/Alex Rivera]]"], "meeting-type": "1-1"}, P,
                      {"Decisions": "We decided to centralize tier-1 support in Lisbon."}, slug="alex 1-1")
        git(self.tmp, "add", "-A"); git(self.tmp, "commit", "-qm", "seed")
        self.ctx = Ctx(str(self.tmp))
        sb_vault.register(self.ctx)
        self.p = self.ctx.provider
        self.p.initialize("session-1")

    def tearDown(self):
        self.p.shutdown()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("SECOND_BRAIN_VAULT", None)

    def _fingerprint(self) -> list[tuple[str, int, str]]:
        out = []
        for f in sorted(self.tmp.rglob("*.md")):
            if ".git" in f.parts:
                continue
            out.append((f.relative_to(self.tmp).as_posix(), f.stat().st_size,
                        f.read_text(encoding="utf-8")[:80]))
        return out

    # ------------------------------------------------------------------ recall
    def test_register_yields_a_provider_that_finds_the_vault(self):
        self.assertEqual(self.p.name, "sb_vault")
        self.assertTrue(self.p.is_available())
        self.assertIn("vault", self.p.system_prompt_block().lower())
        self.assertEqual(self.p.get_tool_schemas(), [])   # tools belong to the second_brain plugin

    def test_prefetch_injects_citations_for_a_real_question(self):
        block = self.p.prefetch("What did we decide about tier-1 support?", session_id="s1")
        self.assertIn("04-meetings/", block)
        self.assertIn("confidence", block)
        status = self.p.recall_status()
        self.assertIsNotNone(status)
        self.assertGreater(status.count, 0)

    def test_prefetch_is_silent_when_the_vault_has_nothing(self):
        self.assertEqual(self.p.prefetch("quantum key distribution roadmap", session_id="s1"), "")
        self.assertIsNone(self.p.recall_status())

    def test_trivial_prompts_never_trigger_recall(self):
        for junk in ("ok", "thanks", "hi!", "/braindump", "", "   "):
            self.assertEqual(self.p.prefetch(junk, session_id="s1"), "", junk)
        self.assertIsNone(self.p.recall_status())

    def test_queued_prefetch_is_consumed_by_the_next_turn(self):
        self.p.queue_prefetch("tier-1 support", session_id="s2")
        for t in list(self.p._threads):
            t.join(timeout=5)
        block = self.p.prefetch("tier-1 support", session_id="s2")
        self.assertIn("04-meetings/", block)
        self.assertEqual(self.p.prefetch("tier-1 support", session_id="other-session"), block)  # recomputed, same evidence

    def test_recall_status_never_reports_a_stale_count(self):
        self.p.prefetch("tier-1 support", session_id="s1")
        self.assertIsNotNone(self.p.recall_status())
        self.p.prefetch("quantum key distribution roadmap", session_id="s1")
        self.assertIsNone(self.p.recall_status())

    # ------------------------------------------------------------------ read-only
    def test_a_full_turn_cycle_writes_nothing(self):
        before = self._fingerprint()
        self.p.system_prompt_block()
        self.p.queue_prefetch("tier-1 support", session_id="s1")
        for t in list(self.p._threads):
            t.join(timeout=5)
        self.p.prefetch("tier-1 support", session_id="s1")
        self.p.sync_turn("What about tier-1?", "We centralized it in Lisbon.", session_id="s1")
        self.p.on_memory_write("add", "memory", "the user prefers Lisbon")
        self.p.on_session_end([{"role": "user", "content": "remember this"}])
        self.assertEqual(self._fingerprint(), before)
        self.assertEqual(git(self.tmp, "status", "--porcelain").stdout.strip(), "")

    def test_it_exposes_no_tools_of_its_own(self):
        out = self.p.handle_tool_call("anything", {})
        self.assertIn("second_brain", out)

    # ------------------------------------------------------------------ degradation
    def test_no_vault_means_unavailable_with_a_usable_reason(self):
        os.environ.pop("SECOND_BRAIN_VAULT", None)
        ctx = Ctx(str(self.tmp / "does-not-exist"))
        sb_vault.register(ctx)
        p = ctx.provider
        self.assertFalse(p.is_available())
        self.assertIn("SECOND_BRAIN_VAULT", p.unavailable_reason())
        p.initialize("s")
        self.assertEqual(p.prefetch("anything", session_id="s"), "")   # degrades, never raises
        p.queue_prefetch("anything", session_id="s")
        p.shutdown()

    def test_a_failing_recall_degrades_to_silence(self):
        broken = types.SimpleNamespace(recall=types.SimpleNamespace(
            prefetch_block=lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("disk on fire"))))
        original, self.p._contract = self.p._contract, broken
        try:
            self.assertEqual(self.p.prefetch("tier-1 support", session_id="s3"), "")
        finally:
            self.p._contract = original

    def test_config_schema_is_declared_for_hermes_memory_setup(self):
        fields = self.p.get_config_schema()
        self.assertEqual([f["key"] for f in fields], ["vault_path"])
        self.assertEqual(fields[0]["env_var"], "SECOND_BRAIN_VAULT")


if __name__ == "__main__":
    unittest.main()
