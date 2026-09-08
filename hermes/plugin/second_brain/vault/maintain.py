"""Maintenance — the deterministic half of task-roundup, the curator sweep, the staleness
check and the vault health audit.

Everything here is mechanical bookkeeping: scan checkboxes, assign anchors, reconcile
TODO.md both ways, rebuild hub listings, count, flag. Anything that needs judgment
(ambiguous ownership, near-duplicates, hub proposals, zombie tasks) is NOT decided here:
it is returned under `needs_judgment` for the model to handle in the calling skill.
"""
from __future__ import annotations

import datetime as dt
import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter, index as index_mod, notes, tasks
from .links import WIKILINK

TODAY = notes.today

CHECKBOX = re.compile(r"^(?P<indent>\s*)- \[(?P<state>[ xX])\] (?P<rest>.*)$")
DONE_STAMP = re.compile(r"\s*✅\s*(\d{4}-\d{2}-\d{2})")
MIRROR = re.compile(r"\[\[[^\]]*#\^t-([a-z0-9]{6})\]\]")
OWNER = re.compile(r"owner:\s*(\S[^—]*?)\s*(?=—|$)")
DUE = re.compile(r"due:?\s*(\d{4}-\d{2}-\d{2})")
FROM = re.compile(r"#from/([a-z0-9-]+)")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# Where actions live (see _CLAUDE.md §7 / task-roundup). None = any section except the excluded ones.
TASK_SOURCES: dict[str, tuple[list[str] | None, list[str]]] = {
    "04-meetings": (["Action items"], []),
    "05-decisions": (["Execution plan"], []),
    "01-daily": (["Pending follow-ups"], []),
    "02-people": (["Timeline", "Open threads"], []),
    "03-projects": (None, ["Success criteria"]),
    "00-inbox": (["Suggested follow-up"], []),
}
TODO_HEADINGS = ["⏰ Overdue", "📅 Today", "🔜 Upcoming (next 7 days)", "🗓 Scheduled (later)", "🧭 No date",
                 "⏳ Waiting on others", "✅ Done (last 14 days)"]
TODO_TEMPLATE_HEAD = """---
type: todo-dashboard
updated: {today}
ai-first: true
---

## For future Claude

Consolidated, auto-generated action list. The source of truth is the linked notes;
this file is a reconcilable view. Checking a box here flips it in the source note
(matched by `^t-id`). Refreshed by task-roundup / the second-brain maintenance tool. Do
NOT hand-edit the action text here — edit it in the source note. You MAY check/uncheck
boxes here.
"""


def _d(s: str | None) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s) if s else None
    except ValueError:
        return None


# ============================================================================ tasks

@dataclass
class Task:
    path: str
    line_no: int
    raw: str
    done: bool
    text: str
    owner: str
    due: str | None
    source_tag: str
    anchor: str | None
    done_date: str | None
    mirror_of: str | None = None
    waiting: bool = False
    note_date: str | None = None
    note_type: str = ""
    note_meta: dict = field(default_factory=dict)


def _user_aliases(root: Path) -> set[str]:
    aliases = {"me", "moi"}
    p = root / "00-inbox" / "MY-PROFILE.md"
    if p.exists():
        m = re.search(r"\*\*Name\*\*:\s*(.+)", p.read_text(encoding="utf-8"))
        if m and "<" not in m.group(1):
            name = m.group(1).strip()
            aliases.update({name.lower(), name.split()[0].lower()})
    return aliases


def parse_task_line(line: str) -> dict | None:
    m = CHECKBOX.match(line)
    if not m:
        return None
    rest = m.group("rest")
    mirror = MIRROR.search(rest)
    anchor = tasks.ANCHOR.search(rest)
    done_stamp = DONE_STAMP.search(rest)
    owner_m, due_m, from_m = OWNER.search(rest), DUE.search(rest), FROM.search(rest)
    text = rest.split(" — ")[0]
    text = DONE_STAMP.sub("", tasks.ANCHOR.sub("", text)).strip(" —")
    return {
        "done": m.group("state") != " ",
        "text": text,
        "owner": re.sub(r"\s*[⏳⚠️]+.*$", "", owner_m.group(1)).strip() if owner_m else "me",
        "due": due_m.group(1) if due_m else None,
        "source_tag": from_m.group(1) if from_m else "",
        "anchor": anchor.group(1) if (anchor and not (mirror and mirror.group(1) == anchor.group(1))) else None,
        "done_date": done_stamp.group(1) if done_stamp else None,
        "mirror_of": mirror.group(1) if mirror else None,
        "waiting": "⏳" in rest or "waiting" in rest.lower(),
    }


