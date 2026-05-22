# Upgrading

How to move an existing vault to a newer version. Each section is self-contained — do
the one for the jump you're making. Works whether you drive the system with **Claude Code**
or with a **scheduled assistant (Cowork) + Obsidian** still running the previous version.

> Golden rule before any upgrade: **commit (or back up) your vault first.** Every step
> below is additive and append-only safe, but a clean checkpoint means a one-command rollback.

---

## 3.0.0 → 3.1.0 — Centralized tasks (`task-roundup`)

**What's new:** a `task-roundup` skill that consolidates the action items you own into a
single **`TODO.md`** at the vault root, with **two-way checkbox sync** via stable block-IDs
(`^t-id`). `daily-brief` gains a roundup phase. Nothing is renamed or removed — this is a
backward-compatible minor release, so no data migration is required, just a one-time
anchor backfill (step D).

### A. Update the tooling

**Claude Code**
```bash
cd /path/to/second-brain        # the tooling repo
git fetch origin && git checkout main && git pull
git checkout v3.1.0             # or stay on main
```
The new skill is now at `.claude/skills/task-roundup/SKILL.md` and auto-triggers. Nothing
else to install.

**Cowork (or another assistant) + Obsidian**
Upload the two changed skill files into your project's files, replacing the old ones:
- `.claude/skills/task-roundup/SKILL.md` (new)
- `.claude/skills/daily-brief/SKILL.md` (updated — adds the roundup phase)

If your project's custom instructions list the skills, add `task-roundup` to that list.

### B. Update your existing vault

**B1. Add `TODO.md`** at the vault root. Either copy the seed:
```bash
cp /path/to/second-brain/vault-starter/TODO.md /path/to/your/vault/TODO.md
```
…or skip it — the first `task-roundup` run creates it.

**B2. Merge the new `_CLAUDE.md` section.** If you **haven't customized** your vault's
`_CLAUDE.md`, just overwrite it with `vault-starter/_CLAUDE.md`. If you **have** customized
it, diff the two and bring over just these changes:

1. Insert a new **section 7 — Tasks & the TODO dashboard** (paste the block below) before
   your current "Auto-orchestration" section.
2. In the auto-orchestration numbered list, add the bullet:
   `Runs task-roundup: collects new action items, reconciles TODO.md check-offs both ways, surfaces overdue/today.`
3. Renumber the trailing sections (Auto-orchestration, Default behavior, What you NEVER do)
   so numbers stay sequential.

<details><summary>Section 7 block to paste</summary>

```markdown
## 7. Tasks & the TODO dashboard

Action items are born scattered across notes (meeting `## Action items`, decision
`## Execution plan`, daily `## Pending follow-ups`, people timeline `Follow-up:` lines,
braindump `## Suggested follow-up`). The `task-roundup` skill consolidates the ones the
user owns into a single **`TODO.md` at the vault root** and keeps the checkboxes synced.

**Source notes are the source of truth; `TODO.md` is a generated, reconcilable view.**

### Action-line convention
- [ ] <action> — owner: me — due: YYYY-MM-DD — #from/meeting ^t-ab12cd
- `owner:` — `me` / your alias = yours; a `[[02-people/...]]` = someone else's.
- `^t-xxxxxx` — a stable block-ID anchor, assigned once by task-roundup, never changed or
  reused. It links a `TODO.md` line back to its source line and makes two-way check-off reliable.

### Sync rules
- Box checked in `TODO.md` → next roundup sets the source line to `[x] ✅ <date>`.
- Box checked in a source note → next roundup checks it in `TODO.md`.
- Completing a task in an append-only zone (`02-people/`, `05-decisions/`) is a checkbox
  toggle + `✅ <date>` stamp only — never rewrite surrounding content.
- Done items stay in `TODO.md` for 14 days, then drop off (history lives in the source + Git).
```
</details>

**B3. (Optional) Adopt the action-line convention** in your own note templates so future
actions carry `owner:` / `due:` / `#from/` and get anchored cleanly. The shipped templates
(`templates/decision.md`, `templates/daily.md`) show the format.

### C. Update the daily automation

The skill file already contains the roundup phase, so if your scheduler simply runs
"follow the daily-brief skill", you're done. **Only if you pinned a hand-written daily
prompt** (common in Cowork), add this phase between the people-update and propagation phases:

```
PHASE 6.5 — TASK ROUNDUP
Run the task-roundup procedure (.claude/skills/task-roundup/SKILL.md):
- Collect the action items the user owns from today's new/updated notes + anything still open
- Assign a ^t-id block-ID to any new action line that lacks one (additive)
- Reconcile checkboxes BOTH ways with the vault-root TODO.md
  (box checked in TODO.md → set source to "[x] ✅ <today>"; checked in source → check in TODO.md)
- Refresh TODO.md, bucketed by due date
- In 02-people/ and 05-decisions/: checkbox toggle + ✅ stamp ONLY
```

### D. One-time migration: backfill anchors

Run the skill once against your existing vault:
```
task-roundup
```
On this first run it scans your existing notes, **appends a `^t-id` to every action line
that lacks one** (additive — it removes nothing), and builds your first `TODO.md`. This is
safe: it doesn't rewrite action text, doesn't touch Compiled truth, and passes the
pre-commit hook. Review the diff and commit:
```bash
cd /path/to/your/vault && git add -A && git commit -m "Backfill task anchors + initial TODO.md (v3.1.0)"
```

### E. Verify

1. Open `TODO.md` — your open actions should be bucketed by due date, each linking back to its source.
2. Tick a box in `TODO.md`, run `task-roundup` again → confirm the box flips to `[x] ✅ <date>` in the source note.
3. Tick a different box inside a source note, run `task-roundup` → confirm it now shows under `## ✅ Done` in `TODO.md`.

### Rollback

```bash
cd /path/to/second-brain && git checkout v3.0.0     # tooling
cd /path/to/your/vault && git revert <backfill-commit>   # or: git checkout <pre-upgrade-commit> -- .
```
The anchors are harmless if left in place, so a full rollback is rarely needed.

### Notes

- **Obsidian** renders `^t-id` as an invisible block reference at end of line — it won't
  clutter your notes, and `[[note#^t-id]]` links jump straight to the action.
- The two-way sync runs at **roundup time** (manual `task-roundup` or the daily brief),
  not live. If you want live check-off inside Obsidian too, the Tasks/Dataview plugins can
  read the same `- [ ]` lines — optional and not required.
