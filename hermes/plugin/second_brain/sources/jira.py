"""Jira Cloud → issues that moved in the window, compact.

Env: JIRA_BASE_URL (https://<site>.atlassian.net), JIRA_EMAIL, JIRA_API_TOKEN (basic auth).
"""
from __future__ import annotations

import base64
import os

from .http import SourceError, clip, request_json

DEFAULT_JQL = "(assignee = currentUser() OR reporter = currentUser() OR watcher = currentUser()) AND updated >= -{h}h ORDER BY updated DESC"


def fetch_issues(since_hours: int = 24, jql: str | None = None, max_results: int = 50) -> dict:
    base, email, tok = (os.environ.get(k) for k in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"))
    if not (base and email and tok):
        raise SourceError("Jira credentials missing: set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN")
    auth = base64.b64encode(f"{email}:{tok}".encode()).decode()
    return request_json(base.rstrip("/") + "/rest/api/3/search", params={
        "jql": jql or DEFAULT_JQL.format(h=since_hours), "maxResults": max_results,
        "fields": "summary,status,assignee,updated,priority,issuetype,project"},
        headers={"Authorization": f"Basic {auth}"})


def digest_issues(raw: dict, max_items: int = 25) -> dict:
    items = []
    for i in raw.get("issues", [])[:max_items]:
        f = i.get("fields", {})
        items.append({"key": i.get("key"), "summary": clip(f.get("summary"), 90),
                      "status": (f.get("status") or {}).get("name", "?"),
                      "type": (f.get("issuetype") or {}).get("name", ""),
                      "assignee": (f.get("assignee") or {}).get("displayName", "unassigned"),
                      "priority": (f.get("priority") or {}).get("name", ""),
                      "updated": (f.get("updated") or "")[:16].replace("T", " "),
                      "project": (f.get("project") or {}).get("key", "")})
    by_status: dict[str, int] = {}
    for it in items:
        by_status[it["status"]] = by_status.get(it["status"], 0) + 1
    lines = [f"- {it['key']} [{it['status']}] {it['summary']} — {it['assignee']}" + (f" · {it['priority']}" if it['priority'] else "")
             for it in items]
    return {"source": "jira", "count": len(items), "by_status": by_status, "items": items,
            "text": "\n".join(lines) or "- no Jira movement"}
