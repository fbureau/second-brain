---
date: YYYY-MM-DD
type: decision
tags: [decision, <domain-tag>]
status: proposed|committed|implemented|reversed
reversibility: reversible|hard-to-reverse|one-way
confidence: high|medium|speculation
project: "[[03-projects/...]]"
decision-maker: "[[02-people/...]]"
stakeholders: ["[[02-people/...]]"]
challenge-analysis: "[[05-decisions/YYYY-MM-DD-challenge-...]]"
ai-first: true
---

## For future Claude

Decision made on [date] regarding [topic]. Reversibility: [...]. Confidence: [...].
[1 sentence on why this matters.]

## Decision

[The decision in 1-2 clear sentences]

## Context

[Why this decision was necessary, what problem it solves, what preceded it]

## Options considered

### Option A: [...]
- For:
- Against:

### Option B: [...]
- For:
- Against:

### Option C (chosen): [...]
- For:
- Against:

## Rationale

[Why this option vs. the others. Explicitly mention the counter-evidence addressed if
a challenge was run.]

## Counter-evidence addressed

[If a challenge-decision was run, restate the counter-evidence here AND explain how it
was addressed in the final decision.]

## Reversal conditions

[Which signals/thresholds would trigger a review of this decision]

## Expected impact

- **Positively impacted stakeholders**:
- **Negatively impacted stakeholders**:
- **Metrics to track**:

## Execution plan

<!-- Action lines carry an owner, a due date, and a ^t-id anchor (assigned by task-roundup) -->
- [ ] [Action 1] — owner: me — due: YYYY-MM-DD — #from/decision ^t-xxxxxx
- [ ] [Action 2] — owner: [[02-people/...]] — due: YYYY-MM-DD

## Timeline (post-decision)

### YYYY-MM-DD
- [Execution update]

## Links

- Challenge analysis: [[05-decisions/YYYY-MM-DD-challenge-...]]
- Meetings: [[04-meetings/...]]
- Project: [[03-projects/...]]
