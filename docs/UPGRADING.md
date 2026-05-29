# Upgrading

Moving an existing vault to a newer version. Find your jump below and follow the numbered
steps. Each upgrade is **additive and append-only safe** — nothing is renamed or deleted.

## How upgrades work here (read once)

There are two parts, and they're separate:

1. **The tooling** = this repo (skills, hooks, docs). You update it with `git pull` (Claude
   Code) or by re-uploading the changed skill files (Cowork). Updating tooling is safe — it
   touches no notes.
2. **Your vault** = your Markdown notes. Most upgrades need *nothing* here. A few add a new
   file or a one-time pass over existing notes — always called out explicitly.

> **Before any upgrade:** commit (or back up) your vault. That's your one-command undo.

**The 3-step shape of every upgrade:**
1. Update the tooling.
2. Apply any vault changes for that version (often none).
3. Verify, then commit your vault.

---

## 3.2.0 → 3.3.0  ·  Personal wiki + Slack as a co-primary source

**TL;DR:** `06-knowledge/` becomes a real **personal wiki** (encyclopedic pages, grown from
the first mention) alongside the existing lessons. Slack stops being under-weighted in the
daily brief when you set one new field. Purely additive — **no vault migration** required.

### What's new
- **Wiki pages** (`type: wiki`) in `06-knowledge/` — encyclopedic pages on concepts/entities/tools/
  teams/jargon. Stubs are auto-created on first mention by `braindump`, `meeting-ingest`,
  `doc-ingest`. Each fact carries an inline citation; `## Sources` is the cumulative trail.
- **`primary-communication-channels`** field in `MY-PROFILE.md` — list `slack` (or `teams`)
  here and `daily-brief` will treat chat as co-primary with email/calendar, collect broadly,
  and render a dedicated `## Themes from Slack` section that doesn't compete with the top-5.
- **`chat-channels-to-ignore`** field — blocklist for noisy channels.

### Steps