def _sections_of(lines: list[str]) -> list[str | None]:
    """Heading (`## X` text) in effect for every line."""
    cur, out = None, []
    for l in lines:
        if l.startswith("## "):
            cur = l[3:].strip()
        out.append(cur)
    return out


def scan_tasks(root: Path) -> tuple[list[Task], dict[str, int]]:
    aliases = _user_aliases(root)
    found, scanned = [], {}
    for folder, (allowed, excluded) in TASK_SOURCES.items():
        base = root / folder
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name in ("README.md", "MY-PROFILE.md", "_index.md"):
                continue
            scanned[folder] = scanned.get(folder, 0) + 1
            text = p.read_text(encoding="utf-8")
            fm, body = frontmatter.read(text)
            lines = text.split("\n")
            secs = _sections_of(lines)
            for i, l in enumerate(lines):
                sec = secs[i]
                if allowed is not None and sec not in allowed:
                    continue
                if sec in excluded:
                    continue
                t = parse_task_line(l)
                if not t:
                    continue
                owner_l = t["owner"].lower().strip("[]")
                mine = owner_l in aliases or owner_l.startswith("me ") or t["owner"] == "me"
                if not mine and not t["waiting"]:
                    continue  # someone else's action, not blocking us
                found.append(Task(path=p.relative_to(root).as_posix(), line_no=i, raw=l, note_date=str(fm.get("date", "")),
                                  note_type=str(fm.get("type", "")), note_meta=fm, **t))
    return found, scanned


def _todo_head_and_entries(root: Path) -> tuple[str, dict[str, dict]]:
    p = root / "TODO.md"
    if not p.exists():
        return TODO_TEMPLATE_HEAD.format(today=TODAY()), {}
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")
    first_h2 = next((i for i, l in enumerate(lines) if l.startswith("## ") and not l.startswith("## For future")), len(lines))
    head = "\n".join(lines[:first_h2]).rstrip("\n") + "\n"
    entries: dict[str, dict] = {}
    for l in lines[first_h2:]:
        t = parse_task_line(l)
        if t and t["mirror_of"]:
            entries[t["mirror_of"]] = t
    return head, entries


def _write_line(root: Path, rel: str, line_no: int, new_line: str) -> None:
    p = root / rel
    lines = p.read_text(encoding="utf-8").split("\n")
    lines[line_no] = new_line
    p.write_text("\n".join(lines), encoding="utf-8")


def _stamp_done(raw: str, date: str) -> str:
    m = CHECKBOX.match(raw)
    rest = m.group("rest")
    parts = rest.split(" — ", 1)
    parts[0] = parts[0].rstrip() + f" ✅ {date}"
    return f"{m.group('indent')}- [x] " + " — ".join(parts)


