# Second Brain

A personal knowledge system you run with **Claude**, built on an **[Obsidian](https://obsidian.md)
vault**. As you work, you tell Claude about your meetings, decisions, people, and stray ideas
— and it files everything into a tidy folder of Markdown notes (your *vault*). Over time that
vault becomes **Claude's long-term memory of your work**: who's who, what was decided and why,
what you're working on, and what you've learned.

The same notes are also *yours* to read: it's an ordinary Obsidian vault, so you browse, edit,
and explore the knowledge graph in Obsidian while Claude reads and writes the same files.

Built for **Claude Cowork** (you work with Claude in conversation; the skills trigger
automatically). It also runs in **Claude Code** for power users who want Git and a local CLI
— see [Setup](#setup) — and, since v4.2, on **Hermes Agent** with a local model through a
plugin that enforces the vault rules in code — see [`docs/HERMES.md`](docs/HERMES.md).

Inspired by [COG-second-brain](https://github.com/huytieu/COG-second-brain) and
[obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain).

## The problem it solves

Claude does have some memory — Cowork persists your workspace, Claude.ai has a Memory
feature, Claude Code can resume sessions — but none of it scales to a personal knowledge
base growing over months and years, and none of it is yours to grep, cite, version, or
move. So this system makes the **vault** the durable memory: every fact, decision, and
interaction is written to a Markdown note in a Git-tracked folder *you own*. Next session
— or in two years, or in another tool — Claude reads the vault and picks up where you
left off, with citations.

You don't file notes by hand. You just *work*, and the skills do the capturing, linking, and
organizing for you.

## How it works

```
        YOU, going through your day
              │   "process this meeting" · "I decided X" · "what should I focus on?"
              ▼
   CLAUDE  +  12 SKILLS   (they trigger automatically from what you say)
        capture  →  organize  →  recall  →  plan  →  maintain
              │   (skills read and write Markdown)
              ▼
   THE VAULT  — a folder of Markdown notes, versioned in Git
   = a second brain that maintains itself, and that Claude can query
```

Each skill is a small instruction file (`SKILL.md`) with a description. When what you say
matches a description, that skill runs — you rarely type a command. You *can* invoke one by
name (e.g. `recall …`) when you want to be explicit.

## Three principles

1. **AI-first** — every note is written to be retrieved and understood by Claude later, not
   scrolled by a human. Machine-readable frontmatter, an English "for future Claude" preamble,
   dated claims, and wikilinks between every person/project/decision.
2. **Append-only** — never overwrite; add a timestamped entry. People and decisions are sacred
   history. Git versions everything, so nothing is ever lost.
3. **MVP 98%** — the minimal structure that works. No religious PARA, no dogmatic Zettelkasten.

## The twelve skills

Grouped by what they're for. You don't memorize these — you describe what you want and the
right one runs.

**Capture** — get things into the vault
| Skill | Use it when | You get |
|---|---|---|
| **braindump** | A loose thought, an idea, a stray observation | A tagged, linked note in `00-inbox/` |
| **meeting-ingest** | You have a meeting transcript or raw notes | A structured note in `04-meetings/` (decisions, actions, people) — **always reads the transcript tab first**, falls back to the summary tab with a degraded-confidence flag when the transcript is missing |
| **doc-ingest** | A strategy doc, analysis, report, deck, or article | A note in `06-knowledge/` with the source (e.g. Google Doc) kept, linked to projects |

**Organize** — mostly automatic, runs while you work
| Skill | Use it when | You get |
|---|---|---|
| **people-update** | After a meaningful interaction with someone | An append-only update to that person's note in `02-people/` |
| **task-roundup** | "what's on my plate?" | One `TODO.md` at the vault root, checkboxes synced both ways with the source notes |
| **daily-brief** | Each day/week, or on demand | A synthesis in `01-daily/`; also auto-ingests meetings, updates people, and rounds up tasks |
| **knowledge-build** | "fais une fiche sur X", "what have we learned about X?", "curate / knowledge garden" | Your personal wiki (`type: wiki`, grown from first mention) + distilled lessons (`type: knowledge`) + a **curator** that maintains domain index hubs (`type: index`) and a root `_INDEX.md`, detects orphans, near-duplicates, aging stubs. Sources land in `06-knowledge/_sources/`. |

**Use** — get value back out
| Skill | Use it when | You get |
|---|---|---|
| **recall** | "what do I know about X?", "did we decide Y?" | A direct answer with citations (note + date) and a confidence level |
| **prioritize** | "what should I focus on?", "plan my day" | A ranked plan: priorities, order, a first step each, and suggested replies |
| **challenge-decision** | Before a high-stakes call (red-team) — or when a decision flips to `status: reversed` (postmortem) | Red-team mode: pressure-tests the call against your vault's history. Postmortem mode: extracts the lesson from the reversal, finds every wiki/lesson resting on the now-wrong hypothesis, proposes targeted updates so the vault learns. |

**Maintain & set up**
| Skill | Use it when | You get |
|---|---|---|
| **vault-tend** | "tidy the vault", "put everything in French", "deduplicate" | Whole-vault maintenance — preview-first, batched, append-only safe |
| **kickstart-backfill** | Once, on day 1 | A vault pre-filled from 1–6 months of your history |

## A day with it

```
You:  "Quick note — the onboarding team is struggling with the new qualification script."
→ braindump files it in 00-inbox/, links [[02-people/Alex Rivera]] and
  [[03-projects/Onboarding Refresh]], offers to update Alex's note.

You:  (paste a meeting transcript)
→ meeting-ingest extracts decisions, actions, and participants into 04-meetings/,
  keeps the Google Doc link, and updates the people involved.

You:  "What should I focus on today?"
→ prioritize reads your TODO.md, calendar, and active projects and hands back a
  ranked plan with a first step for each.

You:  "I'm thinking of centralizing tier-1 support in one hub."
→ challenge-decision scans your past decisions and meetings and red-teams the idea
  with citations from your own notes.
```

## The vault

The vault is an **[Obsidian](https://obsidian.md) vault** — a plain folder of Markdown notes,
synced however you like. That choice does real work:

- **One file, two readers.** Obsidian is your human window (browse, edit, search, graph view);
  Claude is the machine reader. No export, no database — the notes Claude writes are the notes
  you open in Obsidian.
- **`[[wikilinks]]` build a graph.** Every person, project, and decision is linked, so the
  vault becomes a navigable knowledge graph in Obsidian — and survives renames.
- **Future-proof & Git-native.** Flat Markdown is readable by any LLM with no plugins, and
  versions cleanly in Git.

Structure:

```
_CLAUDE.md        ← the vault's own brief, read first every session
TODO.md           ← consolidated action list (task-roundup, two-way checkbox sync)
00-inbox/         ← raw capture · your MY-PROFILE.md lives here
01-daily/         ← daily briefs + journal
02-people/        ← stakeholder CRM (append-only)
03-projects/      ← active and past projects
04-meetings/      ← ingested meetings
05-decisions/     ← decision log (feeds challenge-decision, append-only)
06-knowledge/     ← wiki + lessons + domain index hubs (`_INDEX.md` root, `_sources/` for ingested docs)
07-archive/       ← inactive (never deleted, only moved here)
```

`00-inbox/MY-PROFILE.md` is the keystone: it holds who you are, your priorities, your tone,
and your **working language**. Every skill reads it first, so the vault sounds like you and
writes in your language.

## Setup

You drive the system through **Claude** — the skills are `SKILL.md` files that trigger from
their descriptions, so most of the time you just talk.

1. **Get the files** — clone or download this repo.
2. **Create your vault** — copy `vault-starter/*` into your notes folder, then fill in
   `00-inbox/MY-PROFILE.md` (this is what makes it *yours*). Open that folder as a vault in
   [Obsidian](https://obsidian.md) to browse and edit it as a human.
3. **Give Claude the skills and point them at your vault** — make the `.claude/skills/`
   available to your Claude workspace and tell it where the vault lives.
4. **Start working** — tell Claude about a meeting or a decision, or ask
   *"what should I focus on today?"*. To seed history in one go, run **kickstart-backfill**.

> **Power-user path — Claude Code.** Running this in Claude Code adds Git as a first-class
> citizen: a pre-commit hook that enforces the note rules and blocks destructive edits to
> `02-people/` and `05-decisions/`, plus local CLI control. Daily/weekly briefs run on a
> schedule (native to Cowork-style scheduled tasks; via an external scheduler in Claude Code).
> Full procedure in [`docs/INSTALL.md`](docs/INSTALL.md) and
> [`docs/SCHEDULED-TASKS.md`](docs/SCHEDULED-TASKS.md).

> **Local-model path — Hermes Agent.** `./hermes/install.sh <vault>` installs a plugin whose
> tools generate compliant notes (frontmatter, preamble, append-only, anchors) so a small local
> model only supplies content and judgment. Three skills in phase 1 (braindump, people-update,
> knowledge-stub); the heavy analysis skills stay on Claude. See [`docs/HERMES.md`](docs/HERMES.md).

> **macOS note:** the `.claude/` folder is hidden in Finder (it starts with a dot). It's there
> and required — press **⌘⇧.** to reveal it. Don't rename it.

## Repository layout

```
.
├── CLAUDE.md                  ← project brief: conventions Claude reads every session
├── README.md
├── QUICKSTART.md
├── CHANGELOG.md
├── .claude/
│   ├── skills/                ← the 12 skills (auto-trigger from their description)
│   │   └── braindump · meeting-ingest · doc-ingest · daily-brief · people-update ·
│   │      challenge-decision · task-roundup · knowledge-build · recall · prioritize ·
│   │      vault-tend · kickstart-backfill   (each is a <name>/SKILL.md)
│   └── settings.json          ← config for the Claude Code path
├── hooks/                     ← Git pre-commit vault validation (+ install.sh)
├── hermes/                    ← Hermes Agent edition: plugin (sb_* tools), short skills, install, tests
├── docs/                      ← INSTALL · SCHEDULED-TASKS · USAGE-PATTERNS · ARCHITECTURE · …
├── templates/                 ← note templates (person, project, decision, daily, meeting, wiki, knowledge, doc)
└── vault-starter/             ← copy this into your notes vault
    ├── _CLAUDE.md             ← vault system brief (read first)
    ├── 00-inbox/MY-PROFILE.md ← your profile (fill this in)
    └── 01-daily/ … 07-archive/
```

## Maintenance

- **Git** — commit vault changes often; the append-only history is your audit trail. (In the
  Claude Code path, the pre-commit hook enforces the rules automatically.)
- **Weekly review** — run `daily-brief` in weekly mode; it also folds in `knowledge-build`.
- **Spring cleaning** — `vault-tend` for re-languaging, deduplication, link repair, and tidying.

## Versioning

[Semantic Versioning](https://semver.org/), tagged on `main`. The current version is in
[`VERSION`](VERSION); changes are in [`CHANGELOG.md`](CHANGELOG.md). To move an existing vault
between versions see [`docs/UPGRADING.md`](docs/UPGRADING.md); to cut a release see
[`docs/RELEASING.md`](docs/RELEASING.md).

## Credits

Patterns drawn from:
- [COG-second-brain](https://github.com/huytieu/COG-second-brain) — people CRM, numbered structure, role packs.
- [obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) — AI-first rules, the challenge pattern, append-only flow.

## License

MIT — see [`LICENSE`](LICENSE). Your vault is your own; this repository is only the tooling.
