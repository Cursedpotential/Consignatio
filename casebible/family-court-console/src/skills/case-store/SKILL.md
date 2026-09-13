---
name: fct-case-store
description: "(family-court-toolkit) The embedded SurrealDB case store (search + graph) behind case_put/case_query/case_search/case_graph/case_factor_map/case_timeline/case_export/case_import/case_summary plus case_status/case_docket/case_memo/case_evidence_log/case_eval/case_reference/case_source. Use when logging a fact, event, message, exhibit, filing, draft, memo, or evidence-log entry; linking evidence to an MCL 722.23 factor; searching prior entries; walking a record''s graph neighbourhood; building a court or master timeline; checking case status/docket; matching against behavior-pattern reference data; or backing up/restoring/exporting the case store. Read this before calling any case_* tool for the first time."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/case-store` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# case-store — embedded SurrealDB case store (search + graph)

> _Byline: Claude Code · Fable 5.1 · 2026-09-07._ Built as a separate addition to the MCP
> app (`mcp-app/src/store.ts` + `store-tools.ts`) — never touches `server.ts`/`core.ts`.
> _Byline: Claude Code · Sonnet 5 · 2026-09-07 — 8 new tables, 7 new edges, 7 new tools for
> the owner's 13:09-13:16 orders (filed/draft works, court-vs-master timeline, memos,
> reference data, evidence log, evals, case status, source provenance, case-extract/v1
> importer, platform export). All additive._
> Full build/ops detail: `mcp-app/README-store.md`; design writeup:
> `docs/2026-09-07-case-store-registers.md`.

## What this is

A local, embedded SurrealDB database (`rocksdb://` on disk, namespace `fct`, database
`case`) holding the structured facts of the case: people, the child (initials + age only —
**never a name**), orders (incl. standing orders via `kind`/`in_force`), hearings,
deadlines, events, messages, exhibits, the 12 MCL 722.23 best-interest factors, sources,
notes, court events, filings, drafts, memos, reference data, an evidence log, evals, and a
case-status singleton — plus the edges relating them (`evidences`, `supports_factor`,
`contradicts_factor`, `sent_by`, `sent_to`, `filed_in`, `drafted_as`, `responds_to`,
`entered_at`, `logs`, `evaluates`, `about`, `matches_pattern`). It adds full-text search
(BM25), optional vector search (NVIDIA embeddings, degrades to text-only when not
configured), and graph traversal on top of that structure.

## Court timeline vs master timeline — kept deliberately separate

`court_event` (∪ `hearing` ∪ `deadline` ∪ `order`) is the REAL court-event timeline: dates
the court actually set. `event` (∪ `message` ∪ `exhibit`) is the MASTER timeline: everything
narrated in the corpora, extracted independently of what the court knows. Owner order
2026-09-07 13:09-13:16: keep these separate — `case_timeline({mode: "court"|"master"|
"merged"})` tags every entry with its `lane` rather than blending the two into one
undifferentiated feed.

## Where the file lives

`CUSTODY_CASE_DB` env var, else `~/.config/family-court-toolkit/case.db`. One file, shared
by the MCP tools and the CLI twin (`mcp-app/scripts/case-cli.mjs`) — never open it from two
processes' worth of writes at once (RocksDB is single-writer).

## The two-clock rule

Every `event`, `message`, and `exhibit` carries **two** dates: `occurred_at` (when it
actually happened) and `known_at` (when the owner learned of it). This is the same
knowledge-horizon discipline the platform uses elsewhere — `case_timeline`'s `known_by`
filter answers "what did I know by date X", never "what happened by date X". Always set
both dates on every event/message/exhibit; never collapse them to one date, even when they
happen to be the same.

## Child protection — absolute, checked in two independent places

