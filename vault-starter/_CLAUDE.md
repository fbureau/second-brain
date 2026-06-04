---
type: system-brief
updated: 2026-06-03
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
06-knowledge/    ← personal wiki + lessons + domain indexes
  _INDEX.md      ← auto-maintained root index of 06-knowledge/ (entry point)
  _sources/      ← ingested produced docs (type: doc) live here, not at root
  <domain>.md    ← Map of Content per knowledge domain (type: index)
  <slug>.md      ← wiki pages (type: wiki) and lessons (type: knowledge) at root
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

### 3.8 Working language
Write note **bodies** and chat replies in the **Working language** set in
`00-inbox/MY-PROFILE.md` (default `en`). The `## For future Claude` preamble is **always
English** regardless. If the user writes in another language, capture verbatim content in
its original language but keep the note's structure and preamble per these rules.

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
source: ""                                        # verbatim link to the transcript / Google Doc / recording, if any
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

### `type: knowledge`  (distilled lesson / pattern / framework)
```yaml
date: YYYY-MM-DD              # first crystallized
updated: YYYY-MM-DD
type: knowledge
tags: [knowledge, <topic-tags>]
domain: <domain-slug>         # canonical domain; matches a hub in 06-knowledge/<domain>.md
confidence: high | medium | speculation
needs-review: false          # true if created/updated by knowledge-build in auto mode
ai-first: true
```

### `type: wiki`  (encyclopedic page on a concept, entity, tool, team, process, jargon)
```yaml
date: YYYY-MM-DD              # stub creation
updated: YYYY-MM-DD
type: wiki
tags: [wiki, <topic-tags>]
domain: <domain-slug>         # canonical domain; matches a hub in 06-knowledge/<domain>.md
aliases: ["<other names>", "<acronym>"]   # so recall finds it under any name
confidence: stated | high | medium | speculation
needs-review: true | false    # true on auto-stub until enriched / confirmed
created-from: "[[<trigger-note-path>]]"   # the note that first triggered this page
ai-first: true
```
Wiki pages are grown incrementally. Stubs are created automatically on first mention (by
`braindump`, `meeting-ingest`, `doc-ingest`); every fact in the body cites its source; the
`## Sources` section is the cumulative audit trail (never truncated). See
`.claude/skills/knowledge-build/SKILL.md` for the full protocol.

### `type: doc`  (an ingested produced document)
Path: `06-knowledge/_sources/YYYY-MM-DD-<slug>.md` (not at the root of `06-knowledge/`).
```yaml
date: YYYY-MM-DD              # ingestion date
doc-date: YYYY-MM-DD          # the document's own date (or "unknown")
type: doc
doc-type: strategy | analysis | report | deck | spec | research | external-article
tags: [doc, <topic-tags>]
domain: <domain-slug>         # canonical domain; matches a hub
source: "<verbatim URL or path/title>"
project: "[[03-projects/...]]"
confidence: high | medium | speculation
ai-first: true
```

### `type: index`  (Map of Content / domain hub)
Path: `06-knowledge/<domain>.md` for a domain hub, or `06-knowledge/_INDEX.md` for the root.
```yaml
date: YYYY-MM-DD
updated: YYYY-MM-DD
type: index
tags: [index, <domain>]
domain: <domain-slug>          # the domain this hub indexes (omit for root _INDEX.md)
auto-maintained: true | false  # true = curator updates the listing sections; false = you own it
ai-first: true
```
Hubs are the entry points to the knowledge layer. They list every wiki, lesson, and source
doc tagged with the same `domain:`. `recall` queries hubs first to scope the search. They
are maintained automatically by `knowledge-build` (curator mode); see Section 11.

## 5. Naming conventions

- **Files**: `kebab-case.md` except people (`02-people/First Last.md`).
- **Inbox**: `00-inbox/YYYY-MM-DD-HHMM-slug.md`.
- **Daily**: `01-daily/YYYY-MM-DD.md`.
- **Meetings**: `04-meetings/YYYY-MM-DD-slug.md`.
- **Decisions**: `05-decisions/YYYY-MM-DD-slug.md`.
- **Wiki / lessons**: `06-knowledge/<slug>.md` (kebab-case, **undated** — evergreen).
- **Domain hubs**: `06-knowledge/<domain>.md` (kebab-case, undated).
- **Root index**: `06-knowledge/_INDEX.md` (the underscore makes it sort first in Obsidian).
- **Source documents**: `06-knowledge/_sources/YYYY-MM-DD-<slug>.md` (dated, NOT at the root
  of `06-knowledge/`).

## 6. Curation rules

