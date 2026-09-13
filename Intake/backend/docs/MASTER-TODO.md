# Case Bible Corpus Backend — Master TODO

## Owner scope checkpoint — 2026-09-12

- [x] Record CCC / Intake / Docstore as three isolated systems (documentation decision).
- [ ] Verify Intake indexes readable unique content before organization/evidence selection and retains every duplicate occurrence's provenance.
- [ ] Verify metadata-only visibility for unsupported/empty/broken/unhydrated entries without incidental hydration.
- [ ] Verify selection-aware find/group/compare/decide/move and downstream include/exclude decisions against real files with the human.
- [ ] Track multimodal OCR/STT/video/SLM and multi-vector capabilities separately by actual implementation and live verification status; this scope ruling does not mark them delivered.

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 3 | Platform: Codex / win32 | Changes: preserve boundaries and record bounded live graph proof | Context: continuation verified real metadata and populated restore -->

**Owner decision — 2026-09-12:** CCC means project-local CocoIndex Code indexes only. Intake is the multifaceted CocoIndex-based filesystem workstation, using Weaviate for advanced search and SurrealDB for relationships, with multimodal tools/libraries (OCR, STT, video transcription/processing, advanced SLM extraction/classification). Docstore is CocoIndex + SurrealDB for project documentation. Keep their apps, tracking state, locks, configuration and target ownership isolated; shared technology is not a shared runtime. This defines scope, not proof every feature is implemented.

See [CCC / Intake / Docstore boundaries](../../../../SYSTEM-BOUNDARIES.md) for indexing eligibility, duplicate provenance and the human-agent organizing workflow.

## Active delivery update — 2026-09-11

- [x] Real one-note CocoIndex/NIM/Weaviate/HTTP proof; unchanged repeat skips
  transformation. Runtime teardown bug fixed, 42 expanded scoped tests pass. See
  `LIVE-PROOF-2026-09-11.md`. Native interactive search remains pending.

**Owner priority correction:** Xplorer-based live filesystem organization is phase
one. Run the actual native file manager, its splits/previews/multi-selection and
direct user-directed moves. Selection-aware chat and local/cloud access belong
there. Imported metadata review and evidence/candidate workflows are phase two,
not prerequisites. See `../../docs/DEVELOPMENT.md` for the overriding scope.

- [ ] Native Xplorer desktop bootstrap: browse local/mounted paths, select groups,
  and preview files. Transfer-engine replacement is not a launch prerequisite.
- [x] Initial paste collision/default and skipped-item correction: 16 scoped tests
  and TypeScript check recorded in `../../docs/XPLORER-FIRST-2026-09-11.md`.
- [ ] Connect chat to actual file/group selection; verify a real remote response.
- [ ] Combined filesystem CocoIndex -> Weaviate search integrated with Explorer
  and selection-aware chat. This is part of the MVP, not evidence-stage work.
- [ ] Use local mounts initially; retain the separate remote-filesystem abstraction
  as the intended integration, not a replacement by mounts.

### Implementation checkpoint — 2026-09-11 continued

The MVP items above remain open until native/live integration is verified.
Completed source slices are not a substitute for that acceptance:

- [x] Metadata-only chat selection context, including a 700-entry test; building
  that context does not read file bytes. An active file-preview panel can read
  the selected file; open chat without preview for metadata-only discussion.
- [x] Explorer search panel and assistant search action call the shared native
  filesystem-index bridge; bounded requests, source identities and truthful errors.
- [x] Remote Portkey adapter plus a successful synthetic provider probe; real
  selection-to-chat desktop interaction is still unverified.
- [x] CocoIndex v1 custom Weaviate target, unchanged skip, idempotent writes and
  derived-object retirement without DELETE; tests include the real engine with a
  recording sink. Synthetic live persistence and unchanged replay are verified;
  real service-interruption/recovery and retirement remain unverified live.
- [x] Same-source OS locking, explicit V:/Y: alias registry and honest run-status
  receipts; registry is not automatically activated and no mount index launched.
- [x] Integrated frontend verification: 35 tests across six focused files, and
  TypeScript passes. Backend adapter/runtime/API verification: 36 scoped tests.
- [x] Later integrated checkpoints: 70 focused frontend tests, 40 backend tests,
  seven native tests, native executable build/startup and final binary check.
  Counts include the earlier tests, not additional independent full-suite runs.
- [x] Pinned native compile and runtime startup; responding window, E: WebView
  profile and duplicate-runtime exclusion verified in main receipt.
- [ ] Complete interactive native browsing/group/preview/chat smoke tests.
- [x] Preserve active chat across preview switches; lazy keep-alive and paused
  hidden polling verified by component/hook tests. Native UI proof pending.
- [x] Keyed per-pane selection/preview; focus preserves each group and active pane
  supplies chat context. Nine scoped tests pass; native interaction proof pending.
