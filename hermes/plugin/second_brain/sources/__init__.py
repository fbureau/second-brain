"""Source connectors → compact digests for a small model.

Each module separates `fetch_*` (network, stdlib urllib, credentials from env) from
`digest_*` (pure: raw API JSON → short markdown). Tools call fetch then digest; tests
feed fixtures to digest. The model never sees raw API payloads.
"""
from __future__ import annotations

from . import calendar, drive, jira, slack  # noqa: F401
from .http import SourceError  # noqa: F401

REQUIRED_ENV = {
    "google": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"],
    "slack": ["SLACK_BOT_TOKEN"],
    "jira": ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"],
}
