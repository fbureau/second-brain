# Architecture & design choices

Why the system is built the way it is, and what was drawn from the source projects.

## Where the patterns come from

The system is inspired by two open-source projects.

### COG-second-brain (huytieu)
**Kept:**
- Numbered folder structure (`00-inbox`, `01-daily`, …) → clear for LLMs.
- The idea of a `MY-PROFILE.md` loaded at preflight.
- The people-CRM pattern: compiled truth + timeline.
- A "skills" approach with standardized frontmatter.
- Domain classification (personal / professional / project-specific).
- Role-pack logic (here: defined by the user's profile, not hard-coded).

**Dropped:**
- The 17-skill surface (over-engineered for the need).
- The PM-centric role packs (PRDs, user stories, release notes).
- Multi-step onboarding complexity.

### obsidian-second-brain (Ghelbur)
**Kept:**
- The full AI-first ruleset ("For future Claude" preamble, complete frontmatter, recency markers, verbatim sources, mandatory wikilinks, confidence levels).
- The challenge-decision pattern (red-team against vault history).
- The append-only approach on sensitive notes.
- Systematic propagation (daily note + people + projects).
- "Search before create" to avoid duplicates.

**Dropped:**
- The large slash-command surface (folded into the six skills).
- External integrations (kept generic via MCP / available tools).
- Heavy custom scripting (kept minimal; Git hooks do the lightweight validation).

## The migration: from Cowork to Claude Code

This system originally ran on a scheduled-task assistant (Cowork). It moved to
**Claude Code** to get:

| Capability | Why it matters here |
|---|---|
| Native Git | Commit on every vault change; the append-only history becomes a real audit trail. |
| Skills (`.claude/skills/`) | Auto-trigger from a description; fast to edit and test locally. |
| Pre/post-commit hooks | Continuous vault-coherence validation (AI-first, append-only). |
| Multi-file analysis | Cross-note reasoning across `02-people/*.md`, `05-decisions/*.md`, etc. |
| No platform limits | You run sensitive 1-1 analyses yourself, whenever. |

The one thing Claude Code lacks is a **native scheduler**. The daily/weekly
automations therefore run via an external scheduler — see `SCHEDULED-TASKS.md`.
The trade-off is deliberate: a tool you live in beats a more "automated" tool you ignore.

## Design choices

### Why 8 folders, no more, no fewer
A tested sweet spot. Fewer → classification friction. More → cognitive overload.

| Section | Rationale |
|---|---|
| `00-inbox/` | Buffer for raw capture, so you don't create prematurely in the wrong place. |
| `01-daily/` | The mechanical journal, fed by daily-brief and linked from everywhere. |
| `02-people/` | The CRM — the strategic core for anyone who manages relationships. |
| `03-projects/` | The second pillar — concrete initiatives. |
| `04-meetings/` | Separate from daily because meetings have their own life (re-referenced over time). |
| `05-decisions/` | Critical: the database that feeds `challenge-decision`. |
| `06-knowledge/` | Crystallized cross-project lessons (rare but precious). |
| `07-archive/` | "Inactive but kept" — NEVER delete. |

### Why not strict PARA
PARA (Projects / Areas / Resources / Archives) is elegant but too conceptual for
fast capture; "Areas" becomes a catch-all, and there's no clear home for meetings
and people — the central entities here. This structure is more operational: each
folder maps to a note type with a clear schema.

### Why Markdown + Obsidian
- Flat Markdown is future-proof and Git-native.
- A mature plugin ecosystem and mobile reading.
- Readable by any LLM with no plugins.
- Wikilinks `[[...]]` give a navigable graph that survives renames.

Alternatives (Notion, Google Docs, Apple Notes, Roam, plain-text-only) each lose on
versioning, structure, or LLM-readability.

### Why AI-first, not "human-first"
You won't browse the vault daily — you'll ask Claude, which reads the vault. So each
note must be:
- **Self-contained**: it explains its own context (future-Claude may hit it in isolation).
- **Machine-readable**: structured frontmatter, tags, wikilinks.
- **Recency-marked**: dated claims so the LLM knows what it can trust.

It's the opposite of a "pretty" personal wiki. It's a knowledge base optimized for LLM retrieval.

### Why append-only on some sections
On sensitive notes (people, decisions), overwriting is dangerous:
- You lose history (a dated comment beats a silent correction).
- You introduce invisible contradictions.
- You blind `challenge-decision` (it can't challenge without history).

Append-only enforces a discipline that pays off long-term. The pre-commit hook
guards it mechanically.

### Why six skills
Full coverage with minimal surface:

| Skill | Use case |
|---|---|
| braindump | Fast unstructured capture |
| meeting-ingest | Structured capture (transcript) |
| daily-brief | Periodic automated synthesis + orchestration |
| people-update | Strategic CRM |
| challenge-decision | Anti-bias on high-stakes decisions |
| kickstart-backfill | One-shot Day-1 seeding |

Other skills can be derived from these. Future examples: `prep-1to1` (daily-brief
focused on one person), `quarterly-review` (daily-brief over a 3-month window),
`project-status` (meeting-ingest applied to one project). Add a skill only when a
real, recurring need emerges.

### Why Git hooks now (the source project avoided them)
The source project skipped Git hooks because the old tool synced via cloud storage
and didn't trigger them. On Claude Code, Git is first-class, so a `pre-commit` hook
validates AI-first compliance and blocks destructive diffs on `02-people/` and
`05-decisions/` continuously — what a monthly health check used to approximate. See
`hooks/README.md`.

## Explicit decisions

- **Markdown + YAML frontmatter** — interoperable, future-proof, LLM-readable.
- **Wikilinks `[[...]]` everywhere** — navigable graph, rename-safe.
- **Preamble always in English** — LLMs parse structured English preambles best; the
  body stays in the user's working language for semantic precision.
- **Minimal plugins** — Claude reads raw Markdown; heavy plugins add nothing for the agent.

## Deferred decisions (iterate later)

- **Vector search / RAG** — consider if the vault exceeds ~1000 notes and challenge-decision slows down.
- **Multi-vault (personal vs. work)** — for now, one vault separated by `personal` / `professional` tags.
- **Partial sharing** — currently fully private; later, publish select `06-knowledge/` notes if useful.
- **Fast mobile capture** — for now, capture elsewhere and process into the vault later.

## Credits & inspirations

- **Andrej Karpathy** — the LLM-wiki pattern (the founding idea).
- **Tiago Forte** — Building a Second Brain (PARA, conceptually; dropped in practice).
- **David Allen** — GTD (capture-everything mindset).
- **huytieu** — COG-second-brain (structure and people CRM).
- **Eugeniu Ghelbur** — obsidian-second-brain (AI-first rules and thinking patterns).
- **Niklas Luhmann** — Zettelkasten (atomic notes; dropped in practice).
