# 06-knowledge/

The knowledge layer — a structured graph, not a folder dump. Four flavors live here:

- **Wiki pages** (`type: wiki`) — encyclopedic pages on concepts, entities, tools,
  teams, jargon. Created as stubs on first mention, grown incrementally with cited facts.
- **Lessons** (`type: knowledge`) — distilled patterns, frameworks, principles.
  Recurrence-gated (3+ sources) or born from reversed decisions.
- **Domain hubs** (`type: index`) — one Map of Content per knowledge domain at
  `<domain>.md`, listing every note tagged with the matching `domain:` field.
- **Source documents** (`type: doc`) — ingested docs, kept in `_sources/`.

`_INDEX.md` is the entry point (hubs + health + unsorted); `recall` queries it first.

## Naming conventions

- Wiki / lessons: `<slug>.md` (kebab-case, undated — evergreen)
- Domain hubs: `<domain>.md` (kebab-case, undated)
- Root index: `_INDEX.md`
- Source documents: `_sources/YYYY-MM-DD-<slug>.md` (dated)

## Schema

See `_CLAUDE.md` at the vault root: type schemas `wiki`, `knowledge`, `index`, `doc`.
Every note carries a `domain:` field that routes it into its hub (`unsorted` if unknown).

## Associated skills

`knowledge-build` (wiki + lessons + curator), `doc-ingest` (sources), `recall` (reads
hub-first). The curator maintains hubs and `_INDEX.md` automatically.
