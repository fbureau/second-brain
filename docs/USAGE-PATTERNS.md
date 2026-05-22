# Usage Patterns — Second Brain

How to live with your second brain day to day. Concrete workflows for Claude Code.

The six skills (`braindump`, `meeting-ingest`, `daily-brief`, `people-update`, `challenge-decision`, `kickstart-backfill`) auto-trigger from their descriptions. You can also invoke any of them by name or as a slash command (e.g. `/braindump`, `/meeting-ingest`, `/challenge-decision`). Natural language that matches a skill's description works just as well.

## The typical daily pattern

### Morning (7am-9am)

**Monday at 8am you get a Weekly Review** (via the scheduler — see SCHEDULED-TASKS.md — or run it manually).

5-minute read. Identify:
- THE dominant theme of the past week
- The weak signal worth digging into
- The decision to challenge before it gets made

→ If a decision is forming: run `/challenge-decision` before the first meeting of the week.

### During the day

**Capture systematically:**

```
Flash idea       → /braindump [content]
Meeting done     → /meeting-ingest + upload the call transcript (or a copy of the doc)
Stakeholder touch → /people-update Alex Rivera: [observation]
Decision to make → /challenge-decision [position you're considering]
```

Golden rule: **nothing stays in your head longer than 15 minutes.** Out of the head, into the vault.

### Evening (7pm-8pm)

**At 7pm you get the Daily Brief** (scheduled or invoked via `/daily-brief`).

3-5 minute read. This is your anchor before you disconnect.

Actions:
1. Skim the TL;DR
2. Identify the 1-2 follow-ups that genuinely matter for tomorrow
3. If a weak signal speaks to you: comment on it in the daily note (append) or jot it down for tomorrow's braindump

## Workflows by event type

### Workflow 1 — 1:1 with a direct report

**Before** (2 min)
```
"Quick recap of my 1:1 with Alex Rivera today? Read their note + last 2 meetings."
```
→ Claude gives you the context without you having to dig.

**During**
- Take short notes, or let the call recording run.

**After** (2 min)
```
/meeting-ingest + paste/upload the transcript or notes
```
→ Claude produces the full meeting note, updates Alex Rivera's note, and logs decisions/actions.

**Later**
- When you prep Alex Rivera's quarterly review, you've got 3 months of structured timeline laid out flat in `02-people/Alex Rivera ...md`. That's the payoff.

### Workflow 2 — High-stakes decision (centralization, re-org, transition)

**Step 1 — Framing** (5 min)
```
/challenge-decision I want to centralize tier-1 support in one hub to gain consistency across regions
```
→ Claude runs the red team with vault citations.

**Step 2 — Act on the counter-evidence** (1-2 days)
- Discuss the counter-evidence with the relevant stakeholders.
- Capture those conversations via `/braindump` or `/meeting-ingest`.

**Step 3 — Final decision**
```
"I'm going ahead, but with adjustments X, Y, Z to handle the counter-evidence. Log this."
```
→ Claude creates `05-decisions/YYYY-MM-DD-...md` with a link back to the challenge.

**Step 4 — Follow-up** (3-6 months later)
```
"Review the decision on centralizing tier-1 support. Outcome vs predictions?"
```
→ Claude scans the vault since the decision and tells you what actually happened.

### Workflow 3 — Prepping a critical stakeholder meeting

**Day before the meeting**
```
"I'm seeing Sam Lee tomorrow. Prep me a brief: their note, last meeting, shared projects, open topics."
```
→ Claude generates a mini-brief from the vault.

**After the meeting**
- Standard `/meeting-ingest`.

**Recurring pattern:** if you prep the same stakeholder regularly (a manager, a sponsor), a project note at `03-projects/Relationship — Sam Lee.md` can be worth keeping to track how the relationship evolves strategically.

### Workflow 4 — Project summary for a steering committee

**Request**
```
"Summarize project [name] for the steering committee: status, key decisions over the last 3 months, risks, asks."
```
→ Claude assembles it from `03-projects/`, `04-meetings/`, and `05-decisions/`.

You copy-paste into slides or a doc. **The second brain produces the raw material; you produce the narrative.**

### Workflow 5 — Onboarding a new peer

When you meet a new peer or stakeholder:

**First contact**
```
"Create person: Jordan Park, [role], [team], [region], peer"
```

**First real interaction**
```
/people-update Jordan Park: interaction context, key observations, topics discussed
```

**Progressive build**
- 3-5 interactions later, you'll have a rich compiled picture.
- 10 interactions later, it's a real mental model of the person.

### Workflow 6 — Staying on top of your actions

Actions pile up scattered across meeting notes, decisions, daily follow-ups, and 1-1s.
`task-roundup` pulls the ones **you own** into one `TODO.md` at the vault root and keeps
the checkboxes in sync.

**Anytime**
```
/task-roundup
```
→ Refreshes `TODO.md`: ⏰ overdue, 📅 today, 🔜 upcoming, 🗓 later, 🧭 no date,
⏳ waiting on others, ✅ done. Each line links back to its source note via a `^t-id` anchor.

**Check things off where it's convenient**
- Tick a box in `TODO.md` → the next roundup flips the box in the source note and stamps `✅ <date>`.
- Tick it in the source note (e.g. inside a meeting note) → the next roundup checks it in `TODO.md`.

**It runs itself**
- `daily-brief` runs a roundup every evening, so overdue/today items surface at the top
  of the brief under "Pending follow-ups" without you asking.

