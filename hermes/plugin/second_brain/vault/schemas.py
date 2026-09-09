"""Executable mirror of the vault contract (`vault-starter/_CLAUDE.md`, section 4).

One entry per `type:`. `create_note()` validates against this table, so a note that
violates the contract cannot be written. Keep in sync with `_CLAUDE.md` — the
conformance tests run every generated note through `hooks/pre-commit`.
"""
from __future__ import annotations

UNIVERSAL_REQUIRED = ("date", "type", "tags")
APPEND_ONLY_FOLDERS = ("02-people", "05-decisions")

CONFIDENCE = ["stated", "high", "medium", "speculation"]

TYPES: dict[str, dict] = {
    "braindump": {
        "folder": "00-inbox",
        "filename": "{date}-{hhmm}-{slug}.md",
        "base_tag": "braindump",
        "required": ["domain", "energy"],
        "enums": {
            "domain": ["personal", "professional", "project-specific", "mixed"],
            "energy": ["low", "medium", "high"],
        },
        "defaults": {"related-people": [], "related-projects": []},
        "sections": ["Raw content", "Insight", "Tension / Open question", "Links", "Suggested follow-up"],
    },
    "meeting": {
        "folder": "04-meetings",
        "filename": "{date}-{slug}.md",
        "base_tag": "meeting",
        "required": ["participants", "meeting-type"],
        "enums": {
            "meeting-type": ["1-1", "team-sync", "stakeholder", "external", "townhall"],
            "transcript-source": ["verbatim", "summary-fallback"],
            "confidence": ["high", "medium"],
            "ingestion-mode": ["manual", "auto", "auto-validated"],
        },
        "defaults": {"ingested": "{today}", "source": "pasted transcript", "transcript-source": "verbatim",
                     "confidence": "high"},
        "sections": ["Context", "Participants", "Decisions", "Action items", "Strategic themes", "Key quotes",
                     "Tensions / Disagreements", "Unresolved", "Dynamics", "Links"],
    },
    "person": {
        "folder": "02-people",
        "filename": "{name}.md",
        "base_tag": "person",
        "required": ["relationship"],
        "enums": {
            "region": ["WE", "NA", "LATAM", "APAC", "Global"],
            "relationship": ["direct-report", "peer", "manager", "stakeholder", "external", "external-alumni"],
        },
        "defaults": {"updated": "{today}", "role": "", "company": "", "team": "", "languages": ["en"],
                     "last-interaction": "{today}", "staleness-flag": ""},
        "sections": ["Compiled truth", "Timeline", "Open threads", "Links"],
        "append_only": True,
    },
    "project": {
        "folder": "03-projects",
        "filename": "{slug}.md",
        "base_tag": "project",
        "required": ["status"],
        "enums": {
            "status": ["active", "planning", "completed", "archived", "on-hold"],
            "priority": ["high", "medium", "low"],
        },
        "defaults": {"updated": "{today}", "related-people": [], "related-projects": []},
        "sections": ["Goal", "Success criteria", "Stakeholders", "Key decisions", "Timeline",
                     "Risks & dependencies", "Lessons learned (as we go)", "Links"],
    },
    "decision": {
        "folder": "05-decisions",
        "filename": "{date}-{slug}.md",
        "base_tag": "decision",
        "required": ["status", "reversibility"],
        "enums": {
            "status": ["proposed", "committed", "implemented", "reversed"],
            "reversibility": ["reversible", "hard-to-reverse", "one-way"],
            "confidence": ["high", "medium", "speculation"],
        },
        "defaults": {"stakeholders": []},
        "sections": ["Decision", "Context", "Options considered", "Rationale", "Counter-evidence addressed",
                     "Reversal conditions", "Expected impact", "Execution plan", "Timeline (post-decision)", "Links"],
        "append_only": True,
    },
    "daily": {
        "folder": "01-daily",
        "filename": "{date}.md",
        "base_tag": "daily",
        "required": [],
        "enums": {},
        "defaults": {},
        "sections": ["TL;DR (3 lines)", "Decisions & commitments", "Top topics of the day", "Weak signals to dig into",
                     "Pending follow-ups", "People touched today", "Inputs of the day", "Thinking",
                     "Braindumps of the day", "Meetings ingested today", "Docs ingested today"],
    },
    "knowledge": {
        "folder": "06-knowledge",
        "filename": "{slug}.md",
        "base_tag": "knowledge",
        "required": ["domain"],
        "enums": {"confidence": ["high", "medium", "speculation"]},
        "defaults": {"updated": "{today}", "confidence": "medium", "needs-review": True},
        "sections": ["What we know", "Evidence", "Anti-patterns / caveats", "Links"],
    },
    "wiki": {
        "folder": "06-knowledge",
        "filename": "{slug}.md",
        "base_tag": "wiki",
        "required": ["domain"],
        "enums": {"confidence": CONFIDENCE},
        "defaults": {"updated": "{today}", "aliases": [], "confidence": "speculation", "needs-review": True,
                     "created-from": ""},
        "sections": ["Summary", "What we know", "Open questions / unknowns", "Related", "Sources"],
    },
    "doc": {
        "folder": "06-knowledge/_sources",
        "filename": "{date}-{slug}.md",
        "base_tag": "doc",
        "required": ["domain", "doc-type", "source"],
        "enums": {
            "doc-type": ["strategy", "analysis", "report", "deck", "spec", "research", "external-article"],
            "confidence": ["high", "medium", "speculation"],
        },
        "defaults": {"doc-date": "unknown", "related-people": [], "confidence": "medium"},
        "sections": ["Thesis", "Key claims", "Data points", "Recommendations / proposed decisions",
                     "Open questions / gaps", "Action items", "Links"],
    },
    "index": {
        "folder": "06-knowledge",
        "filename": "{slug}.md",
        "base_tag": "index",
        "required": [],
        "enums": {},
        "defaults": {"updated": "{today}", "auto-maintained": True},
        "sections": ["Summary", "Wiki pages", "Lessons", "Source documents", "Recent activity", "Open questions"],
    },
}

# Daily-note sections other skills append into (must match templates/daily.md).
DAILY_SECTIONS = {
    "braindump": "Braindumps of the day",
    "meeting": "Meetings ingested today",
    "doc": "Docs ingested today",
    "people": "People touched today",
    "thinking": "Thinking",
    "follow-ups": "Pending follow-ups",
}

# Which hub listing section a knowledge note belongs to.
HUB_SECTION_BY_TYPE = {"wiki": "Wiki pages", "knowledge": "Lessons", "doc": "Source documents"}


def is_append_only(rel_path: str) -> bool:
    return any(rel_path.startswith(f"{f}/") for f in APPEND_ONLY_FOLDERS)