**1. Update the tooling**
- *Claude Cowork / Obsidian:* re-upload the updated skill files into your workspace:
  `daily-brief/SKILL.md`, `knowledge-build/SKILL.md`, `braindump/SKILL.md`,
  `meeting-ingest/SKILL.md`, `doc-ingest/SKILL.md`, `recall/SKILL.md`. Also re-upload the
  updated `vault-starter/_CLAUDE.md` (only if you want the new `type: wiki` schema in your
  vault's `_CLAUDE.md` — see step 2).
- *Claude Code:* `git pull` in this repo. Updated skills auto-pick up.

**2. Add the `type: wiki` schema to your vault's `_CLAUDE.md`**
Open `vault-starter/_CLAUDE.md` and your vault's `_CLAUDE.md` side by side. Copy the new
`### type: wiki  (encyclopedic page …)` block from section 4 across, right after the
`type: knowledge` block. (Skip this step if you never customized `_CLAUDE.md` — just copy
the new vault-starter version in full.)

**3. Set your primary communication channels**
Open `00-inbox/MY-PROFILE.md` → **Primary communication channels** and set:
```
- `primary-communication-channels`: [slack]      # or [slack, teams], [email] only, etc.
```
Optionally fill **Chat channels to ignore** with the noisy ones (bots, build alerts, etc.).
Effect is immediate on the next `daily-brief` run.

**4. (Optional) Seed your wiki from existing notes**
Run it once to convert existing concept references into wiki stubs:
```
knowledge-build wiki sweep
```
It scans `06-knowledge/` wikilinks across the vault, creates stubs for every concept that
doesn't have a page yet, and records the trigger source for each. Stubs are flagged
`needs-review: true` — review and enrich at your pace.

**5. (Cowork only) Update your hand-written daily prompt**
If you run a hand-written daily prompt rather than the SKILL auto-trigger, update PHASE 1
step 4 (Chat) to broad-mode + Themes-from-Slack rendering — copy from
[`SCHEDULED-TASKS.md`](SCHEDULED-TASKS.md) line 81. On Claude Code / SKILL auto-trigger this
is already in the skill — nothing to do.

### You're done when
- A new term mentioned in a braindump creates a `type: wiki` stub in `06-knowledge/` with
  `needs-review: true` and the braindump cited in `## Sources`.
- `daily-brief` produces a `## Themes from Slack` section when chat is busy, separate from
  the top-5 topics.
- `recall what is X` returns the wiki page directly when X has a page.

### Rollback
```bash
cd /path/to/second-brain && git checkout v3.2.0   # tooling
```
Wiki notes you accepted stay in the vault (they're just Markdown). To remove the
`primary-communication-channels` line, just delete it from `MY-PROFILE.md`.

---

## 3.1.0 → 3.2.0  ·  Doc ingestion, knowledge base, recall, prioritize, language setting

**TL;DR:** four new skills + a language setting. Purely additive — **no vault migration**.

### What's new
- `doc-ingest` — capture strategy docs / analyses / reports into `06-knowledge/`.
- `knowledge-build` — distill a real knowledge base from the vault (also runs weekly).
- `recall` — ask the vault questions, get cited answers.
- `prioritize` — get a ranked plan of what to do next.
- **Working language** is now a setting in `MY-PROFILE.md`.

### Steps

**1. Update the tooling**
- *Claude Code:* `git pull` in this repo. The four new skills appear under `.claude/skills/`
  and auto-trigger — nothing to install.
- *Cowork / Obsidian:* upload these new/changed files into your project:
  `doc-ingest/SKILL.md`, `knowledge-build/SKILL.md`, `recall/SKILL.md`, `prioritize/SKILL.md`,
  and the updated `daily-brief/SKILL.md`. Add them to your project's skill list if you keep one.

**2. Set your language** (the FR/EN mixing fix)
Open `00-inbox/MY-PROFILE.md` → **Communication preferences** → set:
```
- **Working language**: fr     # or en, es, …
```
From now on every skill writes note bodies and replies in that language. The
"For future Claude" preamble stays English by design. *(Existing notes aren't rewritten;
this applies going forward. Ask `knowledge-build`/`recall` in your language anytime.)*

**3. (Optional) Seed your knowledge base**
Run it once to turn existing meetings/decisions/docs into durable knowledge:
```
knowledge-build
```
Review what it proposes (auto-created notes are flagged `needs-review: true`), then commit.

**4. (Cowork only) Add the weekly knowledge sweep**
If you run a hand-written *weekly* prompt, add one line so it folds in the new behavior:
`After the review, run knowledge-build (conservative sweep; flag new/updated notes needs-review: true).`
On Claude Code this is already in the skill — nothing to do.

### You're done when
- `recall what do I know about <a topic>` returns a cited answer.
- `doc-ingest` + a pasted report creates a note in `06-knowledge/` linked to a project.
- `prioritize` returns a ranked plan.
- New notes come out in your chosen language.

---

## 3.0.0 → 3.1.0  ·  Centralized tasks (`task-roundup` + `TODO.md`)

**TL;DR:** new `task-roundup` skill + a `TODO.md` at the vault root with two-way checkbox
sync. One small vault change (add `TODO.md`) and one one-time pass (backfill anchors).

### Steps

**1. Update the tooling**
- *Claude Code:* `git pull`. New skill at `.claude/skills/task-roundup/`; `daily-brief` updated.
- *Cowork:* upload `task-roundup/SKILL.md` (new) and `daily-brief/SKILL.md` (updated).

**2. Add `TODO.md` to your vault** (or let step 4 create it)
```bash
cp /path/to/second-brain/vault-starter/TODO.md /path/to/your/vault/TODO.md
```

**3. Update your vault's `_CLAUDE.md`** *(skip if you never customized it — just copy the new one)*
Add the new **"Tasks & the TODO dashboard"** section. The easiest path: open
`vault-starter/_CLAUDE.md` and your vault's `_CLAUDE.md` side by side and copy the section
across. The block to add:

<details><summary>Section to paste into your <code>_CLAUDE.md</code></summary>

```markdown
## Tasks & the TODO dashboard

Action items are scattered across notes (meeting `## Action items`, decision
`## Execution plan`, daily `## Pending follow-ups`, people `Follow-up:`, braindump
`## Suggested follow-up`). `task-roundup` consolidates the ones you own into a single
`TODO.md` at the vault root. Source notes are the source of truth; `TODO.md` is a
generated, reconcilable view.

Action-line convention: `- [ ] <action> — owner: me — due: YYYY-MM-DD — #from/meeting ^t-ab12cd`
- `^t-xxxxxx` is a stable block-ID, assigned once by task-roundup, never changed.

Sync: a box checked in `TODO.md` flips its source line to `[x] ✅ <date>` on the next
roundup, and vice-versa. Completing a task in `02-people/` or `05-decisions/` is a checkbox
toggle + `✅` stamp only — never rewrite surrounding content.
```
</details>

**4. One-time: backfill anchors and build the first `TODO.md`**
```
task-roundup
```
It adds a `^t-id` to every existing action line (additive — removes nothing) and builds
`TODO.md`. Review and commit:
```bash
cd /path/to/your/vault && git add -A && git commit -m "Backfill task anchors + TODO.md (v3.1.0)"
```

**5. (Cowork only)** If you run a hand-written *daily* prompt, add a roundup phase — see the
`PHASE 6.5` block in [`SCHEDULED-TASKS.md`](SCHEDULED-TASKS.md).

### You're done when
- `TODO.md` lists your open actions bucketed by due date, each linking to its source note.
- Checking a box in `TODO.md` then running `task-roundup` flips it in the source note.

### Rollback
```bash
cd /path/to/second-brain && git checkout v3.0.0          # tooling
cd /path/to/your/vault   && git revert <backfill-commit> # vault (anchors are harmless if kept)
```

---

### Notes that apply to all upgrades
- **macOS:** the `.claude/` folder is hidden in Finder (dot-folder). Press **⌘⇧.** to reveal it.
- The pre-commit hook permits checkbox toggles and `^t-id` anchors in `02-people/` /
  `05-decisions/` — it only blocks deleting timeline history.