**Tip** — when you say "I owe Alex Rivera the QA plan by Friday", that becomes an anchored
action line in today's daily note and shows up in `TODO.md` automatically. Don't keep tasks
only in your head — out of the head, into a note, and roundup does the rest.

## Advanced patterns

### Pattern A — Automated pre-meeting prep

Create a meta-prompt to run at the start of the day:

```
"Brief my meetings today: for each calendar event, give me a mini-brief if the participants or the topic are in the vault."
```

Calendar data comes through your available tools / MCP servers.

### Pattern B — Retroactive decision

You realize a decision made 3 months ago should have been logged:

```
"I want to log a decision retroactively: [...]. Date: 2026-02-15. Context: [...]"
```

No problem: Claude creates `05-decisions/2026-02-15-...md` with a note "logged retroactively on YYYY-MM-DD".

### Pattern C — Smart cross-referencing

```
"How often is [topic] mentioned in the vault over the last 60 days? Trend?"
```
→ Claude scans the vault and gives you a quantitative signal.

Useful for spotting: topics on the rise, topics fading out, recurring patterns.

### Pattern D — Relationship stress test

Before a hard conversation (corrective feedback, a difficult negotiation, a tense escalation):

```
"Stress test: I'm about to have a hard conversation with Riley Chen about [topic]. Based on the vault, what do I know about their likely reaction? What are the hot buttons?"
```

→ Claude loads the person's note + past meetings and produces a predictive behavioral analysis.

### Pattern E — Capture on the go

You're out and about, a flash idea hits:

1. Voice memo on your phone
2. Auto-transcribe (device dictation)
3. Later, in Claude Code: `/braindump` + paste the transcript

OR: keep a running note in your phone's notes app titled "To braindump → vault", and empty it 2-3 times a week.

## Anti-patterns to avoid

### Anti-pattern 1 — Trying to capture everything

The vault is not an inbox-zero project. **You capture what has value 6 months out.**

Mental filter: if I reread this note in 6 months, does it give me anything?
- Yes → capture
- No → let it go

### Anti-pattern 2 — A "pretty" structured vault

You don't use Obsidian as a reading tool. No need for Markdown tables, emojis, or Mermaid diagrams. **The vault is machine-readable, not human-readable.**

### Anti-pattern 3 — Permanent refactoring

The vault structure is frozen for 6 months minimum. No bi-weekly reorganizing.

If you spot a need for a different structure: note it in `06-knowledge/vault-evolution-ideas.md` and handle it during the quarterly review.

### Anti-pattern 4 — Skipping propagation

When `/meeting-ingest` tells you "I updated 3 people notes and 1 project", **read the report.** That's what keeps the vault alive. Skip it 10 times in a row and the vault starts to drift.

### Anti-pattern 5 — Relying on Claude's memory

Claude Code does not remember all your past conversations. **The vault is the memory.** Every important piece of information has to be logged there.

### Anti-pattern 6 — Skipping challenge-decision

You'll be tempted to skip the challenge on "obvious" decisions. Those are precisely the ones you get wrong most often.

Rule: every **hard-to-reverse** or **one-way** decision goes through `/challenge-decision`. No exceptions.

## Vault-health KPIs

Indicators to watch (you can compute them via a Vault Health scheduled task — see SCHEDULED-TASKS.md):

### Good signals
- Ratio of notes modified/created > 0.5 (the vault is being read and updated, not just written)
- Every project note with `status: active` has at least 1 update every 14 days
- Every person note with `relationship: direct-report` has a logged interaction every 14 days
- Fewer than 10 untriaged notes in `00-inbox/`
- Reversed decisions logged as such (learning loop)

### Bad signals
- 50+ unprocessed notes in `00-inbox/` (capture with no curation)
- Person notes created and never updated (flat profiles)
- Projects with `status: active` and no update in 30 days (zombie projects)
- No decisions logged in `05-decisions/` in 30 days (challenge-decision underused)
- Vault > 500 notes with no archive activity (`07-archive/` empty)

## Quarterly maintenance (1h)

Every 3 months, take an hour to:

1. **Read the month's vault health** (15 min)
2. **Archive what's no longer active** (20 min)
   - Finished projects → `07-archive/`
   - People stale > 6 months → `07-archive/` (but keep the file)
   - Inbox items never processed → either handle them or delete them
3. **Refine the SKILL.md files** (15 min)
   - Identify 1 recurring frustration
   - Edit the matching skill
4. **Update MY-PROFILE.md** (5 min)
   - New role? New project? New peer?
5. **Git commit** (1 min)
   - `git commit -m "Quarterly maintenance YYYY-Q"`

This is the only recurring cost. 4 hours a year for a system that maintains itself the rest of the time. Hard to beat.

## Long-term evolution

### Months 1-3: Build the habit

- Focus: use the six skills, even imperfectly
- Vault should reach 50-100 notes
- You identify your real patterns

### Months 4-6: Refine

- Tune the SKILL.md files to match your actual usage
- Maybe add 1-2 custom skills (e.g. `prep-stakeholder`, `quarterly-retro`)
- Vault at 200-300 notes

### Months 7-12: Compound

- The vault becomes a real second brain: you find things you'd forgotten
- `/challenge-decision` gets powerful (deep vault to draw on)
- Vault at 500-800 notes

### Year 2+: Strategic

- Long-term patterns become visible
- Accumulated relationship capital is documented
- The vault becomes a career asset (transferable knowledge)

**At this stage, you won't let the system go.**

## Final note

The second brain is not a project to finish. It's a practice to maintain.

A few minutes a day, years of compounding benefit.

Imperfect but used beats perfect but never launched.