- [x] Owner selected 8082; old 8081 retired. Dedicated synthetic collection and
  one-note live HTTP search proof passed. See `LIVE-PROOF-2026-09-11.md`.
- [x] Intake-only opt-in resizable Preview + chat view, with short-window fallback;
  22 sidebar/context tests pass. Native UI proof pending, not a docking rewrite.
- [x] Disable inherited upstream updater checks/install in Intake frontend;
  four regression tests. Native plugin gate checks successfully and applies on
  next rebuild/launch; current open desktop was intentionally not interrupted.

Receipts: `../../docs/XPLORER-FIRST-2026-09-11.md`,
`../../docs/RECEIPT-2026-09-11-SELECTION-CHAT.md`, and
`docs/FILESYSTEM-SEARCH-2026-09-11.md`.

### Post-MVP transfer evaluation — owner decision 2026-09-11

- [ ] Reevaluate rclone and Ultracopier as reusable transfer-engine options behind
  the existing abstraction. No replacement or new transfer dependency for MVP.
  References: https://rclone.org/rc/ and https://github.com/alphaonex86/Ultracopier.
- [ ] Correct mixed-result cut clipboard reconciliation after MVP: retain failed
  and skipped entries. Existing clipboard clearing does not delete those files;
  owner accepts the inconvenience for MVP. This does not approve destructive
  replacement or weaken existing safeguards.

Current application root: `E:/AI_Workspace/Projects/Propria/Consignatio/Intake`.
Current routing and priority: [development guide](../../docs/DEVELOPMENT.md).
The historical scope paths below do not supersede this location.

- [x] Local metadata filter/sort and ID-based selection helpers: 19 frontend tests;
  [receipt](../../docs/RECEIPT-2026-09-11-LOCAL-QUERY.md). Not corpus search.
