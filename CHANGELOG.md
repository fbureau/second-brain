# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/):

- **MAJOR** — a breaking change to the vault structure or conventions (requires migration).
- **MINOR** — a new, backward-compatible capability (e.g. a new skill).
- **PATCH** — fixes and documentation tweaks, no behavior change.

The current version is in the [`VERSION`](VERSION) file. Each release is an annotated
Git tag (`X.Y.Z`, no `v` prefix) on `main`. See [`docs/RELEASING.md`](docs/RELEASING.md) for the process
and [`docs/UPGRADING.md`](docs/UPGRADING.md) to move an existing vault between versions.

## [4.3.0] - 2026-09-08

### Added
- **Passive recall — the `sb_vault` memory provider** (`hermes/memory/sb_vault/`). Activated with
  `hermes config set memory.provider sb_vault`, it injects the vault notes relevant to the turn you
  just typed, with paths and dates, before the model thinks to search. Read-only on purpose:
  `sync_turn`, `on_session_end`, `on_pre_compress` and `on_memory_write` are no-ops, so the vault's
  append-only history stays a record of decisions rather than of chatter. Retrieval runs on a
  background thread and stays silent when nothing matches — an empty context beats a plausible
  irrelevant one. It shares its engine with `sb_recall`, so passive and explicit recall never disagree.
- **Retrieval with citations** (`vault/recall.py`, tool `sb_recall`): resolves the people, projects
  and hubs a question mentions (a slug and a spoken name fold onto the same form), pulls the lines
  that actually match with the date heading above them, and returns a confidence of
  `stated | high | medium | speculation | unknown`. A note that hits one term out of three is
  dropped as a near-miss rather than dressed up as evidence, and `unknown` obliges the skill to say
  the vault does not know.
- **Six more tools for parity with the Claude edition**: `sb_agenda` (open work, deadlines, quiet
  projects, cooling relationships and a `signals` list — gathered, deliberately not ranked),
  `sb_decision_context` and `sb_decision_postmortem` (comparable decisions with reversals weighted
  first, unchecked reversal conditions, and what a reversal invalidates elsewhere), `sb_tend`
  (whole-vault audit, preview-first: safe frontmatter fixes on request, everything else as a
  proposal), `sb_backfill_plan` and `sb_backfill_done` (Day-1 backfill as session-sized batches,
  entity phases first, resumable from a state note after an interrupt).
- **Seven more Hermes skills — thirteen in all, full parity**: `recall`, `prioritize`,
  `challenge-decision` (red-team and postmortem), `doc-ingest`, `vault-tend`,
  `kickstart-backfill`, `weekly-review`.
- **`sb-weekly-review` cron job** (Mondays 09:00), and the weekly synthesis it runs.
- **Guardrail scorecard** (`hermes/bench/guardrails.py`, `hermes/tests/test_guardrails.py`): the
  calls a confused small model actually makes — an invented enum, a missing preamble, an overwrite
  instead of an append, a `..` in a path, a typo presented as an exact match, junk argument types —
  each asserted to be refused **by the code**, with a message saying what to do instead. The
  scorecard prints the share that held, and exits non-zero if any leaks.

### Fixed
- **Path traversal in every path-taking tool** (found by the new adversarial suite): `sb_read` would
  return the contents of an absolute path such as `/etc/passwd`, and an append could have written
  outside the vault. `vault.notes.safe_path` now refuses absolute paths, `~`, and any `..` that
  escapes the vault, for reads as well as writes.
- **`sb_vault_activity`** raised a `TypeError` computing the "new note" cutoff, so the tool returned
  an error instead of the day's activity. It also listed `_CLAUDE.md`, `AGENTS.md` and `MY-PROFILE.md`
  as if they were notes.

### Changed
- `hermes/install.sh` also links the memory provider into `$HERMES_HOME/plugins/sb_vault`.
- `docs/HERMES.md` documents phases 3 and 4, the read-only stance of the memory provider, the
  parity table, and how to run the reliability scorecard.

## [4.2.0] - 2026-09-08

