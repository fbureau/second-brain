"""Google Calendar → the day's events, compact."""
from __future__ import annotations

import datetime as dt

from . import google
from .http import clip

API = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def fetch_day(day: str | None = None, tz: str = "Europe/Paris") -> dict:
    d = dt.date.fromisoformat(day) if day else dt.date.today()
    return google.get(API, {"timeMin": f"{d}T00:00:00Z", "timeMax": f"{d + dt.timedelta(days=1)}T00:00:00Z",
                            "singleEvents": "true", "orderBy": "startTime", "maxResults": 50, "timeZone": tz})


def digest_events(raw: dict, user_email: str | None = None, max_items: int = 20) -> dict:
    items = []
    for ev in raw.get("items", [])[:max_items]:
        if ev.get("status") == "cancelled":
            continue
        start = ev.get("start", {}); end = ev.get("end", {})
        s, e = start.get("dateTime", start.get("date", "")), end.get("dateTime", end.get("date", ""))
        all_day = "dateTime" not in start
        minutes = None
        if not all_day and s and e:
            try:
                minutes = int((dt.datetime.fromisoformat(e) - dt.datetime.fromisoformat(s)).total_seconds() // 60)
            except ValueError:
                pass
        attendees = [a.get("displayName") or a.get("email", "") for a in ev.get("attendees", [])
                     if not a.get("self") and a.get("responseStatus") != "declined"]
        items.append({
            "time": "all-day" if all_day else s[11:16],
            "title": clip(ev.get("summary"), 80),
            "minutes": minutes,
            "attendees": attendees[:8],
            "attendee_count": len(attendees),
            "meet": bool(ev.get("hangoutLink") or ev.get("conferenceData")),
            "description": clip(ev.get("description"), 120),
        })
    lines = []
    for it in items:
        who = ", ".join(it["attendees"][:4]) + (f" +{it['attendee_count'] - 4}" if it["attendee_count"] > 4 else "")
        dur = f" ({it['minutes']} min)" if it["minutes"] else ""
        lines.append(f"- {it['time']} {it['title']}{dur}" + (f" — with {who}" if who else "") + (" · Meet" if it["meet"] else ""))
    return {"source": "calendar", "count": len(items), "items": items,
            "text": "\n".join(lines) or "- no events"}