def sync_tasks(root: Path, apply: bool = True) -> dict:
    today = TODAY()
    today_d = dt.date.fromisoformat(today)
    found, scanned = scan_tasks(root)
    head, todo = _todo_head_and_entries(root)
    taken = tasks.existing_anchors(root)
    report = {"scanned": scanned, "tasks": 0, "new_anchors": 0, "reconciled": {"todo_to_source": 0, "source_to_todo": 0},
              "flags": [], "needs_judgment": [], "applied": apply}

    # 1. mirrors (daily "Pending follow-ups") behave like TODO entries: a ticked mirror completes the source
    mirror_done = {t.mirror_of for t in found if t.mirror_of and t.done}
    real = [t for t in found if not t.mirror_of]
    report["tasks"] = len(real)

    # 2. anchors + reconciliation, per source line (write lines bottom-up per file to keep indexes valid)
    by_file: dict[str, list[Task]] = {}
    for t in real:
        by_file.setdefault(t.path, []).append(t)
    for rel, ts in by_file.items():
        for t in sorted(ts, key=lambda x: -x.line_no):
            new_raw = t.raw
            if not t.anchor:
                t.anchor = tasks.new_anchor(root, taken)
                new_raw = new_raw.rstrip() + f" ^t-{t.anchor}"
                report["new_anchors"] += 1
            entry = todo.get(t.anchor)
            completed_elsewhere = (entry and entry["done"]) or t.anchor in mirror_done
            if completed_elsewhere and not t.done:
                new_raw = _stamp_done(new_raw, today)
                t.done, t.done_date = True, today
                report["reconciled"]["todo_to_source"] += 1
            elif t.done and entry and not entry["done"]:
                report["reconciled"]["source_to_todo"] += 1
            if t.done and not t.done_date:
                t.done_date = (entry or {}).get("done_date") or today
            if new_raw != t.raw and apply:
                _write_line(root, rel, t.line_no, new_raw)
            if "unassigned" in t.owner.lower() or "⚠" in t.raw:
                report["needs_judgment"].append({"kind": "unassigned-owner", "path": rel, "line": t.raw.strip()})

    # 3. sources that vanished
    live = {t.anchor for t in real}
    for anchor, entry in todo.items():
        if anchor not in live and not entry["done"]:
            report["flags"].append({"kind": "source-removed", "anchor": anchor, "text": entry["text"]})
            report["needs_judgment"].append({"kind": "source-removed", "anchor": anchor, "text": entry["text"],
                                             "question": "source line is gone — drop from TODO or restore?"})

    # 4. regenerate TODO.md
    buckets: dict[str, list[str]] = {h: [] for h in TODO_HEADINGS}
    for t in sorted(real, key=lambda x: (x.due or "9999", x.path)):
        link = f"[[{t.path[:-3]}#^t-{t.anchor}]]"
        due_d = _d(t.due)
        if t.done:
            if t.done_date and (today_d - dt.date.fromisoformat(t.done_date)).days <= 14:
                buckets["✅ Done (last 14 days)"].append(f"- [x] {t.text} — {link} — done {t.done_date}")
            continue
        if t.waiting and t.owner not in ("me",):
            since = t.note_date or "unknown"
            buckets["⏳ Waiting on others"].append(f"- [ ] (owner: {t.owner}) {t.text} — {link} — since {since}")
            continue
        prio = ""
        if due_d and due_d < today_d:
            prio = "🔴 "
        elif t.note_type == "decision" and t.note_meta.get("reversibility") in ("one-way", "hard-to-reverse"):
            prio = "🔴 "
        elif t.note_type == "project" and t.note_meta.get("status") == "active":
            prio = "🟡 "
        stale = ""
        nd = _d(t.note_date)
        if not due_d and nd and (today_d - nd).days > 21:
            stale = " ⏳ stale"
            report["needs_judgment"].append({"kind": "zombie-task", "path": t.path, "text": t.text,
                                             "question": f"no due date, untouched {(today_d - nd).days}d — still relevant?"})
        tag = f" — #from/{t.source_tag}" if t.source_tag else ""
        line = f"- [ ] {prio}{t.text} — {link}" + (f" — due {t.due}" if t.due else "") + tag + stale
        if not due_d:
            buckets["🧭 No date"].append(line)
        elif due_d < today_d:
            buckets["⏰ Overdue"].append(line)
        elif due_d == today_d:
            buckets["📅 Today"].append(line)
        elif (due_d - today_d).days <= 7:
            buckets["🔜 Upcoming (next 7 days)"].append(line)
        else:
            buckets["🗓 Scheduled (later)"].append(line)
    for anchor, entry in todo.items():
        if anchor not in live and not entry["done"]:
            buckets["🧭 No date"].append(f"- [ ] {entry['text']} — ⚠️ (source removed — confirm) ^t-{anchor}-orphan")

    body = head.rstrip("\n") + "\n"
    for h in TODO_HEADINGS:
        body += f"\n## {h}\n\n" + ("\n".join(buckets[h]) + "\n" if buckets[h] else "")
    fm, rest = frontmatter.read(body)
    fm["updated"] = today
    if apply:
        (root / "TODO.md").write_text(frontmatter.write(fm, rest), encoding="utf-8")
    report["buckets"] = {h: len(v) for h, v in buckets.items()}
    return report


def set_task_state(root: Path, anchor: str, done: bool) -> dict:
    """Flip the SOURCE line carrying ^t-<anchor> (never TODO.md); the next sync propagates."""
    today = TODAY()
    for p in root.rglob("*.md"):
        if p.name == "TODO.md" or ".obsidian" in p.parts:
            continue
        lines = p.read_text(encoding="utf-8").split("\n")
        for i, l in enumerate(lines):
            m = tasks.ANCHOR.search(l)
            if m and m.group(1) == anchor and CHECKBOX.match(l) and not MIRROR.search(l):
                t = parse_task_line(l)
                if done and not t["done"]:
                    lines[i] = _stamp_done(l, today)
                elif not done and t["done"]:
                    lines[i] = CHECKBOX.sub(lambda mm: f"{mm.group('indent')}- [ ] " + DONE_STAMP.sub("", mm.group("rest")), l, count=1)
                p.write_text("\n".join(lines), encoding="utf-8")
                return {"path": p.relative_to(root).as_posix(), "anchor": anchor, "done": done, "line": lines[i].strip()}
    return {"error": f"no source task line carries ^t-{anchor}"}


