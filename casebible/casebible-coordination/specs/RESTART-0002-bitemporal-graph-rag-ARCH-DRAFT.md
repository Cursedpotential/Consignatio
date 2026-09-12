# RESTART-0002 — Bi-Temporal Graph RAG: target architecture (DRAFT, for owner ratification)

> _Byline: Claude Code · Fable 5 · 2026-07-07_
> Companion to `RESTART-0001-source-tables-DRAFT.md` (the evidence-lane DDL). This doc is the
> system-level frame RESTART-0001 plugs into. Owner statement 2026-07-07: *"essentially what we
> are doing is creating a bi-temporal graph RAG… knowledge side uses pg_duckdb + chunked parquet,
> semantically separated; conversation/messaging evidence normalizes into actual PG message by
> message."* Semantica explicitly in scope.

## 1. North star

One bi-temporal graph RAG over the whole corpus, fed by **two ingestion lanes** with different
rigor budgets, retrieved through **four planes**, all sharing **one bi-temporal contract**.

### Lane A — EVIDENCE (court-grade, message-by-message)
Conversation/messaging evidence → parsers → **per-source raw PG tables** (RESTART-0001):
full-fidelity `raw` JSONB, UUIDv7 per message, on-row H1/H2/H3 custody hashes (Option A,
canon 2026-07-02), `conversation_key` + `participants`, `occurred_at` + `ingested_at`.
Nothing inferred at ingest. This lane pays the custody cost because it must survive court.

### Lane B — KNOWLEDGE (fast bulk, "quickly ingested and ready to use")
AI chats + docs + research corpus → semantic chunking → **Parquet on R2**, hive-partitioned,
queried **in place** via pg_duckdb (verified live: v1.1.0 installed in the ovh-data PG, image
`agno-postgres:18-duckdb`). No per-row custody overhead, no PG heap bloat — files land, chunks
are immediately SQL-queryable and embeddable. Chunk provenance = (source_path, file_sha256,
chunk_index, char_span) columns in the parquet, so knowledge stays citable without the
evidence lane's machinery.

## 2. The four retrieval planes

| # | Plane | Store | Role | Bi-temporal carrier |
|---|-------|-------|------|---------------------|
| 1 | Relational/lakehouse | PG (ovh-data) + pg_duckdb → R2 parquet | Ground truth + as-of SQL filters; joins across lanes | `occurred_at` (event) + `ingested_at` (record) on every row/chunk |
| 2 | Vector | Milvus (data-vector app) | Semantic recall; two collections: `evidence_messages` (keyed message_uuid) + `knowledge_chunks` (keyed chunk_id) | scalar fields `occurred_at`, `ingested_at` for time-filtered ANN |
| 3 | Temporal KG | Neo4j via **Graphiti (sole graph writer)** | Entities + relationships + episodes; natively bi-temporal (`valid_at`/`invalid_at` + `created_at`) → point-in-time graph queries for free | Graphiti's own bi-temporal model |
| 4 | Semantic enrichment | **Semantica** (seed-first hybrid, placement per ADR-~0035 decision) | entity-linking · dedup · conflict-resolution · provenance · semantic-extraction over lanes A+B; reads PG, writes derived signals; its `milvus_store` → OUR Milvus, `neo4j_store` = read/derive side — **Graphiti stays the writer** | inherits contract from the rows it reads |

**Query path (hybrid fusion):** question → embed → Milvus top-k (both collections, time-filtered)
∥ Graphiti search (entities/facts, point-in-time) ∥ PG as-of SQL → fuse/rerank → answer with hard
citations (message_uuid / chunk_id + source_path). Graph hops answer "who/how connected/when did
this change"; vectors answer "what's similar"; PG answers "exactly what, exactly when, prove it."

## 3. The bi-temporal contract (every plane, no exceptions)

- **Event time** = `occurred_at` — when it happened in the world (from the source data; H2 input).
- **Record time** = `ingested_at` — when WE learned it (DB default now(), immutable).
- **Corrections never overwrite**: new row/version, old one invalidated (Graphiti does this
  natively; PG lanes are append-only by design; parquet re-drops write new partition versions).
