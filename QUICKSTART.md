# Quickstart

Get running in ~15 minutes.

## 1. What you have

```
CLAUDE.md            ← conventions Claude reads every session
.claude/skills/      ← the 12 skills (auto-trigger from their description)
hooks/               ← Git pre-commit vault validation
docs/                ← INSTALL, SCHEDULED-TASKS, USAGE-PATTERNS, ARCHITECTURE, KICKSTART-PROMPT, UPGRADING, RELEASING
templates/           ← note templates
vault-starter/       ← copy into your notes vault (fill in 00-inbox/MY-PROFILE.md)
```

## 2. Minimal setup

1. Open this repo in **Claude Code**.
2. Copy `vault-starter/*` into your notes vault (an Obsidian vault, anywhere).
3. Edit `00-inbox/MY-PROFILE.md` — replace every `<...>` placeholder with your context.
4. In the vault: `git init`, then `./hooks/install.sh /path/to/vault`.
5. Tell Claude where the vault lives (set `VAULT_PATH` in `CLAUDE.md`).

Full details: [`docs/INSTALL.md`](docs/INSTALL.md).

## 3. The commands to remember

```
/braindump [content]                         ← flash capture
/meeting-ingest  (then paste a transcript)   ← process a meeting
/doc-ingest  (then paste/link a document)    ← capture a strategy doc / report / analysis
/people-update [Name]: [observation]         ← CRM
/daily-brief                                 ← synthesis on demand
/challenge-decision [position you're weighing]← before a high-stakes decision
/task-roundup                                ← consolidate actions into TODO.md
/knowledge-build [topic]                     ← distill durable knowledge
/recall [your question]                      ← query the vault (cited answers)
/prioritize                                  ← what to focus on + a plan
/vault-tend                                  ← whole-vault cleanup (re-language, tidy, dedup)
/kickstart-backfill                          ← once, on Day 1
```

(You don't have to type the command — describing what you want triggers the right skill.)

## 4. First reflex

Tomorrow morning, spend 30 seconds:

```
/braindump here's what's on my mind this morning...
```

If that creates a note in `00-inbox/`, the system works.

## 5. Reading order

| When | Read |
|---|---|
| Now | README.md + this file + `docs/INSTALL.md` |
| Day 1 (copying vault-starter) | `vault-starter/_CLAUDE.md` |
| Week 1 | `docs/USAGE-PATTERNS.md` |
| Month 2 | `docs/ARCHITECTURE.md` |
| Seeding from history | `docs/KICKSTART-PROMPT.md` |

## 6. When it doesn't work

- `MY-PROFILE.md` not filled in → skills run in degraded mode.
- Sources not connected (no email/calendar/chat tools or MCP) → daily-brief finds little.
- Vault not visible to Claude Code → set `VAULT_PATH` and confirm it can read the folder.

## 7. Reality check (after 2 weeks)

- Invoked the skills < 10×? The habit hasn't formed.
- Fewer than 20 notes in the vault? Capture discipline isn't there.
- Haven't read 2 daily briefs? Consumption isn't keeping up with production.

The good system is the one you actually use. MVP 98%.