- [ ] Shared recovery identities, relationship assertions and search contracts.
- [ ] Bounded real multimodal CocoIndex -> Weaviate -> preview investigation loop.
- [ ] Dual-pane adjustable workspace with persistent selection/investigation.
- [ ] Surreal neighborhood graph immediately after searchable MVP (v6–6.5 in
  owner's illustrative sequence); explicit relationships from the beginning.
- [ ] **HOLD: handler choices** — reconcile prior OCR/LibreOffice/hosted Docling
  and unidentified previously tested hosted API with owner before integration.

> Byline: Codex · GPT-5 · prepared for Matthew Salem · 2026-09-09  
> Backend scope: `E:\AI_Workspace\Projects\Propria\casebible\workbench\backend`  
> Unified delivery: [merged Workbench plan](UNIFIED-WORKBENCH-PLAN.md); desktop scope is the enclosing `workbench/` directory.
> Canonical design: [`CASEBIBLE-CORPUS-BACKEND-SYSTEM-DESIGN.html`](CASEBIBLE-CORPUS-BACKEND-SYSTEM-DESIGN.html)  
> Status: planning baseline; unchecked work is not implemented or verified

## Status legend

- `[x]` — verified baseline or completed planning deliverable.
- `[ ]` — not complete.
- **HOLD** — do not implement until the named decision or prerequisite is resolved.
- **GATE** — phase cannot close without the stated verification receipt.
- Every material implementation item needs code, tests, and a dated verification receipt. A passing demo is not a receipt.

## Fixed decisions and constraints

- [x] **CBX-D-001** — Use CocoIndex for incremental discovery/transformation orchestration. **Evidence:** existing text flow and upstream review.
- [x] **CBX-D-002** — Use immutable/versioned Parquet and Lance datasets as the portable analytical lake. **Target:** Backblaze B2 over its S3-compatible API.
- [x] **CBX-D-003** — Use Weaviate for online vector, named-vector, hybrid, and future multi-vector retrieval.
- [x] **CBX-D-004** — Use SurrealDB for graph, temporal, provenance, atomic-unit, and corroboration relationships; do not make it the primary vector store.
- [x] **CBX-D-005** — Treat Weaviate and Surreal as rebuildable projections of a published lake snapshot.
- [x] **CBX-D-006** — Preserve every source occurrence. Model exact copies, corroborating copies, alternate representations, derivatives, and near-duplicate candidates as different relationships.
- [x] **CBX-D-007** — Never infer physical deletion from similarity. Source relocation is a separate dry-run, approval, copy, checksum, receipt, and retention workflow.
- [x] **CBX-D-008** — Keep this lane separate from `scripts/docstore`, the Workbench authority layer, and `ccc` runtime state.
- [x] **CBX-D-009** — Keep the management TUI thin; front-end/TanStack design belongs to a later lane.
- [x] **CBX-D-010** — Require multi-instance isolation across state paths, environments, ports, locks, logs, targets, checkpoints, and B2 prefixes.

## Verified starting baseline

- [x] **CBX-B-001** — Existing project skeleton, CLI, API, Textual TUI, CocoIndex pipeline, configuration, and tests are present. **Path:** `src/casebible_index/`, `tests/`.
- [x] **CBX-B-002** — NVIDIA NIM text enrichment/embedding path exists. **Boundary:** requires fresh provider probe and scale/error hardening.
- [x] **CBX-B-003** — Immutable local Parquet shard output and DuckDB semantic search exist. **Boundary:** not yet the full schema family, Lance materialization, or B2 publication.
- [x] **CBX-B-004** — File inventory, atomic-unit candidates, fingerprints, and dedup-review concepts exist. **Boundary:** must be upgraded to the evidence-safe relationship model.
- [x] **CBX-B-005** — Application command is `casebible-corpus` and does not reuse the `ccc` name. **Boundary:** resource-level collision testing remains open.
- [x] **CBX-B-006** — Current corpus format counts were sampled from `casebible.duckdb.r2_files` for routing priorities. **Boundary:** inventory is not a custody/completeness attestation.
- [x] **CBX-B-007** — Upstream CocoIndex examples were reviewed and mapped in the canonical HTML plan at commit `859896c431fbe70d3ce62069cb3dbd6312af1058`.

## Phase 0 — Contracts and golden corpus

- [ ] **CBX-P0-001** — Define `SourceOccurrenceEnvelope`. **Path:** `src/casebible_index/contracts/source.py`. **Verify:** contract fixtures for local, S3/B2, Drive, and Graph items.
- [ ] **CBX-P0-002** — Define stable IDs for occurrence, raw content, representation, semantic assertion, atomic unit, processor run, and projection. **Path:** `src/casebible_index/contracts/identity.py`. **Verify:** deterministic IDs and collision tests.
- [ ] **CBX-P0-003** — Define append-only hash assertion contract: SHA-256 baseline, size, algorithm/version, scope, worker, time, and verification status. **Verify:** prior-hash import does not overwrite recomputed assertions.
- [ ] **CBX-P0-004** — Freeze relationship vocabulary: `byte_identical_copy`, `corroborates`, `alternate_representation`, `derived_from`, `near_duplicate_candidate`, containment, membership, origin, mention, and temporal relations. **Path:** `src/casebible_index/contracts/relationships.py`.
- [ ] **CBX-P0-005** — Define route decision and processor attempt schemas with uncertainty, evidence, fallback, and terminal state. **Path:** `src/casebible_index/contracts/routing.py`, `contracts/runs.py`.
- [ ] **CBX-P0-006** — Define imported metadata assertion, machine proposal, human overlay, conflict, and effective-metadata view contracts. **Verify:** imported values remain immutable.
- [ ] **CBX-P0-007** — Define vector-space identity: vector name, modality, provider, model revision, shape/dimension, normalization, input digest, and policy version.
- [ ] **CBX-P0-008** — Define search-result provenance contract, including original occurrences, derivation, vector space, context expansion, and generated-content labels.
- [ ] **CBX-P0-009** — Build synthetic/redacted golden corpus. **Path:** `tests/fixtures/golden-corpus/`. **Must include:** exact copies across same and independent lineages; screenshot/native export pair; PDF/DOCX pair; Google Photos sidecar match/conflict/orphan; nested archives; ChatGPT branch; iMessage device exports; repo; scan; malformed files; interrupted run fixtures.
- [ ] **CBX-P0-010 — GATE** — Contract review receipt records schemas, invariants, fixture coverage, and unresolved decisions. **Path:** `docs/receipts/`.

## Phase 1 — Instance isolation and error kernel

- [ ] **CBX-P1-001** — Require and validate `CASEBIBLE_INSTANCE_ID`. Reject empty, reserved, path-unsafe, or ambiguous values. **Path:** `src/casebible_index/instance.py`.
- [ ] **CBX-P1-002** — Derive unique CocoIndex `AppConfig` and `Environment` names, state DB, cache, staging, logs, locks, and run directory from instance ID.
- [ ] **CBX-P1-003** — Derive unique API/TUI ports or require explicit ports; fail fast on collision. Do not inspect or modify `ccc` state.
- [ ] **CBX-P1-004** — Define namespaced B2 staging prefix, Weaviate collection prefix/tenant, Surreal namespace/database, and connector checkpoint prefix.
- [ ] **CBX-P1-005** — Add startup collision audit that prints only non-secret resolved resource names and exits before mutation on conflict.
- [ ] **CBX-P1-006** — Add stage-attempt ledger with statuses `pending`, `running`, `retry_wait`, `partial`, `complete`, `failed`, `dead_letter`, and `cancelled`.
- [ ] **CBX-P1-007** — Add bounded exponential retry with jitter and provider `Retry-After` support. Separate transient, permanent, policy, validation, and resource-limit failures.
- [ ] **CBX-P1-008** — Add timeouts, per-provider concurrency budgets, backpressure, and circuit breakers. Use CocoIndex documented concurrency/timeout/exception mechanisms.
- [ ] **CBX-P1-009** — Add lease, heartbeat, stale-worker recovery, cancellation, and last-committed-batch semantics.
- [ ] **CBX-P1-010** — Redact credentials, tokens, signed URLs, authorization headers, and sensitive payloads from logs/errors.
- [ ] **CBX-P1-011** — Expose honest run totals: discovered, routed, attempted, complete, partial, failed, dead-letter, skipped-by-policy, and projected.
- [ ] **CBX-P1-012 — GATE** — Run two simultaneous application instances alongside a read-only `ccc` state-path audit. Prove no overlapping state, ports, locks, logs, B2 prefixes, Weaviate collections, Surreal namespaces, or checkpoints.

## Phase 2 — Discovery, MIME routing, atomic units, sidecars, and dedup

- [ ] **CBX-P2-001** — Implement provider metadata ingestion before byte reads. **Path:** `src/casebible_index/detection/router.py`.
- [ ] **CBX-P2-002** — Implement bounded magic/signature and encoding detection. Extension remains a hint only. **Path:** `detection/mime.py`.
- [ ] **CBX-P2-003** — Implement archive/container probes with member count, expansion ratio, path traversal, nested-depth, time, and byte limits.
- [ ] **CBX-P2-004** — Implement route policy by media type, container, size, sensitivity, parser safety, model budget, and allowed augmenters.
- [ ] **CBX-P2-005** — Persist complete route-decision evidence and fallback path; never silently drop unsupported files.
- [ ] **CBX-P2-006** — Implement recognizer registry. **Path:** `detection/atomic_units.py`. Recognizers must be versioned and replayable.
- [ ] **CBX-P2-007** — Recognize Facebook/social exports and nested threads/albums/items.
- [ ] **CBX-P2-008** — Recognize Google Takeout/service/album or conversation/assets.
- [ ] **CBX-P2-009** — Recognize ChatGPT export/conversation/branched messages/attachments.
- [ ] **CBX-P2-010** — Recognize iMessage database/export/chat/message/attachment with device/export lineage.
- [ ] **CBX-P2-011** — Recognize code repositories/worktrees/refs/files/symbols without crossing repository boundaries.
- [ ] **CBX-P2-012** — Recognize archives, media collections/albums, mailbox/thread packages, and nested units.
- [ ] **CBX-P2-013** — Implement package-aware sidecar resolver before generic JSON routing. **Path:** `detection/sidecars.py`.
- [ ] **CBX-P2-014** — Import Google Photos JSON sidecars, existing provenance sidecars, and prior hash files as assertions with source and parser provenance.
- [ ] **CBX-P2-015** — Preserve unmatched, multiply matched, and conflicting sidecars for review; never guess a match silently.
- [ ] **CBX-P2-016** — Compute SHA-256 in streaming batches. Add fast hash only as a candidate prefilter, never a final identity claim.
- [ ] **CBX-P2-017** — Implement representation-specific fingerprints: normalized text digest, perceptual image hash, media metadata signature, and declared-version normalization.
- [ ] **CBX-P2-018** — Implement relationship-only dedup classifier with independent-origin override and review reasons.
- [ ] **CBX-P2-019** — Produce copy-suppression candidates only for explicitly policy-eligible exact copies; keep all occurrence records.
- [ ] **CBX-P2-020 — GATE** — Golden corpus proves no corroborating, alternate-format, screenshot, independent-device, or independent-export occurrence is categorized for automatic removal.

## Phase 3 — Text, unstructured extraction, sessions, and code

- [ ] **CBX-P3-001** — Harden text decoding, line-ending normalization, structural splitting, source-span offsets, and oversized-document limits. **Path:** `processors/text.py`.
- [ ] **CBX-P3-002** — Define structured metadata schema: item type, created/modified/capture/sent times with source and confidence, title, short summary, language, participants/candidates, entities, topics, sensitivity, and extraction warnings.
- [ ] **CBX-P3-003** — Probe NVIDIA NIM chat and embedding endpoints before use. Record model revision, dimension, input limits, schema adherence, and rate-limit behavior.
- [ ] **CBX-P3-004** — Add schema validation and repair/retry policy for malformed structured LLM output; retain raw-response digest and redacted diagnostics.
- [ ] **CBX-P3-005** — Keep extracted/summary text separate from original text and require source spans where the extraction type permits them.
- [ ] **CBX-P3-006** — Implement HTML/XML visible-text plus structure/link extraction without discarding original representation.
- [ ] **CBX-P3-007** — Route JSON/JSONL/CSV through export recognizers and schema probes before generic row processing.
- [ ] **CBX-P3-008** — Implement ChatGPT/AI log/session reconstruction, message ordering/branches, attachments, decisions, and whole-session expansion. **Path:** `processors/sessions.py`.
- [ ] **CBX-P3-009** — Implement general session/log decision extraction as proposals with source-message citations.
- [ ] **CBX-P3-010** — Implement code language detection and Tree-sitter-compatible structural splitting. **Path:** `processors/code.py`.
- [ ] **CBX-P3-011** — Extract symbol definitions, references/import context, repository/ref/path, and hierarchical repository summaries.
- [ ] **CBX-P3-012 — GATE** — Retrieval and extraction golden tests meet thresholds and every summary/decision resolves to original occurrences and spans/context.

## Phase 4 — Parquet/Lance lake materialization

- [ ] **CBX-P4-001** — Define versioned Arrow schemas for every dataset family listed in the system design. **Path:** `lake/schemas.py`.
- [ ] **CBX-P4-002** — Implement bounded batch materializer for Parquet with consistent compression, row group sizing, and null/type rules. **Path:** `lake/materialize.py`.
- [ ] **CBX-P4-003** — Implement Lance materialization using fresh versioned table names and bulk batches. Never overwrite/drop/reuse a remote table name.
- [ ] **CBX-P4-004** — Store vector arrays in the lake for reproducibility without making Lance the online advanced-search authority.
- [ ] **CBX-P4-005** — Define partition policy that supports common filters without tiny-file explosion.
- [ ] **CBX-P4-006** — Write run manifest with schema versions, parts, counts, byte sizes, checksums, min/max IDs/times, producer versions, and completion state.
- [ ] **CBX-P4-007** — Validate Parquet with DuckDB and reopen/version-read Lance before publication.
- [ ] **CBX-P4-008** — Implement catalog pointer/reference update only after all immutable artifacts validate. **Path:** `lake/catalog.py`.
- [ ] **CBX-P4-009** — Add schema evolution rules: additive-compatible, backfill-required, and breaking/new-dataset-version.
- [ ] **CBX-P4-010** — Add compaction/optimization plan for local Lance and B2 object sizes; no unbounded in-memory materialization.
- [ ] **CBX-P4-011 — GATE** — A clean environment reads published Parquet through DuckDB and opens Lance tables; manifest checksums/counts reconcile.

## Phase 5 — Weaviate search projection

- [ ] **CBX-P5-001 — HOLD: deployment choice** — Record Weaviate endpoint, authentication, version, tenancy/collection isolation, backup, and retention decisions.
- [ ] **CBX-P5-002** — Define versioned collections and named vectors for content, visual pages, and sensitive face instances. **Path:** `projections/weaviate.py`.
- [ ] **CBX-P5-003** — Store lake IDs, occurrence/unit IDs, filter fields, model/vector-space IDs, and projection version.
- [ ] **CBX-P5-004** — Use async/batched import with bounded concurrency, per-object errors, and idempotent IDs.
- [ ] **CBX-P5-005** — Implement projection checkpoint per immutable lake manifest/version.
- [ ] **CBX-P5-006** — Implement hybrid lexical/vector search with source, unit, type, date, model, sensitivity, and instance filters.
- [ ] **CBX-P5-007** — Support caller-selected named vectors and score-component reporting.
- [ ] **CBX-P5-008** — Implement collection migration strategy: a new model/dimension creates a new version; validate and switch only after benchmark/reconciliation.
- [ ] **CBX-P5-009** — Add complete rebuild and count/ID reconciliation from the lake.
- [ ] **CBX-P5-010 — GATE** — Golden queries meet recall/precision thresholds; rebuild produces identical logical IDs and no cross-instance results.

## Phase 6 — SurrealDB provenance, temporal, and graph projection

- [x] **CBX-P6-001** — Dedicated third deployment, scoped runtime credential, private HTTPS, schema, version and automated backups verified. See [deployment receipt](SURREAL-INTAKE-DEPLOYMENT-2026-09-12.md) and [runtime proof](SURREAL-RUNTIME-PROGRESS-2026-09-12.md). Schema-only restore proven; data-scale recovery remains open.
- [ ] **CBX-P6-002** — Define nodes for occurrence, content, representation, unit, artifact, assertion, entity/event/person candidates, run, review, and projection. **Path:** `projections/surreal.py`.
- [ ] **CBX-P6-003** — Define typed edges for membership, containment, origin, derivation, corroboration, alternate representation, similarity candidate, mention, participant, timing, and human decision.
- [ ] **CBX-P6-004** — Keep imported values, machine proposals, and human overlays separate; expose effective views without destructive merge.
- [ ] **CBX-P6-005** — Bind query parameters; do not interpolate identifiers or user values into SurrealQL.
- [ ] **CBX-P6-006** — Create indexes after measured query plans; no speculative blanket indexing.
- [ ] **CBX-P6-007** — Implement idempotent lake-manifest projection and checkpoint reconciliation.
  - Latest continuation: migration occurrence-content-map adapter implemented and live-proven on migration-builder synthetic output; every occurrence retained and verified SHA-256 only. Exact replay issued zero writes. No completed real migration generation was present locally, so cross-system count/ID reconciliation remains open. See [contract](R2-B2-OCCURRENCE-GRAPH-CONTRACT-V1.md).
  - Latest 2026-09-12: 25-row historical PG catalog applied to live graph; replay issued zero writes and preserved all original row values. Populated restore matched all 33 tables. Full-corpus/lake/live-census reconciliation remains open. See [live proof](LIVE-GRAPH-PROOF-2026-09-12.md).
  - 2026-09-12: explicit inventory/fingerprint manifest adapter implemented and fixture-tested (81 backend tests pass); preserves separate occurrences and exact content identity, supports replay and partial resume. Not a published lake connector; no real corpus load/reconciliation yet. See [input contract](INVENTORY-GRAPH-MANIFEST-V1.md).
- [ ] **CBX-P6-008** — Add graph expansion API for sessions, units, corroborating evidence, derived artifacts, entities, and timelines.
  - 2026-09-12: bounded read-only node neighborhood and readiness endpoints implemented; authenticated HTTPS verified. Full corpus-backed expansion/UI and rebuild reconciliation remain open.
- [ ] **CBX-P6-009 — GATE** — Rebuild from lake; verify cardinalities, forbidden cross-instance edges, provenance paths, and temporal query plans.

## Phase 7 — PDF and Docling

- [ ] **CBX-P7-001** — Implement PDF text/layout/scan detector and route policy. **Path:** `processors/pdf.py`.
- [ ] **CBX-P7-002** — Implement local CPU Docling baseline with document timeout, bounded concurrency, OCR-on-need, table/layout configuration, and content-hash + pipeline-version cache.
- [ ] **CBX-P7-003** — Persist Docling document/JSON, Markdown representation, pages, layout elements, tables/figures, timings, warnings, and per-component errors.
- [ ] **CBX-P7-004** — Treat Docling `PARTIAL_SUCCESS` as partial; prevent complete promotion and expose missing pages/components.
- [ ] **CBX-P7-005** — Benchmark CPU profile on native-text, scanned, mixed, table-heavy, and visually rich golden PDFs.
- [ ] **CBX-P7-006 — HOLD: measured need** — Benchmark separate CUDA/GPU worker and tuned OCR/layout/table batches.
- [ ] **CBX-P7-007 — HOLD: measured need** — Spike remote `docling-serve` only if local throughput/cost fails the agreed gate.
- [ ] **CBX-P7-008** — Add manual-like typed extraction after conversion; schema validate and cite page/span/layout source.
- [ ] **CBX-P7-009** — Produce page images only for routes requiring visual/multivector processing; avoid unconditional storage amplification.
- [ ] **CBX-P7-010 — GATE** — Record per-profile throughput, failure/partial rate, quality, memory, storage amplification, and projected corpus cost before bulk PDF execution.

## Phase 8 — Images, multimodal retrieval, and faces

- [ ] **CBX-P8-001** — Decode/probe JPG, PNG, JPEG, HEIC, WebP, GIF, and SVG safely; capture frame count, dimensions, codec, EXIF, orientation, and color metadata. **Path:** `processors/image.py`.
- [ ] **CBX-P8-002** — Compute versioned perceptual hashes and preserve raw-byte hashes separately.
- [ ] **CBX-P8-003** — Route screenshots/photos-of-documents through OCR and document/corroboration candidates without equating OCR text to native export text.
- [ ] **CBX-P8-004** — Generate captions/classification proposals with model provenance and explicit uncertainty.
- [ ] **CBX-P8-005 — HOLD: provider benchmark** — Benchmark NVIDIA, hosted ColPali/ColModernVBERT-class, Weaviate-supported, Google, and Jina candidates on the golden set.
- [ ] **CBX-P8-006** — Compare shared-space single vectors against page/image late-interaction multi-vectors using recall@k, nDCG, false merges, latency, cost, and storage amplification.
- [ ] **CBX-P8-007** — Implement selected `image_global`, `page_visual`, and `layout_late_interaction` spaces with immutable vector-space IDs.
- [ ] **CBX-P8-008** — Implement face detection to face-instance rows with boxes and technical quality. **Path:** `processors/face.py`.
- [ ] **CBX-P8-009 — HOLD: biometric policy** — Approve access, retention, display, and human-review rules before face embeddings or clustering.
- [ ] **CBX-P8-010** — Face similarity produces anonymous candidate clusters only; a person identity requires a human overlay and audit trail.
- [ ] **CBX-P8-011 — GATE** — Multimodal search meets quality/cost gates and sensitive results cannot cross policy or instance boundaries.

## Phase 9 — Audio and video

- [ ] **CBX-P9-001** — Probe audio/video containers and streams without full decode when possible. **Path:** `processors/audio.py`, `processors/video.py`.
- [ ] **CBX-P9-002** — Implement NVIDIA/LiteLLM-compatible transcription adapter with timecoded segments, language, confidence where supplied, and provider/model provenance.
- [ ] **CBX-P9-003** — Preserve original recording occurrence; transcript, diarization, summary, and decisions are separate derived artifacts.
- [ ] **CBX-P9-004** — Add bounded segmentation, retry/resume at segment boundaries, and whole-recording/session expansion.
- [ ] **CBX-P9-005** — Benchmark speaker diarization as a candidate feature; never convert speaker similarity directly into identity.
- [ ] **CBX-P9-006** — Adapt video by extracting the audio track plus versioned scene/keyframe manifest; do not duplicate entire video bytes into every derivative.
- [ ] **CBX-P9-007** — Route selected keyframes through image/OCR/caption/face processors and maintain timeline links.
- [ ] **CBX-P9-008 — GATE** — Golden recordings prove timestamp accuracy, resume behavior, transcript provenance, cost forecast, and searchable whole-session context.

## Phase 10 — Remote sources

- [ ] **CBX-P10-001** — Define common source adapter and checkpoint interface. **Path:** `sources/base.py`.
- [ ] **CBX-P10-002** — Harden local source around stable occurrence IDs, metadata, signature sampling, and safe path handling. **Path:** `sources/local.py`.
- [ ] **CBX-P10-003** — Implement B2/S3 source using CocoIndex S3 connector, custom endpoint, scoped keys, object metadata, ETag/version/checkpoint, and prefix filters. **Path:** `sources/s3.py`.
- [ ] **CBX-P10-004** — Implement Google Drive source with MIME filters, native Docs/Sheets/Slides representations, stable file IDs, metadata, and checkpoint. **Path:** `sources/google_drive.py`.
- [ ] **CBX-P10-005 — HOLD: auth decision** — Choose Drive service-account/delegated scope and document least privilege.
- [ ] **CBX-P10-006** — Spike OneDrive/SharePoint Graph adapter using drive item IDs and delta links. **Path:** `sources/onedrive.py`.
- [ ] **CBX-P10-007** — Validate Microsoft consumer OneDrive and business/SharePoint behavior separately; do not assume one delta behavior covers all account types.
- [ ] **CBX-P10-008** — Evaluate a bounded rclone/storage-abstraction fallback only where Graph cannot meet source metadata/change requirements.
- [ ] **CBX-P10-009** — Implement optional PostgreSQL reference/overlay source within authority and credential boundaries. **Path:** `sources/postgres.py`.
- [ ] **CBX-P10-010 — GATE** — Connector tests prove incremental add/change/rename/delete-marker behavior, resume, no secret leakage, and stable occurrence identity.

## Phase 11 — B2 publication and safe relocation

- [ ] **CBX-P11-001 — HOLD: infrastructure values** — Record B2 bucket, region endpoint, prefixes, application key scopes, encryption, object lock/versioning, lifecycle, and recovery policy. Do not put secrets in repository files.
- [ ] **CBX-P11-002** — Implement per-instance/run B2 staging upload with multipart resume and checksum/size validation. **Path:** `lake/b2.py`.
- [ ] **CBX-P11-003** — Publish immutable Parquet parts, Lance tables, manifest, and receipt; advance catalog pointer last.
- [ ] **CBX-P11-004** — Add orphaned/incomplete staging inventory and a review proposal. Never permanently delete staging through this application.
- [ ] **CBX-P11-005** — Define copy proposal with exact source occurrence/version, destination, reason, unit context, related corroborating/alternate artifacts, expected hash/size, and collision policy. **Path:** `operations/copy_plan.py`.
- [ ] **CBX-P11-006** — Default relocation command to dry run. Require explicit approved plan ID for any byte copy.
- [ ] **CBX-P11-007** — Copy unique/approved content to destination, verify destination hash/size, then write immutable receipt. **Path:** `operations/receipts.py`.
- [ ] **CBX-P11-008** — Never automatically delete the source after successful copy. Record the human’s separate retention decision.
- [ ] **CBX-P11-009** — Preserve atomic-unit layout or write a complete reversible mapping when normalizing destination layout.
- [ ] **CBX-P11-010 — GATE** — Disaster drill rebuilds catalog/projections from B2 manifests and verifies a sampled source-to-destination custody chain.

## Phase 12 — Search/API/TUI and scale hardening

- [ ] **CBX-P12-001** — Implement backend search service for lexical, semantic, hybrid, named/multi-vector, source/date/type filters, and graph/session/unit expansion. **Path:** `search/service.py`.
- [ ] **CBX-P12-002** — Return score components, vector model/space, matched unit, source occurrences, derived-artifact labels, and lake/projection versions.
- [ ] **CBX-P12-003** — Add API endpoints with paging, bounded result/context size, cancellation, authorization hooks, and stable error contract. **Path:** `api.py`.
- [ ] **CBX-P12-004** — Extend CLI with `doctor`, `plan`, `ingest`, `resume`, `status`, `search`, `project`, `reconcile`, `copy-plan`, and `receipt` commands. **Path:** `cli.py`.
- [ ] **CBX-P12-005** — Extend thin Textual TUI for instance selection/status, connector health, queue/errors, run/resume/cancel, search, and copy-plan review. **Path:** `tui.py`. No front-end design work.
- [ ] **CBX-P12-006** — Add health/readiness endpoints that distinguish service alive, source access, provider readiness, lake writeability, and projection health.
- [ ] **CBX-P12-007** — Add metrics for throughput, queue depth, retry/error class, parser partials, provider latency/429/cost, route uncertainty, sidecar orphan/conflict rate, projection lag, and reconciliation drift.
- [ ] **CBX-P12-008** — Add structured logs and run receipts with redaction and stable correlation IDs.
- [ ] **CBX-P12-009** — Add resource budgets by route: max bytes, pages, frames, duration, expansion ratio, tokens, model calls, and dollars.
- [ ] **CBX-P12-010** — Add benchmark harness and sampled corpus forecast before every large run.
- [ ] **CBX-P12-011** — Add backup/restore and projection-rebuild runbooks. **Path:** `docs/runbooks/`.
- [ ] **CBX-P12-012** — Add dependency/version/security scan and parser isolation review for untrusted inputs.
- [ ] **CBX-P12-013 — GATE** — Representative sampled corpus completes with honest totals, bounded resources, reconcilable lake/projections, provenance-bearing search, and no source mutation.

## Decisions that require owner or measured evidence

- [ ] **CBX-H-001 — HOLD** — Select Weaviate deployment/tenancy/backup profile after current infrastructure inventory.
- [x] **CBX-H-002** — Selected and deployed independent surreal-intake on ovh-files, consignatio/intake, migration 0001. See [deployment receipt](SURREAL-INTAKE-DEPLOYMENT-2026-09-12.md).
- [ ] **CBX-H-003 — HOLD** — Select text embedding and summarization NIM model revisions after live probe and golden-set receipt.
- [ ] **CBX-H-004 — HOLD** — Select multimodal and ColPali-class provider after corpus-specific quality/cost/storage benchmark.
- [ ] **CBX-H-005 — HOLD** — Select Docling production profile—CPU, separate GPU worker, or remote service—after measured throughput/cost.
- [ ] **CBX-H-006 — HOLD** — Select Google Drive authentication and least-privilege scope.
- [ ] **CBX-H-007 — HOLD** — Select OneDrive business/consumer account scope and Graph versus fallback behavior.
- [ ] **CBX-H-008 — HOLD** — Approve biometric/face similarity policy before production embeddings or identity review.
- [ ] **CBX-H-009 — HOLD** — Supply B2 bucket/endpoint/key-scope and retention/object-lock decisions through secret-safe configuration.
- [ ] **CBX-H-010 — HOLD** — Define acceptance thresholds for retrieval recall, extraction accuracy, acceptable partial rate, maximum cost, and projection lag.

## Definition of done

- [ ] **CBX-DONE-001** — Golden corpus plus a representative sampled corpus ingest is reproducible from a clean environment.
- [ ] **CBX-DONE-002** — Two application instances run concurrently without colliding with each other or `ccc`.
- [ ] **CBX-DONE-003** — Every occurrence, hash, route, sidecar link, derived artifact, vector, graph relationship, and review decision has provenance.
- [ ] **CBX-DONE-004** — Corroborating/alternate/derived evidence survives dedup classification and is never automatically categorized for deletion.
- [ ] **CBX-DONE-005** — Parquet and Lance publish immutably to B2 and validate from a separate clean reader.
- [ ] **CBX-DONE-006** — Weaviate and Surreal rebuild from the same lake manifest and reconcile IDs/counts/checkpoints.
- [ ] **CBX-DONE-007** — Search covers text, whole sessions, code, PDFs, images, audio, and the approved subset of video with source-bearing results.
- [ ] **CBX-DONE-008** — Provider/parser errors, partial results, retries, dead letters, costs, and run totals are visible and honest.
- [ ] **CBX-DONE-009** — Copy/move workflow is dry-run first, approval-bound, checksum-verified, receipt-producing, atomic-unit aware, and never deletes sources automatically.
- [ ] **CBX-DONE-010** — Dated verification, recovery, cost, and operational receipts exist; limitations and held decisions remain explicit.

## Change log

- **2026-09-10 — Owner naming decision:** Desktop surface is **Intake**; Vault project is **Consignatio**, designated at `E:\AI_Workspace\Projects\Propria\Consignatio\`. Current source remains `casebible/workbench/`; no relocation performed for this naming update. Apply terminology to UI and deployment configuration in a tested naming migration.

- **2026-09-10 — Codex:** Added [document handling and deduplication build contract](DOCUMENT-HANDLING-AND-DEDUPE.md), including library candidates, document inspection/preview, pair evidence, resource limits, and regression gates. Captured React/Tauri, TanStack Query/Router, Glide Data Grid, Storybook, Context Forge and Portkey integration requirements. These additions are planning work; service provisioning and library installation remain outstanding.

- **2026-09-09 — Codex · GPT-5:** Created the backend-first implementation register from the system design, CocoIndex example review, corpus inventory, systems analysis, and pre-mortem. No backend implementation was started by this planning change.
