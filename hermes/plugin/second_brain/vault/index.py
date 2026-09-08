"""Curator, incremental mode — the deterministic half of `knowledge-build` Mode C.1.

Adds a wiki / lesson / source doc to its domain hub listing (or to `_INDEX.md`
"Unsorted"), prepends a Recent-activity line, refreshes `_INDEX.md` counts.
Rewriting listing sections of `auto-maintained: true` hubs is allowed by the
contract; everything else is append-only.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import frontmatter, notes, schemas

LINK = re.compile(r"\[\[([^\]|#]+)")


def _links_in_section(lines: list[str], start: int, end: int) -> list[str]:
    return [m.group(1) for l in lines[start:end] for m in [LINK.search(l)] if m and l.lstrip().startswith("- ")]


def _replace_section_bullets(root: Path, rel: str, heading: str, bullets: list[str]) -> None:
    fm, body = notes.read_note(root, rel)
    lines = body.split("\n")
    b = notes._section_bounds(lines, heading)
    block = [f"## {heading}", ""] + bullets + [""]
    if b is None:
        cut = notes._footer_start(lines)
        lines = lines[:cut] + [""] + block + lines[cut:]
    else:
        lines = lines[: b[0]] + block + lines[b[1] :]
    notes._write(root / rel, fm, "\n".join(lines).rstrip("\n") + "\n")


def _one_liner(fm: dict, body: str, note_type: str) -> str:
    want = {"wiki": "Summary", "knowledge": "What we know", "doc": "Thesis"}.get(note_type, "Summary")
    lines = body.split("\n")
    b = notes._section_bounds(lines, want)
    if b:
        for l in lines[b[0] + 1 : b[1]]:
            s = l.strip().lstrip("-*[ ").rstrip("]")
            if s and not s.startswith("*Stub"):
                return s[:120]
    if note_type == "doc":
        return f"{fm.get('doc-type', 'doc')}, {fm.get('doc-date', 'unknown')}"
    return "stub — awaiting enrichment" if fm.get("needs-review") else ""


def _counts(root: Path) -> dict:
    c = {"wiki": 0, "knowledge": 0, "doc": 0, "index": 0}
    kdir = root / "06-knowledge"
    for p in kdir.rglob("*.md"):
        if p.name in ("README.md", "_INDEX.md"):
            continue
        fm, _ = frontmatter.read(p.read_text(encoding="utf-8"))
        t = fm.get("type")
        if t in c:
            c[t] += 1
    return c


def curator_incremental(root: Path, rel_path: str, action: str = "added") -> dict:
    fm, body = notes.read_note(root, rel_path)
    note_type = fm.get("type")
    if note_type not in schemas.HUB_SECTION_BY_TYPE:
        return {"skipped": True, "reason": f"type '{note_type}' is not routed by the curator"}
    domain = str(fm.get("domain") or "unsorted")
    link = rel_path[:-3] if rel_path.endswith(".md") else rel_path
    date = notes.today()
    result = {"path": rel_path, "domain": domain}
    index_rel = "06-knowledge/_INDEX.md"
    hub_rel = f"06-knowledge/{domain}.md"
    hub = root / hub_rel

    if domain != "unsorted" and hub.exists():
        hfm, hbody = notes.read_note(root, hub_rel)
        if hfm.get("type") == "index" and hfm.get("auto-maintained") in (True, "true"):
            section = schemas.HUB_SECTION_BY_TYPE[note_type]
            lines = hbody.split("\n")
            b = notes._section_bounds(lines, section)
            existing = _links_in_section(lines, *b) if b else []
            bullets = [l for l in (lines[b[0] + 1 : b[1]] if b else []) if l.lstrip().startswith("- [[")]
            if link not in existing:
                bullets.append(f"- [[{link}]] — {_one_liner(fm, body, note_type)}")
            bullets.sort(key=lambda s: s.lower())
            _replace_section_bullets(root, hub_rel, section, bullets)
            # Recent activity: newest first
            hfm, hbody = notes.read_note(root, hub_rel)
            lines = hbody.split("\n")
            b = notes._section_bounds(lines, "Recent activity")
            recent = [l for l in (lines[b[0] + 1 : b[1]] if b else []) if l.lstrip().startswith("- ")]
            recent = [f"- {date}: {action} [[{link}]]"] + recent[:19]
            _replace_section_bullets(root, hub_rel, "Recent activity", recent)
            hfm, hbody = notes.read_note(root, hub_rel)
            hfm["updated"] = date
            notes._write(hub, hfm, hbody)
            result.update({"hub": hub_rel, "listed_under": section})
        else:
            result.update({"hub": hub_rel, "listed_under": None, "note": "hub is not auto-maintained; left untouched"})
    else:
        if (root / index_rel).exists():
            section = "Unsorted (no domain)" if domain == "unsorted" else "Unsorted by domain"
            ifm, ibody = notes.read_note(root, index_rel)
            lines = ibody.split("\n")
            b = notes._section_bounds(lines, section)
            existing = _links_in_section(lines, *b) if b else []
            if link not in existing:
                suffix = "" if domain == "unsorted" else f" — `domain: {domain}`"
                notes.append_section(root, index_rel, section, [f"- [[{link}]]{suffix}"])
            result.update({"hub": None, "listed_under": f"_INDEX.md → {section}"})
        else:
            result.update({"hub": None, "listed_under": None, "note": "no _INDEX.md yet — run knowledge-build curator --bootstrap"})

    if (root / index_rel).exists():
        c = _counts(root)
        ifm, ibody = notes.read_note(root, index_rel)
        lines = ibody.split("\n")
        b = notes._section_bounds(lines, "Health")
        if b:
            for i in range(b[0] + 1, b[1]):
                if re.match(r"^- \d+ wiki pages", lines[i]):
                    lines[i] = f"- {c['wiki']} wiki pages · {c['knowledge']} lessons · {c['doc']} source docs · {c['index']} hubs."
                    break
        ifm["updated"] = date
        notes._write(root / index_rel, ifm, "\n".join(lines))
        result["index_counts"] = c
    return result