### Added
- **Hermes Agent edition (`hermes/`)** — run the second brain with a local model. A plugin
  (`hermes/plugin/second_brain/`) exposes the vault contract as typed `sb_*` tools (19 in all, across two toolsets); the
  core eleven are
  `sb_brief`, `sb_search`, `sb_read`, `sb_find_person`, `sb_create_note`, `sb_append_timeline`,
  `sb_append_section`, `sb_daily_append`, `sb_new_action`, `sb_curate`, `sb_commit`. Every
  write goes through `vault/notes.py`, which generates frontmatter/path/preamble from an
  executable mirror of `_CLAUDE.md` §4 (`vault/schemas.py`), validates enums, never overwrites,
  and appends only — so a small model cannot violate the AI-first rules. `sb_curate` is the
  deterministic half of the curator (hub listings, recent activity, `_INDEX.md` counts).
- **Three Hermes skills** (`hermes/skills/`): `braindump`, `people-update`, `knowledge-stub` —
  ≤ 40-line procedures in agentskills.io format with Hermes metadata (`requires_toolsets`).
  Analysis stays with the model; plumbing moved into the tools.
- **`hermes/install.sh`**, `SOUL.md`, `config.example.yaml`, `memories/USER.md.example` —
  idempotent install into `~/.hermes/` (symlinks, seeds, `.env`, vault git hook).
- **Conformance suite** (`hermes/tests/`, stdlib `unittest`): every generated note is committed
  through `hooks/pre-commit` in a scratch vault — the hook is the shared judge of both editions.
- **`vault-starter/AGENTS.md`** — entry point for agents that auto-load `AGENTS.md` (Hermes):
  read `_CLAUDE.md` and `MY-PROFILE.md` first, or call `sb_brief`.
- **Maintenance as code** (`vault/maintain.py`, tool `sb_maintain`): task-roundup sync both ways
  (anchors, TODO.md buckets, mirror-aware, removed-source flags), curator sweep with the v4.0
  self-verification loop, staleness flags, health audit. Judgment calls come back as
  `needs_judgment` (unassigned owners, zombies, near-duplicates, hub proposals) for the model.
  `sb_toggle_task` marks a task done by anchor; `sb_vault_activity` lists recent vault changes.
- **Source digests** (`sources/`, toolset `second_brain_sources`): Google Calendar, Drive changes with
  transcript detection, Google Docs reading with the **transcript-first rule in code**
  (`sb_drive_doc` → `transcript_source`), Slack clustered per channel + DMs + mentions, Jira Cloud.
  Stdlib clients, credentials from `~/.hermes/.env`, tools hidden when credentials are missing.