A `child` record may only ever be `{ initials, age }`. `case_put` rejects any `name` field
at the application layer, and the database schema (`child` is `SCHEMAFULL` with only those
two fields defined) rejects it independently even if the application check were ever
bypassed. **This does not, by itself, stop a child's name from appearing in free text** —
an `event.description`, `exhibit.label`, or `note.text` you write yourself can still contain
a name if you type it there. When importing bulk text (the Vincent-style schema importer is
the worked example — see `mcp-app/README-store.md`), redact every child's real name out of
free-text fields before writing them, the same way `importVincentSchema()`'s
`redactChildNames()` does.

## How the other members use this store

- **`best-interest-factors` / `mcl-factor-mapper`** (factors family): read `case_factor_map`
  for the current count of supporting/contradicting events and exhibits per factor (a-l),
  with the top 5 of each — a live version of the worksheet's evidence-strength ratings.
- **`custody-packet-builder`** (drafting): reads `case_timeline` (occurred_at/known_at
  ordered) and `case_graph` on each exhibit to pull its linked events/factors when
  assembling a packet.
- **`documentation-methods`** (documentation): writes FACT log entries via
  `case_put({ table: "event", ... })` and BIFF-reframed messages via
  `case_put({ table: "message", ... })` as they're drafted, so later factor analysis and
  packet building can find them.
- **`verify-michigan-legal-sources` / `trusted-sources`** (verification): write acquired
  authorities via `case_put({ table: "source", ... })` so a source's currency/status travels
  with the case record, not just a citation in a draft.
- **`case_facts` (in `core.ts`)** — `case_summary` returns the same shape (county, court,
  judge, referee, controlling_orders, next_hearing, deadlines, parties as initials, children
  as count+ages), computed from this store instead of the local `case.json` file, so
  `case_facts` can eventually delegate to it once wired.

## Tools (all read `CUSTODY_CASE_DB` / the default path automatically)

| Tool | Use it to |
|---|---|
| `case_put` | Upsert one record (any table) and, in the same call, `RELATE` it to others (e.g. an exhibit `evidences` an event, an event `supports_factor` a factor letter). |
| `case_query` | Run a parameterised SurrealQL query for anything the other tools don't cover. `DELETE`/`REMOVE`/`DEFINE` need `write: true`; results cap at 200 rows. |
| `case_search` | Full-text and (if embeddings configured) vector search over 10 tables (event/message/note/exhibit/memo/filing/draft/court_event/reference/eval) — `mode: "text" \| "vector" \| "hybrid"`; hits include `source` when present. |
| `case_graph` | 1- or 2-hop neighbourhood of a record (`"table:id"`) across any/all of the 13 edge types, with a short summary per neighbor. |
| `case_factor_map` | Per-factor (a-l) support/contradict counts + top 5 each — the live factor worksheet. |
| `case_timeline` | `mode: "court" \| "master" \| "merged"` (default merged) — the court-event timeline vs the corpus-extracted master timeline, each entry tagged `lane`. `known_by` filters the master lane (two-clock discipline); `upcoming` filters the court lane. |
| `case_export` / `case_import` | `case_export({format: "snapshot"\|"platform"})` — JSON snapshot backup, or an NDJSON-per-table platform (probata) bundle. `case_import` auto-detects a snapshot, a Vincent-style schema, or a case-extract/v1 file/directory. |
| `case_summary` | `case_facts`-compatible summary, computed from the store, now including per-table `counts`. |
| `case_status` | `action: "get" \| "set"` — the `case_status:current` singleton (phase, posture, next_court_event, open_deadlines, notes). |
| `case_docket` | List filings + drafts + orders + upcoming court_events, filterable by `status`/`doc_type`/`in_force`. |
| `case_memo` | `action: "put" \| "list" \| "latest"` — analysis/strategy/weakness/direction/finding/risk/goal/issue/advice memos. |
| `case_evidence_log` | `action: "append" \| "list"` — a lightweight evidence handling log ("for when we get to that point"), optionally RELATEd to an exhibit. |
| `case_eval` | `action: "put" \| "list"` — evals/reports (kind, subject, score, verdict). |
| `case_reference` | `action: "load" \| "list" \| "match"` — behavior-detection patterns/ontology/lexicon as reference data (loaded whole, never analyzed); `match` runs pattern/alias matching with spans. |
| `case_source` | Given a `"table:id"` ref, return its `source` block, whether `source.path` exists locally, and the r2 pointer. |

