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

## [3.4.0] - 2026-06-03

### Added
- **`type: index` notes — domain hubs and the root `_INDEX.md`.** `06-knowledge/` is no
  longer a flat dump: a hub at `06-knowledge/<domain>.md` lists every wiki, lesson, and
  source doc tagged with the matching `domain:` field; the root `06-knowledge/_INDEX.md`
  lists the hubs + recent activity + health stats and is the entry point `recall` queries
  first. Classic Map-of-Content / index-note pattern from PKM, adapted to AI-native
  retrieval.
- **`knowledge-build` Curator (Mode C)** — the new organizing layer. Three sub-modes:
  - **Incremental**: every wiki/lesson creation, enrichment, or doc ingestion silently
    updates the matching hub's listings and refreshes the root `_INDEX.md` counters.
  - **Sweep**: runs weekly via `daily-brief` weekly mode (after the lessons pass) or on
    demand. Rebuilds auto-maintained hub listings, detects orphans (no inbound links),
    proposes new hubs when ≥ 3 notes cluster on an unhubbed domain, proposes merges for
    near-duplicates, flags stubs awaiting enrichment (>14 days `needs-review: true`) and
    stale wiki pages (>90 days no update). Structural changes always preview and ask.
  - **Bootstrap**: one-shot migration for existing vaults — moves `type: doc` notes into
    `_sources/`, tags every wiki/lesson/doc with `domain:`, creates the hubs, archives
    vault-meta artifacts (`kickstart-backfill-*`, `vault-health-*`) sitting in `06-knowledge/`,
    writes the root `_INDEX.md`.
- **`vault-tend` Knowledge garden (Operation 8)** — focused 06-knowledge/ maintenance pass
  that delegates to the curator sweep with extra reporting (structural moves, hub
  proposals, merge proposals).
- **`domain:` frontmatter field** on `type: wiki`, `type: knowledge`, `type: doc` —
  canonical domain slug that routes to a hub. Inferred from project/tags/MY-PROFILE at
  creation; `unsorted` if unknown.
- **`## Knowledge domains` section in `MY-PROFILE.md`** — user declares their domain
  taxonomy (5–8 slugs); the curator can propose additions when clusters grow.
- **`auto-maintained:` field on `type: index`** — `true` lets the curator rewrite the
  listing sections; `false` puts you in control.

### Changed
- **`06-knowledge/_sources/` subfolder for ingested docs.** `doc-ingest` now writes
  `type: doc` notes to `06-knowledge/_sources/YYYY-MM-DD-<slug>.md` instead of the root.
  The root of `06-knowledge/` is reserved for wikis, lessons, and hubs — so the flat list
  stays readable as the vault grows.
- **`recall` is now hub-first.** Query order: root `_INDEX.md` → matching domain hub →
  individual wiki/lesson/doc notes → other folders. Falls back to flat scan if hubs
  don't exist yet, and suggests `knowledge-build curator --bootstrap` in that case.
- **`braindump`, `meeting-ingest`, `doc-ingest`** all add `domain:` to the wiki stubs they
  create and call **curator incremental** so the new pages land in their hubs without manual
  intervention.
- **`daily-brief` weekly mode** now runs the curator sweep after the lessons sweep and
  renders a `## Knowledge garden` section with health counters and pending proposals.
- Vault structure description (`_CLAUDE.md`, `CLAUDE.md`, `README.md`) updated for the new
  06-knowledge layout. `vault-starter/_CLAUDE.md` gains Section 9 *Knowledge layer & curator*
  and Section 5 naming conventions for hubs / `_INDEX.md` / `_sources/`.

### Migration (v3.3.0 → v3.4.0)
Additive — old notes work, but to get the value you run **once**: `knowledge-build curator
--bootstrap`. It's interactive, preview-first, batched. Full procedure in
`docs/UPGRADING.md`. After bootstrap, every subsequent capture updates the hubs
automatically.

### Fixed
- **`06-knowledge/` looked like a junk drawer at 30+ files** with three altitudes mixed
  (dated docs / evergreen wikis / one-offs) and no signposting. Hubs + `_INDEX.md` +
  `_sources/` give it a navigable shape; the curator keeps it that way.

## [3.3.0] - 2026-05-29

### Added
- **`type: wiki` notes** — `06-knowledge/` now hosts a real **personal wiki** alongside the
  existing lessons: encyclopedic pages on concepts, entities, tools, teams, processes, and
  jargon. Stubs are **created on first mention** (no recurrence threshold) by `braindump`,
  `meeting-ingest`, and `doc-ingest`; pages grow incrementally as more sources mention the
  same thing. Wiki schema added to `_CLAUDE.md` (`aliases`, `created-from`, mandatory
  `## Sources` audit trail).
- **Wiki stub protocol** in `knowledge-build/SKILL.md` (Mode A.2) — the contract the capture
  skills call to seed a stub with the trigger source recorded. Every fact in the wiki body
  carries an inline citation; the `## Sources` section is cumulative and never truncated.
- **`primary-communication-channels`** field in `MY-PROFILE.md` — sources to treat as
  **co-primary** with email/calendar in `daily-brief`. When `slack` (or another chat tool)
  is listed, chat collection moves to **broad mode** (DMs received + sent, mentions, threads
  participated in, channels active in the last 14 days, reactions placed) and the brief gets
  a dedicated `## Themes from Slack` section that does NOT compete with the top-5 cap.
- **`chat-channels-to-ignore`** field in `MY-PROFILE.md` — explicit blocklist for noisy/off-topic
  channels.

### Changed
- **`knowledge-build` is now two-altitude**: Mode A (wiki, encyclopedic, no recurrence
  threshold) and Mode B (lessons, current behavior — patterns/anti-patterns/principles,
  recurrence-gated). Routing logic at preflight: ambiguous requests produce a wiki page first
  (lower bar, always useful), with a lesson offered if the evidence supports it. Lessons
  now link to the wiki pages they rest on, and wiki pages link to the lessons that draw
  on them — the base becomes a connected graph.
- **`daily-brief` chat collection** is no longer gated on a `priority-chat-channels` whitelist
  by default; when chat is a primary channel, *all* channels the user is actively using are
  scanned, themes are clustered across channels, and the brief surfaces them in their own
  section.
- **`braindump`**: concept wikilinks always create a `type: wiki` stub on first mention
  (replaces the prior "if recurring" gating).
- **`meeting-ingest`**: new step 7.4 — wiki stubs/enrichment for every concept/entity/tool
  the transcript mentions substantively, citing the meeting as the source.
- **`doc-ingest`**: step 4 propagation now creates/enriches wiki pages for the concepts the
  doc describes; lessons remain a separate, recurrence-gated suggestion.
- **`recall`** now searches all three flavors in `06-knowledge/` (`wiki`, `knowledge`, `doc`)
  and uses `aliases:` to match a query under any name. Wiki pages are the hubs to pivot through.
- Vault structure description (`_CLAUDE.md`, `CLAUDE.md`, `README.md`) updated to:
  `06-knowledge/ ← personal wiki (encyclopedic) + lessons (distilled patterns)`.

### Fixed
- **Slack signal was being under-collected** when `priority-chat-channels` was empty or thin
  — daily-brief now defaults to broad collection across active channels when chat is a primary
  source, so heavy Slack days are no longer drowned out by email/calendar volume.

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
