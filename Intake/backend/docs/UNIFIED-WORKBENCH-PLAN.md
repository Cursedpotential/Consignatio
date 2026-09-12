# Intake and Consignatio Vault — unified delivery plan

**Current location, verified after owner relocation:** repository at
`E:\AI_Workspace\Projects\Propria\Consignatio`, application at `Intake/`,
backend at `Intake/backend/`, original dedup/metadata work at sibling `casebible/`.
This supersedes the historical paths below. See
[the relocation receipt](../../docs/GIT-RELOCATION-RECEIPT-2026-09-10.md).

Owner terminology: **Intake** is the desktop work surface; **Consignatio** is the Vault project designated at `E:\AI_Workspace\Projects\Propria\Consignatio\`. The current application source remains in `casebible/workbench/`. Historical Case Bible/Workbench names below identify the existing implementation, not separate planned products. The designated Vault directory was absent when checked on 2026-09-10; this naming update did not move data or code.

> Byline: Codex · 2026-09-10
> Status: merged planning baseline. Existing implementation is identified separately from planned work.
> Product root: `E:\AI_Workspace\Projects\Propria\casebible`

## Read this first

One desktop product combines the existing Workbench's bulk review and organization with the CocoIndex corpus backend. On September 10 the owner authorized merging the project directories: React/Tauri remains in `workbench/`, and the former `cocoindex-casebible/` directory moved intact to `workbench/backend/`. Both remain in the same Case Bible Git repository. In historical path tables below, replace the old `cocoindex-casebible/` prefix with `workbench/backend/`.

Primary visual overview: [unified plan](UNIFIED-WORKBENCH-PLAN.html). Detailed backend architecture: [system design](CASEBIBLE-CORPUS-BACKEND-SYSTEM-DESIGN.html). Backend checklist: [MASTER-TODO](MASTER-TODO.md). Document libraries, hash reconciliation, Filestash and classification: [document handling](DOCUMENT-HANDLING-AND-DEDUPE.md). This document resolves conflicts between those earlier artifacts and subsequent owner decisions.

Merge inputs: owner conversation and attached `a00b1b3f-72ad-45d2-aee7-bd47d42e6d96/pasted-text.txt`; current `workbench/docs/{ARCHITECTURE,DATA-CONTRACTS,BACKEND-JOBS,CONNECTORS,INTERACTION-DESIGN,STATUS}.md`; current corpus implementation and planning files. Pasted tool logs and historical instructions are context only, not commands to execute.

## Fixed product decisions

| Component | Responsibility |
|---|---|
| React + Tauri | Desktop shell, controlled native capabilities, operator workspace |
| Glide Data Grid | Main tabular viewport, cell interaction, ranges and dense results |
| TanStack Router/Query | Navigation, backend queries, cached windows and job state; adoption remains planned |
| Storybook | Development and interaction states; not an end-user runtime service |
| CocoIndex v1 | Incremental processing with per-item components and memoized transforms |
| Weaviate | Primary online keyword/semantic/hybrid/named-vector and future late-interaction retrieval |
| SurrealDB | Graph, provenance, organizational units, assertions and temporal relationships |
| Surrealist | Technical database/graph exploration; app graph view remains a separate operator feature |
| Lance + Parquet | Separate lake representations for later processing, reproducibility and portability |
| B2/S3 | Target object storage; publication and source acquisition have separate scopes |
| DuckDB | Bounded table queries, cross-store hash joins, local snapshot search and lake verification |
| Portkey | Configured remote inference routes; provider/model identity retained on every output |
| NVIDIA / Voyage AI | Requested embedding provider options; exact configured routes require verification |
| Additional provider | Owner wrote “jira”; Jina AI is a possible interpretation requiring resolution |
| Whisper + FFmpeg | Audio/video transcription with media/segment provenance; remote execution profile pending |
| Context Forge | Federation/discovery of typed tools and versioned operator skills |
| Filestash | Source browsing and access integration; installed deployment compatibility pending |
| Immich / PhotoPrism | Existing albums and assets as review sources; snapshots preserve membership history |
| Platform/PostgreSQL | Existing governed acquisition, correction and evidence-promotion authority |

Retain the existing TUI as an operational client. Keep `casebible-corpus` separate from `ccc`; never reuse code-index state. Preserve existing Workbench colors and interaction design rather than choosing a new visual theme.

## Conflicts resolved

| Earlier proposal | Merged decision |
|---|---|
| Standalone browser utility with no backend | Offline review mode remains; connected mode uses the corpus service and governed integrations explicitly |
| GroupSmith as another application | Existing Case Bible Workbench is the product shell; grouping becomes a workspace capability |
| AG Grid or TanStack Table as primary grid | Glide owns rendering. Existing TanStack headless dependencies can remain where useful; no whole-corpus row materialization |
| DuckDB-Wasm and IndexedDB for all storage | IndexedDB can support browser review sessions; desktop query/storage runs behind an adapter. Wasm is optional for bounded browser datasets |
| Backend-only scope excludes frontend | Backend remains first priority; complete desktop delivery is included as a distinct workstream |
| Corpus service may perform any evidence copy | Ordinary lake/storage-copy jobs are separate from governed Platform intake/promotion; custody authority stays with Platform |
| Provisional Workbench `/jobs` routes | Treat as legacy integration draft; generate Platform bindings from its current authoritative schema once verified |
| Rust replacement for CocoIndex | Retain CocoIndex v1; Tauri uses Rust for native shell capabilities without replacing incremental processing |
| Copy/sync implies mirror deletion | Preserve originals and occurrence history; no automatic deletion propagation |

## Existing baseline and verification boundary

Current files show Workbench import, field mapping, dynamic Glide columns, Grid/Gallery views, selection/group/tag interactions, proposal/human overlays, Storybook, a Tauri skeleton and a demo/HTTP job adapter. `STATUS.md` records August 30 tests/builds and a native linker blocker. These are historical results, not fresh execution proof.

Current corpus files show text extraction, NIM calls, immutable local Parquet, DuckDB search, fingerprints, atomic-unit candidates, CLI and Textual TUI. The September 6 receipt records synthetic tests. Weaviate, Surreal, B2 publication, Portkey, Context Forge, Filestash, Whisper and advanced desktop integrations are not established by those receipts.

Do not count demo job success as backend success. Maintain an explicit demo marker in browser/Storybook; connected desktop mode must fail visibly if its service is unavailable.

## Operator workflows and feature list

### Import and inspect

Accept CSV, JSON arrays/wrappers, JSONL and pasted JSON; support delimiter/encoding selection, stable-ID mapping, duplicate-ID diagnostics, original row order, per-row parse errors and a bounded schema preview. Preserve raw input and every original field. Display nested JSON without losing its original types in export. Save reusable mapping profiles.

Open source inventories, lake snapshots and API results through one DatasetAdapter. A dataset window maps display indices to stable IDs; selection never depends on current row positions.

### Search and sort

Provide exact, keyword, semantic, hybrid, hash and similar-item search. Support saved queries, faceted filters, date-field-specific ranges, MIME, store, device/export, atomic unit, classification, processing status and review state. Sort by multiple fields with declared null ordering and a stable ID tie-breaker. Relevance order and field sorting must be explicit modes.

Index text chunks, pages, messages, sessions, code symbols and timestamped transcripts. Return source anchors, matching snippets, snapshot generation, score semantics and availability. Expand to surrounding text, whole session, parent unit or graph neighbors while preserving access scope.

Group results by source/export, conversation, content cluster, corroboration relationship or human group. Optional duplicate collapse is a display setting. Do not turn weak pairwise similarity into transitive equivalence.

### Selection and organization

Support visible/page/filter-wide selection, ranges, noncontiguous selections, invert, group/descendant/ancestor/sibling selection, same-value/pattern recipes, ungrouped/conflicting/proposed-item recipes, and named selections. Always show selected-visible, selected-hidden and total counts.

Filter-wide selection stores a query/snapshot reference plus exclusions; before mutation resolve an immutable selection manifest and preview its count/digest. A later query change does not silently enlarge an already approved action.

Groups support create, merge, split, rename, color, nest, reorder, dissolve and lock. Stable opaque group IDs have human display labels such as G-000001; retired labels are never reused. Allocate labels per review workspace to avoid offline/global counter collisions. Distinguish primary hierarchy placement from membership in several tags/collections.

Tree and grid share stable selection IDs. Validate cycle prevention, locks, cross-scope drops and atomic-container boundaries. Preserve multi-item order. Offer keyboard movement, reveal selection, branch isolation and accessible drag alternatives. Library choice for the tree is a bounded comparison of React Arborist/React Complex Tree, not a second grid choice.

### Review and history

Keep Source, Proposal and Human Decision visible as separate layers. Bulk actions include tags, notes, group assignment, review status, atomic designation and accepting/rejecting/editing suggestions. Confidence recorded by a human is distinct from model confidence.

Use an append-only command/event history for undo/redo of local review edits. Undo of a published external operation is a new compensating proposal, not deletion of its receipt. Concurrent edits use expected revision and report conflicts. Autosave sessions, support named snapshots, export originals/annotations/groups/history, and restore them losslessly. Spreadsheet CSV export must handle formula injection without altering the preserved source values.

### Documents and media

Document preview includes metadata, extracted blocks, sidecars, original/derivative choice, extraction completeness and side-by-side comparisons. Page, cell, message, symbol and media-time anchors survive transformation.

Gallery/contact sheet shares selection and groups with the grid. Add lazy thumbnails, zoom/lightbox, orientation-aware display and comparison. Keep full-resolution media out of the grid's row cache. Whisper transcripts link through extracted audio to original video; diarization is a separate provider step, with speaker candidates distinct from confirmed identities.

Import existing Immich/PhotoPrism albums as frozen membership snapshots. Refresh appends a new snapshot and delta. Embedded metadata, service annotations and human decisions remain separate. Selected opaque source references can enter Platform intake; changes back to albums/tags require a scoped proposal and receipt.

### Dedupe and classification

Own a cross-store hash ledger: reuse imported hashes with algorithm/scope/version provenance; compute missing full hashes on selected bytes; join compatible assertions; flag stale/conflicting digests; preserve every store/device/export occurrence. SHA-256/BLAKE3 establish verified byte identity; RapidFuzz, MinHash/LSH, SimHash, optional TLSH/ImageHash and Weaviate similarity generate candidate relationships.

Classify document types, topics, organizational units and proposed routes. Compare deterministic rules, lightweight supervised models and hosted model predictions on a labeled corpus. Record taxonomy/model/feature versions, calibrate scores and permit abstention. Group train/test splits by source lineage and duplicate family. Human review labels are append-only training inputs.

## Shared backend contracts

| Contract | Required fields/behavior |
|---|---|
| DatasetWindow | dataset/snapshot IDs, query hash, sort specification, row IDs, cursor, count precision, visible fields |
| SelectionManifest | immutable ID/digest, dataset snapshot, resolved IDs or immutable member parts, exclusions, creator, count |
| ReviewCommand | command/idempotency IDs, selection manifest, expected revision, typed operation, actor, timestamp |
| SearchHit | occurrence/artifact/chunk IDs, snapshot, source anchor, snippet, match method/vector space, score semantics, provenance |
| JobRun | instance, kind, scope digest, attempts, progress units, terminal state, cancellation state, receipt references |
| ConnectorSnapshot | connector/instance/native IDs, version/change token, observed time, completeness and membership digest |
| Classification | input artifact, taxonomy/model/feature versions, labels/scores, abstention, evidence and review state |
| ToolManifest | trusted executable/service, input/output schemas, allowed paths/network, timeout/resources, authority, version |

Generate TypeScript clients from versioned OpenAPI/JSON Schema. Corpus jobs and Platform jobs use different adapters where their authority differs. Context Forge wraps the same application operations; it must not introduce a second set of business rules. Federation scope follows authenticated instance/dataset permissions.

## Repository and runtime map

All paths below are relative to the product root. Proposed modules are not yet created.

| Path | Ownership/deliverable |
|---|---|
| `workbench/src/domain/` | review commands, groups, selection, undo and provenance |
| `workbench/src/import/` | schema mapping, profiles and lossless source projection |
| `workbench/src/datasets/` | proposed paged DatasetAdapter and query/window cache |
| `workbench/src/search/` | proposed search/filter/sort saved-view orchestration |
| `workbench/src/components/` | existing grid/gallery plus proposed hierarchy, compare and document panels |
| `workbench/src/connectors/` | proposed Filestash/media adapters and opaque location resolution |
| `workbench/src/jobs/` | existing gateway; reconcile with typed corpus and Platform contracts |
| `workbench/src-tauri/` | capabilities, scoped file access and trusted job launch boundary |
| `workbench/.storybook/` | component states and interaction fixtures |
| `cocoindex-casebible/src/casebible_index/` | existing pipeline; incremental extensions below |
| `.../contracts/`, `.../sources/`, `.../detection/` | proposed envelopes, connectors, MIME/atomic-unit routing |
| `.../processors/`, `.../classification/` | proposed document/media adapters and prediction pipelines |
| `.../dedupe/`, `.../lake/`, `.../projections/` | proposed ledger/reconciliation, Lance/Parquet and Weaviate/Surreal adapters |
| `.../federation/` | proposed Context Forge tool definitions and skill resource catalog |
| `cocoindex-casebible/docs/skills/` | proposed versioned corpus-search, document-review, dedup-review and job-recovery skills |
| `cocoindex-casebible/docs/receipts/` | dated integration, resource, recovery and delivery receipts |

Avoid introducing a `search/` package beside existing `search.py` without an explicit import migration. The docstore lane and global MemSearch/ccc configuration remain separate.

Runtime configuration resolves per-instance state, logs, caches, staging, locks, ports, source cursors, B2 prefixes, Weaviate collections and Surreal namespace/database. Never place generated data in source trees. Secrets remain outside Git and the React renderer. Multiple isolated processes must also share a host-wide resource admission limit.

## Priority and dependency plan

Phase numbers in MASTER-TODO identify backend work packages; they are not a mandate to delay remote text ingestion until after audio/video. The delivery order here prioritizes a usable complete text workflow.

| Priority / milestone | Scope | Dependencies | Completion evidence |
|---|---|---|---|
| P0 / M0 Contracts and limits | Reconcile APIs, identities, selection semantics, versioning, namespaces, resource budgets | current code/docs audit | contract fixtures, collision checks, failure/abstention rules |
| P1 / M1 Durable review | import profiles, autosave, undo/redo, lossless export/reload, stable selections/groups | M0 | full import-to-reload test with hidden selections and nested JSON |
| P1 / M2 Text search and lake | bounded CocoIndex text, Portkey embeddings, Lance/Parquet, Weaviate, desktop search | M0 | source-anchored retrieval, unchanged-input reuse, replayable projection |
| P1 / M3 Cross-store reconciliation | existing hash imports, conflicts, atomic/sidecar links, Surreal graph, dedup review | M0 and M2 schemas | corroborating copies retained; digest scope/version tests |
| P1 / M4 Connected sources | B2/S3 and Drive, Filestash access, Context Forge tools, isolated VPS/Serve setup | M0; credentials/targets verified | per-service integration receipts and authorized scope tests |
| P2 / M5 Structured documents and ML | Office/mail/Docling routes, classifier labels/evaluation, document comparison | M2/M3 | coverage/quality/cost benchmark and source-lineage holdout |
| P2 / M6 Media and sessions | Immich/PhotoPrism snapshots, Whisper A/V, visual PDF/image retrieval, graph/session expansion | M2/M4 | real provider/media tests, timestamp/page anchors, membership deltas |
| P2 / M7 Transfer and governed handoff | copy proposals, source/destination verification, Platform integration | M3/M4 and authoritative Platform schema | copy/retry/disaster receipt; custody boundary verified |
| P3 / M8 Extended retrieval | measured ColPali/NeMo/provider selection, face candidate review, advanced reranking | M5/M6 and evaluation fixtures | quality/cost/storage comparison; versioned vector migration |

Desktop packaging, accessibility, Storybook and crash recovery are acceptance work in every milestone, not a final cosmetic phase.

## Development guide

Before changes inspect product AGENTS, local contracts, dirty status and ownership. Preserve current frontend and backend modules, and scope edits explicitly. No source moves, dependency install, service startup or production run is implied by this planning merge.

Known frontend commands, run from `E:\AI_Workspace\Projects\Propria\casebible\workbench`: `npm run test`, `npm run build`, `npm run build-storybook`; `npm run tauri -- dev` is the native development path once prerequisites are verified. `npm run dev` is browser development, not proof of desktop packaging. Ports must be configured per instance before parallel serving.

Known backend commands, run from `E:\AI_Workspace\Projects\Propria\casebible\workbench\backend`: `uv run ruff check .`, `uv run pytest`, `uv run casebible-corpus --help`. After directory relocation, use `.venv\Scripts\python.exe -m casebible_index.cli --help` to bypass absolute paths embedded in old executable launchers. `inventory`, `detect-units`, `fingerprint`, `index`, `search`, `status`, `serve`, and `tui` exist in the current CLI. Do not document proposed flags as working commands. Before a run, explicitly select a synthetic/sample source and separate output; inspecting status is not an indexing run.

Add a feature by defining its input/output/authority contract, a representative fixture and failure behavior, then implement a bounded adapter and connect a real vertical slice. Add Storybook states and browser tests for selection/keyboard behavior; canvas accessibility requires more than DOM scanning. Record the exact source scope, dependency versions, test results, costs, peak memory, partial states and known gaps in a dated receipt.

Test suites must cover restart during publication, rate limits, invalid provider JSON, invalid vectors, schema drift, changed source bytes, duplicate external callbacks, cursor expiry, offline review edits, concurrent revision conflicts and unauthorized scope. Do not run every service simply to validate a documentation change.

## Systems analysis and pre-mortem

Boundary: desktop review, corpus processing, provider gateway, lake, projections and source adapters; governed evidence workflows enter through a defined external interface.

Accumulating stocks: queued inputs, parser outputs, pending provider calls, review proposals, unprojected lake versions, thumbnail caches and unresolved conflicts. Every stock needs a measured drain rate, durable checkpoint and maximum admitted size.

Reinforcing failure loop: slow provider responses increase pending work, retries add requests, queue/memory grow and timeouts increase. Balancing controls: shared provider admission budget, bounded queues, Retry-After, backoff, circuit breaker and stop threshold. Projection delays must be visible before users interpret search absence as source absence.

Highest-priority intervention: one typed job/selection/receipt contract with shared resource admission and explicit snapshot identities. Then add recovery and drift information. Increasing worker count alone amplifies shared-resource contention.

Assume the first broad release failed: the desktop froze, corroborating exports were collapsed, or a successful-looking job never executed remotely.

| Risk | Enabling condition | Prevention and owner | Gate |
|---|---|---|---|
| Host memory exhaustion | unbounded row/materialization queues and aggregate concurrency | runtime + dataset adapters: process-tree limits, lazy windows, durable queues | measured sample RSS and cancellation drill |
| Lost context/corroboration | content hash substitutes for occurrence identity | dedup/domain: separate occurrences, provenance and relation types | independent-export and screenshot fixtures retained |
| False job success | demo gateway or partial target write presented as complete | jobs/projections: explicit mode and per-stage receipts | real remote operation plus replay/reconciliation |
| Wrong bulk operation scope | filtered selection re-evaluated against changing data | domain/API: frozen selection manifests and expected revisions | hidden/filter-wide selection and concurrent mutation tests |
| Lost review work | session replacement or sync overwrites overlays | persistence/connectors: append-only events, snapshots and conflicts | crash/reload/export round-trip with history |

## Unified TODO and open infrastructure work

- [x] U-001 Merge the attached Workbench requirements with corpus planning and document conflicting assumptions.
- [x] U-002 Identify existing Workbench and corpus baselines from current files; preserve historical verification limits.
- [ ] U-003 Reconcile current Platform OpenAPI against the provisional job adapter and generate types.
- [ ] U-004 Implement shared snapshot/selection/review/job schemas and fixtures.
- [ ] U-005 Complete durable local review vertical slice and then connect real Weaviate search.
- [ ] U-006 Implement document handling, cross-store dedup and ML tasks in the linked contract.
- [ ] U-007 Inspect VPS target and provision a distinct Surreal namespace/database and scoped application user; keep admin credentials out of runtime.
- [ ] U-008 Inspect existing Tailscale Serve mappings; publish the intended healthy backend without overwriting another service. Private Serve access does not imply public Funnel access or a new DNS hostname.
- [ ] U-009 Verify Portkey registrations and exact NVIDIA/Voyage/additional-provider model routes, dimensions and input limits.
- [ ] U-010 Verify Filestash and Surrealist deployment/access; create scoped integration receipts.
- [ ] U-011 Create typed tools and operator skills and register/federate them through Context Forge.
- [ ] U-012 Add remote Whisper execution, diarization adapter, segment resume and original-video time links.
- [ ] U-013 Implement complete search/sort/group/selection surface and synchronized hierarchy/gallery/graph views.
- [ ] U-014 Validate packaged Tauri operation, Storybook/browser tests, memory limits and recovery using a representative sample.

Outstanding service tasks are requested work, not completed provisioning. Exact hosts/endpoints, scoped credentials, provider registrations and resource budgets must be established from live configuration before mutation.
