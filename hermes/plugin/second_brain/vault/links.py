"""Wikilinks, slugs and fuzzy people matching."""
from __future__ import annotations

import difflib
import re
import unicodedata
from pathlib import Path

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def slugify(text: str, max_words: int = 6) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return "-".join(words[:max_words]) or "note"


def wikilinks_in(body: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK.finditer(body)]


def resolve(vault_root: Path, target: str) -> Path | None:
    """Resolve a wikilink target to a file; None if it does not exist."""
    cand = vault_root / (target if target.endswith(".md") else target + ".md")
    if cand.exists():
        return cand
    # bare name (no folder): search by stem
    stem = Path(target).stem.lower()
    for p in vault_root.rglob("*.md"):
        if p.stem.lower() == stem and ".obsidian" not in p.parts:
            return p
    return None


def missing_links(vault_root: Path, body: str) -> list[str]:
    seen, out = set(), []
    for t in wikilinks_in(body):
        if t in seen or t == "TODO":
            continue
        seen.add(t)
        if resolve(vault_root, t) is None:
            out.append(t)
    return out


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()


def find_person(vault_root: Path, name: str, aliases_of=None) -> dict:
    """Fuzzy-match a name against 02-people/*.md.

    Returns {"match": exact|likely|ambiguous|none, "candidates": [{path, name, score}]}.
    `aliases_of(path) -> list[str]` may supply frontmatter aliases for extra matching.
    """
    q = _norm(name)
    q_tokens = set(q.split())
    people_dir = vault_root / "02-people"
    cands = []
    for p in sorted(people_dir.glob("*.md")) if people_dir.exists() else []:
        if p.name in ("README.md", "_index.md"):
            continue
        names = [p.stem] + (list(aliases_of(p)) if aliases_of else [])
        best, exact = 0.0, False
        for n in names:
            nn = _norm(n)
            if nn == q:
                exact, best = True, 1.0
                break
            ratio = difflib.SequenceMatcher(None, q, nn).ratio()
            toks = set(nn.split())
            if q_tokens and q_tokens <= toks:
                best = max(best, 0.85)  # "Alex" for "Alex Rivera": likely, confirm if several Alex
            overlap = len(q_tokens & toks) / max(1, len(q_tokens | toks))
            best = max(best, min(ratio, 0.94), 0.6 * overlap + 0.3 * ratio)  # typos never count as exact
        if best >= 0.45:
            cands.append({"path": f"02-people/{p.name}", "name": p.stem, "score": round(best, 3), "exact": exact})
    cands.sort(key=lambda c: (-c["score"], c["name"]))
    if not cands:
        return {"match": "none", "candidates": []}
    top = cands[0]["score"]
    strong = [c for c in cands if c["score"] >= 0.75]
    if cands[0]["exact"] and sum(1 for c in cands if c["exact"]) == 1:
        return {"match": "exact", "candidates": cands[:5]}
    if len(strong) > 1:
        return {"match": "ambiguous", "candidates": cands[:5]}
    if top >= 0.75:
        return {"match": "likely", "candidates": cands[:5]}
    return {"match": "none", "candidates": cands[:5]}