# ============================================================================ curator sweep

def _knowledge_notes(root: Path) -> list[dict]:
    out = []
    kdir = root / "06-knowledge"
    for p in sorted(kdir.rglob("*.md")):
        if p.name in ("README.md", "_INDEX.md"):
            continue
        fm, body = frontmatter.read(p.read_text(encoding="utf-8"))
        rel = p.relative_to(root).as_posix()
        out.append({"rel": rel, "link": rel[:-3], "stem": p.stem, "fm": fm, "body": body, "type": fm.get("type", "")})
    return out


def _inbound_links(root: Path) -> dict[str, set[str]]:
    """target (without .md, folder-qualified or bare stem) -> set of referring note paths."""
    inbound: dict[str, set[str]] = {}
    for p in root.rglob("*.md"):
        if ".obsidian" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        for m in WIKILINK.finditer(p.read_text(encoding="utf-8")):
            tgt = m.group(1).strip()
            tgt = tgt[:-3] if tgt.endswith(".md") else tgt
            inbound.setdefault(tgt, set()).add(rel)
            inbound.setdefault(Path(tgt).name, set()).add(rel)
    return inbound


def _snapshot(root: Path, rels: list[str]) -> dict[str, str]:
    snap = {}
    for rel in rels:
        p = root / rel
        if p.exists():
            _, body = frontmatter.read(p.read_text(encoding="utf-8"))
            snap[rel] = body
    return snap


