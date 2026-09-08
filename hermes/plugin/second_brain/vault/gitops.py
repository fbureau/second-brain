"""Commit vault changes — the repo's pre-commit hook is the final judge."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)


def is_repo(vault_root: Path) -> bool:
    return _run(["git", "rev-parse", "--is-inside-work-tree"], vault_root).returncode == 0


def commit(vault_root: Path, message: str) -> dict:
    if not is_repo(vault_root):
        return {"ok": False, "error": "vault is not a git repository (run git init + hooks/install.sh)"}
    _run(["git", "add", "-A"], vault_root)
    status = _run(["git", "status", "--porcelain"], vault_root).stdout.strip()
    if not status:
        return {"ok": True, "committed": False, "message": "nothing to commit"}
    res = _run(["git", "commit", "-m", message], vault_root)
    out = (res.stdout + res.stderr).strip()
    if res.returncode != 0:
        return {"ok": False, "error": "commit rejected (pre-commit hook or git error)", "output": out}
    sha = _run(["git", "rev-parse", "--short", "HEAD"], vault_root).stdout.strip()
    return {"ok": True, "committed": True, "sha": sha, "files": status.splitlines()}
