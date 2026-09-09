"""Everything `prioritize` needs, in one call — assembled, never ranked.

Ranking is a judgment call: it depends on what the user is trying to achieve this week,
which of two overdue items actually blocks someone else, and how much a stale relationship
costs. That belongs to the model. What belongs to code is the gathering: which tasks are
open and when they are due, which projects are active and which have gone quiet, who has
not been contacted in a while, and what the vault has been busy with.

So this module returns a *dossier*, with the raw facts each item rests on, and a short
`signals` list naming the tensions the model should resolve.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from . import activity as activity_mod, frontmatter, maintain

HORIZON_DAYS = 7
QUIET_PROJECT_DAYS = 14
BLOCKED_MARKERS = ("blocked", "bloqué", "waiting on", "en attente")


def _d(s) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def _days(value) -> int | None:
    d = _d(value)
    return (dt.date.today() - d).days if d else None


def _task(t) -> dict:
    """A scanned task, flattened for the model — with where it came from, which is what
    makes it rankable ("the CEO asked" and "a note-to-self" are not the same task)."""
    return {"text": t.text, "due": t.due, "owner": t.owner, "waiting": t.waiting,
            "path": t.path, "note_type": t.note_type, "note_date": t.note_date,
            "anchor": t.anchor, "source_tag": t.source_tag,
            "link": f"[[{t.path[:-3]}" + (f"#^t-{t.anchor}]]" if t.anchor else "]]"),
            "reversibility": str(t.note_meta.get("reversibility", "")) if t.note_type == "decision" else "",
            "project_status": str(t.note_meta.get("status", "")) if t.note_type == "project" else ""}


def _projects(root: Path) -> list[dict]:
    out = []
    base = root / "03-projects"
    for p in sorted(base.glob("*.md")) if base.is_dir() else []:
        if p.name in ("README.md", "_index.md"):
            continue
        try:
            fm, body = frontmatter.read(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if str(fm.get("status")) in ("completed", "archived"):
            continue
        quiet = _days(fm.get("updated") or fm.get("date"))
        blocked = [l.strip().lstrip("-* ") for l in body.split("\n")
                   if any(m in l.lower() for m in BLOCKED_MARKERS)][:2]
        out.append({
            "path": p.relative_to(root).as_posix(),
            "name": p.stem,
            "status": str(fm.get("status", "")),
            "priority": str(fm.get("priority", "")),
            "updated": str(fm.get("updated") or fm.get("date") or ""),
            "quiet_days": quiet,
            "quiet": quiet is not None and quiet >= QUIET_PROJECT_DAYS,
            "blocked_notes": blocked,
        })
    out.sort(key=lambda x: (-(x["quiet_days"] or 0),))
    return out


def _people(root: Path) -> list[dict]:
    out = []
    base = root / "02-people"
    for p in sorted(base.glob("*.md")) if base.is_dir() else []:
        if p.name in ("README.md", "_index.md"):
            continue
        try:
            fm, _ = frontmatter.read(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        flag = str(fm.get("staleness-flag") or "")
        gap = _days(fm.get("last-interaction") or fm.get("updated"))
        if not flag and (gap is None or gap < 30):
            continue
        out.append({"path": p.relative_to(root).as_posix(), "name": p.stem,
                    "relationship": str(fm.get("relationship", "")), "days_since": gap,
                    "staleness_flag": flag})
    out.sort(key=lambda x: -(x["days_since"] or 0))
    return out


def agenda(root: Path, horizon_days: int = HORIZON_DAYS, calendar: list | None = None) -> dict:
    """Open work, active projects, cooling relationships and recent vault activity.

    `calendar` is an optional list of events (from `sb_calendar`) folded in as-is, so the
    model sees commitments and tasks side by side without a second round-trip.
    """
    today = dt.date.today()
    found, _scanned = maintain.scan_tasks(root)   # read-only: no anchors written, no TODO.md rewrite
    open_tasks = [_task(t) for t in found if not t.done and not t.mirror_of]

    overdue = [t for t in open_tasks if _d(t["due"]) and _d(t["due"]) < today and not t["waiting"]]
    due_today = [t for t in open_tasks if t["due"] == today.isoformat() and not t["waiting"]]
    soon = [t for t in open_tasks if _d(t["due"]) and not t["waiting"]
            and today < _d(t["due"]) <= today + dt.timedelta(days=horizon_days)]
    waiting = [t for t in open_tasks if t["waiting"]]
    undated = [t for t in open_tasks if not t["due"] and not t["waiting"]]

    projects = _projects(root)
    people = _people(root)
    recent = activity_mod.activity(root, since_hours=72, limit=15)

    signals = []
    if overdue:
        signals.append(f"{len(overdue)} task(s) are past their due date — decide: do, renegotiate, or drop.")
    if len(due_today) + len(soon) > 8:
        signals.append(f"{len(due_today) + len(soon)} task(s) land within {horizon_days} days — more than a "
                       "normal week holds; propose what to push.")
    quiet = [p for p in projects if p["quiet"]]
    if quiet:
        signals.append(f"{len(quiet)} active project(s) have not been touched in {QUIET_PROJECT_DAYS}+ days: "
                       + ", ".join(p["name"] for p in quiet[:4]))
    blocked = [p for p in projects if p["blocked_notes"]]
    if blocked:
        signals.append("blocked work is often someone else's decision — check whether a nudge unblocks: "
                       + ", ".join(p["name"] for p in blocked[:3]))
    if people:
        signals.append(f"{len(people)} relationship(s) are cooling; the oldest is "
                       f"{people[0]['name']} ({people[0]['days_since']} days).")
    if waiting:
        signals.append(f"{len(waiting)} item(s) are waiting on others — a follow-up is cheaper than a redo.")
    if not open_tasks:
        signals.append("no open tasks were found; check that TODO.md is in sync before concluding the list is empty.")

    return {
        "date": today.isoformat(),
        "horizon_days": horizon_days,
        "counts": {"overdue": len(overdue), "today": len(due_today), "soon": len(soon),
                   "waiting": len(waiting), "undated": len(undated), "open_total": len(open_tasks)},
        "tasks": {"overdue": overdue, "today": due_today, "soon": soon, "waiting": waiting,
                  "undated": undated[:20]},
        "projects": projects,
        "cooling_people": people,
        "calendar": calendar or [],
        "recent_activity": recent["items"][:10],
        "signals": signals,
        "next": ("Rank these yourself: nothing here is ordered. Weigh deadline, who is blocked, and the "
                 "user's stated priorities in MY-PROFILE.md. Then give a short plan with a first action."),
    }
