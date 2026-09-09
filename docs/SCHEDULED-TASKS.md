# Scheduled tasks

Claude Code has **no built-in scheduler**. The daily/weekly automations run through
an external scheduler that invokes Claude Code in headless mode. This doc gives
tool-agnostic setups plus the ready-to-use prompts.

## Running a skill headlessly

Claude Code can run non-interactively with `-p` / `--print`. From the repo (or
vault) directory:

```bash
claude -p "Run the daily-brief skill. Mode: daily. Window: today 00:00 → now." \
       --model sonnet
```

Point it at wherever it can read both this repo's `.claude/skills/` and your vault.
Anything you'd type interactively works here; the skill auto-triggers from the prompt.

## Running on Hermes Agent instead

If you run the Hermes edition (`docs/HERMES.md`), skip the external scheduler: `hermes/cron/jobs.sh`
registers the daily digest and the maintenance run as built-in Hermes cron jobs, with a model
per job and delivery to Slack/Telegram. The prompts below remain the reference for the Claude
Code path.

## Scheduler options (pick one)

- **cron** (Linux/macOS) — simplest. One crontab line per task (examples below).
- **launchd** (macOS) — survives sleep better than cron on laptops.
- **A CI scheduler** (e.g. GitHub Actions `schedule:`) — good if the vault is a Git
  repo the runner can clone; commits the generated notes back.
- **Any desktop "scheduled task" tool** — fine if it can run a shell command.

⚠️ A laptop that's asleep won't run cron jobs. If runs are getting skipped, prefer
launchd (macOS), a wake schedule, or a CI scheduler.

## Overview

| Task | Cadence | Suggested model | Skill | Output |
|---|---|---|---|---|
| Daily Brief | Mon–Fri, end of day | **Sonnet 5** | daily-brief (daily mode) | `01-daily/YYYY-MM-DD.md` |
| Weekly Review | Monday mid-morning | **Sonnet 5** (Opus 5 if available) | daily-brief (weekly mode) | `01-daily/YYYY-WW-weekly.md` |
| Vault Health | Monthly, 1st (or next weekday) | **Haiku 4.5** | health audit | `06-knowledge/vault-health-YYYY-MM.md` |
| Stale People Check | Friday late afternoon | **Haiku 4.5** | people staleness scan | flag in Friday's daily note |

### Why these models
- **Sonnet 5** for the briefs: they *reason* (multi-source synthesis, weak-signal and
  cross-time pattern detection). A smaller model produces flat briefs and misses signals.
  The weekly review benefits from **Opus 5** if your plan includes it — it's the run
  that does cross-week pattern detection and the knowledge sweeps.
- **Haiku 4.5** for health/staleness: mechanical work (list, count, filter by date).
  Plenty capable and far cheaper.
- The `--model sonnet` / `--model haiku` / `--model opus` aliases below track the
  latest model in each family (Sonnet 5, Haiku 4.5, Opus 5 as of 2026-08). Pin a full
  model ID instead if you want run-to-run reproducibility.

### Example crontab

```cron
# Daily Brief — weekdays at 19:00
0 19 * * 1-5  cd /path/to/vault && claude -p "$(cat /path/to/prompts/daily-brief.txt)" --model sonnet

# Weekly Review — Monday at 10:00
0 10 * * 1    cd /path/to/vault && claude -p "$(cat /path/to/prompts/weekly-review.txt)" --model sonnet

# Stale People Check — Friday at 17:00
0 17 * * 5    cd /path/to/vault && claude -p "$(cat /path/to/prompts/stale-people.txt)" --model haiku

# Vault Health — 1st of the month at 10:00
0 10 1 * *    cd /path/to/vault && claude -p "$(cat /path/to/prompts/vault-health.txt)" --model haiku
```

Store the prompts below as text files and reference them, or inline them.

---

## Task 1 — Daily Brief (essential)

```
You are running the DAILY BRIEF + AUTO-ORCHESTRATION of the second brain.

Follow .claude/skills/daily-brief/SKILL.md exactly. This is MORE than a brief: it's
when the vault updates itself.

MODE: daily
WINDOW: today 00:00 (local) → now

PHASE 1 — MULTI-SOURCE COLLECTION (step 1 of the SKILL)
1. Email — received in the window; exclude newsletters/notifications/marketing
2. Calendar — today's events, past + ongoing
3. Drive/files — docs created/modified in the window, ESPECIALLY meeting transcripts
4. Chat — if listed in `primary-communication-channels` (MY-PROFILE.md): DMs (received + sent),
   mentions, threads you participated in, AND all channels you've been active in over the
   last 14 days. Cluster by theme, cap ~10 themes. Render in a dedicated `## Themes from Slack`
   section (does NOT compete with the top-5 cap). Else: narrow mode — DMs + mentions + priority
   channels only.
