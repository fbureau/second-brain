---
name: daily-brief
description: Generates a daily (or weekly) brief by synthesizing connected sources (email, calendar, drive, chat) and the vault notes touched during the day. Produces a note in 01-daily/. Also orchestrates auto-ingestion of meetings and auto-update of people notes. Use as a scheduled daily task, or manually when the user says "daily brief", "what happened today", "recap of the day", "weekly review".
---

# Skill: Daily Brief

## When to activate

- **Scheduled daily task** (e.g. end of day) → daily mode.
- **Scheduled weekly task** (e.g. Monday morning) → weekly mode (synthesis of the previous week).
- Manual invocation: "daily brief", "recap of the day", "what happened", "weekly review".

## Preflight

1. **Read `_CLAUDE.md`** (rules, structure, conventions) and `00-inbox/MY-PROFILE.md`.
2. **Get the real timestamp.**
3. **Determine the mode**: daily (default) or weekly (Monday morning or on request).
4. **Define the time window**:
   - daily: today 00:00 → now.
   - weekly: Monday of last week 00:00 → Sunday of last week 23:59.

## Process

### Step 1 — Multi-source collection

Collect from whatever sources are connected (via available tools / MCP servers).
Run in parallel where possible:

#### 1.1 Email
- Emails received in the window.
- Filter out: newsletters, automated notifications, marketing.
- Keep: conversations with colleagues, relevant externals, decision threads.
- Extract: subject, sender, one-line summary, implicit urgency.

#### 1.2 Calendar
- Events in the window (past + ongoing).
- For each: title, participants, duration, notes/description.
- Cross-reference with `04-meetings/`: if already ingested → link, else → flag for potential ingestion.

#### 1.3 Drive / files
- Docs modified or shared in the window.
- Filter out: your own minor edits.
- Keep: new docs received, collaborative docs touched by others, meeting transcripts created.

#### 1.4 Chat (Slack/Teams/etc.)
- DMs received in the window.
- Mentions of the user in channels.
- Important threads in critical channels (defined in `MY-PROFILE.md`).
- Filter out: emoji-only reactions, bot notifications.

#### 1.5 Internal vault
- Notes created or modified in the window (all sections except `07-archive`).
- Especially: new decisions, ingested meetings, people updates, unprocessed braindumps.

### Step 2 — Triage and prioritization

Categorize the collected items:

#### 2.1 Decisions / Commitments
- Any action the user committed to ("I'll handle it", "ok I'll do it", an assigned action item).
- Decisions made by others that impact the user's projects.

#### 2.2 Weak signals
- A topic mentioned repeatedly across channels.
- Detectable interpersonal tensions.
- Shifts in tone/priority from stakeholders.
- First mention of something that could grow.

#### 2.3 Awaited follow-ups
- Action items the user owns with an approaching deadline.
- People waiting on a reply from the user.
- Past commitments to verify.

#### 2.4 Learning / inputs
- Articles shared, docs to read.
- New concepts/frameworks mentioned.
- Best practices surfaced by teams.

#### 2.5 People intel
- People interacted with today.
- New information about known stakeholders (role change, etc.).
- New people encountered (candidates for a person note).

### Step 3 — Intelligent synthesis

⚠️ **Major anti-pattern**: do not produce a flat exhaustive list. The brief must
be **actionable and synthetic**.

Synthesis rules:
- **Top 3–5 topics** only as main sections (not 15).
- **One sentence = one signal** (no vague paraphrase).
- **Always link** to the source (email, meeting, doc, vault note).
- **Recency markers** for external claims.

### Step 4 — Generate the note

**Daily path**: `01-daily/YYYY-MM-DD.md`
**Weekly path**: `01-daily/YYYY-WW-weekly.md` (e.g. `2026-21-weekly.md`)

⚠️ **If the daily note already exists** (because other skills wrote into it during
the day): APPEND, don't replace. Add the brief at the top under `## Daily brief`,
keeping the existing sections (braindumps, ingested meetings).

**Daily format:**

```markdown
---
date: YYYY-MM-DD
type: daily
tags: [daily]
ai-first: true
---

## For future Claude

Daily brief for [date]. Generated automatically at [timestamp] aggregating email,
calendar, drive, chat, and internal vault activity. Top themes: [3-5 keywords].
[Note any unusual signal or urgent follow-up.]

## TL;DR (3 lines)

1. [The most important thing today, one sentence]
2. [The second thing, one sentence]
3. [The third thing, one sentence]

## Decisions & commitments

- [Committed action] — source: [[email/meeting/chat]] — deadline: YYYY-MM-DD
- [Decision by X impacting project Y] — source: [...]

## Top topics of the day

### [Topic 1]
[2-3 sentences synthesizing what happened on this topic, with linked sources]
**Sources**: [[04-meetings/...]], email from [[02-people/...]], chat thread #channel
**Next**: [action or open question]

### [Topic 2]
[...]

## Weak signals to dig into

- [Signal 1] — observed in [sources] — hypothesis: [...]
- [Signal 2] — [...]

## Pending follow-ups

[Fed from the Overdue + Today buckets of [[TODO]]. Each links back to its source note.]
- [ ] [Action] — [[TODO]] → [[<source-note>#^t-id]] — due YYYY-MM-DD
- [ ] [Action] — [[<source-note>#^t-id]] — due YYYY-MM-DD

## People touched today

- [[02-people/Alex Rivera]] — 1-1 + 2 emails — topic: training
- [[02-people/...]] — [...]

## Inputs of the day

- [Article/doc shared by X] — source: [link or drive path] — relevance: [why]

## Braindumps of the day

[Links to braindumps created via the braindump skill — that skill appends here]

## Meetings ingested today

[Links to ingested meetings — meeting-ingest appends here]
```

