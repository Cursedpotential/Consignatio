---
title: Coco super index AND the Intake app — two audits, expectations vs built
date: 2026-09-22
status: AUDIT, re-cut 09:35 on owner correction ("you're conflating intake and the underlying coco superindex" → reading A: index = backend service, Intake = the app, Probata borrows Intake's tooling)
domains: [consignatio, intake, probata, search]
tags: [audit, cocoindex, super-index, search, weaviate, surreal, catalog, bulk-intake, receipt]
---

# Coco super index and the Intake app — expectations vs built

## Correction 2026-09-22 09:23–09:35

The first cut of this receipt treated "the Intake super index" as one thing. Owner: "you're conflating intake and the underlying coco superindex"; reading **A** confirmed 09:35:

- **Coco super index** = `Consignatio/Intake/backend/src/casebible_index` as a backend SERVICE: reads the catalog, extracts, chunks, embeds, writes Parquet / Weaviate / the Surreal file graph, serves search over HTTP.
- **Intake** = the APP on top (the Xplorer-based co-workspace): browse files unindexed, metadata and units in view, search through the index when it exists, mark units, select, start bulk intake into the Go engine. It uses the index; it is not the index.
- **Probata Sources / Read** borrow Intake's search tooling; they own no index and no second catalog read.

The table below is split accordingly. Nothing about the facts changed; the grouping and the build order did.

### Audit 1 — the super index (backend service)

| # | Expectation | Built | State |
|---|---|---|---|
| I-1 | Index the entire corpus, case-related or not | two desktop runs on small folders | **Missing** |
| I-2 | Sourced from the PG `raw_duck` catalog | catalog query targets a table never created (09-18 SQL unrun) | **Broken** |
| I-3 | Stream everything, no 8 MiB / 1M-char / 512-chunk caps | caps still in code | **Broken** |
| I-4 | Archive members indexed in place | not indexed at all | Missing |
| I-5 | NIM embeddings, Gemini summaries, summaries as a separate pass | NIM for both, inline; credits out → 503 | Broken |
| I-6 | Weaviate = vectors (on), Surreal = file graph, DuckDB = lexical | Weaviate opt-in off; `/search` over local Parquet; Surreal projections exist | Partly |
| I-7 | Multimodal (images, video, audio, scanned PDF; entities → Surreal) | image app (09-21) only | Partly |
| I-8 | Hits carry the B2 key + catalog resolution | desktop paths only | Missing |
| I-9 | Deployed as a service on ovh-files | no Dockerfile / Coolify app | Missing |
| I-10 | Replaces nothing; Go engine still processes every selected file | respected | Met |
| I-11 | One app; chat ELT a capability inside it | respected | Met |

**Index build order:** (1) owner go on the 09-18 catalog-link SQL; (2) embedding provider; (3) package + deploy on ovh-files; (4) stream + delete caps + archive members; (5) B2 key + resolution on hits; (6) Weaviate on by default, Surreal graph on every run; (7) first corpus run with a receipt.

### Audit 2 — Intake, the app

| # | Expectation | Built | State |
|---|---|---|---|
| A-1 | Open and see all files unindexed (09-16 "see-files bar") | Probata's Direct storage tab lists B2; the Xplorer client's state: not audited here | Partly |
| A-2 | Metadata and unit marks in view (09-22 09:00) | units exist in `raw_duck.atomic_units`; no surface shows them as marks | Missing |
| A-3 | Search built in from step one: catalog names/paths, contents, meaning, relationships (09-22 09:06) | catalog names/paths only, via Probata's own SQL; the rest waits on Audit 1 | Partly |
| A-4 | Buttons for every tool (09-21 09:52) | none | Missing |
| A-5 | One search workbench, all methods, provenance on results (09-14) | not built | Missing |
| A-6 | Native panels, no iframes, no sample data (09-14) | not built | Missing |
| A-7 | Same tools serve search AND ingest: mark units, auto-select patterns, bulk intake, canonical-home move (09-20) | bulk engine exists in Probata; not fed from the app | Partly |
| A-8 | Rough-draft graphs/timelines before full intake (09-18) | not built | Missing |
| A-9 | Runs before Go intake; discovery drives selection | shape right, never exercised | Partly |

**Intake app build order (does NOT wait on the index):** A-1/A-2 (browse + metadata + unit marks over the catalog and B2, today), A-3 catalog mode now with the other three modes lighting up as Audit 1 lands, A-7 unit marking + bulk start, then A-4/A-5/A-6. Probata Sources = the same screens, borrowed.

---

## Original single-table cut (kept for the record; superseded by the split above)



> _Byline: Claude Code · Fable 5.1 · 2026-09-22 09:20 EDT. Two read-only agents: one gathered every owner statement on the index (memories, CNF, Consignatio and Probata docs, Codex sessions 2026-09-12 → 09-22, Claude logs), the other mapped the code and receipts in `Intake/backend`. Nothing in the live database was queried; counts marked "receipt" come from written receipts and still need a live check._

## Verdict

**The index does not meet the deliverables.** It exists as code that has run twice on a desktop against small folders. It has never been deployed, never run on the corpus, never read the catalog (its only catalog query targets a table that was written 09-18 and never created), never indexed an archive member, refuses any file over 8 MiB, and its two search routes answer 503 today because NVIDIA credits are out. Probata's Intake page does not use it; it reads the Postgres catalog directly with hard-coded table names.

## Item by item

| # | Owner expectation (newest ruling; source) | Built | State |
|---|---|---|---|
| 1 | Index the **entire** vault / B2 corpus, case-related or not (09-18 transcript; 09-19 02:33) | Two desktop runs: synthetic 09-11, one Obsidian vault 09-14. No corpus run, no B2 run. | **Missing** |
| 2 | Runs **before** Go-engine intake; discovery drives selection (09-18) | Pipeline shape is right (index → select → Go intake); never exercised. | Partly |
| 3 | Replaces nothing; Go engine still processes every selected file (09-18 22:15) | Respected. | Met |
| 4 | One app, `casebible_index`; chat ELT is a capability inside it (09-18) | One text app + one image app (09-21), isolated by design. | Met |
| 5 | Answer "what do I have, where, related to what, where should it go" incl. atomic units (09-18; 09-20 20:07) | Units detected by path regex in `raw_duck.atomic_units` (candidates only, "not a proven complete export"); no relation/placement answers. | Partly |
| 6 | Sourced from the PG `raw_duck` catalog, not a re-walk (09-16 rule; 09-22 09:06) | `INTAKE_SOURCE_MODE=catalog` reads `raw_duck.vault_index_source_20260918` — **never created**; script sits behind an open owner checkbox since 09-18. Fails at first fetch. | **Broken** |
| 7 | Surreal backs the file graph; Weaviate = vectors; DuckDB = lexical (09-19 02:28) | Surreal projections + graph routes exist; Weaviate target is opt-in and off by default; `/search` runs over local Parquet, not Weaviate. | Partly |
| 8 | Multimodal — images/video/audio/scanned PDF, CLIP/ColPali, MaxSim, entities → Surreal (09-21 09:52) | Image app added 09-21 (single vector + Jina MaxSim, Tesseract OCR); no video, no audio, no entities to Surreal. | Partly |
| 9 | **Stream everything**; remove the 8 MiB cap (09-19 01:51; 09-20 21:14) | Caps still in code: 8 MiB reject, 1M chars, 512 chunks. The 61 MB conversations.json and 1.3 GB SMS XML fail. | **Broken** |
| 10 | Rough-draft graphs/timelines before full intake, each row linked to source (09-18 22:28) | Not built. | Missing |
| 11 | Embeddings on NVIDIA NIM untouched; summaries on Gemini (09-18 22:43) | NIM used for both embeddings and summaries; Gemini not wired; **credits out → 503**. Summary pass still inline per file, not a separate pass. | Broken |
| 12 | Search wired into Probata + Intake: hybrid, contents and title, whole index (09-21 00:08, 12:27) | Probata's two service calls point at `INTAKE_DISCOVERY_INDEX_URL`, unset, because nothing is deployed. Live search = catalog names/paths only via Probata's own SQL. | **Missing** |
| 13 | Buttons in the web app for every tool (09-21 09:52) | None. | Missing |
| 14 | One search workbench: all methods, tweaks, graphs, indexes, rg; results carry provenance (09-14 20:41) | Not built. | Missing |
| 15 | Native panels in the Xplorer/Intake app, no iframes, no sample data (09-14) | Not built. | Missing |
| 16 | Same tools serve search AND ingest: filter for units, feed bulk intake (09-20) | Bulk intake engine exists in Probata (09-21) but is not fed by the index. | Partly |
| 17 | Built into the catalog + corpus surface as one thing, from step one (09-22 09:06) | Not built. | Missing |

Also not met, from the code map: hits return desktop paths, not B2 keys, so a hit cannot be opened from the vault; ZIP/archive members are not indexed at all; no Dockerfile / Coolify app / compose for the indexer or its API; `/filesystem/search` reads its Weaviate settings per request from raw env with no startup validation.

## Contradictions, resolved by the newest ruling

- Index later vs index everything now → **index everything first** (09-18, reaffirmed 09-20 and 09-22). The 09-16 line survives only as "browsing must work unindexed".
- Chat-scoped index → **general index over all catalog files** (09-18/09-19).
- Caps as design → **remove the cap, stream** (09-19/09-20).
- Gemini vs NIM embeddings → **NIM embeddings, Gemini summaries** (09-18 22:43).

## What it takes to make it meet the deliverables (build order)

1. **Owner go:** run `casebible/tools/vault_index_source_20260918.sql` on the catalog (item 6) — the checkbox open since 09-18.
2. **Embedding provider:** NIM credits, or a decided alternative (item 11). Nothing indexes without it.
3. **Package + deploy** the indexer and its API as a Coolify app on ovh-files, next to the data (items 1, 12).
4. **Stream:** replace the whole-file read with a streaming extractor and a container-file splitter; delete the three caps (item 9). Archive members indexed in place via the rclone/`archive/zip` range-read path already proven 09-20.
5. **Hits carry the B2 key** and the catalog `resolution` flag (item 12).
6. **Weaviate on by default** as the vector target; Surreal file graph fed on every run (item 7).
7. **First corpus run** with a receipt (item 1), then Probata's Sources/Read call this service (items 12–17) — Sources build in `Probata/docs/pending-review/2026-09-21-intake-review-module-rethink.md`.

Items 1 and 2 are the owner's. 3–7 are dispatchable now and each is proven live before the next.
