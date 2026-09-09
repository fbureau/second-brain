"""Deterministic retrieval with citations — the evidence half of `recall`.

The model still writes the answer. This module only decides *what to read*: it resolves
entities mentioned in the question against the vault's own index, scores candidate notes,
pulls the lines that actually match, and attaches a path + date to every one of them.

`confidence` here is about **evidence**, never about truth:

    stated       a matching line was found in an append-only note (people/decisions)
    high         several independent notes agree on the entity, recent
    medium       one note matches, or the matches are old
    speculation  only weak/keyword-level matches
    unknown      nothing matched — the honest answer is "the vault does not know"

The same engine feeds the `sb_vault` memory provider's passive prefetch, so a passive
recall and an explicit `/recall` see exactly the same evidence.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from . import frontmatter, search

# Question scaffolding carries no retrieval signal; dropping it keeps short questions sharp.
STOPWORDS = {
    "what", "who", "when", "where", "which", "why", "how", "did", "do", "does", "is", "are", "was", "were",
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "about", "with", "from", "that", "this",
    "know", "knew", "tell", "say", "said", "remind", "remember", "confirm", "find", "search", "vault", "note",
    "quest", "ce", "que", "qui", "quoi", "quand", "est", "sont", "les", "des", "une", "aux", "avec", "pour",
    "dans", "sur", "nous", "vous", "avons", "avait", "dit", "sait", "savons", "rappelle", "propos",
}
_WORD = re.compile(r"[a-zA-Z0-9À-ɏ][a-zA-Z0-9À-ɏ'-]+")
_CAP = re.compile(r"\b([A-ZÀ-Þ][a-zà-ÿ'’-]+(?:\s+[A-ZÀ-Þ][a-zà-ÿ'’-]+)*)")
APPEND_ONLY = ("02-people/", "05-decisions/")
RECENT_DAYS = 120


def _flat(s: str) -> str:
    """Fold a slug and a spoken name onto the same form: `onboarding-refresh` == `Onboarding Refresh`."""
    return re.sub(r"[-_]+", " ", s).strip().lower()


def _terms(question: str) -> list[str]:
    return [t.lower() for t in _WORD.findall(question) if len(t) > 2 and t.lower() not in STOPWORDS]


def entities(root: Path, question: str, limit: int = 6) -> list[dict]:
    """Vault entities the question mentions: people, projects, and knowledge hubs.

    Matched against note stems and frontmatter aliases, so "Alex" finds `Alex Rivera`
    and an alias in a wiki page finds the page. Capitalised spans are tried first,
    then bare tokens, so "Onboarding Refresh" beats "onboarding" + "refresh".
    """
    spans = [s.strip() for s in _CAP.findall(question)]
    toks = _terms(question)
    found: dict[str, dict] = {}
    for folder in ("02-people", "03-projects", "06-knowledge"):
        base = root / folder
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name in ("README.md", "_INDEX.md"):
                continue
            try:
                fm, _ = frontmatter.read(p.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
            aliases = fm.get("aliases") if isinstance(fm.get("aliases"), list) else []
            names = [p.stem] + [str(a) for a in aliases]
            rel = p.relative_to(root).as_posix()
            for n in names:
                nl = _flat(n)
                words = [w for w in nl.split() if len(w) > 2]
                hit = None
                if any(nl == _flat(sp) or nl in _flat(sp) or _flat(sp) in nl for sp in spans if len(sp) > 2):
                    hit = 1.0
                elif words and all(w in toks for w in words):
                    hit = 0.7
                if hit and (rel not in found or found[rel]["score"] < hit):
                    found[rel] = {"path": rel, "name": p.stem, "type": fm.get("type", ""),
                                  "matched": n, "score": hit}
    out = sorted(found.values(), key=lambda e: (-e["score"], e["path"]))
    return out[:limit]


def _matching_lines(body: str, terms: list[str], max_lines: int = 4) -> list[dict]:
    """Lines that mention a term, with the nearest `###` date heading above them."""
    out, heading, hdate = [], "", ""
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("### "):
            heading = s[4:].strip()
            m = re.match(r"(\d{4}-\d{2}-\d{2})", heading)
            hdate = m.group(1) if m else ""
        if not s or s.startswith("#"):
            continue
        ll = s.lower()
        if any(t in ll for t in terms):
            out.append({"line": s.lstrip("-* ").strip()[:260], "under": heading, "date": hdate})
            if len(out) >= max_lines:
                break
    return out


def _age_days(value) -> int | None:
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(value)[:10])).days
    except (TypeError, ValueError):
        return None


def recall(root: Path, question: str, limit: int = 6, max_notes_read: int = 5) -> dict:
    """Evidence for a question: entities, citations, a confidence level, and what is missing.

    Returns `{question, entities, citations, confidence, coverage, text, gaps}`.
    `text` is the compact block a model can read as-is; `citations` is the structured form.
    """
    terms = _terms(question)
    ents = entities(root, question)
    ranked: list[dict] = []
    seen = set()
    for e in ents:  # an entity's own note is always the first place to look
        ranked.append({"path": e["path"], "type": e["type"], "score": 20.0 + e["score"], "why": "entity"})
        seen.add(e["path"])
    for hit in search.search(root, " ".join(terms) or question, limit=limit * 2):
        if hit["path"] in seen:
            continue
        seen.add(hit["path"])
        ranked.append({**hit, "why": "keyword"})
    ranked = ranked[: max(limit, max_notes_read)]

    def _covers(note_lines: list[dict], title: str) -> bool:
        """Does this note actually address the question, or did one common word match?

        A note that hits one term out of three is a false positive — the difference between
        "the vault has an answer" and "the vault contains the word 'key'".
        """
        if not terms:
            return False
        blob = (" ".join(l["line"] for l in note_lines) + " " + title).lower()
        hits = sum(1 for t in terms if t in blob)
        return hits >= max(2, (len(terms) + 1) // 2) if len(terms) > 1 else hits == 1

    citations, agreeing, has_stated, freshest = [], set(), False, None
    for r in ranked[:max_notes_read]:
        p = root / r["path"]
        if not p.exists():
            continue
        try:
            fm, body = frontmatter.read(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        lines = _matching_lines(body, terms) if terms else []
        if not lines and r["why"] != "entity":
            continue
        date = str(fm.get("updated") or fm.get("date") or "")
        age = _age_days(date)
        if age is not None and (freshest is None or age < freshest):
            freshest = age
        append_only = r["path"].startswith(APPEND_ONLY)
        covers = _covers(lines, Path(r["path"]).stem) or r["why"] == "entity"
        has_stated = has_stated or (append_only and covers)
        if covers:
            agreeing.add(r["path"])
        citations.append({"path": r["path"], "type": fm.get("type", ""), "date": date, "age_days": age,
                          "append_only": append_only, "why": r["why"], "covers": covers, "lines": lines})

    weak = [c["path"] for c in citations if not c["covers"]]
    citations = [c for c in citations if c["covers"]]   # a near-miss is not a citation
    if not citations:
        confidence = "unknown"
    elif has_stated and len(agreeing) >= 2:
        confidence = "stated"
    elif len(agreeing) >= 2 and (freshest is None or freshest <= RECENT_DAYS):
        confidence = "high"
    elif agreeing:
        confidence = "medium"
    else:
        confidence = "speculation"

    gaps = []
    if not ents:
        gaps.append("no known person, project or hub in the question matched a vault note")
    if freshest is not None and freshest > RECENT_DAYS:
        gaps.append(f"the freshest matching note is {freshest} days old — say so in the answer")
    if confidence in ("speculation", "unknown"):
        gaps.append("do not answer from general knowledge: say the vault does not know, and offer to capture it")

    out_lines = []
    for c in citations:
        head = f"- [[{c['path'][:-3]}]] ({c['date'] or 'undated'}{', append-only' if c['append_only'] else ''})"
        out_lines.append(head)
        out_lines += [f"    - {l['line']}" + (f"  — under {l['under']}" if l["under"] else "") for l in c["lines"]]
    return {
        "question": question,
        "entities": ents,
        "citations": citations,
        "weak_matches": weak,
        "confidence": confidence,
        "coverage": {"notes_cited": len(citations), "notes_agreeing": len(agreeing),
                     "weak_matches": len(weak), "freshest_days": freshest},
        "gaps": gaps,
        "text": "\n".join(out_lines) or "- the vault has nothing on this",
    }


def prefetch_block(root: Path, question: str, max_chars: int = 1400) -> tuple[str, int]:
    """Compact recall block for passive injection, plus the number of notes cited.

    Deliberately smaller than `recall()`: passive context must never crowd out the turn.
    """
    res = recall(root, question, limit=4, max_notes_read=3)
    if res["confidence"] == "unknown":
        return "", 0
    head = [f"From your vault (confidence: {res['confidence']}, cite the paths if you use them):"]
    body = []
    for c in res["citations"]:
        body.append(f"- {c['path']} ({c['date'] or 'undated'})")
        body += [f"    {l['line'][:180]}" for l in c["lines"][:2]]
    block = "\n".join(head + body)
    if len(block) > max_chars:
        block = block[:max_chars].rsplit("\n", 1)[0] + "\n    …"
    return block, len(res["citations"])
