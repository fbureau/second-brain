# Second Brain on Hermes Agent

The Hermes edition of the second brain: a **plugin** that turns the vault contract into
typed tools, a handful of **short skills** that call them, and (phase 2) **cron jobs**.
Designed for small local models — the code guarantees the note format, the model only
supplies content and judgment.

```
hermes/
├── plugin/second_brain/     ← Hermes plugin: 11 `sb_*` tools + on_session_start hook
│   └── vault/               ← the vault contract as code (stdlib-only, testable without Hermes)
├── skills/                  ← braindump · people-update · knowledge-stub (≤ 40 lines each)
├── SOUL.md                  ← agent identity: the rules code cannot enforce
├── config.example.yaml      ← settings to merge into ~/.hermes/config.yaml
├── memories/USER.md.example ← pointers only — the vault is the memory
├── install.sh               ← symlinks plugin + skills, seeds SOUL/USER.md/.env, installs the git hook
└── tests/                   ← conformance suite: every generated note must pass hooks/pre-commit
```

## Install (10 min)

```bash
./hermes/install.sh /path/to/your/vault          # vault = a copy of vault-starter/, git-initialised
hermes config set plugins.entries.second_brain.settings.vault_path /path/to/your/vault
hermes config set terminal.cwd /path/to/your/vault
hermes model                                      # pick a tool-calling-capable model, context ≥ 32k
hermes plugins doctor second_brain && hermes plugins list
```

Then in a session: `/braindump the onboarding team is struggling with the new script`.
Full guide, architecture and roadmap: [`docs/HERMES.md`](../docs/HERMES.md).

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

## Tests

```bash
./hermes/tests/run.sh      # Python 3.10+ and git; no Hermes needed
```
