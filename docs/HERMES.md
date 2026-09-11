# Running the Second Brain on Hermes Agent

Since v4.2 the vault can be operated by [Hermes Agent](https://github.com/NousResearch/hermes-agent)
(Nous Research) with a **local model**, alongside — or instead of — Claude Cowork / Claude Code.
Both editions share one contract: the vault (`_CLAUDE.md`, templates, the pre-commit hook).
Only the harness bindings differ.

## Why a plugin, and why it is different from the Claude skills

Small local models don't hold 500-line procedures, eleven "never" rules and a dozen MCP tools
in their head. So the Hermes edition moves the **plumbing into code** and keeps the
**judgment in the model**:

| | Claude edition (`.claude/skills/`) | Hermes edition (`hermes/`) |
|---|---|---|
| Format rules (frontmatter, preamble, paths, append-only, anchors) | instructions the model follows | **enforced by `sb_*` tools** — a non-conforming note cannot be written |
| Bookkeeping (hub listings, `_INDEX.md` counts, anchors, staleness) | done by the model | done by code (`sb_curate`, `sb_new_action`, `sb_append_timeline`) |
| Analysis (classification, extraction, insight, dynamics, recall, synthesis) | model | **model** — unchanged |
| Skill length | 150–500 lines | ≤ 40 lines: which tools, in what order, what to judge |
| Scope | 12 skills incl. red-team, postmortem, curator sweep, vault-tend | 13 skills — full parity |

Token economy follows: a capture costs one `sb_brief` (~500 tokens) + one short skill + a few
tool calls, instead of reading `_CLAUDE.md`, `MY-PROFILE.md` and a 200-line skill.

## Architecture

```
Hermes session (CLI / Slack / Telegram …)
   │  SOUL.md (identity) · USER.md (vault pointer) · skills index
   ▼
skill (procedure)  ──calls──▶  sb_* tools (plugin)  ──writes──▶  vault (Markdown)
                                    │                                  │
                              vault/ package                    pre-commit hook
                         (schemas · notes · links ·           (AI-first + append-only
                          search · tasks · index · git)         — the final judge)
```

- **`hermes/plugin/second_brain/vault/`** — the contract as code. `schemas.py` mirrors
  `_CLAUDE.md` §4 (folders, filenames, required fields, enums, sections). `notes.py` is the
  only writer: it never deletes or rewrites existing lines.
- **`hermes/plugin/second_brain/`** — `register(ctx)` publishes 21 tools under the
  `second_brain` toolset and 5 under `second_brain_sources` (each hidden automatically when
  no vault, or no credentials, are configured) plus an `on_session_start` hook.
- **`hermes/memory/sb_vault/`** — an optional *memory provider* plugin: before each turn it
  injects the vault notes relevant to what you just typed, with citations. Read-only, and it
  shares the retrieval engine with `sb_recall`, so passive and explicit recall never disagree.
- **`hermes/skills/`** — agentskills.io-format `SKILL.md` files with Hermes metadata
  (`requires_toolsets: [second_brain]`), loaded on demand via progressive disclosure.
- **`hermes/SOUL.md`** — the rules code cannot enforce (language, no invention, cite, ask before
  creating a person, describe don't judge).
- **Memory** — Hermes' `MEMORY.md`/`USER.md` hold pointers only; the vault is the memory, as
  in the Claude edition. `vault-starter/AGENTS.md` makes any AGENTS.md-aware agent read
  `_CLAUDE.md` first.
- **`hermes/bench/guardrails.py`** — the reliability scorecard: how much of the contract survives
  a model that gets it wrong (see *Reliability* below).

## Install

```bash
./hermes/setup.sh                    # vault at ~/second-brain
./hermes/setup.sh ~/notes/my-vault   # or wherever you want it
```

That is the whole thing. The script creates the vault from `vault-starter/` if it is missing,
runs `git init` and the first commit, installs the pre-commit hook, links the plugin, the memory
provider and the skills into `$HERMES_HOME`, writes `config.yaml` (backing up any existing one),
and finishes by checking that the plugin can actually read the vault. Re-running it is safe, and
it never overwrites a model you already configured.

It works identically for **Hermes Desktop** and the CLI: both resolve the same home
(`~/.hermes` on macOS and Linux, `%LOCALAPPDATA%\hermes` on Windows).

Two things the script deliberately leaves to you:

1. **Your profile** — fill `<vault>/00-inbox/MY-PROFILE.md`. Every skill reads it at preflight,
   and the working language set there decides the language of every note body.
2. **Your model** — pick one that does reliable **function calling** with a context window
   ≥ 32k. Ollama defaults to 4k, which is unusable here: raise `num_ctx`. Hermes 4 14B is the
   natural fit, being post-trained for tool use; Qwen3 14B and Gemma 4 12B also work.

`hermes/install.sh` is still there for a piecemeal install, but it assumes the vault and
`$HERMES_HOME` already exist and leaves the configuration to you.

### Smoke test
```
/braindump the onboarding team struggles with the new tier-1 script, Alex flagged edge cases
```
Expected: `sb_brief` → `sb_find_person("Alex")` → (ask if none) → `sb_create_note` →
`sb_daily_append` → `sb_commit`. The note in `00-inbox/` has frontmatter, an English preamble,
wikilinks; `git log` in the vault shows the commit; the hook accepted it.

## Maintenance, sources and the daily digest

**Plumbing vs judgment, per skill.** The tools do the bookkeeping; the model keeps the analysis:

| Skill | The tool does | The model does |
|---|---|---|
| `task-roundup` | `sb_maintain(scope=tasks)`: scan every action line, assign `^t-` anchors, reconcile checked boxes both ways (TODO.md ↔ source, mirrors in daily notes included), regenerate the buckets, flag removed sources and zombie tasks | decide the `needs_judgment` cases: unassigned owners, removed sources, zombies, and (scope `all`) near-duplicate pages and hub proposals |
| curator | `sb_maintain(scope=curator)`: rebuild `auto-maintained` hubs from scratch, refresh `_INDEX.md` (hubs, sources, unsorted, health with orphans / stubs / stale / near-duplicates), run the v4.0 self-verification loop (max 3 passes) | write summaries, decide merges, approve new hubs |
| staleness | set/clear `staleness-flag` on direct-reports, peers and managers (30d / 60d), frontmatter only | nothing — it is bookkeeping |
| `daily-digest` | `sb_calendar`, `sb_drive_changes`, `sb_slack`, `sb_jira`, `sb_vault_activity` return compact digests (a busy Slack day becomes ~15 lines); `(auto-logged)` people entries are formatted by `sb_append_timeline` | the synthesis: TL;DR, top topics across sources, weak signals, what to ingest |
| `meeting-ingest` | `sb_drive_doc` applies the **transcript-first** rule (Transcript tab → `verbatim`; summary tab → `summary-fallback` with a warning; else whole doc) and returns the text; `sb_create_note type=meeting` carries `transcript-source`/`confidence` | filter noise, extract decisions / actions / tensions / dynamics, judge reversibility |

**Sources need credentials in `~/.hermes/.env`** (the tools hide themselves otherwise):

| Source | Variables | How to get them |
|---|---|---|
| Google Calendar / Drive / Docs | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` | a Desktop OAuth client in Google Cloud Console + one consent run (scopes `calendar.readonly`, `drive.readonly`, `documents.readonly`) — the refresh token is long-lived |
| Slack | `SLACK_BOT_TOKEN` (`xoxb-…`: `channels:history`, `channels:read`, `groups:history`, `im:history`, `users:read`), optional `SLACK_USER_ID` for mentions | a Slack app installed in your workspace |
| Jira Cloud | `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` | id.atlassian.com → API tokens |

The connectors are stdlib `urllib` clients; each `digest_*` function is pure and unit-tested on fixtures.
Real API calls were not exercised in CI — the first `sb_calendar()` in your session is the integration test.

**Cron.** `hermes/cron/jobs.sh` registers three jobs — `sb-daily-digest` (weekdays 19:00, skills daily-digest +
meeting-ingest, delivered where you want), `sb-maintenance` (daily 07:30, task-roundup with `sb_maintain(scope=all)`,
which reports its open questions instead of deciding them because nobody is watching), and `sb-weekly-review`
(Mondays 09:00, the week's synthesis):

```bash
MODEL_MID=ollama/hermes4:14b DELIVER=slack ./hermes/cron/jobs.sh
```

Model per job is a flag (`--model`, `--provider`): use the smallest model that passes your smoke test for
maintenance, a stronger one for the digest.

## Passive recall, parity, and a number for the whole claim

### Passive recall (`sb_vault` memory provider)

The tools answer when the model thinks to ask. The memory provider answers before it does: it runs
the retrieval engine on what you just typed and injects the matching notes, with their paths and
dates, under the turn.

```bash
hermes config set memory.provider sb_vault     # installed by hermes/install.sh
```

Four decisions worth knowing about:

- **Read-only.** `sync_turn`, `on_session_end` and `on_memory_write` are deliberate no-ops. Notes
  are written only through the `sb_*` tools, by a skill you invoked. A vault whose history writes
  itself is no longer an audit trail.
- **Never blocking.** Retrieval runs on a background thread; `prefetch` returns what is ready. A
  cold cache costs nothing but a turn without recall.
- **Silent when it has nothing.** No match means no block — better an empty context than a
  plausible irrelevant one, which is exactly what makes a small model confabulate.
- **Evidence, not a summary.** What lands in context is note paths plus the lines that matched, so
  the model quotes and cites instead of paraphrasing something it never read.

Only one external memory provider can be active at a time, so this replaces (rather than joins)
another one.

### Parity: the remaining six skills

| Skill | Tool | What the tool refuses to decide |
|---|---|---|
| `recall` | `sb_recall` | the answer. It returns citations and a `confidence` of `stated / high / medium / speculation / unknown`; a near-miss keyword hit is dropped rather than dressed up as evidence, and `unknown` means the skill must say the vault does not know |
| `prioritize` | `sb_agenda` | the ranking. Tasks, deadlines, quiet projects, cooling relationships and a `signals` list come back unordered on purpose |
| `challenge-decision` | `sb_decision_context` / `sb_decision_postmortem` | the argument. It surfaces comparable decisions with reversals first, the stakeholders they named, and committed reversal conditions nobody revisited |
| `vault-tend` | `sb_tend` | everything but the frontmatter keys with one correct value. Language drift, broken links, duplicate people and archive candidates come back as proposals, never as edits |
| `kickstart-backfill` | `sb_backfill_plan` / `sb_backfill_done` | the ingestion. It computes date-windowed batches that fit one session, puts the entity phases first so people are deduplicated before meetings arrive, and records progress in the vault so an interrupted run resumes |
| `doc-ingest` | `sb_drive_doc` | the reading. It applies the transcript-first rule and hands over the text |

### Reliability

The project's claim is that a 12B model can run this because the tools hold the contract. That is
measurable, so it is measured:

```bash
python3 hermes/bench/guardrails.py --verbose
```

`hermes/tests/test_guardrails.py` sends the calls a confused small model actually makes — an invented
enum value, a missing preamble, an overwrite instead of an append, a path with `..` in it, a typo'd
name presented as an exact match, junk arguments of the wrong type — and asserts each one is refused
**by the code**, with a message saying what to do instead. The scorecard prints the share that held.

It has already paid for itself: it found an absolute path (`/etc/passwd`) reaching `sb_read`, now
refused by `vault.notes.safe_path` for every path-taking tool.

## Vault location resolution

`plugins.entries.second_brain.settings.vault_path` → `SECOND_BRAIN_VAULT` env → the current
directory or a parent containing `_CLAUDE.md`. When none resolves, the `sb_*` tools are hidden
(`check_fn`) and `on_session_start` logs a warning.

## How it was built

All of it shipped in 4.2.0, in four passes. The order is worth knowing, because it is the order in
which the pieces depend on each other — the contract had to be executable before anything could be
trusted to a small model.

| Pass | What it added |
|---|---|
| 1 | the plugin core (`vault/` as an executable contract), 3 capture skills, install, the conformance suite |
| 2 | `sb_maintain` (TODO sync both ways, curator sweep with self-verification, staleness, health, `needs_judgment`), the source digests, `daily-digest` / `meeting-ingest` / `task-roundup`, cron |
| 3 | the `sb_vault` memory provider for passive recall, `weekly-review`, and the guardrail scorecard |
| 4 | parity with the Claude edition: `sb_recall`, `sb_agenda`, `sb_decision_context`, `sb_decision_postmortem`, `sb_tend`, `sb_backfill_plan`, and the six skills that use them |

Ideas that have not been built: a semantic index (the current search is lexical and hub-first, which
has been enough), and per-model tuning of the skill texts once there is real usage to tune against.

## Troubleshooting

- **Tools missing in the session** → the vault could not be located: check the config key or `SECOND_BRAIN_VAULT`, then `hermes plugins doctor second_brain`.
- **`sb_commit` returns `commit rejected`** → the pre-commit hook fired; the `output` field says which rule (frontmatter, preamble, append-only). Fix the note through the tools, commit again.
- **Model edits notes with `write_file` instead of `sb_*`** → tighten the skill call in your prompt (`/braindump …`), or restrict the toolset for cron jobs; the hook still protects history.
- **Passive recall never fires** → `memory.provider` must be `sb_vault`, and `hermes/install.sh` must
  have linked `~/.hermes/plugins/sb_vault`. It is silent by design on trivial prompts and on questions
  the vault cannot answer, so test it with a question you know is covered.
- **Run the suite** → `./hermes/tests/run.sh` (no Hermes needed) · scorecard: `python3 hermes/bench/guardrails.py`.
