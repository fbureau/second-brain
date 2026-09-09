"""`kickstart-backfill` as a work plan — the arithmetic in code, the ingestion in the model.

Day-1 backfill is the one operation where a small model reliably falls over: three months
of calendar and Drive is hundreds of items, far past any local context window, and a model
that loses its place mid-run creates duplicate people and half-written projects.

So the plan is computed here instead. This module turns a date range into ordered batches
small enough to survive one session each, tells the model which entities already exist so
it fuzzy-matches instead of creating, and records progress in the vault itself
(`00-inbox/_backfill-state.md`) so an interrupted run resumes rather than restarts.

It never ingests anything: fetching is the source tools' job, writing is `sb_create_note`'s.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from . import frontmatter, notes

STATE_FILE = "00-inbox/_backfill-state.md"
BATCH_DAYS = 14
ORDER = ["people", "projects", "meetings", "decisions", "knowledge"]
STATE_PREAMBLE = (
    "Progress record for the one-shot Day-1 backfill. It exists so an interrupted run resumes at the "
    "right batch instead of re-ingesting history and creating duplicates. Written by the backfill "
    "planner; safe to delete once the backfill is complete."
)


def _d(s) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def _existing(root: Path) -> dict:
    """What the vault already holds, so the model matches instead of creating duplicates."""
    out: dict[str, list[str]] = {"people": [], "projects": [], "meetings": [], "decisions": []}
    for folder, key in (("02-people", "people"), ("03-projects", "projects"),
                        ("04-meetings", "meetings"), ("05-decisions", "decisions")):
        base = root / folder
        if not base.is_dir():
            continue
        for p in sorted(base.glob("*.md")):
            if p.name in ("README.md", "_index.md"):
                continue
            out[key].append(p.stem)
    return out


def read_state(root: Path) -> dict:
    p = root / STATE_FILE
    if not p.exists():
        return {"exists": False, "done_batches": [], "started": None}
    fm, body = frontmatter.read(p.read_text(encoding="utf-8"))
    done = re.findall(r"- \[x\] (\S+)", body)
    return {"exists": True, "done_batches": done, "started": str(fm.get("date", "")),
            "range": str(fm.get("backfill-range", ""))}


def _write_state(root: Path, batches: list[dict], since: str, until: str) -> str:
    p = root / STATE_FILE
    prev = read_state(root)
    done = set(prev["done_batches"])
    lines = [f"- [{'x' if b['id'] in done else ' '}] {b['id']} — {b['phase']} · {b['since']} → {b['until']}"
             for b in batches]
    fm = {"date": notes.today(), "type": "braindump", "tags": ["braindump", "backfill"],
          "domain": "mixed", "energy": "medium", "backfill-range": f"{since}/{until}",
          "related-people": [], "related-projects": [], "ai-first": True}
    body = (f"{notes.PREAMBLE_HEADING}\n\n{STATE_PREAMBLE}\n\n"
            f"## Raw content\n\nBackfill batches for {since} → {until}. Tick a box when its batch is "
            f"fully ingested and committed.\n\n" + "\n".join(lines) + "\n")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(frontmatter.write(fm, body), encoding="utf-8")
    return STATE_FILE


def plan(root: Path, since: str, until: str | None = None, batch_days: int = BATCH_DAYS,
         sources: list[str] | None = None, write_state: bool = True) -> dict:
    """Ordered batches for a backfill over `since` → `until` (default: today).

    Batches run newest-first inside each phase: recent history is both better remembered
    and more useful, so an abandoned backfill still leaves the vault in a usable state.
    """
    start, end = _d(since), _d(until) if until else dt.date.today()
    if start is None:
        return {"error": f"invalid start date: {since!r} (expected YYYY-MM-DD)"}
    if end is None:
        return {"error": f"invalid end date: {until!r} (expected YYYY-MM-DD)"}
    if start > end:
        return {"error": f"start {since} is after end {end.isoformat()}"}
    span = (end - start).days
    if span > 400:
        return {"error": f"range spans {span} days; backfill is designed for 1-6 months — narrow it"}

    windows = []
    cursor = end
    while cursor > start:
        w_start = max(start, cursor - dt.timedelta(days=batch_days))
        windows.append((w_start, cursor))
        cursor = w_start
    if not windows:
        windows = [(start, end)]

    sources = sources or ["calendar", "drive", "slack"]
    existing = _existing(root)
    batches = []
    for phase in ORDER:
        if phase in ("people", "projects"):
            # entity phases run once over the whole range: they are the dedup foundation
            batches.append({"id": f"{phase}-all", "phase": phase, "since": start.isoformat(),
                            "until": end.isoformat(), "sources": sources,
                            "goal": {"people": "identify recurring participants and create person notes "
                                               "(ask before each creation, fuzzy-match first)",
                                     "projects": "identify recurring work threads and create project notes"}[phase]})
            continue
        for w_start, w_end in windows:
            batches.append({"id": f"{phase}-{w_start.isoformat()}", "phase": phase,
                            "since": w_start.isoformat(), "until": w_end.isoformat(), "sources": sources,
                            "goal": {"meetings": "ingest meetings that had a transcript or real substance; skip "
                                                 "status calls with no decision",
                                     "decisions": "record decisions that were actually made and are still live",
                                     "knowledge": "extract recurring lessons into 06-knowledge and build hubs"}[phase]})

    state = read_state(root)
    done = set(state["done_batches"])
    remaining = [b for b in batches if b["id"] not in done]
    state_path = _write_state(root, batches, start.isoformat(), end.isoformat()) if write_state else None

    return {
        "range": {"since": start.isoformat(), "until": end.isoformat(), "days": span},
        "batch_days": batch_days,
        "sources": sources,
        "batches": batches,
        "remaining": remaining,
        "resuming": bool(done),
        "done_count": len(done),
        "existing_entities": {k: len(v) for k, v in existing.items()},
        "known_people": existing["people"],
        "known_projects": existing["projects"],
        "state_note": state_path,
        "rules": [
            "One batch per session: a batch that does not fit is split, never rushed.",
            "Every backfilled note carries the (Backfilled) marker and `ingestion-mode: auto`.",
            "Never create a person without sb_find_person first, and ask the user before creating one.",
            "Dates come from the source, never from inference; when a date is unknown, write 'unknown'.",
            "Commit after each batch, then tick its box in the state note so a crash resumes here.",
        ],
        "next": (f"{len(remaining)} batch(es) left. Start with {remaining[0]['id']} if any, fetch its window "
                 f"from the configured sources, and stop at the end of the batch — do not run ahead."),
    }


def mark_batch_done(root: Path, batch_id: str) -> dict:
    """Tick a batch in the state note (the only write this module makes after planning)."""
    p = root / STATE_FILE
    if not p.exists():
        return {"error": "no backfill in progress — run the planner first"}
    fm, body = frontmatter.read(p.read_text(encoding="utf-8"))
    pattern = re.compile(r"^- \[ \] (" + re.escape(batch_id) + r")\b", re.M)
    if not pattern.search(body):
        return {"error": f"batch '{batch_id}' not found or already done", "batch": batch_id}
    body = pattern.sub(r"- [x] \1", body, count=1)
    fm["updated"] = notes.today()
    p.write_text(frontmatter.write(fm, body), encoding="utf-8")
    remaining = len(re.findall(r"- \[ \] ", body))
    return {"batch": batch_id, "marked": "done", "remaining": remaining, "state_note": STATE_FILE}