1. **Search before create** — always check if the note exists before creating one. Fuzzy match for names.
2. **Stub rather than skip** — if a linked note doesn't exist yet, create a minimal stub rather than skipping the link. Concepts/entities → wiki stub via the protocol in `knowledge-build/SKILL.md`.
3. **No orphan note** — every new note is referenced from at least one other place (today's daily note, a project, a person, or a domain hub).
4. **Active dedup** — if you detect a duplicate (same person, same project, same concept), merge instead of duplicating. The curator (Section 9) flags these on the weekly sweep.
5. **Append-only on sensitive notes** (people, decisions) — never overwrite, always timeline. Same for the `## Sources` section of any wiki page.
6. **Tag the domain** — every wiki, lesson, and source doc carries a `domain:` field that matches a hub at `06-knowledge/<domain>.md`. The curator routes notes into hubs by this field. If the domain doesn't exist yet, the curator either adds the note to "Unsorted" in `_INDEX.md` or proposes a new hub when 3+ notes cluster.

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

In **weekly mode**, daily-brief also runs `knowledge-build` — a conservative sweep that
proposes new/updated `06-knowledge/` notes, flagged `needs-review: true` for you to confirm.

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

## 9. Knowledge layer & curator

`06-knowledge/` is a structured graph, not a folder dump. Three altitudes live there:

- **Wiki pages** (`type: wiki`) — encyclopedic, grown from the first mention.
- **Lessons** (`type: knowledge`) — distilled patterns, recurrence-gated.
- **Source documents** (`type: doc`) — ingested produced docs, **kept in `06-knowledge/_sources/`**
  so they don't pollute the durable knowledge at the root.

Navigation works through **domain hubs** (`type: index`), not through subfolders:

- A hub per knowledge domain lives at `06-knowledge/<domain>.md` (e.g. `salesforce.md`,
  `booksy.md`, `change-management.md`). Each hub lists every wiki, lesson, and source doc
  tagged with the matching `domain:` field.
- The root `06-knowledge/_INDEX.md` lists all domain hubs + recent activity + health stats.
  This is the entry point for `recall` and for any human exploration.
- The domain taxonomy is declared by the user in `00-inbox/MY-PROFILE.md` under
  `## Knowledge domains` and refined by the curator over time.

### Curator (built into `knowledge-build`)
Two modes keep the knowledge layer organized:

- **Incremental** — runs every time a wiki or lesson is created, enriched, or a doc is
  ingested. It updates the matching domain hub's listing (silent, additive) and refreshes
  the root `_INDEX.md` counters.
- **Sweep** — runs weekly as part of `daily-brief` weekly mode, or on demand
  (`knowledge-build curator`, `vault-tend knowledge garden`). It rebuilds hub listings from
  scratch (handles renames / deletes), detects orphans (no inbound links), proposes new
  hubs when 3+ notes cluster on a yet-unhubbed domain, proposes merges for near-duplicates,
  flags stubs awaiting enrichment, and refreshes `_INDEX.md`. **Structural changes (creating
  hubs, merging notes, moving notes) always preview and ask.** Listing refreshes inside an
  existing `auto-maintained: true` hub are silent.

### Bootstrap (one-shot)
On first install or after upgrading from < v3.4.0, run `knowledge-build curator --bootstrap`.
The curator:
1. Creates `06-knowledge/_sources/` and moves all existing `type: doc` notes into it.
2. Reads `## Knowledge domains` from `MY-PROFILE.md`; infers missing domains from the
   existing notes' tag clusters; asks before adding any.
3. Creates the domain hubs and the root `_INDEX.md`.
4. Tags every existing wiki/lesson/doc with `domain:` (asks on ambiguous cases).
5. Moves vault-meta artifacts (`kickstart-backfill-*`, old `vault-health-*`) to
   `07-archive/` if they're sitting in `06-knowledge/` (asks first).
6. Reports the result; nothing destructive is auto-applied.

## 10. Default behavior

When a skill runs, you:

1. Read this `_CLAUDE.md` first.
2. Read the relevant notes (people, projects) before writing.
3. Apply the AI-first rules 100%.
4. Create missing links (stubs if needed).
5. Report at the end: what was created/modified, with paths.
6. Ask for confirmation before any destructive action (deletion, structural refactor).

## 11. What you NEVER do

- Delete a note (use `07-archive/` instead).
- Overwrite a section without a timestamp.
- Create a person note without checking fuzzy matches.
- Invent sources or dates (prefer "unknown" or "as of <date>, from conversation").
- Reformat old notes without asking.
- **Auto-ingest a meeting marked sensitive without user validation.**
- **Modify "Compiled truth" in auto mode** (manual `people-update` only).
- Edit the `(auto-logged)` or `(Backfilled)` markers.
- **Hand-edit the listing sections of an `auto-maintained: true` index hub** — the curator
  rewrites them. Edit the hub's intro/summary instead, or set `auto-maintained: false`.
- **Write a `type: doc` note at the root of `06-knowledge/`** — they go in `_sources/`.
- **Drop the `domain:` tag** when creating a wiki/lesson/doc — if you genuinely don't know,
  use `domain: unsorted` and the curator will surface it.
