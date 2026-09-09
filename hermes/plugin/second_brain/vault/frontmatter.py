"""Minimal YAML frontmatter reader/writer for vault notes.

Deliberately stdlib-only and limited to the subset the vault schemas use:
scalars, quoted strings, inline lists (`[a, "b"]`), block lists (`- item`).
Unknown keys are preserved; nothing is reordered on rewrite.
"""
from __future__ import annotations

import re
from typing import Any

FENCE = "---"
_INLINE_LIST = re.compile(r"^\[(.*)\]$")


def split(text: str) -> tuple[list[str], str]:
    """Return (frontmatter_lines, body) — frontmatter_lines empty if none."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != FENCE:
        return [], text
    for i in range(1, len(lines)):
        if lines[i].strip() == FENCE:
            return lines[1:i], "\n".join(lines[i + 1 :])
    return [], text


def _unquote(v: str) -> Any:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v == "true":
        return True
    if v == "false":
        return False
    return v


def _split_inline_list(inner: str) -> list[Any]:
    items, cur, depth, quote = [], "", 0, None
    for ch in inner:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            cur += ch
        elif ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            items.append(_unquote(cur))
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(_unquote(cur))
    return items


def _strip_comment(v: str) -> str:
    # drop a trailing `# comment` that is not inside quotes
    out, quote = "", None
    for ch in v:
        if quote:
            out += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out += ch
        elif ch == "#":
            break
        else:
            out += ch
    return out.rstrip()


def parse(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    key: str | None = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith(("  - ", "- ")) and key is not None:
            data.setdefault(key, [])
            if not isinstance(data[key], list):
                data[key] = []
            data[key].append(_unquote(_strip_comment(raw.split("-", 1)[1])))
            continue
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        key = k.strip()
        v = _strip_comment(v)
        if v == "":
            data[key] = ""
            continue
        m = _INLINE_LIST.match(v.strip())
        if m:
            data[key] = _split_inline_list(m.group(1))
        else:
            data[key] = _unquote(v)
    return data


_NEEDS_QUOTE = re.compile(r"[:#\[\]{}\"']|^\s|\s$|^[-?&*!|>%@`]")


def _render_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    if s == "" or _NEEDS_QUOTE.search(s) or s.lower() in ("true", "false", "null", "yes", "no"):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def render(data: dict[str, Any]) -> str:
    out = [FENCE]
    for k, v in data.items():
        if isinstance(v, list):
            out.append(f"{k}: [" + ", ".join(_render_scalar(x) for x in v) + "]")
        else:
            out.append(f"{k}: {_render_scalar(v)}")
    out.append(FENCE)
    return "\n".join(out)


def read(text: str) -> tuple[dict[str, Any], str]:
    fm_lines, body = split(text)
    return parse(fm_lines), body


def write(data: dict[str, Any], body: str) -> str:
    body = body.lstrip("\n")
    return render(data) + "\n\n" + body
