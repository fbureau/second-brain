"""`sb_vault` — the Second Brain vault as a Hermes memory provider.

Hermes' memory providers store what you said to the agent. This one does the opposite:
your **vault** is already the memory, so the provider never writes to it. It only reads,
so that a question like "what did we decide about the tiering?" arrives with the relevant
notes already in context, before the model spends a turn calling `sb_search`.

Deliberate design choices:

- **Read-only.** `sync_turn`, `on_session_end` and `on_memory_write` are no-ops. Notes are
  written only by the `second_brain` tools, through skills you invoked, so the append-only
  history stays an audit trail of decisions and not of chatter.
- **Never blocking.** `queue_prefetch` runs the retrieval on a background thread and
  `prefetch` returns whatever is ready. A slow disk delays nothing.
- **Evidence, not answers.** The injected block is a list of note paths with the lines that
  matched, so the model quotes and cites rather than paraphrasing from a summary.
- **No tools of its own.** The tools live in the `second_brain` plugin; a provider that
  registered a second recall tool would just give a small model two ways to do one thing.

Install: `hermes/install.sh` symlinks this into `$HERMES_HOME/plugins/sb_vault/`, then
`hermes config set memory.provider sb_vault`. Only one external provider is active at a time.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider, RecallStatus, is_trivial_prompt

logger = logging.getLogger(__name__)

PROVIDER_NAME = "sb_vault"
GLYPH = "🧠"
SYSTEM_BLOCK = (
    "Your long-term memory is the user's Second Brain vault of Markdown notes, not this chat. "
    "Vault excerpts may be injected below a turn: quote them and cite the note path. "
    "If the vault has nothing on a subject, say so rather than guessing — then offer to capture it "
    "with the second_brain tools. Never write to the vault except through those tools."
)


def _load_contract():
    """Import the `vault` contract package from the sibling `second_brain` plugin.

    Loaded by path under a private module name rather than `import second_brain.vault`:
    the tool plugin is itself loaded under a synthetic module name by Hermes, and importing
    it a second time here would give us a second copy of its state.
    """
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "second_brain" / "vault",                    # installed side by side in plugins/
        here.parents[1] / "plugin" / "second_brain" / "vault",     # repo layout (and symlinked installs)
        here.parent / "second_brain" / "second_brain" / "vault",
    ]
    env = os.environ.get("SECOND_BRAIN_PLUGIN")
    if env:
        candidates.insert(0, Path(env).expanduser() / "vault")
    for pkg in candidates:
        init = pkg / "__init__.py"
        if not init.exists():
            continue
        name = "_sb_vault_contract"
        if name in sys.modules:
            return sys.modules[name]
        spec = importlib.util.spec_from_file_location(name, str(init), submodule_search_locations=[str(pkg)])
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:  # a half-imported contract must not take the session down
            sys.modules.pop(name, None)
            logger.debug("sb_vault: could not import the vault contract from %s: %s", pkg, exc)
            continue
        return mod
    try:  # last resort: the package is importable on sys.path (tests, a pip install)
        return importlib.import_module("second_brain.vault")
    except Exception:
        return None


class SecondBrainVaultMemory(MemoryProvider):
    """Passive, read-only recall from the Second Brain vault."""

    def __init__(self, vault_path: Optional[str] = None, max_chars: int = 1400):
        self._configured_path = vault_path
        self._max_chars = max_chars
        self._contract = None
        self._vault = None
        self._lock = threading.Lock()
        self._pending: Dict[str, str] = {}          # session_id -> ready recall block
        self._counts: Dict[str, int] = {}
        self._last_status: Optional[RecallStatus] = None
        self._threads: List[threading.Thread] = []
        self._closing = False

    @property
    def name(self) -> str:
        return PROVIDER_NAME

    # -- lifecycle ---------------------------------------------------------
    def _resolve_vault(self):
        contract = self._contract or _load_contract()
        if contract is None:
            return None, None
        try:
            return contract, contract.Vault.locate(self._configured_path or os.environ.get("SECOND_BRAIN_VAULT"))
        except Exception as exc:
            logger.debug("sb_vault: vault not located: %s", exc)
            return contract, None

    def is_available(self) -> bool:
        contract, vault = self._resolve_vault()
        return vault is not None

    def unavailable_reason(self) -> str:
        if _load_contract() is None:
            return "the second_brain plugin is not installed next to sb_vault (run hermes/install.sh)"
        return ("no vault found — set SECOND_BRAIN_VAULT, or "
                "plugins.entries.second_brain.settings.vault_path in config.yaml")

    def initialize(self, session_id: str, **kwargs) -> None:
        self._contract, self._vault = self._resolve_vault()
        if self._vault is not None:
            logger.info("sb_vault memory: recalling from %s", self._vault.root)

    def shutdown(self) -> None:
        self._closing = True
        for t in list(self._threads):
            t.join(timeout=1.0)
        self._threads.clear()

    # -- recall ------------------------------------------------------------
    def system_prompt_block(self) -> str:
        return SYSTEM_BLOCK

    def _compute(self, query: str, session_id: str) -> None:
        try:
            block, count = self._contract.recall.prefetch_block(self._vault.root, query, self._max_chars)
        except Exception as exc:
            logger.debug("sb_vault prefetch failed: %s", exc)
            return
        if not block:
            return
        with self._lock:
            self._pending[session_id] = block
            self._counts[session_id] = count

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        if self._vault is None or self._closing or is_trivial_prompt(query):
            return
        t = threading.Thread(target=self._compute, args=(query, session_id), daemon=True,
                             name="sb-vault-prefetch")
        self._threads = [x for x in self._threads if x.is_alive()][-4:]
        self._threads.append(t)
        t.start()

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """Return the queued block; compute inline on the first turn, when nothing is queued yet."""
        if self._vault is None or is_trivial_prompt(query):
            self._last_status = None
            return ""
        with self._lock:
            block = self._pending.pop(session_id, "")
            count = self._counts.pop(session_id, 0)
        if not block:
            self._compute(query, session_id)
            with self._lock:
                block = self._pending.pop(session_id, "")
                count = self._counts.pop(session_id, 0)
        self._last_status = RecallStatus(provider_label="vault", count=count, glyph=GLYPH) if block else None
        return block

    def recall_status(self) -> Optional[RecallStatus]:
        return self._last_status

    # -- deliberately inert ------------------------------------------------
    def sync_turn(self, user_content: str, assistant_content: str, **kwargs) -> None:
        """No-op: the vault records decisions, not conversation. Capture goes through the skills."""

    def on_memory_write(self, action: str, target: str, content: str, metadata=None) -> None:
        """No-op for the same reason — a MEMORY.md write must not silently become a note."""

    def on_session_end(self, messages) -> None:
        """No-op: end-of-session extraction is exactly the "write behind your back" this avoids."""

    def on_pre_compress(self, messages) -> str:
        """Nothing to hand the summariser: the evidence it needs is already cited in the transcript."""
        return ""

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        return json.dumps({"error": f"{PROVIDER_NAME} exposes no tools; use the second_brain toolset"})

    # -- setup -------------------------------------------------------------
    def get_config_schema(self) -> List[Dict[str, Any]]:
        return [{
            "key": "vault_path",
            "description": "Absolute path to your Second Brain vault (the folder holding _CLAUDE.md)",
            "required": False,
            "type": "text",
            "env_var": "SECOND_BRAIN_VAULT",
        }]


def register(ctx) -> None:
    """Hermes plugin entry point."""
    vault_path = None
    try:
        vault_path = ctx.get_config("vault_path", default=None)
    except Exception:
        pass
    ctx.register_memory_provider(SecondBrainVaultMemory(vault_path=vault_path))