- Payoff for the case: *"as of what was known on date X"* queries — both what the record shows
  happened by X, and what had been discovered/produced by X. That distinction is litigation gold
  (discovery timing, spoliation windows, narrative drift).

## 4. Component readiness (audited 2026-07-07)

| Component | State | Evidence |
|---|---|---|
| PG 18 + pg_duckdb 1.1.0 | ✅ LIVE (installed, not just available) | live query vs agentos-db on ovh-data |
| pgcrypto / pgvector | ✅ LIVE (1.4 / 0.8.2) | same |
| RESTART-0001 evidence DDL | 🟡 DRAFT rev 2 — needs ratify + apply | has occurred_at+ingested_at on every table already |
| Parsers (SMS-XML, FB-JSON, iMessage TXT/HTML) | ✅ built, verified green | retarget outputs to 0001 tables |
| Custody canon H1/H2/H3 + cb_custody_chain tool | ✅ proven, shipped | plugin v0.5.1 |
| Milvus (data-vector) | ✅ live+healthy; collections = 🔴 to design v2 | old forensic_* schemas closed 07-07 |
| Neo4j + Graphiti | ✅ live; pipeline fixed 07-04 (nemotron LLM + nv-embed-v1) | graphiti-mcp healthy on agno net |
| Semantica | 🟡 placement DECIDED (seed-first hybrid), deploy CLOSED-superseded 07-07 → re-queue against 0001/0002 schemas | dev-resources source ~1800 files; wiring cfg exists (evidence/semantica_wiring.py, needs re-derive) |
| Semantic chunker + parquet writer | 🔴 GAP — build item (prefer off-the-shelf splitter, minimal glue) | |
| pg_duckdb → R2 wiring (httpfs/secrets) | 🔴 GAP — one-time setup, R2 creds already exist (rclone/OVH-2) | |
| Embedding model decision | 🔴 OPEN — see §6 | symmetric-only (learned gotcha); model change = full re-embed |
| Retrieval/fusion API + eval harness | 🔴 GAP — last mile | |
| Docs (arch doc, ADR, schema docs) | 🔴 to recreate alongside schemas | this doc is the seed |

## 5. Build order

1. **Ratify + apply RESTART-0001** (evidence lane DDL) — everything keys off it.
2. **Knowledge lane bring-up**: chunker → parquet layout on R2 (`knowledge/` prefix,
   hive-partitioned by source/ingest-date) → pg_duckdb SECRET + `read_parquet` views in PG →
   smoke: SQL over chunks end-to-end. *(Fastest path to "knowledge base ready to use."of the two lanes — do it in parallel with 1.)*
3. **Milvus collections v2** (`evidence_messages`, `knowledge_chunks`) derived from 0001 +
   the parquet chunk schema — needs the embedding decision first.
4. **Graphiti episode mapping**: group_ids `casebible-evidence` / `casebible-knowledge`;
   episode = message-batch / chunk-doc; backfill policy.
5. **Semantica re-queue**: re-derive wiring vs new schemas; seed-first from PG; deploy
   (its own APPROVALS item — prod infra).
6. **Retrieval fusion + eval**: hybrid query API; gold questions from the labeling workbook
   double as retrieval eval.
7. **Docs**: architecture doc + ADR (bi-temporal graph RAG) + regenerated schema docs.

## 6. Open decisions (owner)

1. **Embedding model** (one per store, symmetric-only): bge-m3 1024-d (CF Workers AI ≈$0; NIM
   endpoint was 500ing 07-04) · nv-embed-v1 4096-d (NIM, proven for memsearch) · codestral-embed
   (OpenRouter). Bigger dim = bigger Milvus footprint; changing later = re-embed everything.
2. **Parquet layout**: plain hive-partitioned parquet now (simplest, pg_duckdb-native) vs
   standing up the R2 Iceberg Data Catalog immediately (schema evolution + time-travel at the
   file layer; heavier setup). Recommend: plain parquet now, Iceberg when churn justifies it.
3. **Chunker**: off-the-shelf semantic splitter (minimize-custom-code rule) — pick during lane-B
   bring-up; conversation-aware chunking for AI chats (split on topic/session boundaries, not
   blind token windows).
4. **Ratify this doc + RESTART-0001** so lanes can build against them.
