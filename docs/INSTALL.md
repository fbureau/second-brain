# Installation — Second Brain

Full setup in 4 steps (~30-45 min the first time).

This repo is the **tooling** for an AI-first personal knowledge system: six Claude Code
skills, note templates, Git hooks, and a `vault-starter/` you copy into your actual
notes vault. You drive it with **Claude Code** (CLI, desktop, or web).

The **vault** is a separate folder of Markdown notes — an Obsidian vault, synced however
you like. It is the *memory*. Claude has no persistent memory across sessions; the vault
is what persists.

## Prerequisites

- [ ] **Claude Code** installed and signed in (CLI, desktop, or web).
- [ ] **Git** (versioning the vault is first-class here).
- [ ] (Recommended) **Obsidian** to browse/edit the vault as a human — https://obsidian.md
- [ ] (Optional) **Connected sources via MCP / available tools** — email, calendar, drive,
      chat. These feed `daily-brief`, `meeting-ingest`, and `kickstart-backfill`. The system
      works without them, just with less to synthesize.

## Step 1 — Get the repo and point Claude Code at it (5 min)

1. Clone or copy this repo somewhere stable:

   ```bash
   git clone <repo-url> second-brain
   cd second-brain
   ```

2. Open the project in Claude Code (open the folder in the desktop/web app, or run the
   CLI from inside it). Claude Code automatically reads:
   - `CLAUDE.md` — the project brief and the non-negotiable AI-first rules.
   - `.claude/settings.json` — permissions (read/write/edit, git status/add/commit/diff/log
     are pre-allowed; `git push`, `rm`, `git reset` prompt for confirmation).
   - `.claude/skills/*/SKILL.md` — the six skills, which auto-trigger from their
     `description`.

3. Sanity check — ask Claude Code:

   ```
   Read CLAUDE.md and list the six skills you have available.
   ```

   You should get back: braindump, meeting-ingest, daily-brief, people-update,
   challenge-decision, kickstart-backfill.

## Step 2 — Set up the vault (15 min)

### 2.1 Choose where the vault lives

The vault can be a sibling folder, a subfolder, or its own Git repository. Pick a stable
path, e.g. `~/notes/second-brain`.

### 2.2 Copy the starter vault

Copy everything in `vault-starter/` into your new vault folder:

```bash
mkdir -p ~/notes/second-brain
cp -r vault-starter/* ~/notes/second-brain/
cp -r vault-starter/.* ~/notes/second-brain/ 2>/dev/null || true
```

Confirm you see:
- `_CLAUDE.md` at the root (the vault system brief, read first every session that touches
  the vault).
- The eight numbered folders `00-inbox/` … `07-archive/`.
- `00-inbox/MY-PROFILE.md`.

### 2.3 Tell the skills where the vault is

Open `CLAUDE.md` in this repo and set `VAULT_PATH` to the folder you chose:

```
VAULT_PATH: ~/notes/second-brain
```

The skills read and write there. (If you point Obsidian at the same folder, you get a
human-friendly view of everything Claude writes.)

### 2.4 Fill in MY-PROFILE.md

Open `00-inbox/MY-PROFILE.md` in the vault and replace every `<...>` placeholder with your
real context: your name and role, working style, communication preferences, working
language, and which **connected sources (via MCP / available tools)** you have.

⚠️ **Important**: this file is read by every skill at preflight. Without it, the skills run
in a degraded mode.

### 2.5 Initialize Git and install the hooks

Version the vault — the append-only history is the whole point.

```bash
cd ~/notes/second-brain
git init
cat > .gitignore << 'EOF'
.obsidian/workspace*
.obsidian/cache
.trash/
EOF
git add .
git commit -m "Initial vault setup"
```

Install the pre-commit hook. Run the installer from this tooling repo and point it at the
vault repo:

```bash
# from the tooling repo:
./hooks/install.sh ~/notes/second-brain
```

The hook validates AI-first compliance (frontmatter, `ai-first: true`, the
`## For future Claude` preamble) and refuses commits that destroy append-only history in
`02-people/` and `05-decisions/`. See `hooks/README.md` for the full check list. Don't
bypass it with `--no-verify` unless you understand why it fired.

> If the vault lives **inside** this repo, just run `./hooks/install.sh` with no argument.

## Step 3 — Verify the skills work (10 min)

