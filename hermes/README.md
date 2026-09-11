# Second Brain on Hermes Agent

The Hermes edition of the second brain: a **plugin** that turns the vault contract into typed
tools, thirteen **short skills** that call them, an optional **memory provider** for passive
recall, and **cron jobs**. Designed for small local models — the code guarantees the note
format, the model only supplies content and judgment.

```
hermes/
├── plugin/second_brain/     ← the plugin, self-contained: 27 `sb_*` tools in two toolsets
│   ├── skills/              ← the 13 skills, inside the package so a URL install carries them
│   ├── starter/             ← the vault template `sb_setup` scaffolds from
│   ├── vault/               ← the vault contract as code (stdlib-only, testable without Hermes):
│   │                          notes · links · search · tasks · index · maintenance · recall ·
│   │                          agenda · decisions · tend · backfill
│   └── sources/             ← Calendar · Drive/Docs (transcript-first) · Slack · Jira → compact digests
├── memory/sb_vault/         ← optional memory provider: read-only passive recall, with citations
├── cron/jobs.sh             ← `hermes cron create`: daily digest · maintenance · weekly review
├── bench/guardrails.py      ← reliability scorecard: how much holds when the model gets it wrong
├── SOUL.md                  ← agent identity: the rules code cannot enforce
├── config.example.yaml      ← settings to merge into ~/.hermes/config.yaml
├── memories/USER.md.example ← pointers only — the vault is the memory
├── setup.sh                 ← one command: vault, git, hook, plugin, config, self-check
├── install.sh               ← the piecemeal variant (assumes the vault already exists)
└── tests/                   ← conformance suite: every generated note must pass hooks/pre-commit
```

## Install

**From Hermes Desktop**: Settings → Plugins → install from URL, paste
`https://github.com/fbureau/second-brain/tree/main/hermes/plugin/second_brain`, then say
"set up my second brain". The plugin ships its own skills and vault template, so that is all.

**From a terminal**: `./hermes/setup.sh` — same result, plus the vault's pre-commit hook.

Full guide: [`docs/HERMES.md`](../docs/HERMES.md).

## Tools

| Tool | Guarantees |
|---|---|
| `sb_setup` | creates the vault from the bundled template and remembers where it is — the only tool offered when no vault exists, hidden once one does |
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
