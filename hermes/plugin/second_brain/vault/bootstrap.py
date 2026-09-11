"""Create a vault from the starter bundled inside the plugin.

This exists so the whole thing can be installed from Hermes Desktop's plugin window and
work, with no terminal and no configuration. The starter travels inside the plugin
package (`second_brain/starter/`), so a plugin installed from a Git URL carries
everything it needs to scaffold a vault on first use.

Two rules it will not break:

- **It never writes into a directory that already holds notes.** If the target exists and
  is not an empty folder, it refuses and says so, rather than merging into someone's
  Obsidian vault.
- **It never runs on its own.** Creating a folder in someone's home is a decision, so it
  happens when the user asks, through `sb_setup`, not silently at session start.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .notes import VaultError

BRIEF_FILE = "_CLAUDE.md"
DEFAULT_DIR = "second-brain"
STARTER = Path(__file__).resolve().parent.parent / "starter"

# Keys `remember()` may return. Disjoint from `create()`'s on purpose: the tool merges both
# reports, and a shared key silently replaced one message with the other.
REMEMBER_KEYS = ("remembered", "env_file", "already_set", "remember_error", "remember_hint")


def default_path() -> Path:
    return Path.home() / DEFAULT_DIR


def starter_available() -> bool:
    return (STARTER / BRIEF_FILE).exists()


def _git(root: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, timeout=30)


def _init_git(root: Path) -> dict:
    """`git init` + first commit. The vault's history is its audit trail, so it is not optional."""
    try:
        if _git(root, "rev-parse", "--is-inside-work-tree").returncode == 0:
            return {"git": "already a repository"}
        if _git(root, "init", "-q").returncode != 0:
            return {"git": "could not initialise (is git installed?)"}
        _git(root, "add", "-A")
        res = _git(root, "-c", "user.email=you@example.com", "-c", "user.name=Second Brain",
                   "commit", "-qm", "Initial vault", "--no-verify")
        return {"git": "initialised" if res.returncode == 0 else "initialised, first commit failed"}
    except (OSError, subprocess.SubprocessError) as e:
        return {"git": f"unavailable ({type(e).__name__})"}


def _install_hook(root: Path) -> dict:
    """Copy the pre-commit hook when the plugin sits inside a checkout of the repo.

    A plugin installed from a URL has no `hooks/` next to it, so this is best-effort: the
    vault still works, it just loses the extra safety net. `setup.sh` installs it properly.
    """
    src = Path(__file__).resolve().parents[4] / "hooks" / "pre-commit"
    dst = root / ".git" / "hooks" / "pre-commit"
    if not src.exists() or not dst.parent.is_dir():
        return {"hook": "not installed (the plugin was installed without the repo; optional)"}
    try:
        shutil.copy(src, dst)
        dst.chmod(0o755)
        return {"hook": "installed — it refuses notes that break the AI-first rules"}
    except OSError as e:
        return {"hook": f"not installed ({e})"}


def create(path: str | None = None) -> dict:
    """Scaffold a vault at `path` (default `~/second-brain`) and report what happened."""
    if not starter_available():
        raise VaultError("the plugin is missing its bundled starter — reinstall it")
    target = Path(path).expanduser() if path else default_path()

    if (target / BRIEF_FILE).exists():
        return {"path": str(target), "created": False,
                "note": "a vault is already there — nothing was touched",
                "next": f"point the plugin at it: set vault_path to {target}, or export SECOND_BRAIN_VAULT"}
    if target.exists() and any(target.iterdir()):
        raise VaultError(f"{target} already contains files and is not a vault. Choose an empty folder, "
                         f"or pass the path of your existing vault instead of creating one.")

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(STARTER, target, dirs_exist_ok=True)
    report = {"path": str(target), "created": True,
              "folders": sorted(d.name for d in target.iterdir() if d.is_dir())}
    report.update(_init_git(target))
    report.update(_install_hook(target))
    report["profile"] = f"{target}/00-inbox/MY-PROFILE.md"
    report["next"] = (
        "Two things now. 1) Ask the user for their name, working language and main projects, then "
        f"write them into {report['profile']} with sb_append_section — every skill reads it. "
        "2) Tell them the vault path has been remembered, and that they can move the folder later by "
        "updating vault_path in the plugin settings."
    )
    return report


def remember(path: Path, hermes_home: Path | None = None) -> dict:
    """Persist the vault path so the next session finds it without any configuration.

    Written to `$HERMES_HOME/.env`, which both Hermes Desktop and the CLI read, because it
    is the one place a plugin can write without parsing someone's `config.yaml`.
    """
    home = hermes_home or Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
    env = home / ".env"
    try:
        home.mkdir(parents=True, exist_ok=True)
        existing = env.read_text(encoding="utf-8") if env.exists() else ""
        if f"SECOND_BRAIN_VAULT={path}" in existing:
            return {"remembered": True, "env_file": str(env), "already_set": True}
        kept = [l for l in existing.splitlines(keepends=True) if not l.startswith("SECOND_BRAIN_VAULT=")]
        env.write_text("".join(kept) + f"SECOND_BRAIN_VAULT={path}\n", encoding="utf-8")
        os.environ["SECOND_BRAIN_VAULT"] = str(path)   # effective immediately, not just next session
        return {"remembered": True, "env_file": str(env), "already_set": False}
    except OSError as e:
        return {"remembered": False, "remember_error": str(e),
                "remember_hint": f"set vault_path to {path} in the plugin settings instead"}
