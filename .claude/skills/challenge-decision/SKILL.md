---
name: challenge-decision
description: Two modes around a decision. RED-TEAM (pre-decision): pressure-test a decision or plan against the vault's history before committing. POSTMORTEM (post-decision, since v4.0): when a decision flipped to status:reversed, run a learning loop — extract the lesson, find every other vault note that rests on the same hypothesis, and propose updates to wikis/lessons. Use when the user says "challenge this", "red team", "stress test", "before I decide", "I'm thinking of X" (red-team), or "postmortem", "what went wrong", or auto-detected by daily-brief when a 05-decisions/ note flips to reversed (postmortem).
---

# Skill: Challenge Decision

This skill operates in **two modes** around a decision:

- **Red-team** (pre-decision) — pressure-test a decision being considered, against the
  vault's history. The original purpose.
- **Postmortem** (post-decision, since v4.0) — when a decision has flipped to
  `status: reversed`, run a structured learning loop: extract the lesson, find every other
  vault note that rests on the same hypothesis, propose updates so the vault learns.

Same skill, same philosophy (no agreeableness, mandatory vault citations, honest about
silence). The mode is determined at activation.

## When to activate

**Red-team mode**
- The user explicitly says: "challenge", "red team", "stress test", "challenge-decision".
- The user states a **high-stakes** decision or plan: "I'm thinking of...", "I'm going to...", "we should...".
- The user asks "what do you think?" about a business decision.
- The target decision (if it exists in `05-decisions/`) has `status: proposed | committed`.

**Postmortem mode**
- The user says: "postmortem", "what went wrong", "learn from this", "we reversed X — now what".
- The target decision in `05-decisions/` has `status: reversed`.
- **Auto-trigger by daily-brief**: when a decision flipped to `status: reversed` since the
  last brief, daily-brief invokes this skill in postmortem mode (auto-marked
  `needs-review: true`).

**Do NOT use challenge-decision when:**
- The topic is minor or trivial → answer normally.
- The topic is purely technical (code, configuration) → answer normally.
- The decision is already committed and executing successfully → use `meeting-ingest` or
  `people-update` to log it (red-team is for pre-commit, postmortem is for reversed).

### Mode routing
1. If the target decision is explicit and lives in `05-decisions/`: read its `status:`.
   `reversed` → postmortem; `proposed | committed` → red-team; `implemented` → red-team
   only if the user is reconsidering it (weighing an unwind or a course change) — if
   it's executing successfully, log the update instead (see "Do NOT use" above).
