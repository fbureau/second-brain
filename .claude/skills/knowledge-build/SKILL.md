---
name: knowledge-build
description: Builds and maintains 06-knowledge/ as both a personal wiki (encyclopedic pages on concepts, entities, jargon, processes — grown incrementally from the first mention) and a lessons base (distilled patterns, frameworks, anti-patterns, principles from reversed decisions). Wiki stubs are created on first mention from braindump/meeting-ingest/doc-ingest. Lessons sweep runs weekly. Use when the user says "build/update knowledge", "wiki on X", "fais une fiche sur X", "what have we learned about X", "consolidate learnings", "synthesize".
---

# Skill: Knowledge Build

This skill makes `06-knowledge/` earn its place. Left alone, that folder stays nearly empty
and you wonder what it's for. This skill turns it into a real **second brain** at two
altitudes:

- **Wiki** (`type: wiki`) — encyclopedic pages on the concepts, entities, jargon, tools,
  teams, processes you encounter. Created as **stubs on the first mention** and grown
  incrementally over time as more sources mention the same thing. This is your personal
  Wikipedia.
- **Lessons** (`type: knowledge`) — distilled syntheses of recurring patterns, frameworks,
  principles, and anti-patterns mined from across the vault. Gated by recurrence (3+
  sources) and decision reversals.

Both altitudes live in `06-knowledge/`, both must cite their sources (rule 3.4), and both
are queried by `recall` and `challenge-decision`. The difference is altitude and threshold,
not folder.

## When to activate

**Wiki mode**
- **Auto (on first mention)** — invoked by `braindump`, `meeting-ingest`, `doc-ingest`
  whenever they extract a wikilink to a `06-knowledge/<concept>.md` that doesn't yet exist.
  They call the **Wiki stub protocol** (see below) to seed a minimal stub with the trigger
  source recorded.
- **Manual** — "fais une fiche sur X", "wiki on X", "write a knowledge note about Y".
- **On enrichment** — when a new source (meeting, doc, braindump) mentions an entity
  already in the wiki, append the new facts with inline citations (never silently overwrite).

**Lessons mode**
- **Manual** — "consolidate learnings", "what have we learned about X", "synthesize lessons
  on X", "build the knowledge base".
- **Auto (weekly)** — invoked as a phase of `daily-brief` weekly mode: a conservative sweep
  that proposes new/updated lessons for review.
- **Offered** after a significant `doc-ingest` or a `reversed` decision (rich lesson sources).

**Do NOT use when:**
- The user wants an answer, not a synthesis → use `recall`.
- The user wants to ingest a document → use `doc-ingest` (which then triggers this skill for
  stubs / lesson candidates).

## Preflight

1. **Read `_CLAUDE.md`** (rules, schemas for `type: wiki` and `type: knowledge`) and
   `00-inbox/MY-PROFILE.md` (working language).
2. **Get the real timestamp.**
3. **Route the invocation:**
   - Triggered by another skill with a target slug → **Wiki stub protocol** (one stub, fast).
   - User named one topic (`"wiki on pricing"`, `"what have we learned about X"`) →
     **Topic mode** (either wiki page or lesson, by intent — see routing below).
   - No topic, sweep mode (auto/weekly) → **Lessons sweep**, conservative.
4. **Wiki vs lessons routing for a named topic:**
   - "Wiki / fiche / encyclopedic / what is X / who is team Y" → Wiki page.
   - "Lesson / pattern / what we learned / what works for X / anti-pattern" → Lesson.
   - Ambiguous → produce / refresh the **wiki page** first (lower bar, always useful); offer
     a lesson on top if the evidence supports it.

## Mode A — Wiki (encyclopedic pages)

### A.1 Path & naming
`06-knowledge/<slug>.md` (evergreen, kebab-case, **undated**). Same folder as lessons —
distinguished by `type: wiki` in frontmatter.

The slug is the canonical name of the thing:
- Concepts: `pricing-tiers.md`, `qualification-script.md`
- Teams: `onboarding-team.md`, `customer-success-emea.md`
- Tools: `chargebee.md`, `salesforce-instance.md`
- Processes: `weekly-business-review.md`, `incident-postmortem-process.md`
- Jargon: `mqp.md` (with the expansion in the page)

### A.2 Wiki stub protocol (called by other skills)

When `braindump`, `meeting-ingest`, or `doc-ingest` detect a new concept/entity wikilink
`[[06-knowledge/<slug>]]` that doesn't exist yet:

