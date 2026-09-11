# Second Brain on Hermes Agent

The Hermes edition of the second brain: a **plugin** that turns the vault contract into typed
tools, thirteen **short skills** that call them, an optional **memory provider** for passive
recall, and **cron jobs**. Designed for small local models — the code guarantees the note
format, the model only supplies content and judgment.

```
hermes/
├── plugin/second_brain/     ← Hermes plugin: 26 `sb_*` tools in two toolsets + on_session_start hook
│   ├── vault/               ← the vault contract as code (stdlib-only, testable without Hermes):
│   │                          notes · links · search · tasks · index · maintenance · recall ·
│   │                          agenda · decisions · tend · backfill
│   └── sources/             ← Calendar · Drive/Docs (transcript-first) · Slack · Jira → compact digests
├── memory/sb_vault/         ← optional memory provider: read-only passive recall, with citations
├── skills/                  ← 13 skills: capture (braindump, people-update, knowledge-stub, meeting-ingest,
│                              doc-ingest) · routine (daily-digest, weekly-review, task-roundup) ·
│                              thinking (recall, prioritize, challenge-decision) · upkeep (vault-tend,
│                              kickstart-backfill)
├── cron/jobs.sh             ← `hermes cron create`: daily digest · maintenance · weekly review
├── bench/guardrails.py      ← reliability scorecard: how much holds when the model gets it wrong
├── SOUL.md                  ← agent identity: the rules code cannot enforce
├── config.example.yaml      ← settings to merge into ~/.hermes/config.yaml
├── memories/USER.md.example ← pointers only — the vault is the memory
├── install.sh               ← symlinks plugin + skills, seeds SOUL/USER.md/.env, installs the git hook
└── tests/                   ← conformance suite: every generated note must pass hooks/pre-commit
```

## Install

One command. It creates the vault, initialises git, links the plugin, and writes the
configuration itself. Works the same for Hermes Desktop and the CLI, and is safe to re-run.

```bash
./hermes/setup.sh                    # vault at ~/second-brain
./hermes/setup.sh ~/notes/my-vault   # or wherever you want it
```

Then two things only you can do:

1. Fill in `<vault>/00-inbox/MY-PROFILE.md` — your name, your language, your projects.
   Every skill reads it at startup.
2. In Hermes, pick a model that does reliable tool calling, then try
   `/braindump the onboarding team is struggling with the new script`.

If the `sb_*` tools do not appear, quit Hermes completely and reopen it: plugins are
discovered at startup. `hermes/install.sh` remains for the piecemeal install (it assumes the
vault and `~/.hermes` already exist).

Architecture and the full guide: [`docs/HERMES.md`](../docs/HERMES.md).

## Tools

| Tool | Guarantees |
|---|---|
| `sb_brief` | ~500-token operating brief (rules, profile essentials, counts) instead of 400 lines |
| `sb_search` / `sb_read` | hub-first, frontmatter-aware search; read one note |
| `sb_find_person` | fuzzy match against `02-people/` — exact / likely / ambiguous / none |
| `sb_create_note` | frontmatter + path + `## For future Claude` from the schema; enum validation; never overwrites; reports missing wikilinks |
| `sb_append_timeline` | dated `### YYYY-MM-DD — title` entry, stamps `updated`/`last-interaction`, clears staleness — the only way to touch append-only notes |
| `sb_append_section` / `sb_daily_append` | append at the end of a section (created if missing); daily note scaffolded on demand |
| `sb_new_action` | task line with a fresh, unique `^t-` anchor |
| `sb_curate` | curator incremental: hub listing (sorted), recent activity, `_INDEX.md` counts |
| `sb_commit` | `git commit` — the vault's pre-commit hook is the final judge |
| `sb_maintain` | TODO.md sync both ways, curator sweep (self-verifying), staleness flags, health — returns `needs_judgment` for the model |
| `sb_toggle_task` / `sb_vault_activity` | mark a task done in its source note by anchor; what changed in the vault recently |
| `sb_recall` | citations with the matching lines and a `confidence` of stated / high / medium / speculation / **unknown** — a near-miss is dropped, never dressed up as evidence |
| `sb_agenda` | open tasks, deadlines, quiet projects, cooling relationships and `signals` — gathered, deliberately **not** ranked |
| `sb_decision_context` / `sb_decision_postmortem` | comparable past decisions, reversals first; then what a reversal invalidates elsewhere |
| `sb_tend` | whole-vault audit, preview-first: safe frontmatter fixes apply on request, everything else comes back as a proposal |
| `sb_backfill_plan` / `sb_backfill_done` | Day-1 backfill as session-sized batches, entities first, resumable after an interrupt |
| `sb_calendar` / `sb_drive_changes` / `sb_drive_doc` / `sb_slack` / `sb_jira` | toolset `second_brain_sources` — compact digests; `sb_drive_doc` picks the Transcript tab first |

## Tests

```bash
./hermes/tests/run.sh                      # Python 3.10+ and git; no Hermes needed
python3 hermes/bench/guardrails.py -v      # scorecard: malformed calls refused by the code
```

The suite commits every generated note through `hooks/pre-commit`, so the hook is the shared judge
of both editions. `test_guardrails.py` is the adversarial half: it sends the calls a confused small
model actually makes and asserts each one is refused by the code rather than by a prompt.