2. If the user named a mode keyword ("postmortem" / "challenge"), trust the keyword.
3. If ambiguous: ask one short question ("red-team this decision before you commit, or
   postmortem the reversal?") before proceeding.

## Philosophy

> The goal is NOT to be agreeable. It's to pressure-test thinking against the
> user's own verified history.

This is the **anti-confirmation-bias** skill. When someone makes high-impact
decisions, their worst enemy is the silent repetition of past failure patterns.
This skill forces the user to confront the current decision with their own history.

3 principles:
1. **Mandatory vault citations** — no generic pushback; concrete material from the user's notes.
2. **No agreeableness** — if the decision is solid, say so; if it's fragile, don't soften it.
3. **If the vault is silent** — say so honestly; don't invent contradictions.

## Preflight

1. **Read `_CLAUDE.md`** (rules, structure) and `00-inbox/MY-PROFILE.md` (working
   language, critical stakeholders, per-skill preferences).
2. **Get the real timestamp.**
3. **Identify the decision to challenge**:
   - From the argument given at invocation.
   - Otherwise, infer from recent conversation (ask for confirmation).

## Process — Red-team mode

This section is the red-team flow (pre-decision). For the postmortem flow (post-reversal),
see *Postmortem mode* below.

### Step 1 — Frame the decision

Restate the decision in clear, testable terms:

- **Position**: [the decision in one sentence]
- **Underlying premises**: [3-5 implicit assumptions]
- **Reversibility**: reversible | hard-to-reverse | one-way (cf. the Bezos framework)
- **Impacted stakeholders**: people, teams, projects
- **Time horizon**: short | medium | long

Ask the user for confirmation before continuing. **If the premises are misidentified,
everything downstream will be biased.**

### Step 2 — Vault research (in parallel where possible)

Search several sections of the vault:

#### 2.1 Past decisions (`05-decisions/`)
- Decisions on similar topics (keywords, related projects).
- Reversed decisions (`status: reversed`) — especially valuable.
- Decisions of the same nature (one-way, hard-to-reverse) on adjacent topics.

#### 2.2 Meetings (`04-meetings/`)
- Meetings where the topic was discussed.
- "Tensions" and "Unresolved" sections touching the topic.
- Historical disagreements between the relevant stakeholders.

#### 2.3 Daily notes (`01-daily/`)
- "Weak signals" and "Anti-patterns" surfaced in weekly reviews.
- Past energy/focus alignment (is the decision consistent with what the user actually pursued?).

#### 2.4 People (`02-people/`)
- Compiled truth of impacted stakeholders.
- Historical signals of opposition or friction on the topic.
- Relationship patterns predicting buy-in or resistance.

#### 2.5 Knowledge (`06-knowledge/`)
- Frameworks or lessons already crystallized on similar topics.
- Documented anti-patterns.

#### 2.6 Archive (`07-archive/`)
- Old projects on adjacent topics — especially failures.
- Past hypotheses that proved false.

### Step 3 — Red-team synthesis

Build a structured analysis across 4 angles:

#### 3.1 Vault counter-evidence
**Explicitly** cite the notes that contradict or qualify the current decision:

```
- 2025-11-12: In [[01-daily/2025-11-12]] you wrote that "centralizing support on a
  single timezone created more friction than expected". The current decision is
  exactly this pattern.

- 2025-09-03: Decision [[05-decisions/2025-09-03-process-unification]] was reversed
  4 months later. The "unify for consistency" logic ran into local specifics.
  A similar pattern is possible here.

- [[02-people/Jordan Park]] expressed opposition in September 2025 (see
  [[04-meetings/2025-09-15-stakeholder-sync]]) to any centralization impacting their
  region. Their note flags "high political weight on regional autonomy".
```

#### 3.2 Blind spots
What the user might be ignoring, based on their notes:

```
- The vault contains NO note on the training impact of this transition. Heavy blind-spot potential.
- Stakeholders in one region aren't mentioned anywhere in the current decision, though
  they were affected by the previous similar decision (see [[05-decisions/...]]).
- No reference to metric X in the recent vault — possibly wrongly ignored?
```

#### 3.3 Pattern matching
Identify whether the current decision resembles a pattern that already played out:

```
Pattern detected: "centralize for efficiency → field friction → reversal"
- Occurrence 1: [[05-decisions/2025-03-process-tier1]] (reversed)
- Occurrence 2: [[05-decisions/2025-09-tooling-unification]] (reversed)
- Risk of occurrence 3 here.

Different conditions this time? Verify explicitly.
```

#### 3.4 Honest verdict
3 possible options:

**Option A: The vault supports the decision**
```
Verdict: The vault is consistent with this decision.
- Positive precedents: [[...]] (similar, executed successfully in 2025-06)
- Stakeholders historically aligned
- No contradiction found

Caveat: confidence limited by [blind spots identified above].
```

**Option B: The vault contradicts or warns**
```
Verdict: The vault suggests strong caution.
- 2 prior failure patterns on adjacent topics
- At least 1 key stakeholder historically opposed
- You flagged this risk yourself in [[01-daily/...]] 6 months ago

Recommendation: before proceeding, explicitly address the counter-evidence above.
```

**Option C: Vault silent**
```
Verdict: The vault doesn't contain enough history on this topic to challenge seriously.
Be aware this analysis is limited.

Suggestion:
- Look at adjacent patterns (I found X, Y, Z that might be relevant)
- Log this decision in 05-decisions/ so you can challenge it yourself in 6 months
```

### Step 4 — Generate the analysis note

**Path**: `05-decisions/YYYY-MM-DD-challenge-<slug>.md`

⚠️ This note is NOT the decision itself — it's the challenge analysis. If the user
then decides, they (or you via meeting-ingest) will create a separate decision note.

```markdown
---
date: YYYY-MM-DD
type: decision-challenge
tags: [challenge, <domain-tags>]
related-decision: "[to create if the user confirms]"
status: under-review
ai-first: true
---

## For future Claude

Red-team analysis of a decision the user is considering on [date]. Topic: [topic].
Reversibility: [reversibility]. The analysis surfaced [N counter-evidence from vault,
N blind spots, N patterns]. Verdict: [supports|warns|silent].

## Decision under consideration

**Position**: [...]

**Underlying premises**:
1. [...]
2. [...]
3. [...]

**Reversibility**: [...]
**Horizon**: [...]
**Stakeholders**: [[02-people/...]], [[02-people/...]]

## Vault counter-evidence

[Structured list with exact citations]

## Blind spots

[What the vault doesn't cover but should]

## Pattern matching

[If a pattern is detected]

## Verdict

[Option A, B, or C with rationale]

## Questions to ask before deciding

[3-5 concrete questions generated from the analysis]

## If the decision is made

→ Log in `05-decisions/YYYY-MM-DD-<slug>.md` with a link to this challenge.
→ At minimum, explicitly address the counter-evidence above in the decision note.
```

### Step 5 — Propagation

- **Daily note**: append to `01-daily/YYYY-MM-DD.md` under a `## Thinking` section:
  ```
  - Red team on [topic]: [[05-decisions/2026-05-20-challenge-...]] — verdict: warns
  ```
- **No people / project propagation at this stage** (the decision isn't made).

### Step 6 — Report

```
✓ Challenge analysis created: 05-decisions/2026-05-20-challenge-centralize-tier1.md
✓ Vault scanned: 12 relevant notes found
✓ Counter-evidence: 3 strong, 2 moderate
✓ Patterns detected: 1 (centralization → reversal x2 historically)
✓ Blind spots: 2 identified (training, one region's stakeholders)
✓ Verdict: warns

Strong recommendation: explicitly address the 3 counter-evidence items before proceeding.

Want me to dig into a particular angle? Or log the decision directly if you decide to proceed?
```

## Postmortem mode (since v4.0)

Triggered when a `05-decisions/` note has flipped to `status: reversed` — either manually
("postmortem on this decision") or automatically by daily-brief on the day the status flips.

The goal is not to assign blame. It's to make the vault **learn** so the same hypothesis
doesn't quietly recur in three other places.

### Why a loop
A reversed decision rarely lives alone. The hypothesis that turned out wrong usually shows
up in: other decisions that cited the same assumption, wiki pages stating it as fact, lessons
written when the assumption was still believed, and project plans built on top of it. The
job is to find every load-bearing reference and update it — in one pass that converges, not
endless wandering.

### The 3-step loop

```
                ┌───────────────────────────────────┐
                │ 1. Extract the lesson             │
                │    (what was the hypothesis,      │
                │     what reversed it, when)       │
                └─────────────────┬─────────────────┘
                                  ▼
                ┌───────────────────────────────────┐
                │ 2. Cross-reference the vault      │
                │    (decisions, wikis, lessons,    │
                │     meetings citing the           │
                │     hypothesis)                   │
                └─────────────────┬─────────────────┘
                                  ▼
                ┌───────────────────────────────────┐
                │ 3. Propose updates                │
                │    (wikis, lessons, decisions     │
                │     status, hub recent activity)  │
                └─────────────────┬─────────────────┘
                                  ▼
                       preview → ask → apply
```

Bounded: each step has a concrete exit condition. The loop terminates when step 3 has been
applied or declined — never re-invoked silently.

### Step P1 — Extract the lesson

Read the reversed `05-decisions/` note end-to-end. Identify:
- **Original hypothesis**: the load-bearing assumption that turned out wrong. State it in one
  sentence, verbatim from the original note where possible.
- **What reversed it**: which evidence, event, or downstream finding flipped the call. Cite
  the meeting, doc, or daily note where it surfaced.
- **Cost / scope of impact**: what had to be undone, what stays, what changed for downstream
  work. One paragraph max.
- **The durable lesson**: distill in one sentence the rule a future-you would want to apply.
  This sentence is what propagates to wikis and lessons in Step P3.

### Step P2 — Cross-reference the vault

Find every load-bearing reference to the original hypothesis:

1. **Other `05-decisions/`** — search for decisions that cite the same hypothesis (text
   match + semantic match on the lesson sentence). Flag them. If any is `status: committed
   | implemented`, it's a candidate for re-review.
2. **Wiki pages (`type: wiki`)** — search for pages whose `## What we know` or `## Summary`
   states the (now-wrong) hypothesis as fact. List them with the offending line + a
   citation.
3. **Lessons (`type: knowledge`)** — search for lessons that derived from the hypothesis or
   rest on it. These are highest-priority updates — a wrong lesson keeps propagating.
4. **Meetings (`04-meetings/`)** — find recent meetings where the hypothesis was discussed.
   Mostly for context, not for update; they're already historical record.
5. **Domain hubs (`type: index`)** — note which hub(s) the impacted pages belong to. The
   curator will refresh `## Recent activity` automatically on Step P3.
6. **Projects (`03-projects/`)** — any active project whose plan rests on the hypothesis?
   Flag for the user; don't auto-rewrite a project (those are user-owned).

Output a short manifest:
```
Cross-references found:
- 2 decisions: [[2025-09-...]] (committed → re-review), [[2025-11-...]] (implemented)
- 3 wiki pages: [[06-knowledge/qualification-script]] (line 14), [[06-knowledge/sf-routing]] (line 8), [[06-knowledge/agentforce]] (line 22)
- 1 lesson: [[06-knowledge/onboarding-handoff-lessons]] (`## What we know` bullet 2)
- 4 meetings referenced (context only, no update)
- 1 active project: [[03-projects/CS Refresh ES]] (rests on the hypothesis — needs your call)
```

### Step P3 — Propose updates

For each item from P2, produce a concrete edit preview the user can accept/reject. Group by
target file. Use append-only conventions where applicable (decisions, lessons).

- **Wiki pages** — append a dated correction to `## What we know` with citation back to the
  reversed decision, mark the superseded statement explicitly: `2026-06-18: supersedes the
  earlier claim that "<hypothesis>" — see [[05-decisions/2026-04-12-...]] (reversed). The
  correct framing is: "<distilled lesson>". (confidence: high, source: reversal)`. Add the
  reversed decision to the wiki's `## Sources`.
- **Lessons** — same append-only correction in `## What we know` + a new entry in
  `## Evidence` linking the reversed decision. If the lesson is now fundamentally wrong
  (not just nuanced), set `confidence: speculation` and `needs-review: true` so a human
  decides whether to retire it (`vault-tend archive` or rewrite).
- **Other decisions** — if any committed/implemented decision rests on the same
  hypothesis, propose a `## Update — 2026-06-18` block on its timeline (append-only)
  flagging the reversal upstream, with the user's call to make.
- **New `type: knowledge` lesson** — if no existing lesson captures the durable rule from
  Step P1, propose creating one in `06-knowledge/<slug>-lessons.md` (or enriching the
  nearest existing one). `confidence: high`, `domain:` inferred, evidence = the reversed
  decision + cross-referenced wikis. The curator incremental update places it in the
  matching hub.
- **The reversed decision itself** — append `## Lesson — YYYY-MM-DD` with the distilled
  sentence and a link to the new/enriched lesson, so the decision now self-documents the
  outcome.

**Preview-first, batched, human-in-the-loop**. Show the user the full set of proposed edits
before applying anything. Apply in one transaction (so a partial-failure can be reverted).
After apply, call `knowledge-build` curator incremental for each touched note so hubs and
`_INDEX.md` refresh.

### Auto mode (daily-brief postmortem auto-trigger)

When daily-brief detects a decision flipped to `status: reversed` in the window:
1. Invoke this skill in postmortem mode for that decision.
2. Run Steps P1 and P2 fully, produce the manifest.
3. **Stop at P3**: do NOT auto-apply edits. Surface the proposal in the brief under
   `## Decisions reversed — pending postmortem` with the manifest and the previewed edits.
4. Mark the analysis note (one created in `06-knowledge/<slug>-postmortem.md` or appended
   to the reversed decision) with `needs-review: true`.
5. The user runs Step P3 manually next morning, with the previews ready.

This keeps the autonomous pipeline conservative — auto-detection and auto-analysis, but
edits across the vault remain a human decision.

### Postmortem note template

When postmortem produces a standalone artifact (rather than just inline lesson updates),
write `06-knowledge/<decision-slug>-postmortem.md`:

```markdown
---
date: YYYY-MM-DD
type: knowledge
tags: [knowledge, postmortem, <domain>]
domain: <domain-slug>
confidence: high
needs-review: true | false
ai-first: true
---

## For future Claude

Postmortem of [[05-decisions/<decision>]] (reversed YYYY-MM-DD). Extracts the durable
lesson, lists vault references that rested on the reversed hypothesis, and points to the
proposed/applied updates.

## The hypothesis that reversed

<one sentence, verbatim where possible>

## What reversed it

<one paragraph, citing the trigger>

## The durable lesson

<one sentence, the rule for future-you>

## Vault references found

<the P2 manifest>

## Updates proposed / applied

- ✓ Wiki updates: <list with paths>
- ✓ Lesson enriched / created: <path>
- ⏳ User decision needed: <projects, committed decisions to re-review>

## Links

- Reversed decision: [[05-decisions/...]]
- Domain hub: [[06-knowledge/<domain>]]
- Updated wikis: [[06-knowledge/...]]
- Updated/created lesson: [[06-knowledge/...]]
```

## Anti-patterns to avoid

❌ **Being agreeable** — never accommodating. If the decision is fragile, say so.
❌ **Inventing contradictions** — if the vault is silent, say so. Don't fabricate.
❌ **Generic pushback** — every counter-evidence MUST point to a precise note (path + date).
❌ **Skipping the verdict** — always conclude with A, B, or C. No "it depends".
❌ **Over-weighting an isolated signal** — a past failure isn't proof. Cite it but qualify it.
❌ **Forgetting blind spots** — that's often where the real value hides.
❌ **Confusing challenge with opposition** — the goal isn't to say no, it's to pressure-test for a better decision.

## Special cases

### Decision about a person (hiring, performance conversation, escalation)
Reinforce reading `02-people/[Person].md`:
- Compiled truth + full timeline.
- Past interaction patterns.
- Historical tensions.

Be especially careful: people decisions are rarely reversed cleanly.

### Technical / process decision
Load `06-knowledge/`:
- Documented frameworks.
- Lessons learned.
- Explicit anti-patterns.

### Political / strategic decision (cross-region, executives)
- Map impacted stakeholders by influence and historical opposition.
- Look for precedents of cross-region change.
- Consider second-order effects (who reacts to whose reaction).

### Urgent / reactive decision
Even under urgency, do a mini-version:
- 1 major counter-evidence if found.
- 1 critical blind spot.
- Verdict in 2 sentences.

A degraded challenge beats a total skip.

### Decision where the user is emotionally over-invested
You can detect it from tone (charged vocabulary, strong certainties, unjustified urgency).
In that case, be even more rigorous about vault citations — they're your only objective anchor.
Mention the detected emotional signal factually, without psychologizing.

## Final note

This skill is underused if the user doesn't trigger it regularly. The invocation
cost is ~5 minutes; the cost of a decision biased by confirmation can be huge
(reversibility, political capital, team).

You can **proactively offer** to invoke this skill when you detect a high-stakes
decision being stated without an explicit challenge. Light suggestion, not insistent:
"Want me to challenge this decision against your vault before you proceed?"
