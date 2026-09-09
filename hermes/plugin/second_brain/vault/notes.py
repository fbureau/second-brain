"""Create and append to notes so that the AI-first contract cannot be violated.

Every write goes through here: frontmatter from the schema, mandatory
`## For future Claude` preamble, append-only on sensitive notes, dated entries.
Nothing in this module ever deletes or rewrites existing content.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from . import frontmatter, links, schemas

PREAMBLE_HEADING = "## For future Claude"
_H2 = re.compile(r"^## ")


class VaultError(Exception):
    pass


def today() -> str:
    return dt.date.today().isoformat()


def now_hhmm() -> str:
    return dt.datetime.now().strftime("%H%M")


# --------------------------------------------------------------------------- read

def safe_path(root: Path, rel_path: str) -> Path:
    """Resolve a vault-relative path, refusing anything that leaves the vault.

    A model that passes `/etc/passwd` or `../../notes.md` is confused rather than hostile,
    but the consequence is identical, so the contract refuses both — reads included, since
    a read is how content escapes into a reply.
    """
    raw = str(rel_path or "").strip()
    if not raw:
        raise VaultError("path is required (vault-relative, e.g. '02-people/Alex Rivera.md')")
    if raw.startswith(("/", "\\", "~")) or (len(raw) > 1 and raw[1] == ":"):
        raise VaultError(f"path must be vault-relative, not absolute: {raw}")
    root_r = root.resolve()
    try:
        resolved = (root / raw).resolve()
    except (OSError, RuntimeError):
        raise VaultError(f"invalid path: {raw}")
    if resolved != root_r and root_r not in resolved.parents:
        raise VaultError(f"path escapes the vault: {raw}")
    return resolved


def read_note(root: Path, rel_path: str) -> tuple[dict, str]:
    p = safe_path(root, rel_path)
    if not p.exists():
        raise VaultError(f"note not found: {rel_path}")
    return frontmatter.read(p.read_text(encoding="utf-8"))


def _write(p: Path, fm: dict, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(frontmatter.write(fm, body), encoding="utf-8")


# --------------------------------------------------------------------------- create

def _fill(v: Any) -> Any:
    if v == "{today}":
        return today()
    return v


def build_frontmatter(note_type: str, fields: dict) -> dict:
    if note_type not in schemas.TYPES:
        raise VaultError(f"unknown note type '{note_type}'; known: {', '.join(schemas.TYPES)}")
    spec = schemas.TYPES[note_type]
    fm: dict[str, Any] = {"date": fields.get("date") or today()}
    fm["type"] = note_type
    tags = list(fields.get("tags") or [])
    if spec["base_tag"] not in tags:
        tags.insert(0, spec["base_tag"])
    fm["tags"] = tags
    for k, v in spec.get("defaults", {}).items():
        fm[k] = _fill(fields.get(k, v))
    for k, v in fields.items():
        if k not in fm and k not in ("date", "type", "tags"):
            fm[k] = v
    missing = [k for k in spec["required"] if fm.get(k) in (None, "", [])]
    if missing:
        raise VaultError(f"type '{note_type}' requires fields: {', '.join(missing)}")
    for k, allowed in spec.get("enums", {}).items():
        if k in fm and fm[k] not in ("", None) and str(fm[k]) not in allowed:
            raise VaultError(f"{k}='{fm[k]}' not allowed; use one of: {' | '.join(allowed)}")
    fm["ai-first"] = True
    return fm


def note_path(root: Path, note_type: str, fm: dict, slug: str | None = None, name: str | None = None) -> Path:
    spec = schemas.TYPES[note_type]
    ctx = {
        "date": fm["date"],
        "hhmm": now_hhmm(),
        "slug": links.slugify(slug or name or fm.get("title", "") or "note"),
        "name": (name or slug or "Unnamed").strip(),
    }
    return root / spec["folder"] / spec["filename"].format(**ctx)


def create_note(root: Path, note_type: str, fields: dict, preamble: str, sections: dict[str, str] | None = None,
                slug: str | None = None, name: str | None = None) -> dict:
    """Write a new note. Refuses to overwrite. Returns {path, missing_links}."""
    preamble = (preamble or "").strip()
    if len(preamble) < 40:
        raise VaultError("preamble too short: 2-3 English sentences (what / why / when) are required")
    fm = build_frontmatter(note_type, fields or {})
    p = note_path(root, note_type, fm, slug=slug, name=name)
    if p.exists():
        raise VaultError(f"note already exists: {p.relative_to(root).as_posix()} (append instead of creating)")
    spec = schemas.TYPES[note_type]
    sections = sections or {}
    body = [PREAMBLE_HEADING, "", preamble, ""]
    ordered = list(spec["sections"]) + [h for h in sections if h not in spec["sections"]]
    for h in ordered:
        content = (sections.get(h) or "").strip()
        if not content and note_type != "daily":
            continue
        body += [f"## {h}", "", content or "-", ""]
    text = "\n".join(body).rstrip() + "\n"
    _write(p, fm, text)
    rel = p.relative_to(root).as_posix()
    return {"path": rel, "missing_links": links.missing_links(root, text)}


# --------------------------------------------------------------------------- append

def _section_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    """(start_idx_of_heading, end_idx_exclusive) for `## heading`, else None."""
    target = f"## {heading}".strip().lower()
    start = None
    for i, l in enumerate(lines):
        if l.strip().lower() == target:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _H2.match(lines[j]):
            end = j
            break
    return start, end


def _footer_start(lines: list[str]) -> int:
    """Index where a trailing nav footer (`---` then `→ Previous/Next`) starts, else len."""
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "---" and any(l.lstrip().startswith("→") for l in lines[i + 1 :]):
            return i
    return len(lines)


def append_section(root: Path, rel_path: str, heading: str, new_lines: list[str], create: bool = True) -> dict:
    """Append lines at the end of `## heading` (created at the end if missing). Never edits existing lines."""
    fm, body = read_note(root, rel_path)
    lines = body.split("\n")
    new_lines = [l.rstrip() for l in new_lines if l is not None]
    bounds = _section_bounds(lines, heading)
    if bounds is None:
        if not create:
            raise VaultError(f"section '## {heading}' not found in {rel_path}")
        cut = _footer_start(lines)
        head = "\n".join(lines[:cut]).rstrip("\n")
        foot = "\n".join(lines[cut:]).strip("\n")
        body = head + f"\n\n## {heading}\n\n" + "\n".join(new_lines) + "\n" + (f"\n{foot}\n" if foot else "")
    else:
        start, end = bounds
        seg = lines[start:end]
        while seg and not seg[-1].strip():
            seg.pop()
        # drop a lone scaffold placeholder ("-" or "[...]") when real content arrives
        if len(seg) >= 2 and seg[-1].strip() in ("-", "") or (len(seg) >= 2 and seg[-1].startswith("[") and seg[-1].endswith("]")):
            if len(seg) == 2 or all(not s.strip() for s in seg[1:-1]):
                seg = seg[:1]
        seg = seg + ([""] if len(seg) == 1 else []) + new_lines + [""]
        body = "\n".join(lines[:start] + seg + lines[end:])
    _write(safe_path(root, rel_path), fm, body.rstrip("\n") + "\n")
    return {"path": rel_path, "section": heading, "appended": len(new_lines)}


def append_timeline(root: Path, rel_path: str, title: str, lines: list[str], date: str | None = None,
                    marker: str | None = None) -> dict:
    """Append a dated `### YYYY-MM-DD — title` entry under `## Timeline` (append-only zone friendly).

    Also stamps `updated:` and, for people, `last-interaction:` and clears `staleness-flag`.
    """
    date = date or today()
    fm, _ = read_note(root, rel_path)
    header = f"### {date} — {title.strip()}" + (f" {marker}" if marker else "")
    entry = ["", header] + [l if l.startswith(("-", "  ")) else f"- {l}" for l in lines if l.strip()]
    res = append_section(root, rel_path, "Timeline", entry)
    fm, body = read_note(root, rel_path)
    if "updated" in fm or fm.get("type") in ("person", "project"):
        fm["updated"] = date
    if fm.get("type") == "person":
        fm["last-interaction"] = date
        if fm.get("staleness-flag"):
            fm["staleness-flag"] = ""
    _write(safe_path(root, rel_path), fm, body)
    res.update({"entry": header})
    return res


def ensure_daily(root: Path, date: str | None = None) -> str:
    date = date or today()
    rel = f"01-daily/{date}.md"
    if not (root / rel).exists():
        create_note(root, "daily", {"date": date},
                    f"Daily note for {date}. Created by the second-brain plugin the first time a skill "
                    f"appended to it; the daily-brief fills in the synthesis sections later.")
    return rel


def daily_append(root: Path, section: str, line: str, date: str | None = None) -> dict:
    rel = ensure_daily(root, date)
    return append_section(root, rel, section, [line])
