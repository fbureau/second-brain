"""`vault-tend` as a preview engine — detection in code, decisions with the user.

Whole-vault maintenance is where an over-eager agent does the most damage: a "cleanup"
that rewrites a person note, or a "deduplication" that merges two real people with the
same first name. So this module never touches anything unless it is asked to, and even
then only for the handful of repairs that are safe by construction.

Two tiers, and the split is the whole point:

    safe        frontmatter gaps that have one correct value (`ai-first: true`, a `date`
                recoverable from the filename, a missing base tag). Applied on request.
    proposals   language drift, missing preambles, broken wikilinks, duplicate people,
                archive candidates. Reported, never applied — each one needs a human
                or at least a model that read the note.

Nothing here deletes, and nothing here writes inside `02-people/` or `05-decisions/`
beyond frontmatter keys the contract fixes.
"""
from __future__ import annotations

import datetime as dt
import difflib
import re
from pathlib import Path

from . import frontmatter, links, notes, schemas

SKIP_FILES = {"README.md", "TODO.md", "_CLAUDE.md", "AGENTS.md", "CLAUDE.md"}
SKIP_DIRS = {".obsidian", ".git", ".trash"}
ARCHIVE_AFTER_DAYS = 365
PREAMBLE = "## For future Claude"
# Function words that are frequent enough to identify a note's language from a few lines.
LANG_MARKERS = {
    "fr": (" le ", " la ", " les ", " des ", " une ", " est ", " nous ", " pour ", " avec ", " que ", " qui "),
    "en": (" the ", " and ", " with ", " that ", " this ", " for ", " was ", " we ", " has ", " are "),
    "es": (" el ", " los ", " las ", " una ", " para ", " con ", " que ", " este ", " son "),
}


def _detect_language(text: str) -> str:
    t = " " + re.sub(r"\s+", " ", text.lower()) + " "
    scores = {lang: sum(t.count(m) for m in markers) for lang, markers in LANG_MARKERS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] >= 3 else "unknown"


def _iter(root: Path):
    for p in sorted(root.rglob("*.md")):
        if SKIP_DIRS & set(p.parts) or p.name in SKIP_FILES:
            continue
        yield p


def _age(value) -> int | None:
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(value)[:10])).days
    except (TypeError, ValueError):
        return None


