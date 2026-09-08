"""Hermes Agent plugin: Second Brain vault tools.

Registered under the `second_brain` toolset. Vault location, in order:
  1. config.yaml → plugins.entries.second_brain.settings.vault_path
  2. environment  → SECOND_BRAIN_VAULT
  3. the current working directory (or a parent) containing `_CLAUDE.md`

Nothing Hermes-specific is imported at module level, so the `vault` package stays
usable (and testable) outside Hermes.
"""
from __future__ import annotations

import logging
import os

from . import schemas, tools
from .vault import ENV_VAR, Vault, VaultError

TOOLSET = "second_brain"
SOURCES_TOOLSET = "second_brain_sources"
log = logging.getLogger("second_brain")


def register(ctx) -> None:
    def vault_path() -> str | None:
        try:
            configured = ctx.get_config("vault_path", default=None)
        except Exception:  # older/newer ctx without get_config
            configured = None
        return configured or os.environ.get(ENV_VAR) or None

    tools.configure(vault_path)

    def vault_available() -> bool:
        try:
            Vault.locate(vault_path())
            return True
        except VaultError:
            return False

    for schema in schemas.ALL_VAULT:
        ctx.register_tool(name=schema["name"], toolset=TOOLSET, schema=schema,
                          handler=tools.HANDLERS[schema["name"]], check_fn=vault_available)

    # Source digests live in their own toolset and hide themselves when credentials are absent.
    for schema in schemas.ALL_SOURCES:
        kind = tools.SOURCE_ENV[schema["name"]]
        ctx.register_tool(name=schema["name"], toolset=SOURCES_TOOLSET, schema=schema,
                          handler=tools.HANDLERS[schema["name"]],
                          check_fn=(lambda k=kind: vault_available() and tools.source_available(k)))

    def on_session_start(session_id=None, model=None, platform=None, **kwargs):
        try:
            v = Vault.locate(vault_path())
            log.info("second_brain: vault %s (lang=%s)", v.root, v.working_language())
        except VaultError as e:
            log.warning("second_brain: %s — tools hidden until a vault is configured", e)

    ctx.register_hook("on_session_start", on_session_start)