def _sweep_once(root: Path, apply: bool) -> dict:
    today = TODAY()
    today_d = dt.date.fromisoformat(today)
    knotes = _knowledge_notes(root)
    hubs = {str(n["fm"].get("domain")): n for n in knotes if n["type"] == "index" and n["fm"].get("domain")}
    content = [n for n in knotes if n["type"] in ("wiki", "knowledge", "doc")]
    by_domain: dict[str, list[dict]] = {}
    for n in content:
        by_domain.setdefault(str(n["fm"].get("domain") or "unsorted"), []).append(n)
    report = {"hubs_rebuilt": [], "proposals": [], "health": {}, "needs_judgment": []}

    # hubs
    for domain, hub in hubs.items():
        if hub["fm"].get("auto-maintained") not in (True, "true"):
            continue
        members = by_domain.get(domain, [])
        changed = False
        for ntype, section in (("wiki", "Wiki pages"), ("knowledge", "Lessons"), ("doc", "Source documents")):
            want = sorted((f"- [[{n['link']}]] — {index_mod._one_liner(n['fm'], n['body'], ntype)}" for n in members if n["type"] == ntype),
                          key=str.lower)
            _, hbody = notes.read_note(root, hub["rel"])
            lines = hbody.split("\n")
            b = notes._section_bounds(lines, section)
            have = [l for l in (lines[b[0] + 1 : b[1]] if b else []) if l.lstrip().startswith("- [[")]
            if have != want:
                changed = True
                if apply:
                    index_mod._replace_section_bullets(root, hub["rel"], section, want)
        if changed:
            counts = {t: sum(1 for n in members if n["type"] == t) for t in ("wiki", "knowledge", "doc")}
            if apply:
                hfm, hbody = notes.read_note(root, hub["rel"])
                lines = hbody.split("\n")
                b = notes._section_bounds(lines, "Recent activity")
                recent = [l for l in (lines[b[0] + 1 : b[1]] if b else []) if l.lstrip().startswith("- ")]
                recent = [f"- {today}: curator sweep rebuilt listings ({counts['wiki']} wikis · {counts['knowledge']} lessons · {counts['doc']} docs)"] + recent[:19]
                index_mod._replace_section_bullets(root, hub["rel"], "Recent activity", recent)
                hfm, hbody = notes.read_note(root, hub["rel"])
                hfm["updated"] = today
                notes._write(root / hub["rel"], hfm, hbody)
            report["hubs_rebuilt"].append(hub["rel"])

    # proposals & health
    for domain, members in by_domain.items():
        if domain != "unsorted" and domain not in hubs and len(members) >= 3:
            report["proposals"].append({"kind": "new-hub", "domain": domain, "notes": [n["link"] for n in members]})
    inbound = _inbound_links(root)
    # _INDEX.md is the curator's own bookkeeping, not a reference: a note listed only there is still an orphan.
    orphans = [n["link"] for n in content
               if not ((inbound.get(n["link"], set()) | inbound.get(n["stem"], set())) - {n["rel"], "06-knowledge/_INDEX.md"})]
    stubs, stale = [], []
    for n in content:
        if n["type"] == "wiki" and n["fm"].get("needs-review") in (True, "true"):
            d = _d(str(n["fm"].get("date", "")))
            if d and (today_d - d).days > 14:
                stubs.append(n["link"])
        if n["type"] == "wiki":
            u = _d(str(n["fm"].get("updated", "") or n["fm"].get("date", "")))
            if u and (today_d - u).days > 90:
                stale.append(n["link"])
    dups = []
    stems = [n for n in content]
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            a, b_ = stems[i]["stem"].lower(), stems[j]["stem"].lower()
            if a != b_ and difflib.SequenceMatcher(None, a, b_).ratio() > 0.7:
                dups.append((stems[i]["link"], stems[j]["link"]))
    counts = {"wiki": sum(1 for n in content if n["type"] == "wiki"), "knowledge": sum(1 for n in content if n["type"] == "knowledge"),
              "doc": sum(1 for n in content if n["type"] == "doc"), "index": len(hubs)}
    report["health"] = {"counts": counts, "orphans": orphans, "stubs_to_enrich": stubs, "stale_wikis": stale,
                        "near_duplicates": dups}
    for a, b_ in dups:
        report["needs_judgment"].append({"kind": "near-duplicate", "notes": [a, b_], "question": "same thing? propose a merge"})
    for pz in report["proposals"]:
        report["needs_judgment"].append({"kind": "new-hub", **pz, "question": "3+ notes share this domain — create the hub?"})

    # _INDEX.md
    index_rel = "06-knowledge/_INDEX.md"
    if (root / index_rel).exists() and apply:
        hub_lines = []
        for domain in sorted(hubs):
            m = by_domain.get(domain, [])
            c = {t: sum(1 for n in m if n["type"] == t) for t in ("wiki", "knowledge", "doc")}
            hfm_now, _ = notes.read_note(root, hubs[domain]["rel"])  # re-read: the hub loop above may have stamped it
            hub_lines.append(f"- [[{hubs[domain]['link']}]] ({c['wiki']} wikis · {c['knowledge']} lessons · {c['doc']} source docs · updated {hfm_now.get('updated', '?')})")
        index_mod._replace_section_bullets(root, index_rel, "Domain hubs", hub_lines)
        docs = sorted((n for n in content if n["type"] == "doc"), key=lambda n: str(n["fm"].get("date", "")), reverse=True)[:10]
        index_mod._replace_section_bullets(root, index_rel, "Sources (most recent 10)",
                                           [f"- [[{n['link']}]] — {n['fm'].get('domain', 'unsorted')}, {n['fm'].get('doc-type', 'doc')}" for n in docs])
        unsorted_dom = [f"- [[{n['link']}]] — `domain: {d}`" for d in sorted(by_domain) if d != "unsorted" and d not in hubs
                        for n in sorted(by_domain[d], key=lambda n: n["link"])]
        index_mod._replace_section_bullets(root, index_rel, "Unsorted by domain", unsorted_dom)
        index_mod._replace_section_bullets(root, index_rel, "Unsorted (no domain)",
                                           [f"- [[{n['link']}]]" for n in by_domain.get("unsorted", [])])
        health = [f"- {counts['wiki']} wiki pages · {counts['knowledge']} lessons · {counts['doc']} source docs · {counts['index']} hubs.",
                  f"- {len(orphans)} orphans (no inbound links).",
                  f"- {len(stubs)} stubs awaiting enrichment (>14 days `needs-review: true`).",
                  f"- {len(stale)} stale wiki pages (>90 days no update).",
                  f"- {len(dups)} near-duplicates flagged for review."]
        for title, items in (("Orphans", orphans), ("Stubs to enrich", stubs), ("Stale wikis", stale),
                             ("Near-duplicates", [f"{a} ↔ {b_}" for a, b_ in dups])):
            if items:
                health += ["", f"### {title}"] + [f"- [[{x}]]" if "↔" not in x else f"- {x}" for x in items]
        index_mod._replace_section_bullets(root, index_rel, "Health", health)
        ifm, ibody = notes.read_note(root, index_rel)
        ifm["updated"] = today
        notes._write(root / index_rel, ifm, ibody)
    return report


