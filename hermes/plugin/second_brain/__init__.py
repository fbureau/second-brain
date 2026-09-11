"""Hermes Agent plugin: Second Brain vault tools.

Self-contained on purpose. The skills live in `skills/` and the vault template in
`starter/`, both inside this package, so installing the plugin from Hermes Desktop's
plugin window (a Git URL) brings everything with it — no terminal, no copying, no
configuration file to edit by hand.

Vault location, in order:
  1. config.yaml → plugins.entries.second_brain.settings.vault_path
  2. environment  → SECOND_BRAIN_VAULT (this is where `sb_setup` records its answer)
  3. the current working directory, or a parent, containing `_CLAUDE.md`

When none of those resolves, every tool hides itself except `sb_setup`, which creates the
vault. So a fresh install is never a dead end: the model always has exactly one thing it
can do, and the user never sees a toolset that errors on every call.

Nothing Hermes-specific is imported at module level, so the `vault` package stays usable
(and testable) outside Hermes.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from . import schemas, tools
from .vault import ENV_VAR, Vault, VaultError

TOOLSET = "second_brain"
SOURCES_TOOLSET = "second_brain_sources"
SKILLS_DIR = Path(__file__).resolve().parent / "skills"
log = logging.getLogger("second_brain")


def _register_own_skills(ctx) -> int:
    """Publish the bundled skills so they travel with the plugin.

    Registered with their own frontmatter, because the description is what makes a skill
    trigger and it has to survive the trip.
    """
    if not SKILLS_DIR.is_dir():
        return 0
    registered = 0
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        name = skill_md.parent.name
        fm, description = {}, ""
        try:
            text = skill_md.read_text(encoding="utf-8")
            if text.startswith("---"):
                import yaml
                fm = yaml.safe_load(text.split("---", 2)[1]) or {}
                description = str(fm.get("description", ""))
        except Exception as e:  # a malformed skill must not cost us the whole plugin
            log.debug("second_brain: could not read %s: %s", skill_md, e)
        try:
            ctx.register_skill(name, skill_md, description=description, frontmatter=fm)
            registered += 1
        except Exception as e:
            log.debug("second_brain: could not register skill '%s': %s", name, e)
    return registered


def _advertise_skills_dir() -> None:
    """Link the bundled skills into `$HERMES_HOME/skills` so they are addressable by name.

    A plugin-registered skill resolves as `second_brain:<name>`; Hermes auto-loads the ones
    under its own skills directory, which is what makes `/braindump` work. A symlink rather
    than a copy, so updating the plugin updates the skills. Best-effort: the registrations
    above still work if this fails (Windows without developer mode, a read-only home).
    """
    home = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
    target = home / "skills" / "second-brain"
    try:
        if target.is_symlink() and target.resolve() == SKILLS_DIR:
            return
        if target.exists() and not target.is_symlink():
            return  # a real directory someone put there; leave it alone
        target.parent.mkdir(parents=True, exist_ok=True)
        target.unlink(missing_ok=True)
        target.symlink_to(SKILLS_DIR, target_is_directory=True)
        log.info("second_brain: skills linked into %s", target)
    except OSError as e:
        log.debug("second_brain: could not link skills into %s: %s", target, e)


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

    # sb_setup is the one tool that must be visible when there is no vault yet — it is what
    # creates one. Hidden once a vault exists, so it cannot be called by accident later.
    for schema in schemas.ALL_SETUP:
        ctx.register_tool(name=schema["name"], toolset=TOOLSET, schema=schema,
                          handler=tools.HANDLERS[schema["name"]],
                          check_fn=lambda: not vault_available())

    for schema in schemas.ALL_VAULT:
        ctx.register_tool(name=schema["name"], toolset=TOOLSET, schema=schema,
                          handler=tools.HANDLERS[schema["name"]], check_fn=vault_available)

    # Source digests live in their own toolset and hide themselves when credentials are absent.
    for schema in schemas.ALL_SOURCES:
        kind = tools.SOURCE_ENV[schema["name"]]
        ctx.register_tool(name=schema["name"], toolset=SOURCES_TOOLSET, schema=schema,
                          handler=tools.HANDLERS[schema["name"]],
                          check_fn=(lambda k=kind: vault_available() and tools.source_available(k)))

    _register_own_skills(ctx)
    _advertise_skills_dir()

    def on_session_start(session_id=None, model=None, platform=None, **kwargs):
        try:
            v = Vault.locate(vault_path())
            log.info("second_brain: vault %s (lang=%s)", v.root, v.working_language())
        except VaultError:
            from .vault import bootstrap
            log.info("second_brain: no vault yet — sb_setup will create one at %s", bootstrap.default_path())

    ctx.register_hook("on_session_start", on_session_start)
