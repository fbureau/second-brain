# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/):

- **MAJOR** — a breaking change to the vault structure or conventions (requires migration).
- **MINOR** — a new, backward-compatible capability (e.g. a new skill).
- **PATCH** — fixes and documentation tweaks, no behavior change.

The current version is in the [`VERSION`](VERSION) file. Each release is an annotated
Git tag (`vX.Y.Z`) on `main`. See [`docs/RELEASING.md`](docs/RELEASING.md) for the process
and [`docs/UPGRADING.md`](docs/UPGRADING.md) to move an existing vault between versions.

## [3.2.0] - 2026-05-22

### Added
- **`doc-ingest` skill** — the document twin of `meeting-ingest`: ingests a produced doc
  (strategy, analysis, report, deck, spec, external article) into a `06-knowledge/` note
  with verbatim source, dated claims + confidence levels, and links to the relevant projects.
- **`knowledge-build` skill** — distills `06-knowledge/` from across the vault (recurring
  themes, lessons, anti-patterns, reversed-decision lessons), with citations and confidence.
  Manual, and a conservative auto sweep during the **weekly review** (flags `needs-review`).
- **`recall` skill** — queries the vault to find/confirm info, answering with citations
  (path + date) and a confidence level, and saying honestly when the vault is silent.
- **`prioritize` skill** — recommends priority actions and a short plan (order, how to
  handle, suggested replies) from `TODO.md`, calendar, active projects, and recent signals.
- **`vault-tend` skill** — a standing "knowledge-manager team" for whole-vault maintenance:
  re-language the vault to one language, normalize frontmatter, repair broken wikilinks,
  deduplicate people/projects, tidy formatting, propose archives, or any vault-wide adjustment.
  Always preview-first, confirmation-gated, batched (one commit per batch), and append-only safe.
- **`type: knowledge` and `type: doc`** frontmatter schemas in `_CLAUDE.md`.

### Changed
- **Source links are preserved on ingest**: `meeting-ingest` gains a `source:` field (the
  transcript / Google Doc / recording link) and `doc-ingest` keeps the original Google Doc URL
  in both frontmatter and `## Links`, so you can always reopen the source.
- **Working language is now a setting**: `MY-PROFILE.md` declares it (default `en`); every
  skill writes note bodies and replies in that language while the "For future Claude"
  preamble stays English. Documented in `_CLAUDE.md` (rule 3.8) and `CLAUDE.md`.
- `daily-brief` weekly mode now also runs `knowledge-build`.
- Docs updated: README, QUICKSTART, `docs/UPGRADING.md` (rewritten as a clearer step-by-step),
  `docs/INSTALL.md` (note on the hidden `.claude` folder on macOS).

## [3.1.0] - 2026-05-22

### Added
- **`task-roundup` skill** — consolidates the action items you own from across the vault
  (meeting `## Action items`, decision `## Execution plan`, daily `## Pending follow-ups`,
  people `Follow-up:`, braindump `## Suggested follow-up`) into a single **`TODO.md` at the
  vault root**.
- **Two-way checkbox sync** via stable Obsidian block-IDs (`^t-id`): notes stay the source
  of truth, `TODO.md` is a generated, reconcilable view. Checking a box in either place
  propagates to the other; completions are stamped `✅ <date>`.
- Buckets: overdue / today / upcoming / later / no-date / waiting-on-others / done
  (done kept 14 days). Optional priority (🔴/🟡) and task-staleness flags.
- Seed `vault-starter/TODO.md`.

### Changed
- **`daily-brief`** now runs a roundup phase every run and surfaces overdue/today items
  at the top of the brief.
- `_CLAUDE.md` documents the action-line convention + two-way sync rules (new section 7;
  later sections renumbered).
- Action-line convention threaded through `meeting-ingest`, `braindump`, and the
  `decision` / `daily` templates so roundup is cheap.
- Docs updated: README, QUICKSTART, USAGE-PATTERNS, SCHEDULED-TASKS, `hooks/README`.
- Append-only safe: completing a task in `02-people/` or `05-decisions/` is a checkbox
  toggle + `✅` stamp only — the pre-commit hook still permits it.

## [3.0.0] - 2026-05-22

Migration from a scheduled-task assistant (Cowork) to Claude Code, fully translated to
English and de-personalized.

### Changed
- Skills now live at `.claude/skills/<name>/SKILL.md` and auto-trigger from their description.
- Fully English and de-personalized — usable by anyone. Identity lives only in
  `00-inbox/MY-PROFILE.md`, shipped as a blank fillable template.
- Git is first-class: added a `pre-commit` hook that enforces AI-first compliance and
  blocks destructive diffs on `02-people/` and `05-decisions/`.
- Added project `CLAUDE.md` and `.claude/settings.json`.
- Scheduling reframed for an external scheduler (cron / launchd / CI); Claude Code has no
  native cron — see `docs/SCHEDULED-TASKS.md`.
- Docs rewritten for Claude Code; generic example names throughout.

### Preserved (design decisions carried over)
- Staleness-flag: frontmatter-only.
- Auto-update people: aggregated `(auto-logged)` timeline entry, raw facts only; Compiled
  truth never touched in auto mode.
- Auto-ingest meetings: orchestrated by daily-brief.
- Sensitive 1-1s: manual validation required.
- challenge-decision weighting: `needs-review: true` notes at 70%; backfilled at 30%.

---

_Pre-migration history (Cowork era, French). Listed for continuity; predates this repo._

## [2.0.0] - 2026-05-22

- `daily-brief` became the orchestrator: auto-ingests detected transcripts (with
  guardrails) and auto-updates existing people notes.
- Added the `staleness-flag` frontmatter field (set by the Friday check, cleared on the
  next detected interaction — self-healing).
- Added the `kickstart-backfill` skill (one-shot Day-1 seeding from 1–6 months of history).
- Added `ingestion-mode` and `needs-review` to the meeting schema.

## [1.0.0] - 2026-05-20

- Five skills: braindump, meeting-ingest, daily-brief, people-update, challenge-decision.
- Vault starter (8 folders + `_CLAUDE.md` + `MY-PROFILE.md`).
- Four templates (person, project, decision, daily).
- Docs: README, INSTALL, SCHEDULED-TASKS, USAGE-PATTERNS, ARCHITECTURE.
