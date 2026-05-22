# Releasing

How versions are cut for this repo. Lightweight on purpose.

## Scheme

[Semantic Versioning](https://semver.org/) — `vMAJOR.MINOR.PATCH`:

| Bump | When | Examples |
|---|---|---|
| **MAJOR** | Breaking change to the vault structure or conventions; existing vaults need a migration step | renaming/renumbering folders, changing the frontmatter contract, removing a marker other skills rely on |
| **MINOR** | New, backward-compatible capability | a new skill (e.g. `task-roundup`), a new optional frontmatter field |
| **PATCH** | Fixes and doc tweaks, no behavior change | wording fixes, hook bugfix, doc clarifications |

The single source of the current number is the [`VERSION`](../VERSION) file. Every
release is an **annotated Git tag** `vX.Y.Z` on `main`.

## Release process

1. **Branch** off `main`: `git checkout -b claude/<feature>`.
2. Build the change. Bump [`VERSION`](../VERSION) to the target number.
3. Add a dated section to [`CHANGELOG.md`](../CHANGELOG.md) (`## [X.Y.Z] - YYYY-MM-DD`,
   grouped into Added / Changed / Fixed / Removed).
4. If it's a MAJOR or a behavior-affecting MINOR, add a migration entry to
   [`docs/UPGRADING.md`](UPGRADING.md).
5. Open a PR; merge to `main` (the merge commit is the release point).
6. **Tag and push:**
   ```bash
   git checkout main && git pull
   git tag -a v3.1.0 -m "v3.1.0 — <one-line summary>"
   git push origin v3.1.0
   ```

## Conventions

- One tag per release; never move a published tag.
- The tag message mirrors the CHANGELOG section's headline.
- `VERSION` on `main` always equals the latest released tag (or the in-flight number on a
  release branch).
- Hotfix on an old line: branch from the tag (`git checkout -b hotfix/x.y.z vX.Y.0`), fix,
  bump PATCH, tag `vX.Y.1`.

## History anchor

`v3.0.0` was tagged retroactively on the Claude Code migration merge. Earlier versions
(`v1.0.0`, `v2.0.0`) are the pre-migration Cowork-era releases, recorded in the CHANGELOG
for continuity; they predate this repository's tagged history.
