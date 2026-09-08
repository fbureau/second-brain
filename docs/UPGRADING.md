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

## 4.1.0 → 4.2.0  ·  Hermes Agent edition (plugin + short skills)

**TL;DR:** a new `hermes/` folder lets a local model operate the vault through a plugin that
enforces the note contract in code. Nothing changes for Claude Cowork / Claude Code users —
additive, **no vault migration**.

### Steps

**1. Update the tooling** — `git pull`.

**2. (Optional) Install the Hermes edition**
```bash
./hermes/install.sh /path/to/your/vault
hermes config set plugins.entries.second_brain.settings.vault_path /path/to/your/vault
hermes config set terminal.cwd /path/to/your/vault
hermes plugins doctor second_brain
```
Full guide: `docs/HERMES.md`.

**3. (Optional) Add `AGENTS.md` to your vault** — `cp vault-starter/AGENTS.md /path/to/your/vault/`
so any AGENTS.md-aware agent reads `_CLAUDE.md` first. Harmless for Claude.

### You're done when
- `hermes plugins list` shows `second_brain` enabled and `/braindump …` creates a committed note in `00-inbox/`.

### Rollback
```bash
cd /path/to/second-brain && git checkout 4.1.0
```

---

## 4.0.0 → 4.1.0  ·  Audit release (hook hardening, doc fixes, template alignment)

**TL;DR:** A repo-wide audit fixed ~50 defects: the pre-commit hook now blocks note
deletion/renames in append-only folders and validates the staged content (including
accented filenames); templates gained the missing `domain:` field plus new `meeting.md`
and `wiki.md`; the vault-starter ships the 06-knowledge layout; docs were de-staled.
Additive — **no vault migration**.

### Steps

**1. Update the tooling** — `git pull` (Claude Code) or re-upload the changed files (Cowork).

**2. Re-install the hook if your vault COPIED it.** `install.sh` symlinks when possible
(symlinked hooks pick up the new version automatically), but falls back to copying:

```bash
# from the tooling repo — safe to re-run either way:
./hooks/install.sh /path/to/your/vault
```

**3. Nothing else to do.** New starter files (`_INDEX.md`, `_sources/`) only affect fresh
vaults; existing vaults get the same layout via `knowledge-build curator --bootstrap`.
Optionally add `domain:` to any of your notes created from the old `doc`/`knowledge`
templates — the curator flags them as unsorted otherwise.

### You're done when
- `git rm` on a note in `02-people/` is blocked by the hook with "move to 07-archive/ instead".
- A note named with accents (e.g. `02-people/José García.md`) triggers the hook checks.

### Rollback
```bash
cd /path/to/second-brain && git checkout 4.0.0
```

---

## 3.4.0 → 4.0.0  ·  Transcript-first meetings + postmortem mode + curator self-verification

**TL;DR:** Three quality-leak fixes that didn't exist as concepts before.
- `meeting-ingest` now reads the **transcript** tab of Drive meeting artifacts, not the
  summary tab (which was the silent default and was losing ~half the signal).
- `challenge-decision` gains a **postmortem mode** that fires when a decision flips to
  `status: reversed`, runs a bounded 3-step learning loop, and proposes targeted updates
  across every wiki/lesson that rested on the now-wrong hypothesis.
- `knowledge-build` curator sweep gains a **self-verification loop** — it now reaches a
  stable state before exit instead of running one pass and hoping.

Additive — no destructive migration. The new behaviors fire on new events; existing notes
are untouched.

### Steps

**1. Update the tooling**
- *Claude Cowork:* re-upload the updated skill files: `meeting-ingest/SKILL.md`,
  `challenge-decision/SKILL.md`, `knowledge-build/SKILL.md`, `daily-brief/SKILL.md`.
- *Claude Code:* `git pull` in this repo.

**2. (Optional) Re-process old auto-ingested meetings**
If you have auto-ingested meetings in `04-meetings/` from before v4.0 that you suspect were
ingested from the summary tab, re-invoke `meeting-ingest` manually on each (Drive link or
the calendar event). The skill enters "post-auto validation" mode, re-reads from the
transcript if available, and updates the note with the richer source. The original
`(auto-logged)` markers stay intact.

This is purely opportunistic — no need to do it in bulk. Focus on meetings whose decisions
or lessons matter most.

**3. (Optional) Run postmortems on past reversed decisions**
For decisions in `05-decisions/` that are already `status: reversed` from before v4.0 (the
auto-trigger only fires on *new* flips), invoke manually if you want the learning loop:
```
postmortem on [[05-decisions/2025-09-...]]
```
The skill produces the manifest + previewed edits across the vault. Accept the ones you
care about.

**4. Nothing else to do**
- The new `transcript-source` and `confidence` fields on `type: meeting` are optional —
  old meetings without them keep working.
- The curator self-verification loop activates automatically on the next weekly sweep.
- The daily-brief reversed-decision auto-trigger activates the next time you run a brief.

### You're done when
- A new meeting auto-ingested by daily-brief shows `transcript-source: verbatim` (or
  `summary-fallback` with the explicit limitation callout if the transcript was missing).
- Flipping a decision to `status: reversed` and running tomorrow's daily-brief surfaces a
  `## Decisions reversed — pending postmortem` section with the manifest.
- The weekly review's `## Knowledge garden` section now reports how many passes the
  curator took to stabilize.

### Rollback
```bash
cd /path/to/second-brain && git checkout 3.4.0
```
No vault changes to revert — v4.0 is purely additive on the tooling side.

---

## 3.3.0 → 3.4.0  ·  Knowledge layer (domain hubs, `_INDEX.md`, `_sources/`) + curator

