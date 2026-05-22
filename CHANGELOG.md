# Changelog

## v3.1 — Centralized task management

- **New `task-roundup` skill.** Consolidates the action items you own from across the
  vault (meeting `## Action items`, decision `## Execution plan`, daily `## Pending
  follow-ups`, people `Follow-up:`, braindump `## Suggested follow-up`) into a single
  **`TODO.md` at the vault root**.
- **Two-way checkbox sync** via stable Obsidian block-IDs (`^t-id`): notes stay the
  source of truth, `TODO.md` is a generated, reconcilable view. Checking a box in either
  place propagates to the other; completions are stamped `✅ <date>`.
- **`daily-brief` integration**: a roundup phase reconciles `TODO.md` every run and
  surfaces overdue/today items at the top of the brief.
- Buckets: overdue / today / upcoming / later / no-date / waiting-on-others / done
  (done kept 14 days). Optional priority (🔴/🟡) and task-staleness flags.
- Updated `_CLAUDE.md` (action-line convention + sync rules), templates, `meeting-ingest`,
  `braindump`, README, QUICKSTART, USAGE-PATTERNS, and SCHEDULED-TASKS accordingly.
- Append-only safe: completing a task in `02-people/` or `05-decisions/` is a checkbox
  toggle + `✅` stamp only — the pre-commit hook still permits it.

## v3 — Migration to Claude Code (English, generic)

### Major changes
- **Migrated from a scheduled-task assistant (Cowork) to Claude Code.** Skills now
  live at `.claude/skills/<name>/SKILL.md` and auto-trigger from their description.
- **Fully translated to English** and **de-personalized** — usable by anyone. The
  user's identity now lives only in `00-inbox/MY-PROFILE.md`, which ships as a blank
  fillable template.
- **Git is first-class.** Added a `pre-commit` hook (`hooks/`) that enforces AI-first
  compliance and blocks destructive diffs on `02-people/` and `05-decisions/`.
- **Project `CLAUDE.md`** at the repo root with the conventions Claude reads each session.
- **`.claude/settings.json`** with a sensible default permission set.
- **Scheduling reframed** for an external scheduler (cron / launchd / CI), since
  Claude Code has no native cron — see `docs/SCHEDULED-TASKS.md`.
- Docs rewritten for Claude Code: `INSTALL`, `SCHEDULED-TASKS`, `USAGE-PATTERNS`,
  `ARCHITECTURE`, `KICKSTART-PROMPT`.
- Generic example names throughout (Alex Rivera, Jordan Park, Sam Lee, Riley Chen);
  domain-specific examples replaced with domain-neutral equivalents.

### Preserved design decisions
- Staleness-flag: frontmatter-only (no body "Alerts" section).
- Auto-update people: aggregated `(auto-logged)` timeline entry, raw facts only,
  Compiled truth never touched in auto mode.
- Auto-ingest meetings: orchestrated by daily-brief (not a separate task).
- Sensitive 1-1s: manual validation required (never auto-ingested).
- challenge-decision weighting: `needs-review: true` notes at 70%; backfilled notes at 30%.

## v2 — Auto-orchestration + staleness management

- `daily-brief` became the system's orchestrator: auto-ingests detected transcripts
  (with guardrails) and auto-updates existing people notes.
- Added the `staleness-flag` frontmatter field (set by the Friday check, cleared on
  the next detected interaction — self-healing).
- Added the `kickstart-backfill` skill (one-shot Day-1 seeding from 1–6 months of history).
- Added `ingestion-mode` and `needs-review` to the meeting schema.

## v1 — Initial release

- Five skills: braindump, meeting-ingest, daily-brief, people-update, challenge-decision.
- Vault starter (8 folders + `_CLAUDE.md` + `MY-PROFILE.md`).
- Four templates (person, project, decision, daily).
- Docs: README, INSTALL, SCHEDULED-TASKS, USAGE-PATTERNS, ARCHITECTURE.