def _safe_frontmatter_fixes(fm: dict, rel: str, name: str) -> dict:
    """Frontmatter keys with exactly one correct value. Anything judgement-shaped stays out."""
    fixes = {}
    if fm.get("ai-first") is not True:
        fixes["ai-first"] = True
    if not fm.get("date"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
        if m:
            fixes["date"] = m.group(1)
    t = fm.get("type")
    if t in schemas.TYPES:
        base = schemas.TYPES[t]["base_tag"]
        tags = fm.get("tags")
        tags = list(tags) if isinstance(tags, list) else ([tags] if tags else [])
        if base not in tags:
            fixes["tags"] = [base] + tags
    return fixes


def tend(root: Path, scope: str = "all", apply_safe: bool = False, target_language: str | None = None) -> dict:
    """Audit the whole vault. `scope`: all | frontmatter | language | links | duplicates | archive.

    With `apply_safe=True`, only the `safe` tier is written. Everything else comes back as
    a proposal carrying the evidence the model needs to decide.
    """
    want = {"all", scope}
    report: dict = {"scope": scope, "applied_safe": bool(apply_safe), "scanned": 0,
                    "safe_fixes": [], "proposals": [], "counts": {}}
    people_names: list[tuple[str, str]] = []
    notes_seen: list[dict] = []

    for p in _iter(root):
        rel = p.relative_to(root).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        report["scanned"] += 1
        fm, body = frontmatter.read(text)
        ntype = str(fm.get("type", ""))
        notes_seen.append({"rel": rel, "fm": fm, "type": ntype})

        if {"all", "frontmatter"} & want:
            fixes = _safe_frontmatter_fixes(fm, rel, p.name)
            if fixes:
                if apply_safe:
                    fm2 = dict(fm)
                    fm2.update(fixes)
                    p.write_text(frontmatter.write(fm2, body), encoding="utf-8")
                report["safe_fixes"].append({"path": rel, "fixes": fixes, "written": bool(apply_safe)})
            if not fm.get("type"):
                report["proposals"].append({"kind": "no-type", "path": rel,
                                            "question": "no `type:` — classify it or move it to 00-inbox/"})

        if {"all", "language"} & want:
            if PREAMBLE not in body:
                report["proposals"].append({"kind": "missing-preamble", "path": rel,
                                            "question": "no '## For future Claude' preamble — write 2-3 English "
                                                        "sentences (what / why / when) at the top"})
            else:
                head = body.split(PREAMBLE, 1)[1][:400]
                if _detect_language(head) not in ("en", "unknown"):
                    report["proposals"].append({"kind": "preamble-not-english", "path": rel,
                                                "detected": _detect_language(head),
                                                "question": "the preamble must be English even when the body is not"})
            if target_language:
                lang = _detect_language(body[:2500])
                if lang not in (target_language, "unknown"):
                    report["proposals"].append({"kind": "body-language", "path": rel, "detected": lang,
                                                "target": target_language,
                                                "question": f"body reads as '{lang}'; re-language to "
                                                            f"'{target_language}' preserving quotes verbatim"})

        if {"all", "links"} & want:
            broken = links.missing_links(root, body)
            if broken:
                report["proposals"].append({"kind": "broken-links", "path": rel, "targets": broken[:8],
                                            "question": "create stubs, fix the spelling, or drop the link — "
                                                        "check for a near-miss before creating anything"})

        if ntype == "person":
            people_names.append((rel, p.stem))

        if {"all", "archive"} & want and "07-archive" not in p.parts:
            age = _age(fm.get("updated") or fm.get("date"))
            status = str(fm.get("status", ""))
            if status in ("completed", "archived") or (age is not None and age > ARCHIVE_AFTER_DAYS
                                                       and ntype in ("project", "meeting", "braindump")):
                report["proposals"].append({"kind": "archive-candidate", "path": rel, "age_days": age,
                                            "status": status,
                                            "question": "move to 07-archive/ (never delete) — confirm first"})

    if {"all", "duplicates"} & want:
        for i, (rel_a, a) in enumerate(people_names):
            for rel_b, b in people_names[i + 1:]:
                ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
                shared_first = a.split()[:1] == b.split()[:1] and len(a.split()) != len(b.split())
                if ratio >= 0.82 or shared_first:
                    report["proposals"].append({
                        "kind": "duplicate-people", "paths": [rel_a, rel_b], "similarity": round(ratio, 3),
                        "question": "same person or two people? Read both timelines before merging; a merge is "
                                    "append-only (copy entries into the survivor, archive the other)."})
        stems: dict[str, list[str]] = {}
        for n in notes_seen:
            if n["type"] in ("wiki", "knowledge"):
                stems.setdefault(Path(n["rel"]).stem.lower(), []).append(n["rel"])
        for stem, rels in stems.items():
            if len(rels) > 1:
                report["proposals"].append({"kind": "duplicate-knowledge", "paths": rels, "stem": stem,
                                            "question": "two knowledge notes share a name — merge into one wiki "
                                                        "page and leave a pointer"})

    kinds: dict[str, int] = {}
    for pr in report["proposals"]:
        kinds[pr["kind"]] = kinds.get(pr["kind"], 0) + 1
    report["counts"] = {"safe_fixes": len(report["safe_fixes"]), "proposals": len(report["proposals"]), **kinds}
    report["next"] = ("Nothing in `proposals` has been applied. Show the user a grouped preview, ask for a go on each "
                      "group, then apply in batches with one commit per batch. Never delete a note: archive it.")
    return report
