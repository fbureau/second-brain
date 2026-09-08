#!/usr/bin/env bash
#
# Register the Second Brain automations as Hermes cron jobs.
#
#   MODEL_MID=ollama/hermes4:14b  DELIVER=slack  ./hermes/cron/jobs.sh
#
# Each job runs in a fresh Hermes session with only the skills it needs. Prompts are
# self-contained on purpose (cron sessions carry no chat history). Re-running this
# script replaces jobs of the same --name (hermes cron create is idempotent on name;
# if your version is not, `hermes cron list` / `hermes cron delete <id>` first).
set -euo pipefail

MODEL_MID="${MODEL_MID:-}"          # synthesis jobs (digest); e.g. ollama/hermes4:14b or anthropic/claude-sonnet-5
MODEL_SMALL="${MODEL_SMALL:-$MODEL_MID}"   # bookkeeping + judgment on flagged cases
DELIVER="${DELIVER:-local}"         # local | slack | telegram | discord | origin | comma-separated
PROVIDER_FLAG=${PROVIDER:+--provider "$PROVIDER"}
mid=${MODEL_MID:+--model "$MODEL_MID"}
small=${MODEL_SMALL:+--model "$MODEL_SMALL"}

hermes cron create "weekdays at 19:00" \
  "Run the second-brain DAILY DIGEST for today. Follow the daily-digest skill exactly: sb_brief, collect every configured source (calendar, drive, slack, jira, vault activity), synthesize TL;DR / top topics / weak signals into today's daily note with sb_daily_append, auto-log interactions on KNOWN people only with marker (auto-logged), refresh tasks with sb_maintain(scope=tasks), commit, and reply with the digest text. Never create a person note, never ingest a sensitive meeting, never invent a date." \
  --skill daily-digest --skill meeting-ingest $mid $PROVIDER_FLAG --deliver "$DELIVER" --name "sb-daily-digest"

hermes cron create "daily at 07:30" \
  "Run the second-brain MAINTENANCE. Follow the task-roundup skill with sb_maintain(scope=all): sync TODO.md, rebuild knowledge hubs, refresh staleness flags, audit health, then commit. Nobody is watching: for every needs_judgment item, do NOT change anything — list the question in your reply instead. Reply with: overdue/today counts, hubs rebuilt, stale people, and the open questions." \
  --skill task-roundup $small $PROVIDER_FLAG --deliver "$DELIVER" --name "sb-maintenance"

# Phase 3 — weekly review (LLM-heavy synthesis of the week's daily notes). Uncomment when the skill lands.
# hermes cron create "mondays at 09:00" \
#   "Run the second-brain WEEKLY REVIEW: read last week's 01-daily notes with sb_search/sb_read, synthesize themes, decisions, people focus, patterns, energy, plan for next week into 01-daily/YYYY-WW-weekly.md via sb_create_note(type=daily...)." \
#   --skill weekly-review $mid $PROVIDER_FLAG --deliver "$DELIVER" --name "sb-weekly-review"

echo
hermes cron list
