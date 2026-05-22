# 01-daily/

Daily briefs and journal. One note per day, usually created automatically by the
`daily-brief` scheduled task.

## Naming convention

- Daily: `YYYY-MM-DD.md`
- Weekly review: `YYYY-WW-weekly.md` (ISO week number)

## Append-only, multi-skill

This section is written by several skills throughout the day:
- `braindump` appends to `## Braindumps of the day`
- `meeting-ingest` appends to `## Meetings ingested today`
- `challenge-decision` appends to `## Thinking`
- `daily-brief` writes the main synthesis at the top (but preserves sections already appended by others)

## Schema

See `_CLAUDE.md` at the vault root, type schema `daily`.

## Associated skills

`daily-brief` (scheduled daily task), plus propagation from all other skills.
