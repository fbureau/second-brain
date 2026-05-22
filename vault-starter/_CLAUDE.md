---
type: system-brief
updated: 2026-05-22
ai-first: true
---

# _CLAUDE.md — Vault system brief

## For future Claude

You operate inside the user's second brain. This file is your source of truth for
the vault's structure, conventions, and rules. **Read it first in every session
that touches the vault.** The user's personal context lives in
`00-inbox/MY-PROFILE.md` — read that too at preflight.

---

## 1. About the user

Read `00-inbox/MY-PROFILE.md`. It defines who the user is, their role, their working
style, their active domains, critical stakeholders, and per-skill preferences. Every
skill loads it at preflight to personalize behavior.

## 2. Vault structure

```
00-inbox/        ← raw, untriaged capture (to process)
01-daily/        ← daily briefs and journal
02-people/       ← stakeholder notes (CRM)
03-projects/     ← active and past projects
04-meetings/     ← ingested meetings
05-decisions/    ← log of important decisions
06-knowledge/    ← durable syntheses, frameworks, lessons
07-archive/      ← inactive (never deleted)
```

## 3. AI-first rules (NON-NEGOTIABLE)

Every note created or modified MUST comply:

### 3.1 "For future Claude" preamble
Every note begins with a `## For future Claude` (2-3 sentences in English) summarizing
the what/why/when. Future-you reads it in 10 seconds before parsing the rest.

### 3.2 Machine-readable frontmatter
Mandatory universal fields:
```yaml
---
date: YYYY-MM-DD
type: <note-type>
tags: [...]
ai-first: true
---
```

### 3.3 Recency markers
Every external claim carries its date inline:
```
- Feature X launched (as of 2026-03, source: internal changelog)
```

### 3.4 Verbatim sources
Inline URL or reference, never a paraphrased citation.

### 3.5 Wikilinks mandatory
Every person, project, or concept referenced = `[[02-people/Alex Rivera]]`,
`[[03-projects/Onboarding Refresh]]`.

### 3.6 Confidence levels
When relevant: `stated` | `high` | `medium` | `speculation`.

### 3.7 Append-only
NEVER overwrite an existing note. Add entries to "Timeline" or "Updates" sections
with a timestamp.

## 4. Type schemas (frontmatter by type)

### `type: braindump`
```yaml
date: YYYY-MM-DD
type: braindump
tags: [braindump, <domain>]
domain: personal | professional | project-specific | mixed
energy: low | medium | high
ai-first: true
```

### `type: meeting`
```yaml
date: YYYY-MM-DD
type: meeting
tags: [meeting, <project-tag>]
participants: ["[[02-people/...]]", ...]
project: "[[03-projects/...]]"
meeting-type: 1-1 | team-sync | stakeholder | external | townhall
duration: <min>
ingestion-mode: manual | auto | auto-validated   # auto = ingested by daily-brief; auto-validated = auto then reviewed
needs-review: true | false                        # true if auto and not yet reviewed
ai-first: true
```

### `type: person`
```yaml
date: YYYY-MM-DD              # first logged interaction
updated: YYYY-MM-DD
type: person
tags: [person, <role-tag>, <region-tag>]
role: ""
company: ""
team: ""
region: WE | NA | LATAM | APAC | Global
relationship: direct-report | peer | manager | stakeholder | external
last-interaction: YYYY-MM-DD
staleness-flag: ""            # e.g. "stale-30d-since-2026-05-22" — set by Stale People Check, cleared by daily-brief on next interaction
ai-first: true
```

### `type: project`
```yaml
date: YYYY-MM-DD              # creation
updated: YYYY-MM-DD
type: project
tags: [project, <domain-tag>]
status: active | planning | completed | archived | on-hold
priority: high | medium | low
related-people: ["[[02-people/...]]", ...]
related-projects: ["[[03-projects/...]]", ...]
ai-first: true
```

### `type: decision`
```yaml
date: YYYY-MM-DD
type: decision
tags: [decision, <domain-tag>]
status: proposed | committed | implemented | reversed
project: "[[03-projects/...]]"
stakeholders: ["[[02-people/...]]", ...]
reversibility: reversible | hard-to-reverse | one-way
confidence: high | medium | speculation
ai-first: true
```

### `type: daily`
```yaml
date: YYYY-MM-DD
type: daily
tags: [daily]
ai-first: true
```

## 5. Naming conventions

- **Files**: `kebab-case.md` except people (`02-people/First Last.md`).
- **Inbox**: `00-inbox/YYYY-MM-DD-HHMM-slug.md`.
- **Daily**: `01-daily/YYYY-MM-DD.md`.
- **Meetings**: `04-meetings/YYYY-MM-DD-slug.md`.
- **Decisions**: `05-decisions/YYYY-MM-DD-slug.md`.

## 6. Curation rules