- **Three more Hermes skills**: `daily-digest` (synthesis + auto-logged people + TODO refresh, returns
  the digest for delivery), `meeting-ingest` (transcript-first, propagation, ask before decision notes),
  `task-roundup` (resolves the maintenance tool's open cases).
- **`hermes/cron/jobs.sh`** — `sb-daily-digest` (weekdays 19:00) and `sb-maintenance` (daily 07:30) with
  per-job model and delivery target.
- **`docs/HERMES.md`** — architecture, install, phase 2 (plumbing vs judgment table, credentials, cron),
  roadmap (phase 3: memory provider for passive recall, weekly review).
- **`LICENSE`** — MIT.

### Changed
- README and `CLAUDE.md` describe the third path (Cowork · Claude Code · Hermes).

### Migration (v4.1.0 → v4.2.0)
Tooling only; nothing changes in existing vaults. Optionally copy `vault-starter/AGENTS.md`
into your vault if you run an AGENTS.md-aware agent. See `docs/UPGRADING.md`.

## [4.1.0] - 2026-08-12

Repo-wide audit release: a multi-agent audit (cross-file consistency, skill integrity,
shell correctness, docs freshness, template↔schema alignment, model-era prompt quality)
surfaced ~50 defects; every confirmed one is fixed here. Additive — no vault migration.

### Added
- **Pre-commit hook: deletion & rename protection.** Deleting a note in `02-people/` or
  `05-decisions/` — the most destructive diff of all — used to pass the hook silently
  (`--diff-filter=ACM` excluded deletions). Now blocked; a move to `07-archive/` (the
  sanctioned retirement path) passes; a rename anywhere else is blocked. Deleting a vault
  note in other folders warns (archive instead).
- **Templates `meeting.md` and `wiki.md`** — the two note types skills produce most that
  had no standalone template (meeting includes the v4.0 `transcript-source`/`confidence`
  fields).
- **`vault-starter/06-knowledge/` ships the knowledge layout** — seeded `_INDEX.md`,
  `_sources/` (with README), a modernized folder README (wiki/lessons/hubs/sources), and
  `domain:` on the example note. A fresh vault no longer starts pre-bootstrap.
- **`_CLAUDE.md`**: v4.0 meeting fields (`ingested`, `transcript-source`, `confidence`) in
  the `type: meeting` schema; orchestrator list gains the reversed-decision postmortem
  trigger; structure diagram gains `TODO.md`; "Other system types" note (decision-challenge,
  weekly-review, todo-dashboard, profile, backfill-report); `languages` on `type: person`.
- **`daily-brief` weekly template** gains the `## Knowledge garden` and `## Knowledge
  updates` sections its own weekly-mode instructions referenced.
- **`SCHEDULED-TASKS.md` Task 1** gains the transcript-first rule (PHASE 5) and a new
  PHASE 6.7 (reversed-decision postmortem) — the scheduled prompt had missed both v4.0
  behaviors; Task 2 now runs the curator self-verification loop.

### Changed
- **Pre-commit hook correctness**: checks now validate the **staged blob** (`git show :file`)
  instead of the working tree (partial stages are validated as committed); non-ASCII
  filenames (accented people names) no longer skip every check (`core.quotePath=off`);
  renames no longer bypass checks (`--no-renames`); backfilled monthly headers
  (`### YYYY-MM (Backfilled — aggregated)`) and suffixed markers (`(Backfilled, no
  transcript)`) are now protected; CRLF notes are no longer falsely rejected.
- **`install.sh`** resolves the hooks dir via `git rev-parse --git-path hooks` — works in
  worktrees and submodules where `.git` is a file.
- **`.gitignore`**: `.obsidian/` patterns now match at any depth (`**/` prefix) so a nested
  vault's workspace noise is actually ignored.
- **`settings.json`**: `git commit --no-verify` now prompts (ask) instead of riding the
  blanket `git commit` allow.
- **Daily-note section names unified**: braindump → `## Braindumps of the day`,
  meeting-ingest → `## Meetings ingested today`, doc-ingest → `## Docs ingested today` —
  the skills, the daily template, and the folder README previously disagreed, which would
  have produced duplicate sections.
- **`task-roundup`**: scans `03-projects/` (its own TODO template already showed a
  project-sourced task); people `Follow-up:` lines are collected only in checkbox form
  (people-update now writes them as checkboxes); never assigns a new anchor to mirror
  lines that reference an existing anchor via wikilink (prevented duplicate tasks from
  daily-brief's `## Pending follow-ups` mirror).
- **`challenge-decision`**: mode routing for `status: implemented` decisions aligned with
  the activation rules (red-team only when reconsidering; otherwise log).
- **`meeting-ingest`**: duplicate step `7.4` renumbered (Daily note → 7.5, Action items
  → 7.6).
- **Preflights**: braindump, meeting-ingest, people-update, and challenge-decision now
  read `00-inbox/MY-PROFILE.md`, matching the "every skill reads it" contract.
- **Docs de-staled**: the five remaining "six skills" claims (QUICKSTART, INSTALL ×3,
  USAGE-PATTERNS ×2, ARCHITECTURE ×2, CLAUDE.md intro) now say twelve; INSTALL's sanity
  check lists all 12; ARCHITECTURE's migration section reflects the Cowork-primary /
  Claude Code-power-user positioning and the current 06-knowledge layer.
- **Tag scheme documented as it actually is**: tags are `X.Y.Z` (no `v` prefix) —
  RELEASING.md, CHANGELOG header, and UPGRADING's four rollback commands (which would
  have failed as written) corrected.
- **Model recommendations refreshed** (SCHEDULED-TASKS): Sonnet 5 for briefs (Opus 5 for
  the weekly review if available), Haiku 4.5 for mechanical scans; note that `--model`
  aliases track the latest in each family.
- **Stale People Check** restriction uses the real `relationship:` enum (`manager`, not
  `manager-of-mine`) in SCHEDULED-TASKS and MY-PROFILE.
- **`vault-tend`**: large-vault scans can fan out parallel subagents (read-only phase).
- `_CLAUDE.md` rule 3.7 scoped: append-only applies to sensitive notes + wiki `## Sources`
  (taken literally, the old wording forbade legitimate edits like wiki enrichment and
  checkbox sync); "see Section 11" → "see Section 9" (curator).

### Fixed
- `templates/doc.md`, `templates/knowledge.md`, and the starter example note were missing
  the `domain:` field required since v3.4.
- `recall`'s worked example used a `.md`-suffixed wikilink, contradicting the extensionless
  convention every other skill relies on.
- `kickstart-backfill` announced "4 phases" but defines five; Phase 5 heading normalized.
- `knowledge-build`'s `_INDEX.md` template now documents the `## Health` listing
  subsections its own sweep steps (orphans, stubs, curator-unstable) write to.
- QUICKSTART: duplicated sentence removed; docs listing includes UPGRADING and RELEASING.

## [4.0.0] - 2026-06-18

### Added
- **`meeting-ingest` transcript-first source priority.** Drive meeting artifacts ship with
  two tabs — a verbatim transcript and an AI-generated summary. The summary is the default
  tab and is lossy (~40-60% signal loss: dynamics, exact decision wording, side-discussions,
  hesitation). `meeting-ingest` now ALWAYS reads the transcript first and falls back to the
  summary only when the transcript is unavailable, marking the note `confidence: medium`,
  `transcript-source: summary-fallback`, `needs-review: true`, with the limitation called out
  in the "For future Claude" preamble. New frontmatter fields on `type: meeting`:
  `transcript-source` and `confidence`. Auto mode applies the same rule.
- **`challenge-decision` postmortem mode.** Pendant to the existing red-team mode. Triggered
  when a `05-decisions/` note flips to `status: reversed` — either manually ("postmortem on
  this decision") or auto-detected by daily-brief on the day of the flip. Runs a bounded
  3-step learning loop:
  1. **Extract the lesson** — hypothesis, what reversed it, durable rule.
  2. **Cross-reference the vault** — every decision, wiki, lesson, project that rested on
     the reversed hypothesis. Produces a load-bearing-references manifest.
  3. **Propose updates** — append-only dated corrections on impacted wikis/lessons, status
     flags on dependent decisions, optionally a new `type: knowledge` lesson capturing the
     rule. Preview-first, batched, human-in-the-loop.
  Postmortem writes a standalone artifact at `06-knowledge/<decision-slug>-postmortem.md`
  (curator routes it to the matching domain hub via the `domain:` field). Auto mode runs
  steps P1–P2 only; P3 (the cross-vault edits) always awaits human approval.
- **`daily-brief` reversed-decision auto-trigger (Step 6.7).** Detects decisions that
  flipped to `status: reversed` since the last brief and invokes
  `challenge-decision` in postmortem mode for each. Surfaces the manifests + proposed
  edits in a conditional `## Decisions reversed — pending postmortem` section.
- **`knowledge-build` curator self-verification loop (Mode C.2 step 9).** The weekly
  sweep now reaches a stable state before exit: snapshot → verification pass → if zero
  diff, exit; otherwise re-iterate on the unstable hubs. Bounded at 3 passes total; if
  still unstable, the unstable hubs are flagged under `## Health → Curator unstable` in
  `_INDEX.md` (a bug signal, not a loop runaway). The report says how many passes it took
  to stabilize.

### Changed
- `challenge-decision` skill description now declares two modes (red-team + postmortem)
  and the new auto-trigger surface. The pre-existing red-team flow is now labeled
  `## Process — Red-team mode` for clarity; semantics unchanged.
- `meeting-ingest` schema for `type: meeting` adds `transcript-source` and `confidence`.

### Migration (v3.4.0 → v4.0.0)
Additive — no schema breakage for existing meetings (the new fields are optional and
default sensibly). For existing reversed decisions in the vault, the postmortem auto-trigger
only fires on flips *after* the upgrade — to retroactively run postmortems on older
reversals, invoke `challenge-decision postmortem` manually on each. Full procedure in
`docs/UPGRADING.md`.

### Fixed
- **Quiet quality leak in auto-ingested meetings**: defaulting to the Drive summary tab
  was silently degrading every downstream analysis that depended on meetings (people
  timelines, decision evidence, lesson extraction). Now caught at the source.
- **Curator drift**: the sweep was a single pass — a hub whose constituent notes changed
  during the pass could be left in an inconsistent state until the next weekly run. The
  self-verification loop closes this.

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
