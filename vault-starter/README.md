# Vault Starter

Copy this folder into your Obsidian vault (or wherever your notes live). It seeds the
AI-first structure the skills expect.

## Structure

```
.
├── _CLAUDE.md              ← System brief (read by Claude every session)
├── 00-inbox/               ← Raw, untriaged capture
│   └── MY-PROFILE.md       ← Your profile (read by every skill) — FILL THIS IN
├── 01-daily/               ← Daily briefs + journal
├── 02-people/              ← Stakeholder CRM
├── 03-projects/            ← Active and past projects
├── 04-meetings/            ← Ingested, structured meetings
├── 05-decisions/           ← Log of important decisions
├── 06-knowledge/           ← Durable syntheses, frameworks, lessons
└── 07-archive/             ← Inactive (never deleted)
```

## How to use it

1. **Copy this whole folder** into your notes vault.
2. **Open `_CLAUDE.md`** and read it (10 min).
3. **Edit `00-inbox/MY-PROFILE.md`** with your real context (manager, peers, projects, channels).
4. (Optional) **Sync** your vault to cloud storage if you want mobile access.
5. **Init Git** in the vault for versioning:
   ```bash
   cd /path/to/your/vault
   git init
   echo ".obsidian/workspace*" >> .gitignore
   git add .
   git commit -m "Initial vault setup"
   ```
   If you want the AI-first pre-commit validation, install the hooks from this repo's
   `hooks/` folder (see `hooks/README.md`).

## First use

Once Claude Code can see your vault and the skills are in place:

1. **First braindump**:
   ```
   /braindump my priorities this week are X, Y, Z
   ```
   → Check it creates `00-inbox/YYYY-MM-DD-HHMM-...md`.

2. **First person note**:
   ```
   create person: Alex Rivera, specialist, peer, region WE
   ```
   → Check `02-people/Alex Rivera.md` is created with the right schema.

3. **First daily brief**:
   ```
   /daily-brief
   ```
   → Check it scans sources and creates `01-daily/YYYY-MM-DD.md` (short while the vault is empty).

## Naming conventions (reminder)

- Files: `kebab-case.md` except people (`02-people/First Last.md`)
- Inbox: `00-inbox/YYYY-MM-DD-HHMM-slug.md`
- Daily: `01-daily/YYYY-MM-DD.md`
- Meetings: `04-meetings/YYYY-MM-DD-slug.md`
- Decisions: `05-decisions/YYYY-MM-DD-slug.md`

## Important note

The vault is designed to be read by Claude (future-you), not scrolled by a human.
You'll use Claude Code as the main interface to query and write. No need for visual
polish — focus on machine-readable structure. Every note follows the **AI-first
rules** in `_CLAUDE.md`.