1. Create the file `06-knowledge/<slug>.md` with the stub template (A.3) populated with:
   - Frontmatter `type: wiki`, `needs-review: true`, `confidence: speculation`,
     `created-from: "[[<trigger-note-path>]]"`.
   - One line in `## Summary` if the trigger note gave a definition / one-line context;
     otherwise leave the stub explicitly empty: `*Stub — first mentioned in [[…]] on YYYY-MM-DD.
     Awaiting more sources.*`.
   - The trigger note in `## Sources` with the date and a verbatim quote/snippet (≤ 1 line)
     of how it was mentioned.
2. Backlink it from the trigger note's `## Links → Concepts` (already required by the
   calling skill's wikilink rule).
3. Do NOT block on the user — the stub is created silently as part of the calling skill's
   propagation. The user reviews `needs-review: true` stubs later (surfaced by daily-brief
   or `vault-tend`).

### A.3 Wiki page template

```markdown
---
date: YYYY-MM-DD              # stub creation
updated: YYYY-MM-DD
type: wiki
tags: [wiki, <topic-tags>]
aliases: ["<other names>", "<acronym>"]   # so recall finds it under any name
confidence: stated | high | medium | speculation
needs-review: true | false    # true on auto-stub until the user confirms / enriches
created-from: "[[<trigger-note-path>]]"   # the note that triggered the stub
ai-first: true
---

## For future Claude

Wiki page on [topic]. [One sentence stating what it is, in plain words.] Built incrementally
from the sources listed at the bottom — every fact in this note traces to one of them.

## Summary

[1–3 sentences. The thing in plain language: what it is, why it matters here. This is what
recall returns first.]

## What we know

[Bulleted, structured facts. Each bullet ends with a citation `— [[<source>]] (as of YYYY-MM)`.
Group by sub-topic if the page grows beyond ~15 bullets.]

- <Fact 1> — [[04-meetings/2026-04-12-...]] (as of 2026-04)
- <Fact 2> — [[06-knowledge/2026-05-22-market-analysis-...]] (confidence: medium)
- <Fact 3 from external source> — https://… (as of 2026-03)

## Open questions / unknowns

- [What the vault doesn't yet say about this thing — surface, don't hide.]

## Related

- People: [[02-people/...]]
- Projects: [[03-projects/...]]
- Related wiki: [[06-knowledge/...]]
- Lessons: [[06-knowledge/...]]  (links to `type: knowledge` notes that draw on this entity)

## Sources

> Cumulative provenance. Every time this page is touched, add the source here with the date.
> Never remove an entry — this is the audit trail.

- [[<trigger-note-path>]] — YYYY-MM-DD (stub created, "<verbatim 1-line snippet>")
- [[<source-2>]] — YYYY-MM-DD (added: <what was added>)
- <external URL> — YYYY-MM-DD (added: <what was added>)
```

### A.4 Enrichment (subsequent encounters)

When the wiki page already exists and a new source mentions the entity:

- **Append, don't overwrite** the body. New facts go into `## What we know` with their
  inline citation. If a prior fact is contradicted, add the new fact with its date and a
  note (`*supersedes the 2026-03 statement — see [[…]] for context*`); never delete the
  prior fact.
- **Always add an entry to `## Sources`** with the date and a one-line "what was added".
- Update `updated:` in frontmatter.
- If the source materially upgrades confidence (e.g. a doc with primary data on a previously
  speculative claim), bump `confidence:` and remove `needs-review: true` if appropriate.

### A.5 Wiki anti-patterns
❌ Writing a fact without a citation — every line traces to a source.
❌ Silently overwriting prior content — append with dates, even on corrections.
❌ Inventing facts the vault doesn't support — say `unknown` in `## Open questions`.
❌ Promoting a single mention into a thick page — start as a stub, grow with evidence.

## Mode B — Lessons (distilled patterns)

### B.1 Detect lesson candidates
A candidate is something **recurring or load-bearing**, not a one-off:
- A topic mentioned across **3+** meetings/daily notes/docs.
- A repeated **anti-pattern** or friction surfaced in weekly reviews.
- A **principle revealed by a decision** — especially a `reversed` one (the most valuable lessons).
- A **framework or concept** introduced by an ingested doc (`type: doc`).
- A **stable fact about how things work** consolidated across many wiki pages.

Weight evidence the way the rest of the system does: human/manual signal full weight;
`needs-review: true` notes at ~70%; `(Backfilled)` at ~30%. Don't build durable lessons on
weak signal alone.

### B.2 Match against existing lessons
For each candidate, search `06-knowledge/` for `type: knowledge` notes on the topic:
- **Exists** → update (Step B.4): add new evidence and a dated note; never silently overwrite.
- **Doesn't exist** → draft a new lesson (Step B.3).
- **Overlaps two notes** → propose a merge rather than a third overlapping note.

