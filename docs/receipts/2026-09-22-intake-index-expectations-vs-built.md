---
title: Intake CocoIndex super index — expectations and deliverables vs what is built
date: 2026-09-22
status: AUDIT — owner asked 09:12 "does the index meet expectations and deliverables"; answer: no, on 14 of 17 items
domains: [consignatio, intake, probata, search]
tags: [audit, cocoindex, super-index, search, weaviate, surreal, catalog, bulk-intake, receipt]
---

# Intake super index — expectations vs built

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
