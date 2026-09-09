"""Tool handlers: `def handler(args: dict, **kwargs) -> str` returning JSON, errors as {"error": ...}."""
from __future__ import annotations

import json
import os
from typing import Callable

from .sources import SourceError, calendar, drive, jira, slack
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
        except (VaultError, SourceError) as e:
            return _ok({"error": str(e)})
        except Exception as e:  # never raise into the agent loop
            return _ok({"error": f"{type(e).__name__}: {e}"})
    wrapper.__name__ = fn.__name__
    return wrapper


def _int(v, default):
    try:
        return int(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


# ----------------------------------------------------------------------------- vault

@_guard
def sb_brief(args):
    return _vault().brief()


@_guard
def sb_search(args):
    v = _vault()
    hits = v.search(args["query"], folder=args.get("folder"), note_type=args.get("type"), limit=_int(args.get("limit"), 8))
    return {"query": args["query"], "results": hits, "silence": not hits}


@_guard
def sb_read(args):
    fm, body = _vault().read_note(args["path"])
    limit = _int(args.get("max_chars"), 6000)
    return {"path": args["path"], "frontmatter": fm, "body": body[:limit], "truncated": len(body) > limit}


@_guard
def sb_find_person(args):
    return _vault().find_person(args["name"])


@_guard
def sb_create_note(args):
    res = _vault().create_note(args["type"], args.get("fields") or {}, args.get("preamble", ""),
                               args.get("sections") or {}, slug=args.get("slug"), name=args.get("name"))
    res["next"] = ("create stubs for missing_links (wiki: sb_create_note type=wiki; people: ask the user first), "
                   "then sb_daily_append, then sb_commit") if res["missing_links"] else "sb_daily_append, then sb_commit"
    return res


@_guard
def sb_append_timeline(args):
    return _vault().append_timeline(args["path"], args["title"], args["lines"], date=args.get("date"), marker=args.get("marker"))


@_guard
def sb_append_section(args):
    return _vault().append_section(args["path"], args["heading"], args["lines"])


@_guard
def sb_daily_append(args):
    return _vault().daily_append(args["section"], args["line"], date=args.get("date"))


@_guard
def sb_new_action(args):
    return {"line": _vault().new_action(args["text"], owner=args.get("owner") or "me", due=args.get("due"),
                                        source_tag=args.get("source_tag") or "daily")}


@_guard
def sb_curate(args):
    return _vault().curate(args["path"], action=args.get("action") or "added")


@_guard
def sb_commit(args):
    return _vault().commit(args["message"])


@_guard
def sb_maintain(args):
    apply = args.get("apply", True)
    apply = apply if isinstance(apply, bool) else str(apply).lower() not in ("false", "0", "no")
    res = _vault().maintain(args.get("scope") or "all", apply)
    res["next"] = ("resolve each needs_judgment item (ask the user when it is their call), then sb_commit"
                   if res.get("needs_judgment") else "sb_commit")
    return res


@_guard
def sb_toggle_task(args):
    done = args.get("done", True)
    done = done if isinstance(done, bool) else str(done).lower() not in ("false", "0", "no")
    return _vault().set_task_state(str(args["anchor"]).replace("^t-", ""), done)


@_guard
def sb_vault_activity(args):
    return _vault().activity(_int(args.get("since_hours"), 24), _int(args.get("limit"), 40))


# ----------------------------------------------------------------------------- analysis

@_guard
def sb_recall(args):
    res = _vault().recall(args["question"], _int(args.get("limit"), 6))
    res["next"] = ("Answer from these citations only, giving path and date for each claim. "
                   if res["confidence"] not in ("unknown", "speculation")
                   else "The vault does not know. Say so plainly, do not answer from general knowledge, "
                        "and offer to capture the answer with braindump.")
    return res


@_guard
def sb_agenda(args):
    return _vault().agenda(_int(args.get("horizon_days"), 7), args.get("calendar"))


@_guard
def sb_decision_context(args):
    return _vault().decision_context(args["subject"])


@_guard
def sb_decision_postmortem(args):
    return _vault().decision_postmortem(args["path"])


@_guard
def sb_tend(args):
    apply_safe = args.get("apply_safe", False)
    apply_safe = apply_safe if isinstance(apply_safe, bool) else str(apply_safe).lower() in ("true", "1", "yes")
    return _vault().tend(args.get("scope") or "all", apply_safe, args.get("target_language"))


@_guard
def sb_backfill_plan(args):
    return _vault().backfill_plan(args["since"], args.get("until"), _int(args.get("batch_days"), 14),
                                  args.get("sources"))


@_guard
def sb_backfill_done(args):
    return _vault().backfill_done(str(args["batch_id"]))


# ----------------------------------------------------------------------------- sources

@_guard
def sb_calendar(args):
    v = _vault()
    raw = calendar.fetch_day(args.get("day"))
    return calendar.digest_events(raw)


@_guard
def sb_drive_changes(args):
    raw = drive.fetch_changes(_int(args.get("since_hours"), 24))
    return drive.digest_changes(raw)


@_guard
def sb_drive_doc(args):
    fid = str(args["file_or_url"]).strip()
    if "/d/" in fid:
        fid = fid.split("/d/")[1].split("/")[0]
    return drive.read_doc(fid, _int(args.get("max_chars"), 60000))


@_guard
def sb_slack(args):
    raw = slack.fetch_activity(_int(args.get("since_hours"), 24))
    ignore = args.get("ignore_channels") or []
    return slack.digest_activity(raw, ignore=ignore)


@_guard
def sb_jira(args):
    raw = jira.fetch_issues(_int(args.get("since_hours"), 24), jql=args.get("jql"))
    return jira.digest_issues(raw)


VAULT_HANDLERS = {
    "sb_brief": sb_brief, "sb_search": sb_search, "sb_read": sb_read, "sb_find_person": sb_find_person,
    "sb_create_note": sb_create_note, "sb_append_timeline": sb_append_timeline, "sb_append_section": sb_append_section,
    "sb_daily_append": sb_daily_append, "sb_new_action": sb_new_action, "sb_curate": sb_curate, "sb_commit": sb_commit,
    "sb_maintain": sb_maintain, "sb_toggle_task": sb_toggle_task, "sb_vault_activity": sb_vault_activity,
    "sb_recall": sb_recall, "sb_agenda": sb_agenda, "sb_decision_context": sb_decision_context,
    "sb_decision_postmortem": sb_decision_postmortem, "sb_tend": sb_tend,
    "sb_backfill_plan": sb_backfill_plan, "sb_backfill_done": sb_backfill_done,
}
SOURCE_HANDLERS = {"sb_calendar": sb_calendar, "sb_drive_changes": sb_drive_changes, "sb_drive_doc": sb_drive_doc,
                   "sb_slack": sb_slack, "sb_jira": sb_jira}
SOURCE_ENV = {"sb_calendar": "google", "sb_drive_changes": "google", "sb_drive_doc": "google", "sb_slack": "slack", "sb_jira": "jira"}
HANDLERS = {**VAULT_HANDLERS, **SOURCE_HANDLERS}


def source_available(kind: str) -> bool:
    from .sources import REQUIRED_ENV
    return all(os.environ.get(k) for k in REQUIRED_ENV[kind])
