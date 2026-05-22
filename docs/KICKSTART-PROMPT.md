# One-Shot Prompt: Kickstart Backfill

If you don't have time to set up the `kickstart-backfill` skill, you can **paste this prompt directly** into a Claude Code conversation to run the backfill. The dedicated skill lives at `.claude/skills/kickstart-backfill/SKILL.md` and auto-triggers when available; this doc is the fallback pasteable prompt.

**Before pasting**: make sure your data sources (email, calendar, drive, and chat if available) are reachable via the available tools / MCP servers.

---

## Prompt to paste (adjust the time window if needed)

```
Hi Claude.

We're going to run a KICKSTART BACKFILL of my second brain. Mode: one-shot.

GOAL: pre-fill MY vault with ~30-60 strategic notes based on the LAST 3 MONTHS
(from [DATE-3M] to [TODAY]) of my calendar, email, and drive data (and chat
if available).

The goal is NOT to be exhaustive. The goal is to capture my existing mental
model: top stakeholders, active projects, major decisions, key meetings.

Read first:
- _CLAUDE.md at the vault root
- 00-inbox/MY-PROFILE.md
- .claude/skills/kickstart-backfill/SKILL.md if it exists (otherwise, follow
  the process below)

==========================================
4-PHASE PROCESS (ASK FOR VALIDATION AT EACH PHASE)
==========================================

PHASE 1 — STAKEHOLDERS
1. Scan calendar: extract participants from events over the last 3 months,
   ranked by frequency
2. Scan email: extract recurring senders/recipients (exclude
   noreply/newsletters)
3. Present me the TOP 15 by interaction frequency
4. Ask me who to include (default: top 15) and the relationship for each
5. For each validated person, create 02-people/First Last.md with:
   - Frontmatter filled in (inferred role, best-guess region, confirmed
     relationship, last-interaction)
   - MINIMAL "compiled truth": just the observable professional background,
     NO invented psychology / motivations
   - Timeline grouped by MONTH (aggregated entries), marked "(Backfilled)"
   - Explicit note: "Compiled truth to enrich over future interactions"

PHASE 2 — PROJECTS
1. Detect candidate projects:
   - Recurring topics in email threads (3+ similar threads)
   - Recurring calendar events
   - Active drive folders
2. Present me the candidates with their "signal strength" (strong/moderate/weak)
3. Ask me which to keep + the "one-sentence goal" for each
4. Create 03-projects/<slug>.md with:
   - status: active (default)
   - Auto-detected stakeholders
   - Backfilled timeline grouped by month
   - "(Backfilled)" marker

PHASE 3 — HISTORICAL DECISIONS (optional — ask me if you skip)
1. Scan emails and drive docs for words signaling decisions ("we've decided",
   "approved", "let's go with", "reversal", etc.)
2. List me the candidate decisions (max 10)
3. Ask me which to log
4. Create 05-decisions/YYYY-MM-DD-<slug>.md with:
   - status: implemented (retroactive)
   - Note: "Logged retroactively via kickstart-backfill. Source materials
     reviewed but full rationale may be incomplete."

PHASE 4 — KEY MEETINGS (max 10, ask me which)
1. Identify strategically important meetings (stakeholder reviews, 1-1s with
   manager, major decisions)
2. Ask me which to formalize
3. For those with a transcript available in drive: process via standard
   meeting-ingest
4. For the others: minimal note with known participants/topic/outcome,
   "(Backfilled, no transcript)" marker

==========================================
NON-NEGOTIABLE RULES
==========================================

- Follow AI-first rules 100% (preamble "For future Claude", frontmatter,
  wikilinks, recency markers)
- "(Backfilled)" marker on ALL retroactive timeline entries
- Compiled truth = OBSERVABLE only, no psychological inference
- Validation at each phase before creating
- Maximum 60 notes total (quality > volume)
- No duplicates (fuzzy match before create)

==========================================
FINAL REPORT
==========================================

At the end, create 06-knowledge/kickstart-backfill-YYYY-MM-DD.md with:
- Stats (N people, N projects, N decisions, N meetings)
- Important caveats for future-Claude (reduced weighting of backfilled notes
  vs real-time for 6-8 weeks)
- Links to all created notes
- 3 todos for me over the next 7 days (enrich compiled truth, validate project
  goals, check duplicates)

==========================================
GO
==========================================

Start with PHASE 1. Present me your calendar + email scan first, before
creating anything. Estimated total ETA: ~45 min.
```

---

## Usage notes

1. **Before pasting**: replace `[DATE-3M]` and `[TODAY]` with the real dates, or let Claude compute them.

2. **Adjust the window**:
   - **1 month**: for a quick test (15-20 min, ~15-20 notes)
   - **3 months**: recommended for startup (45 min, ~30-50 notes)
   - **6 months**: if you want an already very rich vault (90 min, ~50-80 notes)

3. **Success conditions**:
   - Your data sources (drive, email, calendar) are reachable and authenticated via the available tools / MCP servers
   - Your vault is already set up with `_CLAUDE.md` and `MY-PROFILE.md`
   - You're available ~45 min to validate each phase (this is NOT fire-and-forget)

4. **If it goes off the rails**:
   - If Claude creates too many notes -> interrupt and say "limit yourself to a strict top 10"
   - If Claude invents "compiled truth" -> interrupt and say "stick to observable, no psychology"
   - If Claude forgets the `(Backfilled)` marker -> have it fixed before the next phase

5. **After the backfill**:
   - Take 30 min during the week to re-read the people notes and enrich the compiled truth with what YOU actually know
   - Validate the project goals
   - Run your first manual `daily-brief` to confirm it cross-references the new notes (e.g. that it surfaces a stakeholder like Alex Rivera alongside the right project)

6. **Limit to know**:
   - The context window has a limit. On 6 months of data, you risk saturating it.
   - If you want to do 6 months and it falls apart, do 2 passes: 6->3 months, then 3->today.

## Important: weighting for challenge-decision

For the first 6-8 weeks after the backfill, `challenge-decision` should weight backfilled notes more weakly than real-time notes. The kickstart-backfill skill's final report logs this caveat explicitly in `06-knowledge/kickstart-backfill-YYYY-MM-DD.md` — `challenge-decision` reads that note to adjust its scoring.

Why? Backfilled compiled truths are based on the observable (calendar + emails), not on real lived interactions. That's useful for bootstrapping, but less reliable than a note enriched by 10 real interactions. For example, a backfilled note on Jordan Park or Sam Lee captures who they email and meet with, but not how they actually behave in a negotiation — so a decision like "centralize tier-1 in one hub" or a change to "the qualification script" should still be pressure-tested against your own judgment, not just the backfilled signal.
