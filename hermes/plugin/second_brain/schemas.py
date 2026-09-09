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

SB_MAINTAIN = {
    "name": "sb_maintain",
    "description": "Run the deterministic maintenance pass: sync every action item into TODO.md both ways (assign "
                   "anchors, reconcile checked boxes, bucket by due date), rebuild domain hubs and _INDEX.md, refresh "
                   "staleness flags, audit health. Returns a report plus needs_judgment — the cases only you can decide "
                   "(unassigned owners, removed sources, zombie tasks, near-duplicates, hub proposals). Use apply=false "
                   "for a dry run.",
    "parameters": {"type": "object", "properties": {
        "scope": {"type": "string", "description": "all | tasks | curator | staleness | health (default all)"},
        "apply": {"type": "boolean", "description": "Write changes (default true)."}},
        "required": []},
}

SB_TOGGLE_TASK = {
    "name": "sb_toggle_task",
    "description": "Mark a task done (or reopen it) in its SOURCE note by anchor, stamping ✅ date. Use when the user "
                   "says they finished something that has a ^t-id; then sb_maintain(scope=tasks) refreshes TODO.md.",
    "parameters": {"type": "object", "properties": {
        "anchor": {"type": "string", "description": "The 6-char anchor (with or without ^t-)."},
        "done": {"type": "boolean", "description": "true = done (default), false = reopen"}},
        "required": ["anchor"]},
}

SB_VAULT_ACTIVITY = {
    "name": "sb_vault_activity",
    "description": "Notes created or modified in the vault during the window (git history + mtimes). The 'internal "
                   "vault' source of the daily digest.",
    "parameters": {"type": "object", "properties": {
        "since_hours": {"type": "integer", "description": "Window in hours (default 24)."},
        "limit": {"type": "integer"}},
        "required": []},
}

SB_CALENDAR = {
    "name": "sb_calendar",
    "description": "Google Calendar events of a day as a compact digest (time, title, duration, attendees, Meet). "
                   "Use for the daily digest and to cross-check meetings before ingesting transcripts.",
    "parameters": {"type": "object", "properties": {
        "day": {"type": "string", "description": "YYYY-MM-DD (default today)."}},
        "required": []},
}

SB_DRIVE_CHANGES = {
    "name": "sb_drive_changes",
    "description": "Google Drive files modified in the window, compact, with meeting transcripts flagged. Use for the "
                   "daily digest; hand transcript ids to sb_drive_doc / meeting-ingest.",
    "parameters": {"type": "object", "properties": {
        "since_hours": {"type": "integer", "description": "Window in hours (default 24)."}},
        "required": []},
}

SB_DRIVE_DOC = {
    "name": "sb_drive_doc",
    "description": "Read a Google Doc as text applying the transcript-first rule: the 'Transcript' tab if present "
                   "(transcript_source=verbatim), else a summary tab (summary-fallback → confidence: medium, "
                   "needs-review: true), else the whole document. Use before ingesting a meeting from Drive.",
    "parameters": {"type": "object", "properties": {
        "file_or_url": {"type": "string", "description": "Drive file id or docs.google.com URL."},
        "max_chars": {"type": "integer", "description": "Truncate after N chars (default 60000)."}},
        "required": ["file_or_url"]},
}

SB_SLACK = {
    "name": "sb_slack",
    "description": "Slack activity in the window, clustered per channel (volume, top posters, your posts, threads), plus "
                   "DMs and mentions of you. Compact — the raw messages never enter the context.",
    "parameters": {"type": "object", "properties": {
        "since_hours": {"type": "integer", "description": "Window in hours (default 24)."},
        "ignore_channels": {"type": "array", "items": {"type": "string"}, "description": "Channels to skip (from MY-PROFILE chat-channels-to-ignore)."}},
        "required": []},
}

SB_JIRA = {
    "name": "sb_jira",
    "description": "Jira issues that moved in the window (assigned to / reported by / watched by you), compact with "
                   "status counts. Optional custom JQL.",
    "parameters": {"type": "object", "properties": {
        "since_hours": {"type": "integer", "description": "Window in hours (default 24)."},
        "jql": {"type": "string", "description": "Override JQL (default: my issues updated in the window)."}},
        "required": []},
}

# --------------------------------------------------------------------------- analysis (phase 4)

SB_RECALL = {
    "name": "sb_recall",
    "description": "Answer-grade evidence for a question about what the user already knows: the notes that match, "
                   "the exact lines, a date for each, and a confidence level (stated | high | medium | speculation | "
                   "unknown). Use before answering ANY 'what do I know / did we decide / have I talked to' question. "
                   "confidence=unknown means the vault does not know — say that instead of guessing.",
    "parameters": {"type": "object", "properties": {
        "question": {"type": "string", "description": "The question in the user's own words."},
        "limit": {"type": "integer", "description": "Max notes to consider (default 6)."}},
        "required": ["question"]},
}

