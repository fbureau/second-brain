"""Action-line convention and stable `^t-` anchors (see _CLAUDE.md section 7)."""
from __future__ import annotations

import random
import re
import string
from pathlib import Path

ANCHOR = re.compile(r"\^t-([a-z0-9]{6})\b")
_ALPHABET = string.ascii_lowercase + string.digits


def existing_anchors(vault_root: Path) -> set[str]:
    found: set[str] = set()
    for p in vault_root.rglob("*.md"):
        if ".obsidian" in p.parts:
            continue
        try:
            found.update(ANCHOR.findall(p.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):
            continue
    return found


def new_anchor(vault_root: Path, taken: set[str] | None = None) -> str:
    taken = taken if taken is not None else existing_anchors(vault_root)
    while True:
        a = "".join(random.choice(_ALPHABET) for _ in range(6))
        if a not in taken:
            taken.add(a)
            return a


def action_line(vault_root: Path, text: str, owner: str = "me", due: str | None = None,
                source_tag: str = "daily", anchor: str | None = None) -> str:
    """`- [ ] <text> — owner: me — due: YYYY-MM-DD — #from/<source> ^t-xxxxxx`"""
    text = text.strip().rstrip(".")
    parts = [f"- [ ] {text}", f"owner: {owner}"]
    if due:
        parts.append(f"due: {due}")
    parts.append(f"#from/{source_tag} ^t-{anchor or new_anchor(vault_root)}")
    return " — ".join(parts)
