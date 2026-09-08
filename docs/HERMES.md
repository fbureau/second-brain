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
| Scope | 12 skills incl. red-team, postmortem, curator sweep, vault-tend | phase 1: braindump, people-update, knowledge-stub; heavy analysis stays on Claude |

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
- **`hermes/plugin/second_brain/`** — `register(ctx)` publishes 11 tools under the
  `second_brain` toolset (hidden automatically when no vault is configured) and an
  `on_session_start` hook.
- **`hermes/skills/`** — agentskills.io-format `SKILL.md` files with Hermes metadata
  (`requires_toolsets: [second_brain]`), loaded on demand via progressive disclosure.
- **`hermes/SOUL.md`** — the rules code cannot enforce (language, no invention, cite, ask before
  creating a person, describe don't judge).
- **Memory** — Hermes' `MEMORY.md`/`USER.md` hold pointers only; the vault is the memory, as
  in the Claude edition. `vault-starter/AGENTS.md` makes any AGENTS.md-aware agent read
  `_CLAUDE.md` first.

## Install

1. Vault: copy `vault-starter/` somewhere, fill `00-inbox/MY-PROFILE.md`, `git init`, first commit.
2. `./hermes/install.sh /path/to/vault` — symlinks the plugin into `~/.hermes/plugins/second_brain`
   and the skills into `~/.hermes/skills/second-brain`, seeds `SOUL.md` and `memories/USER.md`
   (never overwrites existing ones), writes `SECOND_BRAIN_VAULT` to `~/.hermes/.env`, installs
   the pre-commit hook in the vault.
3. Config (or merge `hermes/config.example.yaml`):
   ```bash
   hermes config set plugins.entries.second_brain.settings.vault_path /path/to/vault
   hermes config set terminal.cwd /path/to/vault
   ```
4. Model: `hermes model` — pick something that does reliable **function calling** with a context
   window ≥ 32k (Ollama defaults to 4k: raise `num_ctx`). Candidates on a laptop: Hermes 4 14B,
   Qwen3 14B / 30B-A3B, Gemma 4 12B. Validate with the smoke test below before trusting it.
5. `hermes plugins doctor second_brain` · `hermes plugins list`.

### Smoke test
```
/braindump the onboarding team struggles with the new tier-1 script, Alex flagged edge cases
```
Expected: `sb_brief` → `sb_find_person("Alex")` → (ask if none) → `sb_create_note` →
`sb_daily_append` → `sb_commit`. The note in `00-inbox/` has frontmatter, an English preamble,
wikilinks; `git log` in the vault shows the commit; the hook accepted it.

## Phase 2 — maintenance, sources, digest

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

**Cron.** `hermes/cron/jobs.sh` registers two jobs — `sb-daily-digest` (weekdays 19:00, skills daily-digest +
meeting-ingest, delivered where you want) and `sb-maintenance` (daily 07:30, task-roundup with `sb_maintain(scope=all)`,
which reports its open questions instead of deciding them because nobody is watching):

```bash
MODEL_MID=ollama/hermes4:14b DELIVER=slack ./hermes/cron/jobs.sh
```

Model per job is a flag (`--model`, `--provider`): use the smallest model that passes your smoke test for
maintenance, a stronger one for the digest.

## Vault location resolution

`plugins.entries.second_brain.settings.vault_path` → `SECOND_BRAIN_VAULT` env → the current
directory or a parent containing `_CLAUDE.md`. When none resolves, the `sb_*` tools are hidden
(`check_fn`) and `on_session_start` logs a warning.

## Roadmap

| Phase | Release | Content |
|---|---|---|
| 1 | 4.2.0 | plugin core, 3 skills (braindump, people-update, knowledge-stub), install, conformance tests |
| 2 | 4.2.0 | `sb_maintain` (TODO sync both ways + curator sweep with self-verification + staleness + health, `needs_judgment` for the model), source digests (Calendar, Drive with transcript-first Docs reading, Slack, Jira), skills `daily-digest`, `meeting-ingest`, `task-roundup`, cron jobs |
| 3 | 4.3.0 | `sb-vault` memory provider (passive recall via `prefetch`), `weekly-review`, reliability measurements |

## Troubleshooting

- **Tools missing in the session** → the vault could not be located: check the config key or `SECOND_BRAIN_VAULT`, then `hermes plugins doctor second_brain`.
- **`sb_commit` returns `commit rejected`** → the pre-commit hook fired; the `output` field says which rule (frontmatter, preamble, append-only). Fix the note through the tools, commit again.
- **Model edits notes with `write_file` instead of `sb_*`** → tighten the skill call in your prompt (`/braindump …`), or restrict the toolset for cron jobs; the hook still protects history.
- **Run the suite** → `./hermes/tests/run.sh` (no Hermes needed).
