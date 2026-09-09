"""Google OAuth2 (refresh-token flow) shared by Calendar, Drive and Docs.

Env: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN — obtain the refresh
token once with the OAuth playground or a one-off consent script (scopes: calendar.readonly,
drive.readonly, documents.readonly).
"""
from __future__ import annotations

import os
import time

from .http import SourceError, request_json

TOKEN_URL = "https://oauth2.googleapis.com/token"
_cache: dict = {"token": None, "exp": 0.0}


def access_token() -> str:
    if _cache["token"] and time.time() < _cache["exp"] - 60:
        return _cache["token"]
    cid, sec, rt = (os.environ.get(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"))
    if not (cid and sec and rt):
        raise SourceError("Google credentials missing: set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN")
    res = request_json(TOKEN_URL, data={"client_id": cid, "client_secret": sec, "refresh_token": rt,
                                        "grant_type": "refresh_token"}, form=True)
    _cache["token"], _cache["exp"] = res["access_token"], time.time() + int(res.get("expires_in", 3600))
    return _cache["token"]


def get(url: str, params: dict | None = None) -> dict:
    return request_json(url, params=params, headers={"Authorization": f"Bearer {access_token()}"})