Ask Claude Code to run a few skills against the vault. Each one should read `_CLAUDE.md`
and `MY-PROFILE.md` first, then write a note following the AI-first rules.

```
1. braindump: quick test to validate the install
   → creates a note in 00-inbox/

2. add person: Alex Rivera, peer, EMEA
   → creates 02-people/Alex Rivera.md with the right schema
   → then archive or delete this test note when done

3. daily brief
   → generates 01-daily/YYYY-MM-DD.md (short at first, since the vault is empty)
```

Notes:
- Skills auto-trigger from their `description`, but you can always invoke one explicitly by
  name (e.g. "use the braindump skill to …").
- `daily-brief` also orchestrates `meeting-ingest` and `people-update` when there's relevant
  activity from connected sources.
- Delete the test notes once everything works (move to `07-archive/` rather than hard-delete,
  per the vault rules), then commit.

✅ If all three produce correctly structured notes, the install is good.

## Step 4 — Set up scheduled automations (pointer)

Claude Code has **no built-in cron**. Daily/weekly automations (daily brief, weekly review,
optional vault health check) run via an **external scheduler** that invokes Claude Code on a
cadence.

See **`docs/SCHEDULED-TASKS.md`** for tool-agnostic setups and the exact prompts. Don't
configure the scheduler here.

A typical setup once you get there:
- **Daily brief** — every evening (`daily-brief`, mode `daily`).
- **Weekly review** — Monday morning (`daily-brief`, mode `weekly`).
- (Optional) **Vault health check** — monthly audit of orphans, stale stubs, and dormant
  people notes.

## Final checklist

- [ ] Repo cloned; Claude Code reads `CLAUDE.md`, `.claude/settings.json`, and the six skills.
- [ ] Vault folder created from `vault-starter/` (eight folders + `_CLAUDE.md`).
- [ ] `VAULT_PATH` set in `CLAUDE.md`.
- [ ] `MY-PROFILE.md` filled in with your real context.
- [ ] Git initialized in the vault; first commit made.
- [ ] Pre-commit hook installed (`./hooks/install.sh <vault-path>`).
- [ ] Skill smoke test passed (braindump + add person + daily brief).
- [ ] (Optional) Connected sources reachable via MCP / available tools.
- [ ] Scheduled automations configured per `docs/SCHEDULED-TASKS.md`.

## First real use

Give it ~2 weeks to settle in:

- **Week 1** — use the skills as often as possible, even for trivial things. That's the
  learning phase.
- **Week 2** — iterate on what's missing. Tweak the `SKILL.md` files to match how you
  actually work.

After two weeks you'll have a vault with a few dozen useful notes, a clear sense of which
skill to reach for when, and the adjustments made for your real workflow.

## Troubleshooting

### Claude Code can't find or read the vault
- Check that `VAULT_PATH` in `CLAUDE.md` points at the real folder.
- Ask explicitly: "Read `_CLAUDE.md` from the vault."
- Confirm the path is readable and the eight numbered folders are present.

### A skill doesn't auto-trigger
- Invoke it explicitly by name: "use the braindump skill for …".
- Confirm `.claude/skills/<name>/SKILL.md` exists and its frontmatter `description` is intact.
- Restart the Claude Code session so it re-reads the skills.

### A connected source returns nothing
- Confirm the MCP server / tool is configured and authenticated.
- These sources are optional — the system still works without them, just with less to
  synthesize. Note in `MY-PROFILE.md` which sources you actually have.

### The pre-commit hook rejects a commit
- It's protecting append-only history in `02-people/` and `05-decisions/`, or flagging a
  note missing frontmatter / the `## For future Claude` preamble. Read the message; fix the
  note. See `hooks/README.md`.
- Don't `--no-verify` past it unless you genuinely understand why it fired.

### Vault feels slow in Obsidian
- Normal beyond a few hundred notes. Disable non-essential Obsidian plugins (graph view in
  particular). Avoid heavy plugins like Dataview early on. This doesn't affect Claude Code.

## Evolution

This is a starting point you'll grow by using it:
- Add skills (project synthesis, 1:1 prep, monthly retro, etc.).
- Refine the `SKILL.md` files to match your real patterns.
- Add your own templates.

Commit every change with a clear message — you'll build a full evolution history of your
second brain in Git.
