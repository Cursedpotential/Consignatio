# Architecture Brief: Semantica and the Case Bible Evidence Pipeline
> _Byline: Claude Code (ORCHESTRATOR + Architect sub-agent) · Opus 4.8 · 2026-06-27 · for the owner's Semantica hard-stop_

## ✅ UPDATE (ORCHESTRATOR, post-brief): a CLEAN copy was found in the active repo
The #1 blocker below (corrupted source) is **RESOLVED**. A clean, readable copy is in the **active build repo** at `Agno-MCP-Platform/docs/wiki/tools/semantica/semantica/` — verified valid Python (`core/orchestrator.py`, `conflicts/conflict_detector.py` both parse), with `pyproject.toml`: **Semantica v0.3.0-alpha — "An Open Source Framework for building Semantic Layers and Knowledge Engineering", MIT license, by Hawksight AI.** So: (a) we can read REAL code to confirm/refine the integration plan; (b) MIT license = clean to adopt/cherry-pick (matches the personal-use/OSS-on-merit stance). The taxonomy-based analysis below stands; a targeted real-code read of the 3 collision points + `conflicts/`/`decision_recorder` is the next step once the owner picks a scope (A/B/C). _(The dev-resources/OneDrive copy remains corrupted — ignore it; use the repo copy.)_

## ⚠️ Original brief caveat — the dev-resources copy is CORRUPTED
The Semantica copy at `dev-resources/Archives/OTHER_RESOURCES_TO_SORT/Case/wiki/project-docs/components/tools/semantica/semantica/` (~1800 files) is **byte-corrupted** (OneDrive/cloud-sync rot). Verified directly: `conflicts/conflict_detector.py` is high-entropy binary (`file` says `data`, not Python); `context/agent_context.py` has null-byte blocks; `core/lifecycle.py` contains a TypeScript plan from a *different* project (content scrambled across files); every `*_usage.md` is blank whitespace.
**The source code is unreadable from this copy.** Only the directory + filename **taxonomy** is intact and reliable — everything below is inferred from that taxonomy, not from read source. **#1 action: pull a clean copy (original repo / fresh export) and confirm against real code before building anything.**

## 1. What Semantica is
A general-purpose, **plugin-based semantic-ETL / knowledge-graph construction framework** (Python). Raw data → parse → entity/relation extraction → entity-resolution dedup → embed → vector + graph stores, with **provenance and conflict-detection threaded through every stage**. Domain-agnostic (not evidence-specific). Plugin-registry pattern: `core/{plugin_registry,orchestrator,lifecycle,config_manager}.py`; every module repeats `registry.py + methods.py + config.py + *_provenance.py`; `pipeline/` is a DAG orchestration layer.