def curator_sweep(root: Path, apply: bool = True, max_passes: int = 3) -> dict:
    """Sweep with the v4.0 self-verification loop: repeat until a pass changes nothing (max 3)."""
    watched = [n["rel"] for n in _knowledge_notes(root) if n["type"] == "index"] + ["06-knowledge/_INDEX.md"]
    report, passes = {}, 0
    before = _snapshot(root, watched)
    while passes < max_passes:
        passes += 1
        report = _sweep_once(root, apply)
        after = _snapshot(root, watched)
        if after == before or not apply:
            break
        before = after
    report["passes"] = passes
    report["stable"] = passes < max_passes or after == before if apply else True
    if apply and not report["stable"]:
        report["needs_judgment"].append({"kind": "curator-unstable", "question": "sweep did not converge in 3 passes — inspect hubs"})
    return report


# ============================================================================ staleness

def staleness(root: Path, apply: bool = True, stale_days: int = 30, critical_days: int = 60) -> dict:
    today = TODAY()
    today_d = dt.date.fromisoformat(today)
    rep = {"critical": [], "stale": [], "cleared": [], "skipped": 0}
    pdir = root / "02-people"
    for p in sorted(pdir.glob("*.md")) if pdir.exists() else []:
        if p.name in ("README.md", "_index.md"):
            continue
        fm, body = frontmatter.read(p.read_text(encoding="utf-8"))
        if fm.get("relationship") not in ("direct-report", "peer", "manager"):
            rep["skipped"] += 1
            continue
        last = _d(str(fm.get("last-interaction", "")))
        if not last:
            continue
        days = (today_d - last).days
        cur = str(fm.get("staleness-flag", "") or "")
        rel = p.relative_to(root).as_posix()
        if days > critical_days:
            new = cur if cur.startswith(f"stale-{critical_days}d") else f"stale-{critical_days}d-since-{today}"
            rep["critical"].append({"path": rel, "days": days})
        elif days >= stale_days:
            new = cur if cur.startswith(f"stale-{stale_days}d") else f"stale-{stale_days}d-since-{today}"
            rep["stale"].append({"path": rel, "days": days})
        else:
            new = ""
            if cur:
                rep["cleared"].append({"path": rel, "days": days})
        if new != cur and apply:
            fm["staleness-flag"] = new
            notes._write(p, fm, body)
    return rep


# ============================================================================ health

def health(root: Path) -> dict:
    today_d = dt.date.fromisoformat(TODAY())
    rep: dict = {"counts": {}, "zombie_projects": [], "untriaged_inbox": 0, "decisions_last_30d": 0}
    for folder in sorted(d.name for d in root.iterdir() if d.is_dir() and re.match(r"^0[0-7]-", d.name)):
        files = [f for f in (root / folder).rglob("*.md") if f.name != "README.md"]
        rep["counts"][folder] = len(files)
        for f in files:
            fm, _ = frontmatter.read(f.read_text(encoding="utf-8"))
            if folder == "03-projects" and fm.get("status") == "active":
                u = _d(str(fm.get("updated", "") or fm.get("date", "")))
                if u and (today_d - u).days > 30:
                    rep["zombie_projects"].append(f.relative_to(root).as_posix())
            if folder == "00-inbox" and fm.get("type") == "braindump":
                rep["untriaged_inbox"] += 1
            if folder == "05-decisions" and fm.get("type") == "decision":
                d = _d(str(fm.get("date", "")))
                if d and (today_d - d).days <= 30:
                    rep["decisions_last_30d"] += 1
    return rep


# ============================================================================ dispatcher

def run(root: Path, scope: str = "all", apply: bool = True) -> dict:
    scope = (scope or "all").lower()
    out: dict = {"scope": scope, "applied": apply, "needs_judgment": []}
    if scope in ("all", "tasks"):
        out["tasks"] = sync_tasks(root, apply)
        out["needs_judgment"] += out["tasks"].pop("needs_judgment", [])
    if scope in ("all", "curator"):
        out["curator"] = curator_sweep(root, apply)
        out["needs_judgment"] += out["curator"].pop("needs_judgment", [])
    if scope in ("all", "staleness"):
        out["staleness"] = staleness(root, apply)
    if scope in ("all", "health"):
        out["health"] = health(root)
    return out