### B.3 Write a lesson
**Path**: `06-knowledge/<concept-slug>.md` (evergreen, kebab-case — not dated).

```markdown
---
date: YYYY-MM-DD              # first crystallized
updated: YYYY-MM-DD
type: knowledge
tags: [knowledge, <topic-tags>]
confidence: high | medium | speculation
needs-review: false          # true when created/updated in auto mode, until confirmed
ai-first: true
---

## For future Claude

Durable lesson on [topic]: [one-line statement of what's known]. Distilled from N vault
sources (listed under Evidence). Use as a reference for planning, recall, and challenge-decision.

## What we know

[The framework / lesson / principle / stable fact, stated plainly. This is the payload.]

## Evidence

- [[05-decisions/2025-09-03-...]] (reversed) — showed that <lesson> (as of 2025-09)
- [[04-meetings/2026-02-...]] — <supporting observation> (as of 2026-02)
- [[06-knowledge/<wiki-page>]] — <wiki fact this lesson rests on>

## Anti-patterns / caveats

- [What not to do, or where this lesson stops being reliable.]

## Links

- Projects: [[03-projects/...]]
- Related wiki: [[06-knowledge/...]]  (the entities/concepts this lesson is about)
- Related lessons: [[06-knowledge/...]]
```

Rules:
- **Cite everything.** Each statement traces to a vault note (path + date). No uncited assertions.
- **Recency markers** on time-sensitive facts.
- **Confidence** at the note level and on shaky individual claims.
- **Append, don't overwrite**, when updating: add new evidence and date the change
  (`*(updated 2026-05-22, +2 sources)*`); keep the prior synthesis unless it's now wrong,
  in which case add a dated correction rather than deleting.

### B.4 Update an existing lesson
Same template, append-only on `## Evidence` and `## What we know`. If a wiki page the lesson
rests on now contradicts the lesson, mark the lesson `needs-review: true` and add a
`## Open questions` section flagging the contradiction with citations.

### B.5 Auto mode (weekly) specifics
- Be **conservative**: create/update at most a few lessons per run; prefer updating evidence
  over inventing new concepts.
- Mark anything created/updated automatically `needs-review: true` and list it in the
  weekly review for the user to confirm. Never finalize interpretive lessons silently.
- Never touch a note the user has curated by hand (no `needs-review` flag and recently
  `updated`) beyond appending new evidence.

## Connect (both modes)
- Backlink each new wiki / lesson from the projects, decisions, and people it informs (add
  to their `## Links`).
- Cross-link related notes so the base becomes a graph, not a pile. **Wiki pages link to
  lessons that draw on them; lessons link to the wiki pages they reference.**

## Report

```
WIKI
✓ New stub: 06-knowledge/qualification-script.md (needs-review: true, from [[04-meetings/2026-05-22-team-sync]])
✓ Enriched: 06-knowledge/onboarding-team.md (+1 source: [[06-knowledge/2026-05-22-market-analysis-emea]], confidence high)

LESSONS
✓ Lesson updated: 06-knowledge/change-rollout-lessons.md (+2 sources, confidence high)
✓ New lesson: 06-knowledge/regional-autonomy-constraints.md (needs-review: true)
✓ Cross-linked to [[03-projects/Onboarding Refresh]], [[05-decisions/...]]
→ Sweep found 1 more lesson candidate ("tooling-before-training") with only 2 sources — left for next time
```

## General anti-patterns
❌ **Fabricating** — only crystallize what the vault supports; cite or don't claim.
❌ **Overwriting human-curated notes** — append dated evidence; don't rewrite their synthesis.
❌ **Uncited assertions** — every line traces to a source, in both modes.
❌ **Auto-finalizing interpretation** — auto-created/updated notes flag `needs-review: true`.
❌ **Building on weak signal** — respect the 70%/30% weighting for auto/backfilled notes.
❌ **Mixing altitudes in one note** — a wiki page describes a *thing*; a lesson describes a
   *pattern/principle*. If they get tangled, split them and cross-link.

## Special cases

### Reversed decisions
The richest lesson source. When a `05-decisions/` note is `status: reversed`, mine it for
the lesson and the conditions that triggered the reversal — that's gold for `challenge-decision`.

### Topic mode
"What have we learned about X" → produce/refresh exactly one focused note on X, with a
direct answer up top and the evidence below. Routes to wiki or lesson per A vs B above.

### Working language
Bodies in the vault's working language (`MY-PROFILE.md`); the preamble is always English.