Key modules (from filenames): **ingest/** (~20 connectors incl. `mcp_ingestor`+`mcp_client`), **parse/** (~18 formats incl. `docling_parser`), **semantic_extract/** (NER/relation), **deduplication/** (entity resolution: duplicate_detector, similarity, cluster_builder, entity_merger), **context/** (entity_linker, context_graph, causal_analyzer + agent_memory + decision_recorder/provenance + policy_engine), **conflicts/** (contradiction detection across sources), **embeddings/** (text + graph), **vector_store/** (Pinecone, hybrid), **graph_store/** (neo4j, age, neptune, falkordb), **kg/**, **export/** (rdf/owl/lpg/parquet/arrow/…), **provenance/**, **visualization/**.

## 2. Where it fits — overlays PROCESS stages 2–5
| Current stage | Semantica equivalent | Verdict |
|---|---|---|
| SORT (md5→sha256, type vault) | `ingest/file_ingestor` | **Leave alone** (current SORT is evidence-grade) |
| 1 CUSTODY (sha256 + write-once blob + 3-level hash chain) | *none* | **Leave alone** — no forensic-custody equivalent |
| 2 PARSE (per-message, speakers never blended) | `parse/` + `semantic_extract/` | **Augment / partial overlap** (generic parsers lack the evidence rules) |
| 3 STORE (`normalized_record` PG = SSOT) | `graph_store/age_store`, `export/parquet` | **Leave alone** — keep PG as SSOT |
| 4 KNOWLEDGE (bge-m3 → Milvus) | `embeddings/` + `vector_store/` | **Could replace/wrap** — but Milvus not in its registry (Pinecone is) |
| 5 GRAPH (entities/timeline → Graphiti/Neo4j) | `context/entity_linker` + `graph_store/neo4j_store` | **Augment / overlap** — Semantica writes Neo4j directly; Graphiti also owns Neo4j |
| *(new)* | `conflicts/`, `context/decision_recorder` | **Net-new** — nothing today does cross-source contradiction detection or decision provenance |

**Honest fit:** Semantica is the **semantic-enrichment layer between PARSE and the stores** (extract → resolve → link → embed → graph) **plus two things you don't have**: cross-source **conflict/contradiction detection** and **decision provenance**. It is **not** a replacement for CUSTODY or your evidence-specific per-message parsers.

## 3. The three hard collisions
1. **Two graph stores on one Neo4j** (Graphiti vs Semantica `neo4j_store`, different schemas) — would corrupt each other. **Only one may own graph writes.** *(biggest)*
2. **Two vector paths** (Milvus/bge-m3 vs Semantica/Pinecone) — pick one; else cost + drift.
3. **Two dedup philosophies** — forensic sha256 (exact byte identity, evidence integrity) vs Semantica fuzzy entity-merge. **sha256 = files; Semantica = entities only.** Fuzzy merge must NEVER touch evidence-file identity or the custody chain.

Custody hashing, the per-message parsers, and the PG SSOT have **no real overlap** with Semantica and should stay as-built. Feed Semantica your *already-parsed* `normalized_record`, not raw files, to preserve "speakers never blended."

## 4. Integration options
- **A — adopt Semantica wholesale** (replace extract/knowledge/graph; keep only custody+PG). Pros: one off-the-shelf engine (fits "minimize custom code"); free conflict-detection + decision-provenance + visualization. Cons: surrenders Graphiti temporal model + Milvus path; evidentiary invariants now depend on a generic framework. **Effort High / Risk High.**
- **B — cherry-pick modules** (lift `conflicts/` + `context/decision_recorder` + maybe `semantic_extract/`+`entity_linker`; discard its dedup/embeddings/vector/graph stores). Pros: keeps custody/parsers/Milvus/Graphiti untouched; adds exactly the 2 missing capabilities; no store collisions; reversible. Cons: code archaeology on a (clean) copy; plugin coupling may resist extraction. **Effort Medium / Risk Low–Med. ← lowest-regret.**
- **C — bolt on as read-only enrichment** (run the vertical to STORE, hand `normalized_record` to Semantica via its `mcp_ingestor` → its own parallel stores). Pros: zero risk to custody/parsers/SSOT; native MCP fit; lets you A/B Semantica's graph vs Graphiti. Cons: genuinely two graphs + two vector indexes (cost/drift, "which graph is truth?"); defers the hard decisions. **Effort Medium / Risk Low (but defers).**

## 5. Open decisions for the owner
1. **Get a clean Semantica source** *(blocking — nothing built until real code is read)*.
2. **Who owns the graph?** Graphiti **or** Semantica `neo4j_store`, not both on one Neo4j.
3. **Who owns embeddings/vectors?** Standardize on Milvus+bge-m3 (write a Milvus plugin) or adopt Semantica's path. Avoid two indexes.
4. **Dedup boundary** — confirm: sha256 = files; Semantica = entities only.
5. **Scope A / B / C** — B or C protect the evidentiary chain; reserve A only if Semantica becomes the platform's core knowledge engine.
6. **Want conflict-detection + decision-provenance?** Semantica's standout net-new value for a *legal* corpus — if yes, argues for ≥ Option B regardless.

**Recommendation:** pull a clean Semantica, then **Option B** — cherry-pick `conflicts/` + `decision_recorder` + `entity_linker`/`semantic_extract` between PARSE and the existing Milvus/Graphiti stages, keeping custody, parsers, PG SSOT, Milvus, and Graphiti exactly as built. Adds the two missing capabilities, triggers none of the three collisions, reversible.
