---
date: YYYY-MM-DD              # meeting date
ingested: YYYY-MM-DD          # ingestion date
type: meeting
tags: [meeting, <project-tags>, <topic-tags>]
participants: ["[[02-people/...]]"]
project: "[[03-projects/...]]"      # optional if cross-cutting
meeting-type: 1-1|team-sync|stakeholder|external|townhall
duration: <min>
source: "<verbatim link to the transcript / Google Doc / recording, or 'pasted transcript'>"
transcript-source: verbatim|summary-fallback   # which Drive tab/file was ingested
confidence: high|medium                        # medium when transcript-source: summary-fallback
ai-first: true
---

## For future Claude

This is the ingested record of a [meeting-type] held on [date] with [participants].
It covered [main topic]. Key outcomes: [N decisions, N action items]. [Note any
unresolved item or follow-up. If ingested from the summary tab, state the
information-loss limitation explicitly.]

## Context

[2-3 sentences: why this meeting, what preceded it, the situation at the time.]

## Participants

- [[02-people/Name 1]] — role in the meeting

## Decisions

### [Short decision title]
- **What**: [decision]
- **Why**: "[verbatim or paraphrased rationale]"
- **Decision-maker(s)**: [[02-people/...]]
- **Reversibility**: reversible|hard-to-reverse|one-way
- **Impact**: [[02-people/...]], [[03-projects/...]]

## Action items

<!-- Each line carries owner, due date, #from/meeting tag, and a ^t-id anchor for TODO.md sync -->
- [ ] [Action] — owner: me — due: YYYY-MM-DD — #from/meeting ^t-xxxxxx
- [ ] [Action] — owner: [[02-people/...]] — due: YYYY-MM-DD — #from/meeting ^t-xxxxxx

## Strategic themes

1. **[Theme 1]**: [1-2 sentences]

## Key quotes

> "[Verbatim quote]" — [[02-people/Name]], about [context]

## Tensions / Disagreements

[Optional section, skip if nothing to report.]

## Unresolved

- [Open question] — proposed next step: [action]

## Dynamics

[Optional section, mainly for 1-1 and stakeholder meetings.]

## Links

- Source: [original transcript / Google Doc / recording link, if any]
- People: [all participant + mentioned wikilinks]
- Projects: [wikilinks to discussed projects]
- Related wiki: [[06-knowledge/...]]
- Related decisions: [[05-decisions/...]] if a major decision was logged separately
- Previous meetings: [[04-meetings/...]] if part of a series
