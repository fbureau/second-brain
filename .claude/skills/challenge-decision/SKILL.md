---
name: challenge-decision
description: Red-teams a decision or plan the user is considering by searching their own vault for contradictions (past decisions, meetings, lessons, failures). Produces a critical analysis with vault citations. Use when the user says "challenge this", "red team", "stress test", "before I decide", "I'm thinking of X" on a high-stakes topic, or explicitly "challenge-decision".
---

# Skill: Challenge Decision

## When to activate

- The user explicitly says: "challenge", "red team", "stress test", "challenge-decision".
- The user states a **high-stakes** decision or plan: "I'm thinking of...", "I'm going to...", "we should...".
- The user asks "what do you think?" about a business decision.

**Do NOT use challenge-decision when:**
- The topic is minor or trivial → answer normally.
- The topic is purely technical (code, configuration) → answer normally.
- The decision is already made and executed → use `meeting-ingest` or `people-update` to log it.

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

1. **Read `_CLAUDE.md`** (rules, structure).
2. **Get the real timestamp.**
3. **Identify the decision to challenge**:
   - From the argument given at invocation.
   - Otherwise, infer from recent conversation (ask for confirmation).

## Process

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