5. Internal vault — notes already created/modified today

PHASE 2 — TRIAGE (step 2)   PHASE 3 — SYNTHESIS (step 3)
PHASE 4 — GENERATE THE NOTE (step 4) → 01-daily/YYYY-MM-DD.md
- If it already exists: APPEND under "## Daily brief", don't overwrite.

PHASE 5 — MEETING AUTO-INGESTION (step 5 — CRITICAL)
For each transcript detected today:
- Whitelist: calendar match ✓, participants ≥ 2 incl. the user ✓, duration ≥ 15 min ✓,
  NOT in sensitive-meetings (MY-PROFILE.md) ✓, not already ingested ✓
- If it passes: auto-invoke meeting-ingest in auto mode
  (ingestion-mode: auto, needs-review: true; hard-to-reverse decisions → flag needs-validation)
- TRANSCRIPT-FIRST: read the verbatim transcript tab/file, NEVER the Drive summary tab.
  If only the summary exists, ingest with transcript-source: summary-fallback,
  confidence: medium, needs-review: true, and call it out in the brief.
- If it fails: flag for manual validation in the report
- CAP: max 5 auto-ingests per run

PHASE 6 — PEOPLE AUTO-UPDATE (step 6 — CRITICAL)
For each person interacted with today:
- Fuzzy-match against 02-people/
- If the note exists: update frontmatter (last-interaction, updated, CLEAR staleness-flag)
  and append ONE "### YYYY-MM-DD — Daily interactions (auto-logged)" timeline entry
  (raw facts only; NEVER touch Compiled truth)
- If the note doesn't exist: create NOTHING; list it for validation
- CAP: max 20 auto-updates per run

PHASE 6.5 — TASK ROUNDUP (step 6.5 — CRITICAL)
Run the task-roundup procedure (.claude/skills/task-roundup/SKILL.md):
- Collect the action items the user owns from today's new/updated notes + anything still open
- Assign a ^t-id block-ID to any new action line that lacks one (additive)
- Reconcile checkboxes BOTH ways with the vault-root TODO.md (a box checked in TODO.md →
  set source line to "[x] ✅ <today>"; checked in source → check in TODO.md)
- Refresh TODO.md, bucketed by due date
- Completing a task in 02-people/ or 05-decisions/ = checkbox toggle + ✅ stamp ONLY

PHASE 6.7 — REVERSED-DECISION POSTMORTEM (step 6.7 — since v4.0)
Scan 05-decisions/ for notes whose status flipped to `reversed` since the last brief:
- For each flip: invoke challenge-decision in POSTMORTEM mode (auto). It runs P1
  (extract the lesson) and P2 (cross-reference the vault) and previews the P3 edits.
- NEVER auto-apply the cross-vault edits. Surface the manifest + previewed edits in
  the brief under "## Decisions reversed — pending postmortem" (needs-review: true).
- No flip in the window → skip silently (no empty section).

PHASE 7 — PROPAGATION (step 7)   PHASE 8 — REPORT (step 8)
Report: 📥 auto-ingestion · ⏸ awaiting validation · ✅ tasks (overdue/today/waiting) · 🎯 synthesis (top 3-5, weak signals, near deadlines)

NON-NEGOTIABLE
✓ AI-first 100% (preamble, frontmatter, wikilinks, recency markers)
✓ Top 5 topics max · direct tone, no "great progress today!"
✓ NEVER touch Compiled truth in auto mode
✓ NEVER auto-create a person note (flag for validation)
✓ NEVER auto-ingest a sensitive meeting (see MY-PROFILE.md)
```

Notes: respect the configured timezone; if the user is OOO (per calendar), skip the day.

---

## Task 2 — Weekly Review (essential)

```
Generate the weekly review following .claude/skills/daily-brief/SKILL.md.

Mode: weekly
Window: Monday of last week 00:00 → Sunday of last week 23:59