**TL;DR:** `06-knowledge/` gains a navigable shape — domain index hubs, a root `_INDEX.md`,
and an `_sources/` subfolder for ingested docs — plus a **curator** in `knowledge-build` that
maintains it. One interactive bootstrap migrates your existing vault. Additive — old notes
work; you opt in by running bootstrap once.

### What's new
- **Domain hubs** (`type: index`) at `06-knowledge/<domain>.md`. Each hub lists every wiki,
  lesson, and source doc tagged with the matching `domain:` field.
- **Root `06-knowledge/_INDEX.md`** — entry point that `recall` queries first.
- **`06-knowledge/_sources/` subfolder** — ingested docs (`type: doc`) move here so the root
  of `06-knowledge/` stays readable.
- **`knowledge-build` curator** — incremental on every capture, weekly sweep via daily-brief
  weekly, bootstrap on demand.
- **`domain:` field** required on every new wiki/lesson/doc; the capture skills infer it.
- **`## Knowledge domains` field** in `MY-PROFILE.md`.

### Steps

**1. Update the tooling**
- *Claude Cowork:* re-upload the updated skill files into your workspace:
  `knowledge-build/SKILL.md` (the big one), `daily-brief/SKILL.md`, `braindump/SKILL.md`,
  `meeting-ingest/SKILL.md`, `doc-ingest/SKILL.md`, `recall/SKILL.md`, `vault-tend/SKILL.md`.
  Also re-upload the updated `vault-starter/_CLAUDE.md` and `vault-starter/00-inbox/MY-PROFILE.md`
  if you want the new schemas + `## Knowledge domains` field in your vault.
- *Claude Code:* `git pull` in this repo.

**2. Update your vault's `_CLAUDE.md`**
Open `vault-starter/_CLAUDE.md` and your vault's `_CLAUDE.md` side by side. Copy across:
- The new `### type: index` block in Section 4.
- The `domain:` line added to `type: wiki`, `type: knowledge`, `type: doc` schemas.
- The path note above `type: doc` (`_sources/`).
- The updated vault structure tree in Section 2.
- The new Section 9 *Knowledge layer & curator*.
- The 3 new lines in Section 11 *What you NEVER do* (auto-maintained hubs, doc at root, domain tag).
- Section 5 *Naming conventions*: the 4 new lines (Wiki / Domain hubs / Root index / Source
  documents).

**3. Declare your knowledge domains** in `00-inbox/MY-PROFILE.md`
Add a `## Knowledge domains` section listing your 5–8 top-level domains (the curator can
propose more later). Example for a CS Change Manager:
```
- salesforce: Booksy's CS platform (Service Cloud, Agentforce, routing, go-live).
- booksy: Booksy-internal context (org, strategy, vision, brand).
- change-management: change rollout patterns, lessons, frameworks.
- cs-ops: CS day-to-day ops, KPIs, processes, escalations.
- vendor-stack: third-party tools (Zowie, Amazon Connect, Boost, Chargebee, ...).
- gtm-ops: GTM transformation, service-cloud GTM ways of working.
```

**4. Run the bootstrap migration** (one shot)
```
knowledge-build curator --bootstrap
```
The curator runs in batches with confirmations:
1. Creates `06-knowledge/_sources/`.
2. **Lists every `type: doc` at the root of `06-knowledge/`** and asks before moving them
   into `_sources/`. Rewrites inbound wikilinks.
3. Reads `## Knowledge domains` from your `MY-PROFILE.md`; proposes additional domains
   inferred from your existing tag clusters.
4. **Tags `domain:` on every wiki/lesson/doc** that doesn't have one yet — in batches of
   20, with top-3 candidates per note. You confirm/correct.
5. **Creates the domain hubs** (`06-knowledge/<domain>.md`) with `auto-maintained: true`.
6. **Proposes archival** for vault-meta artifacts sitting in `06-knowledge/`
   (`kickstart-backfill-*`, old `vault-health-*`).
7. **Writes `06-knowledge/_INDEX.md`** and archives the old `README.md` if it's anemic.

Review and commit:
```bash
cd /path/to/your/vault && git add -A && git commit -m "Bootstrap knowledge curator (v3.4.0)"
```

**5. (Cowork only) Add the weekly curator phase**
If you run a hand-written *weekly* prompt rather than the SKILL auto-trigger, add one line
after the lessons sweep:
`Then run knowledge-build curator sweep: rebuild auto-maintained hubs, refresh _INDEX.md, flag orphans / near-duplicates / aging stubs, propose hubs/merges; preview structural changes.`

### You're done when
- `06-knowledge/` shows `_INDEX.md` at top, `_sources/` subfolder, your domain hubs, then
  individual wikis/lessons — visibly less cluttered than before.
- `recall what is X` answers via the matching hub first (faster, more relevant).
- A new braindump mentioning a fresh concept silently creates a wiki stub *and* lands it in
  the right hub.

### Rollback
```bash
cd /path/to/second-brain && git checkout 3.3.0   # tooling
```
Bootstrap changes you accepted (notes moved into `_sources/`, hubs created) stay in the
vault. To revert the vault changes: `git revert <bootstrap-commit>` in your vault repo.

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
cd /path/to/second-brain && git checkout 3.2.0   # tooling
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
cd /path/to/second-brain && git checkout 3.0.0          # tooling
cd /path/to/your/vault   && git revert <backfill-commit> # vault (anchors are harmless if kept)
```

---

### Notes that apply to all upgrades
- **macOS:** the `.claude/` folder is hidden in Finder (dot-folder). Press **⌘⇧.** to reveal it.
- The pre-commit hook permits checkbox toggles and `^t-id` anchors in `02-people/` /
  `05-decisions/` — it only blocks deleting timeline history.
