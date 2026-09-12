# SEMANTICA — PIPELINE code-grounded addendum (to ORCHESTRATOR's SEMANTICA-ANALYSIS.md)

> _Byline: Claude Code (PIPELINE) · Opus 4.8 · 2026-06-27_
> Read of the CLEAN copy: `Agno-MCP-Platform/docs/wiki/tools/semantica/semantica/` (v0.3.0-alpha, MIT).
> Purpose: sharpen the owner's A/B/C scope call with what the code ACTUALLY supports. Read-only, no build.
> Net: the two scariest "collisions" are **configuration, not forced duplication** — Semantica can write
> our existing Neo4j + Milvus. The real decision is narrower than the brief implied.

## 1. The store "collisions" are CONFIGURABLE (brief correction)
`pyproject.toml` optional-deps + the adapter files prove Semantica is backend-pluggable:
- **Graph:** `graph_store/neo4j_store.py` (+ age_store=PG-AGE, falkordb, amazon_neptune). `graph-neo4j = neo4j>=5.0.0`. → Semantica can write **our** Neo4j. We do NOT have to run a 2nd graph.
- **Vector:** `vector_store/milvus_store.py` (+ faiss, hybrid_search). `vectorstore-milvus = pymilvus>=2.0.0`. → Semantica can write **our** Milvus. The brief's "Semantica/Pinecone" is just one option; **Milvus is first-class**. No 2nd index.
- **Embeddings/LLM:** default `sentence-transformers`; optional `llm-litellm` → can route through **our LiteLLM gateway**.

→ Collisions (a) two-graphs and (b) two-vector-paths **dissolve under configuration**. Even Option C (the
mcp_ingestor bolt-on) need not run 2 graphs/2 indexes if Semantica is pointed at our stores.

## 2. So the REAL decision is just: who OWNS the graph WRITE?
Both Graphiti and Semantica can write the same Neo4j, but only one should own entity/relation writes:
- **Keep Graphiti as the graph writer** (ADR-0014/0031: bitemporal/temporal KG, `group_id=casebible`),
  and use Semantica's `semantic_extract/` to produce entities/relations/triplets that FEED Graphiti's
  add. Semantica enriches; Graphiti persists. ← recommended; preserves our committed temporal-graph design.
- OR let Semantica's `neo4j_store` own writes and relegate/drop Graphiti. ← bigger reversal of locked ADRs.

## 3. Dedup boundary is CLEAN (confirms SORT 04:19)
`deduplication/` = `duplicate_detector` + `entity_merger` + `similarity_calculator` + `merge_strategy` —
**entity-level fuzzy merge**, operates on extracted entities, never on file content. It does NOT touch
custody. SORT's forensic sha256/md5 (file identity) + our per-message custody chain stay authoritative.
Semantica's entity-dedup is the natural home for SORT's flagged "13 version-clusters" (same-name/diff-content).
**Hard rule to encode: Semantica dedup is ENTITY-only; custody hashing is never fuzzy.**

## 4. The 2 net-new capabilities are real + legal-relevant (worth having)
- **`conflicts/`** (`conflict_detector`/`analyzer`/`resolver` + `source_tracker` + `investigation_guide`) =
  cross-source CONTRADICTION detection. Directly serves Part 2 (Analysis) + Part 3 (Legal Team): "Source A
  claims X on date D; Source B contradicts" — exactly the custody-case evidence-weighing job.
- **`provenance/`** (`manager`/`integrity`/`bridge_axiom`/`storage`) + **`change_management/`** (ontology
  versioning) = DECISION provenance: an audit trail of WHY the system concluded something. Complements
  custody (which records WHAT/whether-tampered) with WHY/how-derived. `provenance/integrity.py` may even
  reinforce custody — worth a look, but custody stays the forensic SSOT.

## 5. What we'd actually take vs skip (Option B, concrete seam)
Our pipeline: `custody(hash) → parse(per-msg normalized_record) → store(PG) → knowledge(embed→Milvus) → [P3 graph→Graphiti]`.
Semantica slots BETWEEN parse and knowledge/graph:
```
parse → Semantica[ semantic_extract (NER/coref/relation/triplet) → conflicts → provenance ] → embed(Milvus) + graph(Graphiti)
```
- **CHERRY-PICK:** `semantic_extract/`, `conflicts/`, `provenance/`, (optional) `deduplication/` (entity-merge).
- **CONFIGURE its adapters → our stores:** `graph_store/neo4j_store`→our Neo4j (or feed Graphiti), `vector_store/milvus_store`→our Milvus, `llms`→LiteLLM.
- **SKIP (we keep ours):** `ingest/` (we have custody+parsers), `parse/`+`normalize/`+`split/` (our per-message parsers are forensic-grade), and Semantica's `pipeline/` execution engine UNLESS we want its plugin-DAG orchestration (we have evidence/workflows.py). Custody/PG stay exactly as-built.

