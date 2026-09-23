---
tags: [ui-components, search, intake, xplorer, weaviate, surreal, duckdb, cocoindex, rg, owner-directive]
---

# Intake search surface — owner directive, 2026-09-14

> _Byline: Claude Code · Fable 5.1 · 2026-09-14 20:41 EDT — owner words recorded verbatim; decomposition below is the supervisor's reading, to be designed in detail by the Codex design lane and built in slices._

## Owner words (20:41 EDT)

> "The search surface in Intake needs full CocoIndex, Weaviate, Surreal and DuckDB tools. With a rich and intuitive UI that exposes all the different search methods, with tweaks, graphs, indexes and everything. Including also basics like rg."

Context that stands with it: Intake is one human-AI co-workspace on the Xplorer engine (owner 2026-09-14 08:19); search assists browsing and organization and is never an approval gate (`Intake/AGENTS.md`); the store split is settled — CocoIndex pipeline, Parquet/Lance lake, Weaviate for search, SurrealDB for relationships (ADR-0040; system design §1); UI states are one small flag, never banners (owner 2026-09-13 09:45).

## What "full tools" means, per engine

| Engine | Search methods the UI must expose | Tweaks the UI must expose | Index / graph views |
|---|---|---|---|
| **rg (ripgrep)** | literal, regex, case/word toggles, glob include/exclude, file-type filter, over the selected pane/store | context lines, max results, hidden/ignored files, follow symlinks | none; results link straight to file + line, open in preview |
| **Weaviate** | keyword (BM25), vector, hybrid; per named vector (`text` now; `summary`, page/image vectors later) | hybrid alpha, limit, distance/certainty cutoff, filters (source id, path prefix, type, date), rerank on/off | collection list per store with object counts, vector config, freshness; which collection served each result |
| **CocoIndex** | not a search engine: the pipeline. Expose index runs per store: run, status, coverage, unchanged-skip, failures, receipts | caps (file bytes, chars, chunks, inflight), source registry entries | per-store index state and last run; never triggers a corpus-wide launch without an explicit action |
| **SurrealDB** (Intake graph) | relationship queries: same-content occurrences across stores, atomic units and members, package/containment, corroborating copies, provenance/history; saved graph queries with parameters | depth, edge types, store scope | graph view of a selection's neighborhood; table view; export of a query result |
| **DuckDB** (lake) | SQL over the Parquet lake: inventory, fingerprints, exact/near-duplicate groups, package manifests, chunks; semantic search via `array_cosine_similarity` when vectors are in Parquet | free SQL with saved queries; parameters; result cap | dataset/shard list per store with row counts and snapshot ids |

Every result, whatever the engine, carries: engine, index/collection/dataset that served it, score or rank basis, source id, absolute path, and opens into the same preview and selection as a browsed file. Selection-aware chat receives the same context.

## Workspace shape

- One search workbench panel inside the Xplorer workspace, not a second app. Method selector across engines; per-engine parameter drawer; result list unified; a graph tab for Surreal; a table/SQL tab for DuckDB; an index tab for CocoIndex runs and Weaviate collections.
- The current Explorer search panel and `/search` command are the seed; they gain a method selector and result provenance first.
- Backend stays `casebible_index`: add bounded, read-only endpoints per engine (rg runner, Weaviate query with parameters, Surreal saved queries, DuckDB read-only SQL with a cap) behind the existing loopback API; access control before it leaves localhost.

## Slices (each ends with a live click-through)

1. Method selector + result provenance on the existing panel (rg, keyword, hybrid) — the live-search agent's current slice aligns to this.
2. Weaviate parameter drawer + collection/index tab with freshness.
3. DuckDB SQL tab with saved queries over the lake (duplicates, packages, inventory).
4. Surreal graph tab: selection neighborhood, occurrences across stores, atomic units.
5. CocoIndex run controls per store with receipts.

## Not in scope of this directive

Evidence review, classification, custody, promotion. Downstream exclusion decisions never remove anything from the organizing index.

## Record

- File is the record; it is indexed by the Docstore pipeline (Consignatio root). Note: the registry's consignatio root is the `projects/consignatio` overlay, not the canonical `Consignatio/` repo — flagged to the owner 2026-09-14.
- Design detail owner: Codex lane (design lead). Build owner: Intake lanes by slice.
