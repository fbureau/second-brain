"""Google Drive → recently changed docs, and Google Docs → text with the transcript-first rule.

`read_doc` encodes the v4.0 meeting-ingest rule in code: if the document has tabs, the
tab whose title contains "transcript" wins; a summary/notes tab is only a fallback, and
the result says which one was used so the note can carry `transcript-source`.
"""
from __future__ import annotations

import datetime as dt
import re

from . import google
from .http import clip

FILES_API = "https://www.googleapis.com/drive/v3/files"
DOCS_API = "https://docs.googleapis.com/v1/documents/{id}"
KIND = {"application/vnd.google-apps.document": "Doc", "application/vnd.google-apps.spreadsheet": "Sheet",
        "application/vnd.google-apps.presentation": "Slides", "application/pdf": "PDF"}
TRANSCRIPT_HINT = re.compile(r"transcript|transcription", re.I)
SUMMARY_HINT = re.compile(r"summary|notes|résumé|resume|synth", re.I)


def fetch_changes(since_hours: int = 24, max_results: int = 40) -> dict:
    since = (dt.datetime.utcnow() - dt.timedelta(hours=since_hours)).strftime("%Y-%m-%dT%H:%M:%S")
    return google.get(FILES_API, {
        "q": f"modifiedTime > '{since}' and trashed = false",
        "orderBy": "modifiedTime desc", "pageSize": max_results,
        "fields": "files(id,name,mimeType,modifiedTime,webViewLink,lastModifyingUser(displayName,me),owners(displayName))",
    })


def digest_changes(raw: dict, max_items: int = 25) -> dict:
    items = []
    for f in raw.get("files", [])[:max_items]:
        who = (f.get("lastModifyingUser") or {})
        items.append({
            "id": f.get("id"), "name": clip(f.get("name"), 80), "kind": KIND.get(f.get("mimeType"), "file"),
            "modified": (f.get("modifiedTime") or "")[:16].replace("T", " "),
            "by": "me" if who.get("me") else who.get("displayName", "?"),
            "link": f.get("webViewLink", ""),
            "transcript": bool(TRANSCRIPT_HINT.search(f.get("name") or "")),
        })
    lines = [f"- {it['modified']} {it['kind']} “{it['name']}” — by {it['by']}" + (" · **meeting transcript**" if it["transcript"] else "")
             + (f" — {it['link']}" if it["link"] else "") for it in items]
    transcripts = [it for it in items if it["transcript"]]
    return {"source": "drive", "count": len(items), "items": items, "transcripts": transcripts,
            "text": "\n".join(lines) or "- no changes"}


def fetch_doc(file_id: str) -> dict:
    return google.get(DOCS_API.format(id=file_id), {"includeTabsContent": "true"})


def _text_of(body: dict) -> str:
    out = []
    for el in (body or {}).get("content", []):
        para = el.get("paragraph")
        if para:
            out.append("".join(r.get("textRun", {}).get("content", "") for r in para.get("elements", [])))
        table = el.get("table")
        if table:
            for row in table.get("tableRows", []):
                out.append(" | ".join(_text_of(c).strip() for c in row.get("tableCells", [])) + "\n")
    return "".join(out)


def _flatten_tabs(tabs: list) -> list:
    flat = []
    for t in tabs or []:
        flat.append(t)
        flat += _flatten_tabs(t.get("childTabs", []))
    return flat


def extract_transcript(doc: dict) -> dict:
    """Transcript-first selection. Returns {text, transcript_source, tab, tabs}."""
    tabs = _flatten_tabs(doc.get("tabs", []))
    titled = [(t.get("tabProperties", {}).get("title", ""), _text_of(t.get("documentTab", {}).get("body", {}))) for t in tabs]
    names = [n for n, _ in titled]
    for name, text in titled:
        if TRANSCRIPT_HINT.search(name) and text.strip():
            return {"text": text, "transcript_source": "verbatim", "tab": name, "tabs": names}
    for name, text in titled:
        if SUMMARY_HINT.search(name) and text.strip():
            return {"text": text, "transcript_source": "summary-fallback", "tab": name, "tabs": names,
                    "warning": "no transcript tab — summary used; mark confidence: medium, needs-review: true"}
    full = "\n".join(t for _, t in titled if t.strip()) or _text_of(doc.get("body", {}))
    src = "verbatim" if TRANSCRIPT_HINT.search(doc.get("title", "") or "") else "full-document"
    return {"text": full, "transcript_source": src, "tab": None, "tabs": names}


def read_doc(file_id: str, max_chars: int = 60000) -> dict:
    doc = fetch_doc(file_id)
    res = extract_transcript(doc)
    res["title"] = doc.get("title", "")
    res["truncated"] = len(res["text"]) > max_chars
    res["text"] = res["text"][:max_chars]
    return res