## 6. Deploy / cost / privacy flags (PIPELINE's lane)
- **Extraction has two paths:** local `named_entity_recognizer`/`ner_extractor` (likely spaCy/transformers — CPU-ok but adds image weight) vs `llm_extraction.py` (cloud LLM via providers). ⚠ Privacy: LLM extraction SENDS EVIDENCE TEXT to a cloud model — conflicts with "evidence content stays local" (hardware/CPU-only note). → default to LOCAL NER for evidence; reserve LLM extraction for non-sensitive/opt-in. Owner call.
- **Deps:** `semantic_extract` likely pulls spaCy + a model; `sentence-transformers` already implied. Adds to the platform image — folds into the (currently-held) platform-tools rebuild. Manageable, but real weight on the no-GPU box.
- **Alpha (v0.3.0):** pin the exact commit; treat as a vendored donor (like chatminer/dial-stack per canon §5), not a live pip dep that can move under us.

## 7. PIPELINE recommendation
**Option B, scoped tight:** vendor `semantic_extract/` + `conflicts/` + `provenance/` as enrichment BETWEEN
parse and our existing Milvus+Graphiti; keep custody, per-message parsers, PG, Milvus, Graphiti as-built;
Graphiti stays the graph writer (Semantica feeds it); Semantica dedup = entity-only, never custody; default
local NER for evidence privacy. This adds the conflict-detection + decision-provenance the case actually needs
without reversing locked ADRs or running duplicate infra. (Option C / mcp_ingestor = a lighter read-only
bolt-on if the owner wants to trial it first — also viable since it can target our stores, but it leaves the
enrichment outside our custody-anchored workflow.)

## 8. Owner decisions this unblocks
1. Scope **A/B/C** (PIPELINE → **B, tight**). 2. Graph writer = **Graphiti** (recommended) or Semantica.
3. Extraction = **local NER** (privacy) or LLM (quality, sends text out) — or local-default + LLM-opt-in.
4. Want conflict-detection + decision-provenance now, or phase them after the messaging ingest lands?
→ On scope pick, I do the targeted module-level read (signatures + the exact feed-into-Graphiti adapter) +
a revised pipeline diagram, then a vendoring plan. Still HOLDING the platform rebuild + ③/④ per the hard-stop.

## 9. Pipeline diagram — current vs proposed (Option B-tight)
```
CURRENT (as-built, custody-anchored):
  file ─▶ CUSTODY (sha256, write-once blob, evidence_hash)
        ─▶ PARSE (per-message NormalizedRecord — forensic parsers)
        ─▶ STORE (PG: analysis.normalized_record  ← relational SSOT)
        ─▶ KNOWLEDGE (embed bge-m3 ─▶ Milvus casebible_evidence)
        ─▶ [P3, deferred] GRAPH (─▶ Graphiti / Neo4j, group_id=casebible)

PROPOSED — Option B-tight (Semantica = enrichment BETWEEN parse and the stores;
custody/parsers/PG/Milvus/Graphiti unchanged; Semantica writes OUR stores):
  file ─▶ CUSTODY ─▶ PARSE ─▶ STORE(PG)
                                  │
                                  ▼
                    ┌─ SEMANTICA (vendored, configured → our stores) ─┐
                    │  semantic_extract: NER / coref / relation / triplet │   ← entities+relations
                    │  conflicts:        cross-source contradiction detect │   ← NET-NEW (legal value)
                    │  provenance:       decision/derivation audit trail   │   ← NET-NEW
                    │  (opt) deduplication: ENTITY-fuzzy merge (NOT custody)│
                    └──────────────────────┬───────────────────────────────┘
                                  ┌─────────┴─────────┐
                                  ▼                   ▼
                       KNOWLEDGE(Milvus              GRAPH(Graphiti owns the WRITE;
                       casebible_evidence,           Semantica feeds entities/triplets;
                       via vector_store/milvus)      via graph_store/neo4j or hand-off)

  CUSTODY (forensic sha256 + chain) stays the file/identity SSOT — Semantica never touches it.
  Extraction defaults to LOCAL NER (evidence text stays on-box); cloud-LLM extract = opt-in only.
```
Decision knobs (owner): graph WRITER = Graphiti (shown) vs Semantica neo4j_store · extraction =
local NER (privacy) vs cloud-LLM · conflicts+provenance = now vs phase-after-messaging.
