"""Source digests are pure functions over API JSON — tested on embedded fixtures, no network."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hermes" / "plugin"))

from second_brain.sources import calendar, drive, jira, slack  # noqa: E402

CAL = {"items": [
    {"summary": "Weekly 1-1 Alex", "start": {"dateTime": "2026-09-08T10:00:00+02:00"}, "end": {"dateTime": "2026-09-08T10:30:00+02:00"},
     "attendees": [{"email": "me@x.com", "self": True}, {"displayName": "Alex Rivera", "email": "alex@x.com"}], "hangoutLink": "https://meet.google.com/abc"},
    {"summary": "Cancelled thing", "status": "cancelled", "start": {"dateTime": "2026-09-08T11:00:00+02:00"}, "end": {"dateTime": "2026-09-08T12:00:00+02:00"}},
    {"summary": "Offsite", "start": {"date": "2026-09-08"}, "end": {"date": "2026-09-09"},
     "attendees": [{"displayName": f"P{i}", "email": f"p{i}@x.com"} for i in range(6)], "description": "Agenda:\nstrategy\nbudget"},
]}
DRIVE = {"files": [
    {"id": "1", "name": "Weekly 1-1 Alex — Transcript", "mimeType": "application/vnd.google-apps.document", "modifiedTime": "2026-09-08T09:31:00.000Z",
     "webViewLink": "https://docs.google.com/d/1", "lastModifyingUser": {"displayName": "Meet", "me": False}},
    {"id": "2", "name": "Budget 2027", "mimeType": "application/vnd.google-apps.spreadsheet", "modifiedTime": "2026-09-08T08:00:00.000Z",
     "webViewLink": "https://docs.google.com/s/2", "lastModifyingUser": {"displayName": "me", "me": True}},
]}
def _tab(title, text):
    return {"tabProperties": {"title": title}, "documentTab": {"body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": text}}]}}]}}}
DOC_BOTH = {"title": "Weekly 1-1 Alex", "tabs": [_tab("Summary", "AI summary: two decisions.\n"), _tab("Transcript", "Alex: we should revisit training.\nMe: agreed.\n")]}
DOC_SUMMARY_ONLY = {"title": "Weekly 1-1 Alex", "tabs": [_tab("Summary", "AI summary: two decisions.\n")]}
DOC_PLAIN = {"title": "Random doc", "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Plain text body.\n"}}]}}]}}
SLACK = {"users": {"U1": "Alex Rivera", "U2": "Me"}, "channels": [
    {"id": "C1", "name": "onboarding", "is_im": False, "messages": [
        {"type": "message", "user": "U1", "text": "the script confuses agents on edge cases", "reply_count": 3},
        {"type": "message", "user": "U1", "text": "<@U2> can you look at the QA plan?"},
        {"type": "message", "user": "U2", "text": "on it"}]},
    {"id": "C2", "name": "random", "is_im": False, "messages": [{"type": "message", "user": "U1", "text": "lunch?"}]},
    {"id": "D1", "name": "DM", "is_im": True, "messages": [{"type": "message", "user": "U1", "text": "can we talk tomorrow"}]},
]}
JIRA = {"issues": [
    {"key": "CS-12", "fields": {"summary": "Fix routing rule for tier-1", "status": {"name": "In Progress"}, "assignee": {"displayName": "Alex Rivera"},
                                "updated": "2026-09-08T09:00:00.000+0200", "priority": {"name": "High"}, "issuetype": {"name": "Bug"}, "project": {"key": "CS"}}},
    {"key": "CS-13", "fields": {"summary": "Write QA plan", "status": {"name": "Done"}, "assignee": None, "updated": "2026-09-07T18:00:00.000+0200",
                                "priority": None, "issuetype": {"name": "Task"}, "project": {"key": "CS"}}},
]}


class SourceDigestTests(unittest.TestCase):
    def test_calendar_digest(self):
        d = calendar.digest_events(CAL)
        self.assertEqual(d["count"], 2, "cancelled events dropped")
        self.assertIn("- 10:00 Weekly 1-1 Alex (30 min) — with Alex Rivera · Meet", d["text"])
        self.assertIn("- all-day Offsite — with P0, P1, P2, P3 +2", d["text"])
        self.assertLess(len(d["text"]), 400)

    def test_drive_changes_flag_transcripts(self):
        d = drive.digest_changes(DRIVE)
        self.assertEqual(len(d["transcripts"]), 1)
        self.assertIn("**meeting transcript**", d["text"])
        self.assertIn("Sheet “Budget 2027” — by me", d["text"])

    def test_transcript_first_selection(self):
        both = drive.extract_transcript(DOC_BOTH)
        self.assertEqual(both["transcript_source"], "verbatim"); self.assertEqual(both["tab"], "Transcript")
        self.assertIn("Alex: we should revisit training.", both["text"]); self.assertNotIn("AI summary", both["text"])
        only = drive.extract_transcript(DOC_SUMMARY_ONLY)
        self.assertEqual(only["transcript_source"], "summary-fallback"); self.assertIn("needs-review", only["warning"])
        plain = drive.extract_transcript(DOC_PLAIN)
        self.assertEqual(plain["transcript_source"], "full-document"); self.assertIn("Plain text body", plain["text"])

    def test_slack_digest_clusters_and_mentions(self):
        d = slack.digest_activity(SLACK, user_id="U2", ignore=["#random"])
        self.assertEqual([c["channel"] for c in d["channels"]], ["onboarding"], "ignored channel dropped, sorted by volume")
        self.assertEqual(d["channels"][0]["mine"], 1); self.assertEqual(d["channels"][0]["threads"], 1)
        self.assertEqual(len(d["mentions"]), 1); self.assertIn("mention in #onboarding by Alex Rivera", d["text"])
        self.assertIn("- DM with Alex Rivera: 1 msgs", d["text"])
        self.assertEqual(d["count"], 4)

    def test_jira_digest(self):
        d = jira.digest_issues(JIRA)
        self.assertEqual(d["by_status"], {"In Progress": 1, "Done": 1})
        self.assertIn("- CS-12 [In Progress] Fix routing rule for tier-1 — Alex Rivera · High", d["text"])
        self.assertIn("- CS-13 [Done] Write QA plan — unassigned", d["text"])

    def test_missing_credentials_raise_clean_errors(self):
        from second_brain.sources import SourceError, google
        import os
        for k in ("GOOGLE_CLIENT_ID", "SLACK_BOT_TOKEN", "JIRA_BASE_URL"):
            os.environ.pop(k, None)
        google._cache.update(token=None, exp=0)
        with self.assertRaises(SourceError): google.access_token()
        with self.assertRaises(SourceError): slack._call("conversations.list")
        with self.assertRaises(SourceError): jira.fetch_issues()


if __name__ == "__main__":
    unittest.main()
