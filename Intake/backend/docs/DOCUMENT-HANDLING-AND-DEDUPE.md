# Document handling and deduplication build contract

> Byline: Codex · 2026-09-10
> Status: implementation plan; additional libraries and services are not installed by this document.

## Product integration

The operator application is React in Tauri, with TanStack Router/Query, Glide Data Grid for corpus tables, and Storybook for component states. Document inspection and comparison consume the same backend contracts as the TUI. Weaviate provides online search; SurrealDB holds graph relationships; Lance and Parquet provide separate portable lake representations, ultimately stored on B2. Lance is not a Parquet file format.

Tools and skills will be discoverable through Context Forge. Inference uses configured Portkey routes: NVIDIA and Voyage AI, plus the additional provider the owner called “jira,” which must be resolved before registration. Jina AI is a possible intended name, not a confirmed configuration. Provider substitutions must never silently mix vector spaces.

## Document library selection

Keep the existing lightweight text path and introduce heavier dependencies as optional processor groups. Install and pin only after compatibility and license checks. The choices below are implementation candidates, not claims of complete preservation by any parser.

| Route | Library or tool | Required product and acceptance test |
|---|---|---|
| Plain text, Markdown, logs, JSON/JSONL, CSV/TSV | Standard library, existing charset-normalizer; streaming readers | Encoding and parse diagnostics; line/record offsets; original text retained; oversized records bounded |
| HTML | Existing Beautiful Soup | Readable text and heading/link structure; scripts never execute; original HTML remains accessible through a safe derivative viewer |
| Text PDF | Existing pypdf; evaluate pdfplumber for table/geometry extraction | Page-anchored blocks; encryption/empty-text states; multi-column and table fixtures |
| Complex PDF, layout and tables | Docling on a separately constrained worker | Structured document JSON plus text/Markdown derivatives; reading order, table structure, page coordinates and coverage verified |
| DOCX | Existing python-docx; supplemental OOXML inspection when needed | Paragraphs, headings and tables; explicit support/omission report for comments, revisions, headers, footnotes and embedded objects |
| XLSX | Evaluate openpyxl read-only mode | Workbook/sheet/cell references; formulas and cached values distinguished; hidden sheets declared; no macro execution |
| PPTX | Evaluate python-pptx | Slide/shape references, notes and tables; rendering is a separate derivative stage |
| EML/MBOX | Standard-library email and mailbox | Message-ID, headers, recipients, time-zone-bearing dates, body alternatives and attachment links preserved |
| MSG and legacy Office | Evaluate extract-msg; isolated conversion adapter for legacy documents | Attachment completeness and conversion receipt; format-specific errors; no silent flattening |
| XML and archives | Evaluate defusedxml; bounded zipfile/tarfile adapters | Entity expansion blocked; traversal, links, nesting and expansion limits; preserve container membership |
| Images and photo sidecars | Pillow and metadata adapter; evaluate ExifTool | Orientation-aware preview derivative, native metadata assertions, raw sidecar retention and conflict/orphan report |
| Audio/video | FFmpeg/ffprobe plus a remote transcription provider | Stream metadata, timestamped segments, optional speaker candidates, derivative hashes and original-media references |
| Code | Tree-sitter grammar adapters | Repository identity, file/symbol/range references; never run recovered code |

Docling handles several document families through a common representation, but each enabled route must pass this application's fixtures. Its OCR/layout models can consume substantial resources: no automatic model download or desktop inference fallback. Prefer a measured remote worker for model-backed conversion. Simple text extraction remains local and bounded.

