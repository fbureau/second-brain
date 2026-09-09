"""Slack → per-channel themes and mentions since a timestamp, compact.

Env: SLACK_BOT_TOKEN (xoxb-… with channels:history, channels:read, groups:history, im:history,
users:read) and optionally SLACK_USER_ID (to spot mentions of the user).
"""
from __future__ import annotations

import datetime as dt
import os

from .http import SourceError, clip, request_json

API = "https://slack.com/api/"


def _call(method: str, **params) -> dict:
    tok = os.environ.get("SLACK_BOT_TOKEN")
    if not tok:
        raise SourceError("SLACK_BOT_TOKEN missing")
    res = request_json(API + method, params=params, headers={"Authorization": f"Bearer {tok}"})
    if not res.get("ok"):
        raise SourceError(f"slack {method}: {res.get('error')}")
    return res


def fetch_activity(since_hours: int = 24, max_channels: int = 30, per_channel: int = 100) -> dict:
    oldest = (dt.datetime.utcnow() - dt.timedelta(hours=since_hours)).timestamp()
    chans = _call("conversations.list", types="public_channel,private_channel,im,mpim", exclude_archived="true", limit=200)
    users = {u["id"]: (u.get("real_name") or u.get("name")) for u in _call("users.list", limit=500).get("members", [])}
    out = {"channels": [], "users": users}
    for c in [c for c in chans.get("channels", []) if c.get("is_member") or c.get("is_im")][:max_channels]:
        hist = _call("conversations.history", channel=c["id"], oldest=f"{oldest:.6f}", limit=per_channel)
        msgs = [m for m in hist.get("messages", []) if m.get("type") == "message" and not m.get("bot_id") and m.get("subtype") is None]
        if msgs:
            out["channels"].append({"id": c["id"], "name": c.get("name") or ("DM" if c.get("is_im") else c["id"]),
                                    "is_im": bool(c.get("is_im")), "messages": msgs})
    return out


def digest_activity(raw: dict, user_id: str | None = None, ignore: list[str] | None = None, max_channels: int = 12) -> dict:
    user_id = user_id or os.environ.get("SLACK_USER_ID")
    users = raw.get("users", {})
    ignore = {c.lstrip("#") for c in (ignore or [])}
    chans, mentions, dms = [], [], []
    for c in raw.get("channels", []):
        if c["name"] in ignore:
            continue
        msgs = c["messages"]
        posters: dict[str, int] = {}
        mine = 0
        for m in msgs:
            u = users.get(m.get("user"), m.get("user", "?"))
            posters[u] = posters.get(u, 0) + 1
            if user_id and m.get("user") == user_id:
                mine += 1
            if user_id and f"<@{user_id}>" in (m.get("text") or "") and m.get("user") != user_id:
                mentions.append({"channel": c["name"], "by": u, "text": clip(m.get("text"), 160)})
        top = sorted(posters.items(), key=lambda kv: -kv[1])[:3]
        first = clip(msgs[-1].get("text") if msgs else "", 100)
        entry = {"channel": c["name"], "messages": len(msgs), "mine": mine, "top_posters": [p for p, _ in top],
                 "threads": sum(1 for m in msgs if m.get("reply_count")), "sample": first}
        (dms if c["is_im"] else chans).append(entry)
    chans.sort(key=lambda e: -e["messages"])
    lines = [f"- #{e['channel']}: {e['messages']} msgs ({', '.join(e['top_posters'])}) — you posted {e['mine']} — e.g. “{e['sample']}”"
             for e in chans[:max_channels]]
    lines += [f"- DM with {e['top_posters'][0] if e['top_posters'] else '?'}: {e['messages']} msgs — “{e['sample']}”" for e in dms[:8]]
    lines += [f"- mention in #{m['channel']} by {m['by']}: “{m['text']}”" for m in mentions[:10]]
    return {"source": "slack", "channels": chans, "dms": dms, "mentions": mentions,
            "count": sum(e["messages"] for e in chans + dms), "text": "\n".join(lines) or "- Slack quiet"}