**Weekly format** (different — synthesis-focused vs. collection):

```markdown
---
date: YYYY-MM-DD              # first day of the analyzed week
week: YYYY-WW
type: weekly-review
tags: [weekly]
ai-first: true
---

## For future Claude

Weekly review for week [WW] of [YYYY]. Covers [start date] → [end date]. Compiled
from 7 daily briefs + a direct vault scan.

## Themes of the week

[3-5 cross-cutting themes that emerged, with backlinks to daily notes / meetings / decisions]

### [Theme 1]
- Appeared: [first signal]
- Evolution: [how it moved]
- Current state: [resolved / open / escalated]
- Linked to: [[03-projects/...]]

## Decisions of the week

[Structured recap of important decisions, with links to 05-decisions/]

## People focus

[Who emerged most this week? Why?]

## Patterns detected

[Cross-day recurrences, confirmed weak signals]

## Anti-patterns / Friction

[What isn't working, what recurs negatively]

## Energy & focus

[Honest synthesis: where did the energy go, is it aligned with declared priorities?]

## Implicit plan for next week

[What the daily notes suggest as priorities for the coming week]

## Stubs to process

[Incomplete notes or notes awaiting clarification]
```

### Step 5 — Meeting auto-orchestration (CRITICAL)

⚠️ **This is what makes the system run without manual intervention.**

For each meeting transcript detected during the window:

#### 5.1 Whitelist check
A transcript is **auto-ingestable** ONLY if ALL conditions hold:
- ✅ Matches a calendar event in the window (by title, participants, or time).
- ✅ Calendar participants ≥ 2 (including the user).
- ✅ Calendar duration ≥ 15 minutes.
- ✅ NOT in the `sensitive-meetings` list of `00-inbox/MY-PROFILE.md`.
- ✅ Not already ingested (cross-check `04-meetings/` by date + slug).

#### 5.2 Auto-ingest (for transcripts that pass the whitelist)
Invoke `meeting-ingest` in auto mode, with these differences vs. manual:
- Frontmatter: `ingestion-mode: auto` and `needs-review: true`.
- "For future Claude" mentions: `*Auto-ingested via daily-brief on YYYY-MM-DD. needs-review flag is true until the user confirms.*`
- People propagation handled in step 6 (don't duplicate here).
- Hard-to-reverse decisions detected → flag `needs-validation: true` rather than creating directly in `05-decisions/`.

Cap at 5 auto-ingested meetings per daily-brief run to avoid saturating context.
If > 5, ingest the 5 longest/most important and list the rest for the next day.

#### 5.3 Flag for human validation
For transcripts that do NOT pass the whitelist:
- Mention explicitly in the brief:
  ```
  ⏸ Awaiting manual validation:
  - 1-1 with [manager] (sensitive, transcript available) → want me to ingest it?
  - Orphan transcript (no calendar match) → ignore or ingest with context?
  ```
- Auto-ingest NOTHING.
- The user validates yes/no the next day when reading the brief.

### Step 6 — People auto-update (CRITICAL)

For each person the user interacted with during the window (detected via calendar/email/chat):

#### 6.1 Interaction detection
For each person:
- Calendar events (participants including the person).
- Email threads (sender OR recipient = this person; exclude generic cc).
- Chat DMs (direct DM or mention in a critical channel).

#### 6.2 Fuzzy-match against 02-people/
- If the note exists → proceed to update (step 6.3).
- If the note does NOT exist → create NOTHING automatically. Append to the
  "New people detected" section of the brief for the user to validate next day.

#### 6.3 Update the note (auto-logged)
For each person whose note exists:

**Frontmatter**:
- Update `last-interaction: YYYY-MM-DD` (today).
- Update `updated: YYYY-MM-DD` (today).
- **Clear `staleness-flag`** if present (self-healing).

**Timeline**:
Append ONE aggregated entry for the day:
```markdown
### YYYY-MM-DD — Daily interactions (auto-logged)
- Calendar: [events with this person, format "1-1 30min 'title'"]
- Email: [N threads, main topic if detectable]
- Chat: [N DMs or mentions, channel if relevant]
- Source: daily-brief auto-propagation
```

⚠️ **No interpretive observation.** Raw facts only. The "Compiled truth" section is
NEVER touched in auto mode.

⚠️ **Deduplication**: if an `(auto-logged)` timeline entry already exists for the
day (rare: daily-brief run twice), update the existing entry instead of creating a
new one.

#### 6.4 Quantity cap
Auto-update up to 20 people notes per run. If > 20 detected (rare: very busy day),
prioritize:
1. Direct reports
2. Manager
3. Recurring peers
4. Critical stakeholders (per `MY-PROFILE.md`)
5. Others

List the non-updated ones in the brief: "12 other people interacted with today not
auto-updated (volume cap). Invoke people-update manually if needed."

### Step 6.5 — Task roundup & reconciliation (CRITICAL)

Run the `task-roundup` procedure (see `.claude/skills/task-roundup/SKILL.md`):

1. Collect the action items **you own** from today's new/updated notes (ingested
   meetings, decisions, follow-ups) plus anything still open across the vault.
