"""Tiny HTTP helper (stdlib only)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class SourceError(Exception):
    pass


def request_json(url: str, params: dict | None = None, headers: dict | None = None, data: dict | bytes | None = None,
                 method: str | None = None, form: bool = False, timeout: int = 30) -> dict:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
    body = None
    hdrs = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, (bytes, bytearray)):
            body = bytes(data)
        else:
            body = json.dumps(data).encode()
            hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise SourceError(f"HTTP {e.code} from {url.split('?')[0]}: {detail}") from None
    except urllib.error.URLError as e:
        raise SourceError(f"network error reaching {url.split('?')[0]}: {e.reason}") from None


def clip(s: str | None, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"