SB_AGENDA = {
    "name": "sb_agenda",
    "description": "Everything needed to prioritise, gathered but deliberately NOT ranked: open tasks by due date, "
                   "what is waiting on others, active projects and which have gone quiet, cooling relationships, "
                   "recent vault activity, and a 'signals' list of tensions to resolve. You do the ranking.",
    "parameters": {"type": "object", "properties": {
        "horizon_days": {"type": "integer", "description": "Upcoming window in days (default 7)."},
        "calendar": {"type": "array", "items": {"type": "object"}, "description": "Optional events from sb_calendar to fold in."}},
        "required": []},
}

SB_DECISION_CONTEXT = {
    "name": "sb_decision_context",
    "description": "Prior art before a decision (red-team mode): comparable past decisions with reversed ones first, "
                   "the stakeholders they named, related lessons, and committed reversal conditions nobody revisited. "
                   "Use before arguing against a decision so the challenge rests on this vault, not on generalities.",
    "parameters": {"type": "object", "properties": {
        "subject": {"type": "string", "description": "The decision or plan being considered, in one or two sentences."},
        "limit": {"type": "integer", "description": "Max precedents per list (default 5)."}},
        "required": ["subject"]},
}

SB_DECISION_POSTMORTEM = {
    "name": "sb_decision_postmortem",
    "description": "Propagation surface of a reversed decision: its rationale and reversal conditions, notes that link "
                   "to it, notes resting on the same hypothesis, and the stakeholders involved. Use when a note in "
                   "05-decisions/ flips to status: reversed, to run the learning loop.",
    "parameters": {"type": "object", "properties": {
        "path": {"type": "string", "description": "Vault-relative path of the reversed decision note."}},
        "required": ["path"]},
}

SB_TEND = {
    "name": "sb_tend",
    "description": "Whole-vault maintenance audit, preview-first. Returns safe_fixes (frontmatter with one correct "
                   "value) and proposals (language drift, missing preambles, broken links, duplicate people, archive "
                   "candidates) with the evidence for each. NOTHING is applied unless apply_safe=true, and proposals "
                   "are never applied automatically — show them, ask, then act through the write tools.",
    "parameters": {"type": "object", "properties": {
        "scope": {"type": "string", "enum": ["all", "frontmatter", "language", "links", "duplicates", "archive"],
                  "description": "What to audit (default all)."},
        "apply_safe": {"type": "boolean", "description": "Write the safe frontmatter fixes (default false)."},
        "target_language": {"type": "string", "description": "Flag note bodies not in this language, e.g. 'fr'."}},
        "required": []},
}

SB_BACKFILL_PLAN = {
    "name": "sb_backfill_plan",
    "description": "Ordered work plan for the one-shot Day-1 backfill: date-windowed batches sized to fit one session, "
                   "entity phases first so people and projects are deduplicated before meetings are ingested, plus the "
                   "names already in the vault. Resumes from the state note if a previous run was interrupted.",
    "parameters": {"type": "object", "properties": {
        "since": {"type": "string", "description": "Start date, YYYY-MM-DD."},
        "until": {"type": "string", "description": "End date, YYYY-MM-DD (default today)."},
        "batch_days": {"type": "integer", "description": "Days per batch (default 14)."},
        "sources": {"type": "array", "items": {"type": "string"}, "description": "Sources to draw from, e.g. ['calendar','drive','slack']."}},
        "required": ["since"]},
}

SB_BACKFILL_DONE = {
    "name": "sb_backfill_done",
    "description": "Tick one backfill batch as fully ingested and committed, so an interrupted run resumes after it "
                   "instead of re-ingesting. Call it only after the batch's notes are committed.",
    "parameters": {"type": "object", "properties": {
        "batch_id": {"type": "string", "description": "Batch id from sb_backfill_plan, e.g. 'meetings-2026-05-01'."}},
        "required": ["batch_id"]},
}

ALL_VAULT = [SB_BRIEF, SB_SEARCH, SB_READ, SB_FIND_PERSON, SB_CREATE_NOTE, SB_APPEND_TIMELINE, SB_APPEND_SECTION,
             SB_DAILY_APPEND, SB_NEW_ACTION, SB_CURATE, SB_COMMIT, SB_MAINTAIN, SB_TOGGLE_TASK, SB_VAULT_ACTIVITY,
             SB_RECALL, SB_AGENDA, SB_DECISION_CONTEXT, SB_DECISION_POSTMORTEM, SB_TEND, SB_BACKFILL_PLAN,
             SB_BACKFILL_DONE]
ALL_SOURCES = [SB_CALENDAR, SB_DRIVE_CHANGES, SB_DRIVE_DOC, SB_SLACK, SB_JIRA]
ALL = ALL_VAULT + ALL_SOURCES