Sources: [Docling supported formats](https://docling-project.github.io/docling/usage/supported_formats/), [Docling project](https://github.com/docling-project/docling).

## Document service behavior

Every original occurrence receives an identity independent of its content digest. Extracted text, thumbnails, page images, structured document JSON, OCR and transcripts receive separate artifact IDs with parent occurrence, input hash, processor/configuration version and run ID.

The service must support metadata inspection, safe preview, original/derivative selection, source-anchored search snippets, sidecar inspection, extraction coverage, and side-by-side comparison. Supported anchors include PDF page/bounding box, document block, spreadsheet sheet/cell, email message/attachment, source-code range, and audio/video time interval.

Imported metadata assertions, inferred dates/summaries and human annotations occupy separate records. Missing dates stay null; filesystem creation time must not be presented as authorship time. Conflicting sidecars remain visible. Raw parser artifacts can live as objects with table references rather than being duplicated into every chunk row.

## Deduplication library selection

| Method | Library | Interpretation |
|---|---|---|
| Exact bytes | Existing hashlib SHA-256 and blake3 | Reusable content identity after a complete stable read; retain every source occurrence |
| Legacy hash matching | Existing MD5 compatibility fields | Match imported ledgers; never sole evidence of equality |
| Fast prefilter | Existing sampled BLAKE2b and file size | Candidate generation only; confirm against full digest |
| Normalized text | Existing normalized SHA-256 and SimHash | Version normalization rules; preserve original text and distinguish alternate serialization |
| Near-document similarity | Evaluate datasketch MinHash/LSH | Token/shingle candidate retrieval; bounded buckets and pair budgets; approximate recall |
| Candidate comparison | Evaluate RapidFuzz | Compare titles, names, paths and bounded text candidates; scores are not probabilities |
| Binary similarity | Evaluate TLSH | Optional signal for sufficiently long, varied content; unsupported short/low-entropy input is an explicit state |
| Image similarity | Evaluate ImageHash | Candidate perceptual similarity on normalized derivatives; no equality or identity claim |
| Semantic overlap | Existing/provider embeddings through Weaviate | Retrieve candidates in a declared vector space; preserve model and score provenance |

Sources: [datasketch MinHash LSH](https://ekzhu.com/datasketch/lsh.html), [RapidFuzz](https://rapidfuzz.github.io/RapidFuzz/Usage/index.html), [TLSH](https://github.com/trendmicro/tlsh), [ImageHash](https://github.com/JohannesBuchner/imagehash).

Avoid installing a competing all-in-one dedup framework before these bounded primitives are evaluated. Record linkage and learned entity resolution are later capabilities requiring labeled pairs and review.

## Relationship rules

1. Detect package boundaries before proposing file disposition. A Takeout export, Facebook archive, iMessage backup or repository can contain nested units that must travel with their parent.
2. Byte equality permits storage reuse in a content-addressed destination while retaining distinct occurrence, device, acquisition and provenance rows.
3. The same message from two devices can corroborate an event. A screenshot of that message is an alternate representation and possibly corroboration; it is not a removable duplicate based on text matching.
4. Near matches form candidate edges with method/version/score and review state. Similarity is not transitive: A matching B and B matching C does not prove A equals C.
5. Preferred display copies and storage-copy plans are separate decisions. Neither authorizes deletion. Any source relocation uses an approved manifest, copy, verification, receipt and separately authorized source disposition.

## Tables and reproducibility

Extend the lake contract with `source_occurrences`, `content_objects`, `document_blocks`, `table_cells`, `attachments`, `metadata_assertions`, `sidecar_links`, `artifact_derivations`, `fingerprint_assertions`, `candidate_pairs`, `relationship_assertions`, `review_decisions` and `copy_receipts`.

Fingerprint assertions include algorithm/version, input scope, full/sampled coverage, digest, input size, source stability check, worker/run, computation time and verification status. Imported digests are assertions with origin; recomputation appends a separate assertion.

Candidate pairs include both occurrence IDs, content IDs where known, evidence features, candidate-generation method, score semantics, thresholds/version and review state. Feature engineering uses length ratio, shingle overlap, edit similarity, page/message count, lineage/device differences and metadata agreement. Missing values have explicit masks. Split evaluation by export/device/package lineage to prevent duplicate leakage; calibrate any learned score on held-out labeled pairs.

Weaviate objects reference lake IDs and snapshot generation. Surreal edges retain the same assertion IDs. Search filters use access scope and snapshot identity before retrieval and expansion. A failed projection leaves a replayable checkpoint and an explicit stale/partial status.

## Resource and recovery contract

Proposed initial test profile: one document parser, two remote requests, maximum eight pending documents, bounded Arrow batches, and an enforced 512 MiB parser subprocess memory ceiling where the operating system supports it. These are trial limits to measure, not claims about existing enforcement or whole-host RAM usage. Model-backed Docling requires its own separately measured remote profile.

Persist queues and cursors; never load the corpus into a Python list. Apply byte/token limits as well as item counts. Enforce per-document wall time, total run cost and retry budgets. Reuse stable extraction/fingerprint artifacts. DuckDB spill and memory settings, worker RSS, retry backlog and provider cost must be measured. Multiple instances need both separate namespaces and an aggregate host/provider budget.

OneDrive placeholders are metadata-only until an explicitly scoped acquisition job is requested. Hashing and preview reads can hydrate files, so they must not occur during metadata-only discovery.

## Prioritized deliverables

- [ ] P0: Freeze occurrence/artifact/anchor/fingerprint/pair schemas and regression fixtures for corroborating copies.
- [ ] P0: Enforce worker isolation, resource budgets, source stability checks, placeholder policy and crash-resume receipts.
- [ ] P1: Extend existing parsers with document blocks, attachments, extraction coverage and safe preview contracts.
- [ ] P1: Add optional dedup dependency group; benchmark RapidFuzz and datasketch against existing fingerprints.
- [ ] P1: Implement bounded pair generation, pair evidence and review endpoints; expose results in Glide Data Grid.
- [ ] P1: Publish versioned Lance and Parquet records and project searchable content into Weaviate and relationships into SurrealDB.
- [ ] P2: Add Office/mail/table adapters and sidecar association, including orphan/conflict handling.
- [ ] P2: Benchmark remote Docling and optional TLSH/ImageHash on representative fixtures.
- [ ] P2: Deliver desktop preview/comparison components with Storybook states for corrupt, encrypted, partial, offline and conflicting documents.
- [ ] P2: Publish versioned tool schemas and operator skills through Context Forge after bounded integration tests.

## Proposed API and tool surface

Define typed backend operations for `document.inspect`, `document.preview`, `document.blocks`, `document.compare`, `dedupe.candidates`, `dedupe.explain`, `review.propose`, `review.record` and `copy.plan`. Large work returns a job ID, cursor and resumable event stream. Commands require an instance and scope; retries use idempotency keys. Mutation-capable tools have explicit input manifests and authority checks. Context Forge advertises schemas and skill resources without embedding provider credentials.

Desktop credentials remain outside the React renderer. Tauri capabilities are narrowly scoped. The frontend reads through the service; it does not directly administer Weaviate, SurrealDB or storage.

## Acceptance and pre-mortem

## Cross-store deduplication system

The application owns a cross-store hash ledger and reconciliation service. Libraries supply hashing and similarity primitives; the ledger supplies source identity, provenance, review and disposition semantics. Import existing ledger rows and sidecars before scheduling new byte reads.

Represent each hash as an assertion keyed by store, source object identity/version, algorithm, normalization/sampling scope, digest, size, verification state and observation time. Preserve original field names and import origin. Maintain adapter mappings for B2/S3 metadata and inventories, local recovery ledgers, existing database tables, Drive/OneDrive checksums, and provenance sidecars. Unknown algorithms or scopes remain unverified assertions.

Compare only compatible algorithms and scopes. An S3 ETag is not generically an MD5 content digest; multipart uploads and provider behavior matter. Provider checksums, sampled fingerprints, normalized-text hashes and complete raw-byte hashes are distinct. A filename or same-size match is a discovery hint. A stale hash attached to an earlier object version cannot validate current bytes.

Cross-store reconciliation proceeds as follows:

1. Inventory metadata and import known assertions without hydrating placeholders.
2. Resolve store/object/version identity and retain all observed locations.
3. Join compatible digest assertions using partitioned DuckDB/Parquet queries; measure skew and bound group materialization.
4. Classify matches by verification strength, lineage and atomic-unit boundaries. Conflicting digests produce investigation records.
5. Schedule missing full hashes only for selected, authorized source bytes; stream reads and detect changes during hashing.
6. Build exact-content clusters plus separate alternate-representation, corroboration and near-match edges.
7. Produce a reviewable destination plan that may reuse verified stored content while retaining every occurrence and source relationship.

Required additional tables: `stores`, `source_object_versions`, `hash_import_runs`, `hash_field_mappings`, `hash_conflicts`, `content_locations`, `reconciliation_runs` and `cluster_memberships`. Content locations record verification time and availability; a known digest does not prove a location still exists. Package fingerprints include a versioned manifest algorithm and completeness state. Partial exports never qualify as whole-package equality.

## Filestash integration

Filestash is an additional browsing and file-access surface. The desktop app should support opening a known source location in Filestash, inspecting its normalized metadata and matching ledger identity, and returning to the document/search/review context.

Implement a `filestash` adapter after inspecting the installed deployment, enabled storage backends, authentication and supported integration mechanism. Do not assume a public REST endpoint or stable deep-link syntax. Prefer provider-native stable IDs for ledger identity; a browser URL or signed download URL is an expiring access mechanism, not an object ID.

The integration must preserve access scope and avoid publishing credentials or signed URLs to Context Forge or logs. Preview/access is distinct from an approved copy operation. If embedding Filestash in a Tauri webview is unsupported by authentication or frame policy, open a scoped external browser session rather than weakening those controls. Any move initiated through the app still uses its approved plan and verification receipt.

Deliverables: deployment compatibility receipt; source-location resolver; open/browse action; authorization/expired-link tests; object identity reconciliation; and a Storybook mock for unavailable or unauthorized Filestash access.

## ML classification

Use classification to propose document type, topic, organizational unit, extraction route and sensitivity tags. Technical MIME detection remains deterministic evidence; an ML prediction supplements it. Predictions cannot silently override access rules, establish a person's identity, decide legal significance, or authorize source disposition.

Start with a reproducible baseline: scikit-learn pipelines using TF-IDF and a linear classifier, then compare a classifier over hosted embeddings and schema-validated remote LLM classification through Portkey. Choose using labeled corpus results and operational cost. Do not assume a more complex model performs better. Local lightweight statistical classification is separate from downloading or running local embedding/VLM models.

Features can include text, layout/structure summaries, extension/MIME agreement, message/table/page counts and imported metadata. Track which features are derived versus imported. Treat source path and export names cautiously: they can leak labels and fail on a new recovery source.

Support multilabel topics, hierarchical document taxonomy and an explicit unknown/abstain result. Predictions record taxonomy version, model revision, feature pipeline version, training-set digest, input artifact IDs, score/calibration method and run ID. Human correction appends a review label; it never overwrites the original prediction.

Evaluation splits must keep related exports, devices and duplicate clusters together to prevent training/test leakage. Report per-class precision/recall, macro-F1, confusion matrix, calibration and abstention coverage. Low-confidence, disagreement and novel-source items enter review. Reclassification creates a new prediction version. A verified taxonomy and enough reviewed examples are prerequisites for fitting a supervised model.

## Added priorities

- [ ] P0: Inventory existing cross-store hash schemas and publish source-specific field/algorithm/version mappings.
- [ ] P0: Build fixtures for stale object hashes, multipart ETags, conflicting sidecars, repeated occurrences and incomplete packages.
- [ ] P1: Implement ledger imports, compatible-hash joins, conflict reporting and content-location reconciliation.
- [ ] P1: Define taxonomy and label overlays; build classification evaluation with lineage-grouped splits and abstention.
- [ ] P1: Inspect Filestash deployment and prove scoped object resolution without source mutation.
- [ ] P2: Add Filestash desktop actions, cross-store cluster comparison and classification review to Glide Data Grid and Storybook.
- [ ] P2: Federate `hash.lookup`, `hash.reconcile`, `classification.predict`, `classification.review_queue` and `filestash.resolve` through Context Forge with typed scope and provenance contracts.

## Release failure scenario

Assume a release failed because useful corroborating evidence disappeared, parsing exhausted RAM, or a partial extraction appeared complete. Prevent those outcomes with a golden set containing byte copies across devices, DOCX/PDF equivalents, screenshot/export pairs, partial exports, renamed photo sidecars, short TLSH inputs, malformed archives and interrupted jobs.

Required receipts: every occurrence retained; zero automatic deletion; expected pairs found with measured precision/recall; original anchors resolvable; incomplete extraction visibly partial; queues and memory bounded; restart produces no duplicate publication; Weaviate/Surreal IDs reconcile to the lake. Record measured limits and residual gaps before widening the source scope.