2. Assign a `^t-id` block-ID to any new action line that lacks one (additive edit).
3. Reconcile checkboxes both ways with `TODO.md` at the vault root: a box checked in
   `TODO.md` since the last run flips its source line to `[x] ✅ <date>`, and vice versa.
4. Refresh `TODO.md`, bucketed by due date (overdue / today / upcoming / later / no date
   / waiting-on-others / done).

⚠️ Completing a task in `02-people/` or `05-decisions/` is a checkbox toggle + `✅ <date>`
stamp only — never touch Compiled truth in auto mode.

Then surface the result at the top of the brief: feed `## Pending follow-ups` from the
**Overdue** and **Today** buckets (with the `[[TODO]]` backlinks), and flag the overdue count.

### Step 7 — Propagation

- **Link from the previous daily**: append "→ Next: [[YYYY-MM-DD]]" in the previous day's daily note.
- **For the weekly**: link from the 7 daily notes of the week to the weekly review.

### Step 8 — Report

```
✓ Daily brief generated: 01-daily/2026-05-22.md
✓ Sources analyzed: Email (12), Calendar (4 events), Drive (3 docs), Chat (8 threads)

📥 AUTO-INGESTION
✓ 3 meetings auto-ingested (needs-review: true):
  - [[04-meetings/2026-05-22-team-sync]] (15-min morning review recommended)
  - [[04-meetings/2026-05-22-stakeholder-onboarding]]
  - [[04-meetings/2026-05-22-project-sync]]
✓ 8 people notes auto-updated (last-interaction + auto-logged timeline)
✓ 2 staleness-flags cleared (Alex, Jordan)

⏸ AWAITING VALIDATION
- 1-1 with [direct manager] (sensitive, transcript available) → want me to ingest it tomorrow?
- 2 new people detected (never seen in the vault):
  - "Riley Chen" (3 emails today, seems to be a PM) → create a note?
  - "Sam Patel" (1 meeting + 1 email, external context) → create a note?

✅ TASKS
✓ TODO.md refreshed — ⏰ 2 overdue · 📅 3 due today · ⏳ 5 waiting on others
✓ Reconciled 3 check-offs with source notes (2 done here, 1 done in source)

🎯 SYNTHESIS
✓ Top topic: onboarding script friction
✓ Weak signals: 2 (to dig into)
⚠️ 3 follow-up deadlines approaching (D+2, D+3, D+5)

The vault updated itself.
```

## Configuration (from MY-PROFILE.md)

Read these from `00-inbox/MY-PROFILE.md`:

- **Priority chat channels** to monitor — weight signals from them.
- **Critical stakeholders** — prioritize in the "People touched" section.
- **Active projects** (`status: active` in `03-projects/*`) — weight related signals.
- **Brief time / weekly time** — when the scheduled runs happen.
- **Tone** — direct, no "great progress today!" filler.
- **Top topics cap** — default 5.

## Anti-patterns to avoid

❌ **Flat exhaustive list** — synthesize, don't dump.
❌ **Re-paraphrasing what's already in the vault** — link, don't duplicate.
❌ **Inventing themes** — if the day is quiet, the brief is short. That's fine.
❌ **Corporate tone** — direct and concrete.
❌ **Self-congratulation** — no saccharine "great progress!".
❌ **Skipping weak signals** — that's often where the value hides.
❌ **Overwriting an existing daily** — append, never overwrite.

## Special cases

### Quiet day
If the day is quiet (no meetings, few emails, weekend): a minimal 5–10 line brief.
No need to fill space.

### Very busy day
Beyond 5 topics, don't overflow — keep the top 5, mention "+ N minor topics (see vault)".

### Day off
If the user marked OOO in calendar: skip the brief, or generate only a "follow-ups
awaiting your return" section.

### First use (empty vault)
Degraded brief: just the external sources, no vault cross-referencing. Mention that
value grows as the vault fills.
