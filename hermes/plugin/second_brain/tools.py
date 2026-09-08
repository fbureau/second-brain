"""Tool handlers: `def handler(args: dict, **kwargs) -> str` returning JSON, errors as {"error": ...}."""
from __future__ import annotations

import json
from typing import Callable

from .vault import Vault, VaultError

_vault_path_getter: Callable[[], str | None] = lambda: None  # set by register()


def configure(getter: Callable[[], str | None]) -> None:
    global _vault_path_getter
    _vault_path_getter = getter


def _vault() -> Vault:
    return Vault.locate(_vault_path_getter())


def _ok(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _guard(fn):
    def wrapper(args: dict, **kwargs) -> str:
        try:
            return _ok(fn(args or {}))
        except VaultError as e:
            return _ok({"error": str(e)})
        except Exception as e:  # never raise into the agent loop
            return _ok({"error": f"{type(e).__name__}: {e}"})
    wrapper.__name__ = fn.__name__
    return wrapper


@_guard
def sb_brief(args):
    return _vault().brief()


@_guard
def sb_search(args):
    v = _vault()
    hits = v.search(args["query"], folder=args.get("folder"), note_type=args.get("type"),
                    limit=int(args.get("limit") or 8))
    return {"query": args["query"], "results": hits, "silence": not hits}


@_guard
def sb_read(args):
    v = _vault()
    fm, body = v.read_note(args["path"])
    limit = int(args.get("max_chars") or 6000)
    truncated = len(body) > limit
    return {"path": args["path"], "frontmatter": fm, "body": body[:limit], "truncated": truncated}


@_guard
def sb_find_person(args):
    return _vault().find_person(args["name"])


@_guard
def sb_create_note(args):
    v = _vault()
    res = v.create_note(args["type"], args.get("fields") or {}, args.get("preamble", ""),
                        args.get("sections") or {}, slug=args.get("slug"), name=args.get("name"))
    res["next"] = ("create stubs for missing_links (wiki: sb_create_note type=wiki; people: ask the user first), "
                   "then sb_daily_append, then sb_commit") if res["missing_links"] else "sb_daily_append, then sb_commit"
    return res


@_guard
def sb_append_timeline(args):
    return _vault().append_timeline(args["path"], args["title"], args["lines"], date=args.get("date"),
                                    marker=args.get("marker"))


@_guard
def sb_append_section(args):
    return _vault().append_section(args["path"], args["heading"], args["lines"])


@_guard
def sb_daily_append(args):
    return _vault().daily_append(args["section"], args["line"], date=args.get("date"))


@_guard
def sb_new_action(args):
    v = _vault()
    return {"line": v.new_action(args["text"], owner=args.get("owner") or "me", due=args.get("due"),
                                 source_tag=args.get("source_tag") or "daily")}


@_guard
def sb_curate(args):
    return _vault().curate(args["path"], action=args.get("action") or "added")


@_guard
def sb_commit(args):
    return _vault().commit(args["message"])


HANDLERS = {
    "sb_brief": sb_brief, "sb_search": sb_search, "sb_read": sb_read, "sb_find_person": sb_find_person,
    "sb_create_note": sb_create_note, "sb_append_timeline": sb_append_timeline,
    "sb_append_section": sb_append_section, "sb_daily_append": sb_daily_append, "sb_new_action": sb_new_action,
    "sb_curate": sb_curate, "sb_commit": sb_commit,
}
