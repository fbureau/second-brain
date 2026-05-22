# Git hooks — vault coherence

A `pre-commit` hook that validates AI-first compliance and protects append-only
history before anything lands in Git. Suggested by the migration plan as a way to
keep the vault honest automatically.

## What it checks

The single `pre-commit` script runs three checks on staged Markdown notes:

1. **AI-first compliance** — every note inside a numbered vault folder
   (`00-inbox/` … `07-archive/`, excluding `README.md`) must have:
   - YAML frontmatter fenced with `---` … `---`,
   - `ai-first: true` in the frontmatter,
   - a `## For future Claude` preamble.

2. **Append-only history** — for notes in `02-people/` and `05-decisions/`, the
   commit is **rejected** if it deletes:
   - a dated timeline entry header (`### YYYY-MM-DD …`), or
   - a protected `(auto-logged)` / `(Backfilled)` marker.

   Editing `Compiled truth`, `Open threads`, or frontmatter (e.g. updating
   `last-interaction`) is still allowed — only history destruction is blocked.

3. **Frontmatter sanity** — rejects unterminated frontmatter; warns (non-blocking)
   on empty wikilinks `[[ ]]`.

## Install

The hook belongs in **whatever repo holds your vault**. If the vault is versioned
separately from this tooling repo, install it there.

```bash
# Into this repo:
./hooks/install.sh

# Into a separate vault repo:
./hooks/install.sh /path/to/your/vault

# Or point Git at the hooks dir directly:
git config core.hooksPath /path/to/second-brain/hooks
```

## Bypass

For a deliberate history edit (e.g. correcting a genuinely wrong timeline entry):

```bash
git commit --no-verify
```

Use it sparingly — the whole point of append-only is that the history is the audit trail.

## Suggested additional hooks (not implemented)

- **post-commit** auto-sync: push to remote / trigger a vault backup after each commit.
- **pre-push** orphan check: warn about notes with no inbound wikilink before publishing.
- **commit-msg**: enforce a lightweight convention (e.g. `vault:`, `skill:` prefixes).