Method:
1. Read the 7 daily notes of last week in 01-daily/
2. Scan notes created/modified in 04-meetings/, 05-decisions/, 02-people/ in the window
3. Identify 3-5 cross-cutting themes
4. Track decisions made and their status
5. People focus: who emerged most, why
6. Pattern detection: positive AND negative recurrences
7. Anti-patterns / friction: what didn't work
8. Energy & focus: where did energy go; aligned with MY-PROFILE.md priorities?
9. Implicit plan for next week
10. List stubs and incomplete notes to process
11. Run knowledge-build LESSONS sweep: conservative pass that proposes new/updated
    06-knowledge/ lesson notes flagged needs-review: true; list under "## Knowledge updates".
12. Run knowledge-build CURATOR sweep (Mode C.2): rebuild auto-maintained domain hubs,
    refresh 06-knowledge/_INDEX.md, detect orphans, near-duplicates, aging stubs (>14d
    needs-review), stale wikis (>90d). Propose new hubs when 3+ notes cluster on an
    unhubbed domain. Structural changes preview-first. Run the self-verification loop
    (max 3 passes; flag unstable hubs under "## Health → Curator unstable"). Surface
    health counters — and how many passes stabilization took — under "## Knowledge garden".

Output: 01-daily/YYYY-WW-weekly.md (ISO week number), using the SKILL's weekly format.
Link from this note to the 7 daily notes of the week.

End with 3 questions for the week ahead:
- What is THE priority?
- Which weak signal deserves your time?
- Is there a decision to challenge before it's made?
```

---

## Task 3 — Vault Health Check (monthly)

```
Monthly vault-health audit. Read-only except for creating the report note.

1. ORPHAN NOTES — notes with NO inbound wikilink (except 00-inbox/, the buffer).
   For each: propose update, link, or archive.
2. UNFILLED STUBS — notes created as stubs (empty "Compiled truth"/"Goal") for 30+ days.
3. STALE PEOPLE — 02-people/ notes with last-interaction > 90 days.
4. POTENTIAL DUPLICATES — fuzzy-match within 02-people/ and 03-projects/.
5. INVENTORY — count notes per section (with status breakdowns for projects/decisions).
6. PATTERNS — top 10 tags, top 5 most-mentioned people, top 5 active projects,
   recurring unaddressed weak signals.

Output: 06-knowledge/vault-health-YYYY-MM.md (AI-first format) with a final
"Recommendations" section (3-5 concrete actions).

Modify NO note other than the report. Everything else is a proposal for human decision.
```

---

## Task 4 — Stale People Check (Friday)

```
End-of-week staleness scan with staleness-flag updates.

PHASE 1 — SCAN 02-people/
- days_since = today - last-interaction
- Restrict to relationship: direct-report | peer | manager
- Skip relationship: external | external-alumni

PHASE 2 — UPDATE FRONTMATTER (write allowed, frontmatter ONLY)
- days_since > 60 → staleness-flag: "stale-60d-since-YYYY-MM-DD" (today)
- 30 ≤ days_since ≤ 60 → staleness-flag: "stale-30d-since-YYYY-MM-DD"
- days_since < 30 → clear staleness-flag if present

⚠️ ONLY the frontmatter. Do NOT touch timeline, compiled truth, or open threads.

PHASE 3 — REPORT
Append to today's daily note (01-daily/YYYY-MM-DD.md) under "## Stale people watch":
### Critically stale (>60d) · ### Stale (30-60d) · ### Cleared this week
(each: [[02-people/Name]] — last interaction: YYYY-MM-DD (N days) — context: [last topic])
If nothing: "✓ All key relationships up to date."

PHASE 4 — RECOMMENDATIONS
- Critically stale → "reach out this week OR archive if the relationship has ended"
- Stale 30-60d → "watch: will go critically stale without an interaction this week"

RULES: model Haiku · frontmatter (staleness-flag) only · append-only on the daily note.
```

⚠️ `staleness-flag` is also auto-cleared by `daily-brief` as soon as a new
interaction is detected. This Friday task is just a safety net.

## Optimization tips

- **Skip when irrelevant** — daily brief: skip if no calendar events AND no email AND no chat activity.
- **Adjustable cadence** — light usage early? Run the weekly review bi-weekly, or the daily brief 3×/week.
- **Degraded mode** — add "if a source is unreachable, continue without it" to prompts; always produce partial output.

## Iterating on the prompts

After ~2 weeks: read a few recent briefs, note what's missing or noise, edit these
prompts, and commit the change in Git. The prompts are code — treat them as such.