If any store tool returns `{ available: false, reason }`, the native `surrealdb`/
`@surrealdb/node` module failed to load — see `mcp-app/README-store.md`'s install section
(`npm ci --omit=dev` is required after `npm install`) rather than treating it as a data
problem.

## Source provenance — every record links to its original document

Any data record may carry `source: { path, sha256, r2_path, locator, url, row, extract_id }`.
`case_put` preserves it as-is; `case_search`/`case_docket`/`case_timeline` results surface it
per row; `case_source({ id })` resolves it directly (with a local-existence check, no network
calls). The case-extract/v1 importer (below) sets this automatically on every record it
writes.

## Importing the Case Bible extraction (case-extract/v1)

`case_import({ path })` auto-detects a case-extract/v1 envelope (single file or a
`<row>/*.json` directory tree) and routes it through the dedicated importer, which reduces
every child to `{ initials, age }` and redacts that child's real name (and aliases, collected
across the WHOLE batch first) out of every free-text field before writing — the same
discipline the older Vincent-schema importer uses. Idempotent by `extract_id`
(`<row>-<seq>`), so re-running an import merges onto the same records. Never write under
`E:\AI_Workspace\casebible\_intake\` — that tree is owned by other agents; read-only here.

## Reference data (`content/reference/`)

Behavior-detection patterns, ontology terms, and lexicons are REFERENCE data: loaded whole via
`case_reference({action:"load", from_plugin:true})`, never analyzed, never migrated — see
`content/reference/README.md`. This also ingests the existing `content/tools/court-language/
lexicon.json` (mapped to `kind:"lexicon"`) so `case_reference match` sees the same banned-
phrase/absolutes/characterization patterns `court_language_review` already enforces
deterministically.

## CLI (outside the MCP context)

```
node "${CLAUDE_PLUGIN_ROOT}/mcp-app/scripts/case-cli.mjs" put event e1 '{"occurred_at":"...","known_at":"...","description":"..."}'
node "${CLAUDE_PLUGIN_ROOT}/mcp-app/scripts/case-cli.mjs" search "parenting time" --mode hybrid
node "${CLAUDE_PLUGIN_ROOT}/mcp-app/scripts/case-cli.mjs" graph event:e1 --depth 2
node "${CLAUDE_PLUGIN_ROOT}/mcp-app/scripts/case-cli.mjs" summary
```

Run it with no arguments for the full subcommand list.

## Seeding (owner's decision, not automatic)

`mcp-app/scripts/import-vincent-schema.mjs <path> [--dry-run|--commit]` loads a Vincent-style
case schema. It defaults to `--dry-run` (a throwaway in-memory store, prints counts only) —
**never pass `--commit` without the owner explicitly asking for it**; seeding the real case
store is the owner's call. See `mcp-app/README-store.md` for the two real parsing quirks
found in the owner's actual intake file (no code fence; one narrow JSON-escaping bug) and
the free-text child-name redaction this importer performs.

## Backup / export policy

Run `case_export` (or the CLI's `export` subcommand) before any bulk edit or import — it
writes one JSON file per snapshot to `~/.config/family-court-toolkit/exports/`, never
overwriting a prior export (timestamped filenames). Nothing in this member deletes a
snapshot automatically; that's a manual/owner cleanup task.

## Sources

`mcp-app/src/store.ts`, `store-tools.ts`, `README-store.md` · `mcp-app/scripts/case-cli.mjs`,
`import-vincent-schema.mjs` · `mcp-app/tests/store.test.mjs` (30 tests) ·
`docs/2026-09-07-case-store-registers.md` (owner-order design writeup) ·
`content/reference/README.md`, `behavior-patterns.example.json` ·
`references/best-interest-factors/SKILL.md` (the MCL 722.23 factor titles this store seeds) ·
`references/documentation-methods/SKILL.md`, `references/custody-packet-builder/SKILL.md`
(the members that write/read this store).
