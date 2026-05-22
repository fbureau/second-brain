# Second Brain

An AI-first personal knowledge system for Claude Code. It turns your meetings,
decisions, people, and stray thoughts into a structured Markdown vault that Claude
can read, search, and reason over — so your second brain *is* Claude's memory.

Inspired by [COG-second-brain](https://github.com/huytieu/COG-second-brain) and
[obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain).

## Philosophy

> Your vault isn't for you. It's for the future Claude that will query it in 6 months,
> 2 years, 5 years.

Three non-negotiable principles:

1. **AI-first** — every note is built to be retrieved and understood by an LLM, not scrolled by a human.
2. **Append-only** — never overwrite; add with a timestamp. Git versions everything.
3. **MVP 98%** — the minimal structure that works. No religious PARA, no dogmatic Zettelkasten.

## How it works

```
SOURCES (via MCP / available tools)         CLAUDE CODE + 7 SKILLS
  email · calendar · drive · chat   ──────▶   braindump          → fast capture
                                              meeting-ingest     → transcript → structured note
                                              daily-brief        → daily/weekly synthesis + orchestrator
                                              people-update      → append-only stakeholder CRM
                                              challenge-decision → red-team against your own history
                                              task-roundup       → consolidate actions → TODO.md (two-way sync)
                                              kickstart-backfill → one-shot Day-1 seeding
                                                       │
                                                       ▼
                                              THE VAULT (Markdown, versioned in Git)
                                              a second brain that maintains itself
```

## Repository layout

```
.
├── CLAUDE.md                  ← project brief: conventions Claude reads every session
├── README.md
├── QUICKSTART.md
├── CHANGELOG.md
├── .claude/
│   ├── skills/                ← the 6 skills (auto-trigger from their description)
│   │   ├── braindump/SKILL.md
│   │   ├── meeting-ingest/SKILL.md
│   │   ├── daily-brief/SKILL.md
│   │   ├── people-update/SKILL.md
│   │   ├── challenge-decision/SKILL.md
│   │   ├── task-roundup/SKILL.md
│   │   └── kickstart-backfill/SKILL.md
│   └── settings.json          ← Claude Code config
├── hooks/                     ← Git pre-commit vault validation (+ install.sh)
├── docs/
│   ├── INSTALL.md
│   ├── SCHEDULED-TASKS.md
│   ├── USAGE-PATTERNS.md
│   ├── ARCHITECTURE.md
│   └── KICKSTART-PROMPT.md
├── templates/                 ← note templates (person, project, decision, daily)
└── vault-starter/             ← copy into your Obsidian vault
    ├── _CLAUDE.md             ← vault system brief (read first)
    ├── 00-inbox/MY-PROFILE.md ← your profile (fill this in)
    └── 01-daily/ … 07-archive/
```

## Vault structure

```
_CLAUDE.md        ← system brief, read first every session
TODO.md           ← consolidated action list (task-roundup, two-way checkbox sync)
00-inbox/         ← raw capture · MY-PROFILE.md lives here
01-daily/         ← daily briefs + journal
02-people/        ← stakeholder CRM (append-only)
03-projects/      ← active and past projects
04-meetings/      ← ingested meetings
05-decisions/     ← decision log (feeds challenge-decision, append-only)
06-knowledge/     ← durable syntheses, frameworks, lessons
07-archive/       ← inactive (never deleted)
```

## Quick start

See [`docs/INSTALL.md`](docs/INSTALL.md) for the full procedure. In short:

1. Clone this repo and open it in Claude Code.
2. Copy `vault-starter/*` into your notes vault and fill in `00-inbox/MY-PROFILE.md`.
3. `git init` the vault and install the hook: `./hooks/install.sh /path/to/vault`.
4. Try it: `/braindump my priorities this week are X, Y, Z`.
5. (Optional) Wire `daily-brief` to an external scheduler — see [`docs/SCHEDULED-TASKS.md`](docs/SCHEDULED-TASKS.md).

## The seven skills

| Skill | When to use | Output |
|---|---|---|
| **braindump** | Loose ideas, after an informal chat, in the morning | Tagged, linked note in `00-inbox/` |
| **meeting-ingest** | After a meeting (transcript, raw notes) | Structured note in `04-meetings/` (decisions, actions, people) |
| **daily-brief** | Daily/weekly (scheduled) or on demand | `01-daily/YYYY-MM-DD.md` synthesis; orchestrates auto-ingest + people updates + task roundup |
| **people-update** | After a meaningful stakeholder interaction | Append-only update to `02-people/[Name].md` |
| **challenge-decision** | Before a high-stakes decision | Red-team of your idea against vault history |
| **task-roundup** | "what's on my plate", or after new action items land | Consolidated `TODO.md` at the vault root, checkboxes synced both ways |
| **kickstart-backfill** | Once, on Day 1 | Pre-fills the vault from 1–6 months of history |

## Daily use

```
/braindump saw the onboarding team is struggling with the new qualification script
→ creates 00-inbox/...md, links [[02-people/Alex Rivera]] and [[03-projects/Onboarding Refresh]],
  offers a people-update on Alex

/meeting-ingest  (then paste/attach a transcript)
→ extracts decisions/actions/people, creates 04-meetings/...md, updates impacted people notes

/challenge-decision I want to centralize tier-1 support in one hub
→ scans 05-decisions/ and 04-meetings/ for precedents, red-teams with citations from your own notes
```

## Maintenance

- **Git**: commit vault changes often; the append-only history is the audit trail. The
  pre-commit hook enforces AI-first compliance and blocks destructive diffs on
  `02-people/` and `05-decisions/`.
- **Weekly review**: run `daily-brief` in weekly mode.
- **Vault health**: a monthly scheduled check for orphans, stubs, and duplicates.

## Credits

Patterns drawn from:
- [COG-second-brain](https://github.com/huytieu/COG-second-brain) — people CRM, numbered structure, role packs.
- [obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) — AI-first rules, the challenge pattern, append-only flow.
