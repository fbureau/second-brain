"""What changed in the vault recently — for the daily digest's "internal vault" source."""
from __future__ import annotations

import datetime as dt
import subprocess
import time
from pathlib import Path

from . import frontmatter

SKIP = {"README.md", "TODO.md", "_INDEX.md", "_CLAUDE.md", "AGENTS.md", "CLAUDE.md", "MY-PROFILE.md"}


def _git_changed(root: Path, since_hours: int) -> set[str] | None:
    try:
        res = subprocess.run(["git", "log", f"--since={since_hours} hours ago", "--name-only", "--pretty=format:"],
                             cwd=str(root), capture_output=True, text=True, timeout=20)
        if res.returncode != 0:
            return None
        return {l.strip() for l in res.stdout.splitlines() if l.strip().endswith(".md")}
    except (OSError, subprocess.SubprocessError):
        return None


def activity(root: Path, since_hours: int = 24, limit: int = 40) -> dict:
    cutoff = time.time() - since_hours * 3600
    date_cutoff = (dt.datetime.now() - dt.timedelta(hours=since_hours)).date().isoformat()
    changed = _git_changed(root, since_hours)
    items = []
    for p in root.rglob("*.md"):
        if ".obsidian" in p.parts or p.name in SKIP:
            continue
        rel = p.relative_to(root).as_posix()
        recent_git = changed is not None and rel in changed
        recent_fs = p.stat().st_mtime >= cutoff
        if not (recent_git or recent_fs):
            continue
        fm, _ = frontmatter.read(p.read_text(encoding="utf-8"))
        items.append({"path": rel, "type": fm.get("type", ""), "title": p.stem,
                      "modified": dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                      "new": bool(fm.get("date")) and str(fm.get("date", "")) >= date_cutoff})
    items.sort(key=lambda i: i["modified"], reverse=True)
    items = items[:limit]
    by_folder: dict[str, int] = {}
    for i in items:
        f = i["path"].split("/")[0]
        by_folder[f] = by_folder.get(f, 0) + 1
    lines = [f"- {i['modified']} [{i['type'] or 'note'}] [[{i['path'][:-3]}]]" + (" · new" if i["new"] else "") for i in items]
    return {"source": "vault", "since_hours": since_hours, "count": len(items), "by_folder": by_folder, "items": items,
            "text": "\n".join(lines) or "- no vault activity"}
