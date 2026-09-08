"""LLM-visible tool schemas. Descriptions say WHEN to call — small models rely on it."""

_PATH = {"type": "string", "description": "Vault-relative note path, e.g. 02-people/Alex Rivera.md"}
_LINES = {"type": "array", "items": {"type": "string"}, "description": "Markdown lines to append (bullets)."}

SB_BRIEF = {
    "name": "sb_brief",
    "description": "Call this FIRST in any vault task. Returns the compact operating brief: vault path, working "
                   "language, the non-negotiable rules, the user's profile essentials and note counts (~500 tokens). "
                   "Replaces reading _CLAUDE.md and MY-PROFILE.md in full.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

SB_SEARCH = {
    "name": "sb_search",
    "description": "Find candidate notes for a topic, person or project before writing or answering (hub-first, "
                   "frontmatter-aware). Returns paths, types and a snippet. Use it to check whether something already "
                   "exists and to gather citations for recall.",
    "parameters": {"type": "object", "properties": {
        "query": {"type": "string", "description": "Keywords (names, topics, project)."},
        "folder": {"type": "string", "description": "Optional folder to scope, e.g. 05-decisions or 06-knowledge."},
        "type": {"type": "string", "description": "Optional note type filter: person, project, decision, meeting, wiki, knowledge, doc, daily, braindump."},
        "limit": {"type": "integer", "description": "Max results (default 8)."}},
        "required": ["query"]},
}

SB_READ = {
    "name": "sb_read",
    "description": "Read one note (frontmatter + body). Use after sb_search to get the actual content of a note you "
                   "will cite, enrich or append to.",
    "parameters": {"type": "object", "properties": {
        "path": _PATH,
        "max_chars": {"type": "integer", "description": "Truncate the body after this many characters (default 6000)."}},
        "required": ["path"]},
}

SB_FIND_PERSON = {
    "name": "sb_find_person",
    "description": "Fuzzy-match a person's name against 02-people/. ALWAYS call before creating a person note or "
                   "linking a person. match=exact/likely → use the returned path; ambiguous → ask the user; "
                   "none → ask the user before creating.",
    "parameters": {"type": "object", "properties": {
        "name": {"type": "string", "description": "Name as mentioned (full or partial)."}},
        "required": ["name"]},
}

SB_CREATE_NOTE = {
    "name": "sb_create_note",
    "description": "Create a new note of a given type. The tool generates frontmatter, path and the '## For future "
                   "Claude' preamble block from your inputs, validates enums and refuses to overwrite. Returns the path "
                   "and any wikilinks whose target does not exist yet (create stubs for them).",
    "parameters": {"type": "object", "properties": {
        "type": {"type": "string", "description": "braindump | meeting | person | project | decision | daily | knowledge | wiki | doc | index"},
        "fields": {"type": "object", "description": "Frontmatter fields for the type, e.g. {\"domain\":\"professional\",\"energy\":\"medium\",\"tags\":[\"training\"]}. date defaults to today."},
        "preamble": {"type": "string", "description": "2-3 sentences IN ENGLISH: what this note is, why it was written, when."},
        "sections": {"type": "object", "description": "Body sections as {\"Heading\": \"markdown content\"}; use the type's standard headings (e.g. braindump: Raw content, Insight, Tension / Open question, Links, Suggested follow-up). Write these in the working language."},
        "slug": {"type": "string", "description": "3-5 words describing the content (used for the filename)."},
        "name": {"type": "string", "description": "For type=person only: 'First Last' — becomes the filename."}},
        "required": ["type", "fields", "preamble"]},
}

SB_APPEND_TIMELINE = {
    "name": "sb_append_timeline",
    "description": "Append a dated entry to the '## Timeline' of a person, project or decision note (append-only "
                   "zones). Also stamps updated/last-interaction and clears a staleness flag. Never edit those notes "
                   "any other way.",
    "parameters": {"type": "object", "properties": {
        "path": _PATH,
        "title": {"type": "string", "description": "Entry title, e.g. 'Weekly 1-1' or 'Daily interactions'."},
        "lines": {"type": "array", "items": {"type": "string"}, "description": "Bullets: 'Source: …', 'What: …', 'Observation: …', '[ ] Follow-up: … — owner: me' (checkbox form makes it a task)."},
        "date": {"type": "string", "description": "YYYY-MM-DD (default today)."},
        "marker": {"type": "string", "description": "Optional protected marker, e.g. '(auto-logged)'. Omit for manual entries."}},
        "required": ["path", "title", "lines"]},
}

SB_APPEND_SECTION = {
    "name": "sb_append_section",
    "description": "Append lines at the end of a '## Section' of an existing note (created if missing). Use for wiki "
                   "'What we know' facts with citations, 'Sources' audit-trail entries, 'Open threads', 'Links'. "
                   "Never use it to rewrite content.",
    "parameters": {"type": "object", "properties": {
        "path": _PATH,
        "heading": {"type": "string", "description": "Section heading without '## '."},
        "lines": _LINES},
        "required": ["path", "heading", "lines"]},
}

SB_DAILY_APPEND = {
    "name": "sb_daily_append",
    "description": "Append one line to a section of today's daily note (created if missing). Sections: 'Braindumps "
                   "of the day', 'Meetings ingested today', 'Docs ingested today', 'People touched today', 'Thinking', "
                   "'Pending follow-ups'. Call it after every capture so nothing is orphaned.",
    "parameters": {"type": "object", "properties": {
        "section": {"type": "string"},
        "line": {"type": "string", "description": "One markdown bullet, e.g. '- [[00-inbox/2026-06-01-0900-slug]] — topic'."},
        "date": {"type": "string", "description": "YYYY-MM-DD (default today)."}},
        "required": ["section", "line"]},
}

SB_NEW_ACTION = {
    "name": "sb_new_action",
    "description": "Format an action item in the vault's task-line convention with a fresh stable ^t-id anchor. Put the "
                   "returned line into the note section (e.g. 'Suggested follow-up', 'Action items'); task-roundup "
                   "will pull it into TODO.md.",
    "parameters": {"type": "object", "properties": {
        "text": {"type": "string", "description": "The action, imperative, one line."},
        "owner": {"type": "string", "description": "'me' (default) or a person wikilink [[02-people/Name]]."},
        "due": {"type": "string", "description": "YYYY-MM-DD if known; omit otherwise (never invent a date)."},
        "source_tag": {"type": "string", "description": "meeting | decision | daily | 1-1 | braindump | email | chat | doc (default daily)."}},
        "required": ["text"]},
}

SB_CURATE = {
    "name": "sb_curate",
    "description": "Route a wiki page, lesson or source doc into its domain hub (or _INDEX.md Unsorted) and refresh "
                   "counts. Call after creating or enriching any note in 06-knowledge/.",
    "parameters": {"type": "object", "properties": {
        "path": _PATH,
        "action": {"type": "string", "description": "Recent-activity verb: 'stub created' | 'enriched' | 'added' (default)."}},
        "required": ["path"]},
}

SB_COMMIT = {
    "name": "sb_commit",
    "description": "Commit all vault changes with a message. The vault's pre-commit hook validates AI-first compliance "
                   "and append-only history; if it rejects, fix the note and call again. Call once at the end of a task.",
    "parameters": {"type": "object", "properties": {
        "message": {"type": "string", "description": "Conventional summary, e.g. 'braindump: onboarding script friction'."}},
        "required": ["message"]},
}

ALL = [SB_BRIEF, SB_SEARCH, SB_READ, SB_FIND_PERSON, SB_CREATE_NOTE, SB_APPEND_TIMELINE, SB_APPEND_SECTION,
       SB_DAILY_APPEND, SB_NEW_ACTION, SB_CURATE, SB_COMMIT]