1. **Search before create** — always check if the note exists before creating one. Fuzzy match for names.
2. **Stub rather than skip** — if a linked note doesn't exist yet, create a minimal stub rather than skipping the link.
3. **No orphan note** — every new note is referenced from at least one other place (today's daily note, a project, a person).
4. **Active dedup** — if you detect a duplicate (same person, same project), merge instead of duplicating.
5. **Append-only on sensitive notes** (people, decisions) — never overwrite, always timeline.

## 7. Tasks & the TODO dashboard

Action items are born scattered across notes (meeting `## Action items`, decision
`## Execution plan`, daily `## Pending follow-ups`, people timeline `Follow-up:` lines,
braindump `## Suggested follow-up`). The `task-roundup` skill consolidates the ones the
user owns into a single **`TODO.md` at the vault root** and keeps the checkboxes synced.

**Source notes are the source of truth; `TODO.md` is a generated, reconcilable view.**

### Action-line convention
```
- [ ] <action> — owner: me — due: YYYY-MM-DD — #from/meeting ^t-ab12cd
```
- `owner:` — `me` / your alias = yours; a `[[02-people/...]]` = someone else's.
- `^t-xxxxxx` — a stable block-ID anchor (`^t-` + 6 lowercase alphanumerics), assigned
  once by `task-roundup`, **never changed or reused**. It links a `TODO.md` line back to
  its source line and makes two-way check-off reliable.

### Sync rules
- Box checked in `TODO.md` → next roundup sets the source line to `[x] ✅ <date>`.
- Box checked in a source note → next roundup checks it in `TODO.md`.
- Completing a task in an append-only zone (`02-people/`, `05-decisions/`) is a checkbox
  toggle + `✅ <date>` stamp **only** — never rewrite surrounding content.
- Done items stay in `TODO.md` for 14 days, then drop off (history lives in the source + Git).

Skills that create action lines (`meeting-ingest`, `daily-brief`, `challenge-decision`,
`braindump`) should write them in this convention so roundup is cheap; `task-roundup`
backfills anchors on any that lack one.

## 8. Auto-orchestration (daily-brief as conductor)

The system is designed to run **autonomously**. The scheduled `daily-brief` is more
than a brief — it's an orchestrator that:

1. Detects new meeting transcripts → invokes `meeting-ingest` automatically (except sensitive 1-1s → flag for manual validation).
2. Detects the day's people interactions → auto-updates existing people notes (frontmatter + `(auto-logged)` timeline entry).
3. Clears `staleness-flag` when an interaction is detected.
4. Runs `task-roundup`: collects new action items, reconciles `TODO.md` check-offs both ways, surfaces overdue/today.
5. Generates the usual synthetic brief.

### Auto vs. manual marking conventions

**Auto-ingested meetings**:
- Frontmatter: `ingestion-mode: auto`, `needs-review: true`.
- "For future Claude" explicitly mentions `auto-ingested via daily-brief on YYYY-MM-DD`.
- Global confidence degraded until human validation.

**Auto-logged people timeline entries**:
- Explicit `(auto-logged)` suffix in the entry header:
  ```
  ### 2026-05-22 — Daily interactions (auto-logged)
  - Calendar: 1-1 30min "weekly sync"
  - Email: 3 threads about qualification script
  - Chat: 5 DMs
  - Source: daily-brief auto-propagation
  ```
- No interpretive observation — raw facts only (channels, frequency, main topic).
- No modification of "Compiled truth" (manual `people-update` only).

### Auto-ingestion guardrails

A transcript is auto-ingestable ONLY if ALL conditions hold:
- ✅ Matches a calendar event of the day (else = potential false positive).
- ✅ Participants ≥ 2 (else = solo voice memo, not a meeting).
- ✅ Calendar duration ≥ 15 min (else = quick stand-up, not worth it).
- ✅ NOT in the `sensitive-meetings` list of MY-PROFILE.md (manager 1-1s, board, comp discussions).

Anything that doesn't match → flag in the brief, no auto-ingest. The user validates the next day.

### Weighting for challenge-decision

When `challenge-decision` uses notes with `ingestion-mode: auto` not yet reviewed
(`needs-review: true`):
- Weight at ~70% of a manual or validated note.
- Explicit mention in the report: "This analysis includes N auto-ingested notes not yet reviewed. Confidence degraded on those signals."

Backfilled notes (`(Backfilled)` marker) weight at ~30% for the first 6–8 weeks.

### Cleared by real interaction

`staleness-flag` is auto-cleared as soon as a real interaction is detected (by
daily-brief or by manual `people-update`). No human action needed to remove it.

## 9. Default behavior

When a skill runs, you:

1. Read this `_CLAUDE.md` first.
2. Read the relevant notes (people, projects) before writing.
3. Apply the AI-first rules 100%.
4. Create missing links (stubs if needed).
5. Report at the end: what was created/modified, with paths.
6. Ask for confirmation before any destructive action (deletion, structural refactor).

## 10. What you NEVER do

- Delete a note (use `07-archive/` instead).
- Overwrite a section without a timestamp.
- Create a person note without checking fuzzy matches.
- Invent sources or dates (prefer "unknown" or "as of <date>, from conversation").
- Reformat old notes without asking.
- **Auto-ingest a meeting marked sensitive without user validation.**
- **Modify "Compiled truth" in auto mode** (manual `people-update` only).
- Edit the `(auto-logged)` or `(Backfilled)` markers.
