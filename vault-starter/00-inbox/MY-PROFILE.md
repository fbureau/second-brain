---
date: YYYY-MM-DD
updated: YYYY-MM-DD
type: profile
ai-first: true
---

## For future Claude

User profile. This file is read by every skill at preflight to personalize behavior.
Update it whenever context changes (role, projects, integrations). Replace every
`<...>` placeholder below; delete the guidance in brackets once filled.

> **Setup**: this is a template. Fill in the sections below with your real context.
> Without it, the skills run in a degraded mode.

## Identity

- **Name**: <your name>
- **Current role**: <your role>
- **Company / org**: <company, or leave blank if personal use>
- **Direct reports**: <number and short description, or "none">
- **Management scope**: <e.g. local team / international / individual contributor>

## Working style

- <e.g. analytical, hands-on, MVP over perfection>
- <e.g. uses AI agents daily>

## Communication preferences

- **Concise and direct** — no introductory fluff.
- **No corporate-speak.**
- **Working language**: `en` — set this to your language (`en`, `fr`, `es`, `de`, …). Every
  skill writes note **bodies** and replies in this language. The "For future Claude" preamble
  is **always English** regardless (LLMs parse structured English preambles best).
- Prefer a short useful answer over a long empty one.

## Tools / integrations

- **Notes**: Obsidian vault (synced however you prefer).
- **Connected sources** (via available tools / MCP): <email / calendar / drive / chat>
- **Work tools**: <e.g. CRM, ticketing, chat, docs>

## Active domains

[The skills read this to weight domain classification.]

- <domain 1>
- <domain 2>

## Active projects

[Fill in as you go. Skills read this to weight signals and classification.]

-

## Critical stakeholders

[Prioritized in the daily-brief "People touched" section.]

- Manager:
- Direct report(s):
- Key peers:
- Key sponsors / decision makers:

## Primary communication channels

[Sources `daily-brief` treats as **co-primary** with email/calendar — peer in attention,
collection breadth, and brief structure. List the tools where most of your day's signal
actually lives. Example: `[slack]`, `[slack, teams]`. Leave blank to keep the default
(email/calendar/drive primary, chat secondary).]

- `primary-communication-channels`:

## Priority chat channels to monitor

[Optional whitelist *within* the chat source — must-read channels. Used as a weighting
hint; not the gate for whether chat is collected.]

-

## Chat channels to ignore

[Explicit blocklist for noisy channels (bots, build alerts, off-topic).]

-

## Per-skill preferences

### braindump
- Tone: direct, accept raw voice-to-text.
- If an idea concerns an identifiable project: suggest it on the first pass.

### meeting-ingest
- For 1-1s with a direct report: be more thorough on dynamics / personal development.
- Systematically link to the relevant coaching/development project if one exists.

### daily-brief
- Daily run time: <e.g. 19:00 local>
- Weekly run: <e.g. Monday 10:00 local>
- Tone: direct, no "great progress today!".
- Top topics: max 5.

### people-update
- Strict append-only.
- Compiled truth: modify only with recency confirmation (3+ interactions).

### challenge-decision
- No agreeableness.
- Mandatory vault citations.
- If the vault is silent: say so honestly.

## Auto-ingestion preferences

Settings for the daily-brief auto-orchestration.

### Sensitive meetings (manual validation REQUIRED)

Meeting types that are NEVER auto-ingested. daily-brief flags them; you validate
explicitly the next day.

- 1-1 with direct manager (<name to fill in>)
- Performance reviews / compensation discussions
- Board meetings / leadership offsites
- HR conversations (performance management, negotiation, exit)
- 1-1 with a report if a sensitive topic is in the calendar invite

### Auto-ingest whitelist (default ON)

Types auto-ingested by default:
- ✅ Team syncs / recurring standups
- ✅ Stakeholder reviews (multi-participant)
- ✅ Project syncs
- ✅ Recurring non-sensitive 1-1s
- ✅ External meetings (vendors, partners)

### Auto-update people whitelist (default ON for all)

Auto-updating `last-interaction` + `(auto-logged)` timeline entry works for ALL
existing people notes. No blacklist by default.

To exclude someone from auto-logging (confidentiality), add their name here:
- (none by default)

### Technical thresholds

- **Minimum auto-ingest duration**: 15 minutes (calendar duration)
- **Minimum participants**: 2 (including you)
- **Cutoff time**: <e.g. 19:00 local> (meetings after this are ingested the next day)

### Staleness-flag thresholds

- **Stale after**: 30 days without interaction
- **Critically stale after**: 60 days without interaction
- **Auto-archive proposed**: 180 days (monthly vault health suggests it)

Stale People Check restrictions:
- Applies to: `relationship: direct-report | peer | manager-of-mine`
- Skipped for: `relationship: external | external-alumni`
