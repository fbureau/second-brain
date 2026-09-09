"""The vault contract as code. Harness-agnostic: no Hermes import here.

Usage:
    v = Vault.locate()             # env SECOND_BRAIN_VAULT, then cwd/parents holding _CLAUDE.md
    v.create_note("braindump", {...}, preamble, sections)
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import (agenda as agenda_mod, activity as activity_mod, backfill, decisions, frontmatter, gitops,  # noqa: F401
               index, links, maintain, notes, recall as recall_mod, schemas, search, tasks, tend as tend_mod)
from .notes import VaultError  # noqa: F401

ENV_VAR = "SECOND_BRAIN_VAULT"
BRIEF_FILE = "_CLAUDE.md"
PROFILE_FILE = "00-inbox/MY-PROFILE.md"


class Vault:
    def __init__(self, root: Path):
        self.root = Path(root).expanduser().resolve()
        if not (self.root / BRIEF_FILE).exists():
            raise VaultError(f"{self.root} does not look like a vault (no {BRIEF_FILE})")

    # ---------------------------------------------------------------- locate
    @classmethod
    def locate(cls, explicit: str | None = None) -> "Vault":
        cands = []
        if explicit:
            cands.append(Path(explicit))
        if os.environ.get(ENV_VAR):
            cands.append(Path(os.environ[ENV_VAR]))
        here = Path.cwd()
        cands += [here, *here.parents]
        for c in cands:
            c = c.expanduser()
            if (c / BRIEF_FILE).exists():
                return cls(c)
        raise VaultError(f"vault not found — set {ENV_VAR} or plugins.entries.second_brain.settings.vault_path")

    # ---------------------------------------------------------------- brief
    def working_language(self) -> str:
        p = self.root / PROFILE_FILE
        if p.exists():
            m = re.search(r"Working language\*\*:\s*`?([a-z]{2})`?", p.read_text(encoding="utf-8"))
            if m:
                return m.group(1)
        return "en"

    def brief(self, max_profile_chars: int = 1800) -> dict:
        """Compact operating brief for a small model (~500 tokens instead of 400 lines)."""
        profile = ""
        p = self.root / PROFILE_FILE
        if p.exists():
            keep = ("## Identity", "## Communication preferences", "## Active projects", "## Critical stakeholders",
                    "## Knowledge domains", "### Sensitive meetings")
            chunks, take = [], False
            for line in p.read_text(encoding="utf-8").split("\n"):
                if line.startswith("#"):
                    take = line.strip() in keep
                if take and line.strip() and not line.startswith("[") and "<" not in line:
                    chunks.append(line.rstrip())
            profile = "\n".join(chunks)[:max_profile_chars]
        counts = {}
        for folder in sorted(d.name for d in self.root.iterdir() if d.is_dir() and re.match(r"^0[0-7]-", d.name)):
            counts[folder] = sum(1 for f in (self.root / folder).rglob("*.md") if f.name != "README.md")
        return {
            "vault": str(self.root),
            "working_language": self.working_language(),
            "rules": [
                "Note bodies in the working language; the 'For future Claude' preamble is always English.",
                "Date every external claim inline: (as of YYYY-MM).",
                "Cite sources verbatim (URL or note path); never invent sources or dates — write 'unknown'.",
                "Every person/project/concept is a [[wikilink]]; create a stub rather than skip a link.",
                "Confidence levels when relevant: stated | high | medium | speculation.",
                "02-people/ and 05-decisions/ are append-only: use sb_append_timeline, never rewrite.",
                "Never create a person note without sb_find_person first, and ask the user before creating one.",
                "The tools enforce frontmatter/preamble/paths — you supply the content and the judgment.",
            ],
            "profile": profile,
            "note_counts": counts,
            "types": {t: s["folder"] for t, s in schemas.TYPES.items()},
        }

    # ---------------------------------------------------------------- thin wrappers
    def read_note(self, rel: str):
        return notes.read_note(self.root, rel)

    def create_note(self, *a, **kw):
        return notes.create_note(self.root, *a, **kw)

    def append_section(self, *a, **kw):
        return notes.append_section(self.root, *a, **kw)

    def append_timeline(self, *a, **kw):
        return notes.append_timeline(self.root, *a, **kw)

    def daily_append(self, *a, **kw):
        return notes.daily_append(self.root, *a, **kw)

    def find_person(self, name: str):
        def aliases_of(p: Path):
            fm, _ = frontmatter.read(p.read_text(encoding="utf-8"))
            al = fm.get("aliases", [])
            return al if isinstance(al, list) else []
        return links.find_person(self.root, name, aliases_of)

    def search(self, *a, **kw):
        return search.search(self.root, *a, **kw)

    def new_action(self, *a, **kw):
        return tasks.action_line(self.root, *a, **kw)

    def curate(self, rel: str, action: str = "added"):
        return index.curator_incremental(self.root, rel, action)

    def commit(self, message: str):
        return gitops.commit(self.root, message)

    def maintain(self, scope: str = "all", apply: bool = True):
        return maintain.run(self.root, scope, apply)

    def set_task_state(self, anchor: str, done: bool):
        return maintain.set_task_state(self.root, anchor, done)

    def activity(self, since_hours: int = 24, limit: int = 40):
        return activity_mod.activity(self.root, since_hours, limit)

    def recall(self, question: str, limit: int = 6):
        return recall_mod.recall(self.root, question, limit)

    def agenda(self, horizon_days: int = 7, calendar: list | None = None):
        return agenda_mod.agenda(self.root, horizon_days, calendar)

    def decision_context(self, subject: str):
        return decisions.context(self.root, subject)

    def decision_postmortem(self, rel: str):
        return decisions.postmortem(self.root, rel)

    def tend(self, scope: str = "all", apply_safe: bool = False, target_language: str | None = None):
        return tend_mod.tend(self.root, scope, apply_safe, target_language)

    def backfill_plan(self, since: str, until: str | None = None, batch_days: int = 14,
                      sources: list | None = None, write_state: bool = True):
        return backfill.plan(self.root, since, until, batch_days, sources, write_state)

    def backfill_done(self, batch_id: str):
        return backfill.mark_batch_done(self.root, batch_id)
