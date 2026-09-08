"""Cheap, deterministic vault search — hub-first, frontmatter-aware, stdlib only.

Not semantic. Its job is to hand the model a short list of candidate notes with a
snippet each, so the model reads 3 notes instead of scanning 300.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import frontmatter

SKIP_DIRS = {".obsidian", ".git", ".trash"}
# System files describe the vault; they are never the answer to a recall question.
SKIP_FILES = {"README.md", "_CLAUDE.md", "AGENTS.md", "TODO.md", "MY-PROFILE.md"}
SKIP_TYPES = {"system-brief", "profile", "todo-dashboard"}
_WORD = re.compile(r"[a-zA-Z0-9À-ɏ][a-zA-Z0-9À-ɏ'-]+")


def _tokens(s: str) -> list[str]:
    return [t.lower() for t in _WORD.findall(s) if len(t) > 2]


def _iter_notes(root: Path, folder: str | None):
    base = root / folder if folder else root
    for p in sorted(base.rglob("*.md")):
        if SKIP_DIRS & set(p.parts) or p.name in SKIP_FILES:
            continue
        if folder is None and "07-archive" in p.parts:
            continue
        yield p


def search(root: Path, query: str, folder: str | None = None, note_type: str | None = None,
           limit: int = 8) -> list[dict]:
    terms = _tokens(query)
    if not terms:
        return []
    hub_domains = set()
    index = root / "06-knowledge" / "_INDEX.md"
    if index.exists():
        hub_domains = {m.lower() for m in re.findall(r"\[\[06-knowledge/([^\]/]+)\]\]", index.read_text(encoding="utf-8"))}

    results = []
    for p in _iter_notes(root, folder):
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm, body = frontmatter.read(text)
        if fm.get("type") in SKIP_TYPES or (note_type and fm.get("type") != note_type):
            continue
        rel = p.relative_to(root).as_posix()
        name_l = p.stem.lower()
        fm_blob = " ".join(str(v) for v in fm.values()).lower()
        headings = " ".join(l for l in body.split("\n") if l.startswith("#")).lower()
        body_l = body.lower()
        score = 0.0
        for t in terms:
            if t in name_l:
                score += 5
            if t in fm_blob:
                score += 3
            if t in headings:
                score += 2
            score += min(5, body_l.count(t)) * 0.6
        if score == 0:
            continue
        if fm.get("type") == "index" and p.stem.lower() in hub_domains and any(t in name_l for t in terms):
            score += 6  # hub-first: a matching domain hub is the best entry point
        snippet = ""
        for line in body.split("\n"):
            ll = line.lower()
            if any(t in ll for t in terms) and not line.startswith("#"):
                snippet = line.strip()[:200]
                break
        results.append({"path": rel, "type": fm.get("type", ""), "score": round(score, 1), "snippet": snippet})
    results.sort(key=lambda r: -r["score"])
    return results[:limit]
