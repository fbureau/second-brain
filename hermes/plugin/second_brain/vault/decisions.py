"""Evidence for `challenge-decision`, in both of its modes.

A red-team is only worth the turn if it argues from what actually happened here before.
So this module does the archaeology: it finds the decisions this one rhymes with, and
especially the ones that were **reversed**, because a reversal is the vault's cheapest
lesson. It also surfaces the stakeholders, the lessons filed in `06-knowledge`, and the
reversal conditions previous decisions committed to but never checked.

Two entry points:

    context(root, subject)      red-team: what the vault knows before you commit
    postmortem(root, rel_path)  learning loop: what a reversal invalidates elsewhere

Neither of them judges. `context` hands over prior art and open questions; `postmortem`
hands over the notes that rest on the same hypothesis. The argument is the model's job.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from . import frontmatter, links, notes, recall, search

DECISIONS = "05-decisions"
REVERSAL_SECTION = "Reversal conditions"
HYPOTHESIS_SECTIONS = ("Rationale", "Decision", "Context")


def _read(root: Path, rel: str):
    try:
        return frontmatter.read((root / rel).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}, ""


def _section(body: str, heading: str) -> str:
    lines = body.split("\n")
    b = notes._section_bounds(lines, heading)
    if not b:
        return ""
    return "\n".join(l for l in lines[b[0] + 1: b[1]] if l.strip()).strip()


def _all_decisions(root: Path) -> list[dict]:
    out = []
    base = root / DECISIONS
    for p in sorted(base.glob("*.md"), reverse=True) if base.is_dir() else []:
        if p.name in ("README.md", "_index.md"):
            continue
        fm, body = _read(root, f"{DECISIONS}/{p.name}")
        out.append({"path": f"{DECISIONS}/{p.name}", "title": p.stem, "fm": fm, "body": body,
                    "status": str(fm.get("status", "")), "reversibility": str(fm.get("reversibility", "")),
                    "date": str(fm.get("date", ""))})
    return out


def _overlap(a: str, b: str) -> float:
    ta, tb = set(recall._terms(a)), set(recall._terms(b))
    return len(ta & tb) / max(1, len(ta | tb))


def context(root: Path, subject: str, limit: int = 5) -> dict:
    """Prior art for a decision about to be made.

    Returns similar past decisions (reversed ones first — they are the cheap lessons),
    the stakeholders those decisions named, relevant lessons, unchecked reversal
    conditions, and the questions the vault suggests but cannot answer.
    """
    all_dec = _all_decisions(root)
    scored = []
    for d in all_dec:
        sim = max(_overlap(subject, d["title"]), _overlap(subject, d["body"][:2000]))
        if sim < 0.04:
            continue
        # a reversal that rhymes with this subject is worth more than a success that does
        weight = sim + (0.25 if d["status"] == "reversed" else 0.0) \
            + (0.1 if d["reversibility"] == "one-way" else 0.0)
        scored.append({"path": d["path"], "title": d["title"], "date": d["date"], "status": d["status"],
                       "reversibility": d["reversibility"], "similarity": round(sim, 3),
                       "weight": round(weight, 3),
                       "decision": _section(d["body"], "Decision")[:300],
                       "rationale": _section(d["body"], "Rationale")[:300],
                       "reversal_conditions": _section(d["body"], REVERSAL_SECTION)[:300]})
    scored.sort(key=lambda x: -x["weight"])
    similar = scored[:limit]

    reversed_ones = [d for d in scored if d["status"] == "reversed"][:limit]
    stakeholders: dict[str, list[str]] = {}
    for d in similar:
        fm, body = _read(root, d["path"])
        for link in links.wikilinks_in(body) + [str(x) for x in (fm.get("stakeholders") or [])]:
            t = link.strip("[]").strip()
            if t.startswith("02-people/"):
                rel = t if t.endswith(".md") else t + ".md"
                stakeholders.setdefault(rel, []).append(d["path"])

    lessons = [h for h in search.search(root, subject, folder="06-knowledge", limit=limit)
               if h["type"] in ("knowledge", "wiki")]

    unchecked = []
    for d in all_dec:
        if d["status"] not in ("committed", "implemented"):
            continue
        cond = _section(d["body"], REVERSAL_SECTION)
        if not cond or cond == "-":
            continue
        age = None
        try:
            age = (dt.date.today() - dt.date.fromisoformat(d["date"][:10])).days
        except (TypeError, ValueError):
            pass
        if age is not None and age >= 60:
            unchecked.append({"path": d["path"], "title": d["title"], "age_days": age,
                              "reversal_conditions": cond[:200]})
    unchecked.sort(key=lambda x: -x["age_days"])

    questions = []
    if not similar:
        questions.append("The vault holds no comparable decision. Say so — a red-team with no prior art "
                         "is an opinion, and should be labelled as one.")
    if reversed_ones:
        questions.append("A comparable decision was reversed: " + ", ".join(d["title"] for d in reversed_ones[:3])
                         + " — ask what is different this time, in one sentence.")
    if any(d["reversibility"] == "one-way" for d in similar):
        questions.append("Prior art includes a one-way decision — check whether this one can be made reversible "
                         "or staged instead.")
    if not lessons:
        questions.append("No lesson in 06-knowledge covers this. If the decision produces one, file it afterwards.")
    if unchecked[:1]:
        questions.append(f"{len(unchecked)} committed decision(s) have reversal conditions nobody has revisited; "
                         f"the oldest is {unchecked[0]['title']} ({unchecked[0]['age_days']}d).")

    return {
        "subject": subject,
        "similar_decisions": similar,
        "reversed_precedents": reversed_ones,
        "stakeholders": [{"path": k, "cited_in": v} for k, v in sorted(stakeholders.items())],
        "lessons": lessons,
        "unchecked_reversal_conditions": unchecked[:5],
        "questions": questions,
        "next": ("Argue against the decision using these notes, citing paths. Attack the reasoning, not the person. "
                 "If the evidence is thin, say the red-team is weak rather than inventing objections."),
    }


def postmortem(root: Path, rel_path: str) -> dict:
    """What a reversed decision invalidates elsewhere in the vault.

    Finds notes that link to it, notes that share its hypothesis language, and the people
    whose notes recorded a position on it — the propagation surface for the lesson.
    """
    try:
        target = notes.safe_path(root, rel_path)
    except notes.VaultError as e:
        return {"error": str(e)}
    if not target.exists():
        return {"error": f"note not found: {rel_path}"}
    fm, body = _read(root, rel_path)
    if fm.get("type") != "decision":
        return {"error": f"{rel_path} is type '{fm.get('type')}', not a decision"}

    hypothesis = " ".join(_section(body, h) for h in HYPOTHESIS_SECTIONS)[:1200]
    stem = Path(rel_path).stem
    inbound, resting = [], []
    for p in root.rglob("*.md"):
        rel = p.relative_to(root).as_posix()
        if rel == rel_path or ".obsidian" in p.parts or p.name == "TODO.md":
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        targets = [t.strip() for t in links.wikilinks_in(text)]
        if any(t == rel_path[:-3] or Path(t).stem == stem for t in targets):
            inbound.append(rel)
            continue
        nfm, nbody = frontmatter.read(text)
        if nfm.get("type") not in ("decision", "knowledge", "wiki", "project"):
            continue
        sim = _overlap(hypothesis, nbody[:2500])
        if sim >= 0.12:
            resting.append({"path": rel, "type": str(nfm.get("type", "")), "similarity": round(sim, 3),
                            "status": str(nfm.get("status", ""))})
    resting.sort(key=lambda x: -x["similarity"])

    people = sorted({t.strip() for t in links.wikilinks_in(body) if t.strip().startswith("02-people/")})
    timeline = _section(body, "Timeline (post-decision)")

    return {
        "decision": rel_path,
        "status": str(fm.get("status", "")),
        "date": str(fm.get("date", "")),
        "reversibility": str(fm.get("reversibility", "")),
        "decision_text": _section(body, "Decision")[:400],
        "rationale": _section(body, "Rationale")[:600],
        "reversal_conditions": _section(body, REVERSAL_SECTION)[:400],
        "post_decision_timeline": timeline[:800],
        "inbound_notes": sorted(inbound)[:20],
        "notes_resting_on_the_same_hypothesis": resting[:10],
        "stakeholders": people,
        "next": ("Name the lesson in one sentence, in the user's words, not a platitude. Then propose — do not "
                 "apply — an update for each listed note, and a knowledge note for the lesson. 05-decisions/ is "
                 "append-only: record the reversal with sb_append_timeline, never by editing the rationale."),
    }
