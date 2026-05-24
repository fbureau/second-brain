---
name: knowledge-build
description: Builds and maintains the 06-knowledge/ base by synthesizing recurring patterns, frameworks, lessons, and anti-patterns from across the vault (meetings, decisions, ingested docs, daily notes). Turns scattered signal into durable, citeable knowledge that recall and challenge-decision lean on. Runs manually, and automatically during the weekly review. Use when the user says "build knowledge", "update the knowledge base", "what have we learned about X", "consolidate learnings", "synthesize".
---

# Skill: Knowledge Build

This is what makes `06-knowledge/` earn its place. Left alone, that folder stays nearly
empty and you wonder what it's for. This skill **distills the rest of the vault** into
durable knowledge notes — frameworks, lessons, anti-patterns, stable facts — that
`recall` and `challenge-decision` can then cite. Knowledge is the layer where scattered
signal becomes reusable understanding.

## When to activate

- Manual: "build/update knowledge", "consolidate learnings", "what have we learned about X", "synthesize [topic]".
- **Auto (weekly)**: invoked as a phase of `daily-brief` weekly mode — a conservative sweep that proposes new/updated knowledge for review.
- Offered after a significant `doc-ingest` or a `reversed` decision (both are rich knowledge sources).

**Do NOT use when:**
- The user wants an answer, not a synthesis → use `recall`.
- There's nothing to distill yet (sparse vault) → say so; don't fabricate knowledge.

## Preflight

1. **Read `_CLAUDE.md`** (rules, the `knowledge` schema) and `00-inbox/MY-PROFILE.md` (working language).
2. **Get the real timestamp.**
3. **Determine scope**:
   - **Topic mode**: the user names a theme → synthesize just that.
   - **Sweep mode** (default for auto/weekly): scan for emergent themes across recent notes.
4. **Determine invocation mode**: manual (full curation) or auto (conservative, flag for review).

## Process

### Step 1 — Detect knowledge candidates
A candidate is something **recurring or load-bearing**, not a one-off:
- A topic mentioned across **3+** meetings/daily notes/docs.
- A repeated **anti-pattern** or friction surfaced in weekly reviews.
- A **principle revealed by a decision** — especially a `reversed` one (the most valuable lessons).
- A **framework or concept** introduced by an ingested doc (`type: doc`).
- A **stable fact** about how the org/domain works, confirmed across sources.

Weight evidence the way the rest of the system does: human/manual signal full weight;
`needs-review: true` notes at ~70%; `(Backfilled)` at ~30%. Don't build durable knowledge
on weak signal alone.

### Step 2 — Match against existing knowledge
For each candidate, search `06-knowledge/`:
- **Exists** → update it (see Step 4): add new evidence and a dated note; never silently overwrite.
- **Doesn't exist** → draft a new note (Step 3).
- **Overlaps two notes** → propose a merge rather than a third overlapping note.

### Step 3 — Write / update the knowledge note
**Path**: `06-knowledge/<concept-slug>.md` (evergreen, kebab-case — not dated).

```markdown
---
date: YYYY-MM-DD              # first crystallized
updated: YYYY-MM-DD
type: knowledge
tags: [knowledge, <topic-tags>]
confidence: high|medium|speculation
needs-review: false          # true when created/updated in auto mode, until you confirm
ai-first: true
---

## For future Claude

Durable knowledge on [topic]: [one-line statement of what's known]. Distilled from N vault
sources (listed under Evidence). Use as a reference for planning, recall, and challenge-decision.

## What we know

[The framework / lesson / principle / stable fact, stated plainly. This is the payload.]

## Evidence

- [[05-decisions/2025-09-03-...]] (reversed) — showed that <lesson> (as of 2025-09)
- [[04-meetings/2026-02-...]] — <supporting observation> (as of 2026-02)
- [[06-knowledge/2026-05-22-market-analysis...]] — <doc claim> (confidence: medium)

## Anti-patterns / caveats

- [What not to do, or where this knowledge stops being reliable]

## Links

- Projects: [[03-projects/...]]
- Related knowledge: [[06-knowledge/...]]
```

Rules:
- **Cite everything.** Each statement traces to a vault note (path + date). No uncited assertions.
- **Recency markers** on time-sensitive facts.
- **Confidence** at the note level and on shaky individual claims.
- **Append, don't overwrite**, when updating: add new evidence and date the change
  (`*(updated 2026-05-22, +2 sources)*`); keep the prior synthesis unless it's now wrong,
  in which case add a dated correction rather than deleting.

### Step 4 — Connect
- Backlink each knowledge note from the projects/decisions it informs (add to their `## Links`).
- Cross-link related knowledge notes so the base becomes a graph, not a pile.

### Step 5 — Auto mode (weekly) specifics
- Be **conservative**: create/update at most a few notes per run; prefer updating evidence
  over inventing new concepts.
- Mark anything created/updated automatically `needs-review: true` and list it in the
  weekly review for the user to confirm. Never finalize interpretive knowledge silently.
- Never touch a note the user has curated by hand (no `needs-review` flag and recently `updated`)
  beyond appending new evidence.

### Step 6 — Report
```
✓ Knowledge updated: 06-knowledge/change-rollout-lessons.md (+2 sources, confidence high)
✓ New: 06-knowledge/regional-autonomy-constraints.md (needs-review: true)
✓ Cross-linked to [[03-projects/Onboarding Refresh]], [[05-decisions/...]]
→ Sweep found 1 more candidate ("tooling-before-training") with only 2 sources — left for next time
```

## Anti-patterns to avoid
❌ **Fabricating knowledge** — only crystallize what the vault supports; cite or don't claim.
❌ **One-off ≠ knowledge** — require recurrence or a clear principle; don't promote a single event.
❌ **Overwriting human-curated notes** — append dated evidence; don't rewrite their synthesis.
❌ **Uncited assertions** — every line traces to a source.
❌ **Auto-finalizing interpretation** — auto mode flags `needs-review: true`.
❌ **Building on weak signal** — respect the 70%/30% weighting for auto/backfilled notes.

## Special cases

### Reversed decisions
The richest source. When a `05-decisions/` note is `status: reversed`, mine it for the
lesson and the conditions that triggered the reversal — that's gold for `challenge-decision`.

### Topic mode
"What have we learned about X" → produce/refresh exactly one focused note on X, with a
direct answer up top and the evidence below.

### Working language
Bodies in the vault's working language (`MY-PROFILE.md`); the preamble is always English.
