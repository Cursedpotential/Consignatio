# Intake development guide

Updated 2026-09-11. This is the active entry point after directory relocation.

## Product priority

### Owner correction — 2026-09-11: working file manager first

The first milestone is the actual Xplorer-based local/cloud file manager with
chat assistance, not the metadata-review application. The review-first milestone
below is superseded and belongs to phase two.

- Browse actual filesystem/provider locations without importing candidate rows.
- Select files naturally; retain working groups and optional "belong together"
  units without requiring classification or evidence status.
- Choose destinations and perform real move/copy/rename operations, including
  agent assistance over the user's explicit selection and destination.
- Do not require indexing, hashing, evidence acceptance, or a reconstruction
  review workflow before ordinary authorized file operations.
- Use existing Xplorer functionality and extend missing provider/group/chat
  capabilities. Local and mounted paths plus connected cloud providers belong
  in the same work surface; do not claim every provider already works.
- Keep normal collision resolution, correct operation results, cancellation,
  and recoverable handling. These must not become arbitrary corpus-size or
  selected-candidate limits on the live filesystem browser.
- Permanent deletion remains prohibited by the owner's workspace instructions.
  This does not prohibit authorized moves, copies, renames or organization.

Immediate acceptance test: launch native Xplorer, browse a chosen real folder,
multi-select, move to a chosen destination, verify refresh/results, and repeat
with a second group. Then prove a connected cloud route and selection-aware chat.
Use disposable test files for automated move tests, not the source collection.

The existing React review surface is retained as phase-two work, not discarded.
Its bounded JSON/CSV preview is not the replacement file-manager interface.

### Filesystem index and graph — existing decision restored

The original synthesized cookbook map already includes
`meeting_notes_to_surrealdb_graph` in
`backend/docs/CASEBIBLE-CORPUS-BACKEND-SYSTEM-DESIGN.html`, with native graph target
and relation creation. Reuse that integration pattern rather than reopening the
database selection.

Intake's CocoIndex app indexes filesystems, content, archives and organizational
units. Its dedicated Surreal database describes store/location/containment,
logical membership, nested units, sidecars, alternate formats and move history.
It is not the downstream evidence index or evidence-analysis database. No shared
database, credentials or evidence approval workflow is implied by shared software.

The filesystem graph can follow the MVP; powerful filesystem search belongs to
stage one. Browsing and ordinary user-directed moves must work without waiting
for indexing. Keep search integrated into Explorer, not a candidate-review queue.

### Historical review-oriented framing (phase two)

The first product milestone is a human-and-agent recovery investigation surface
over seven overlapping stores, not automatic evidence promotion or bulk cleanup.
Search unreconciled material while preserving its uncertainty and every occurrence.

Required workflow: search -> preview -> explore neighbors -> compare occurrences
and alternative formats -> select -> mark "belong together" -> review a proposed
reconstruction. Logical membership never implies physical movement, classification,
completeness, or permission to discard corroborating material.

Core workspace: two independent navigation panes, persistent preview/metadata,
agent panel and working selection. Resizable panels and saved investigation state
are required. Docking and additional native windows must not duplicate workers.

Weaviate powers advanced search. Surreal's graph follows immediately after the
search MVP (owner's illustrative v5 -> v6–6.5 sequence), not a distant phase.
Stable identities and explicit relationship records precede both integrations.
Lance and Parquet remain distinct portable outputs for later lake processing/B2.

## Handler decision gate

Before selecting or wiring new document/OCR handlers, reconcile earlier research
and consult the owner. LibreOffice is a candidate; Docling is hosted. Another
previously tested hosted API remains to be identified. Do not guess its identity.
Reuse existing text/metadata/sidecars and prior outputs where valid. Preserve
processor versions, extraction failures, partial results and routing reasons.
This gate does not block work on source contracts, search, layout or review rules.

## Current code boundaries

- `src/app/`: application composition.
- `src/features/import/`: bounded JSON/CSV metadata preview and field mapping.
- `src/features/review/`: current single-surface review UI and stories.
- `src/features/jobs/`: job presentation.
- `src/domain/`: framework-free models, local query rules and selection mapping.
- `src/jobs/`: existing job contracts and demo/HTTP adapters.
- `src-tauri/`: native host; one privileged capability boundary.
- `backend/`: CocoIndex pipeline, API, inventory, fingerprints and CLI/TUI.
- `xplorer-copilot-buildkit/`: independent source/reference repositories, not
  runtime dependencies to consume implicitly. Preserve licensing when porting.
- `../casebible/`: original vault/dedup work; separate from application source.

Do not create competing identities in frontend, Weaviate and Surreal. Hash values
describe content assertions, not source-occurrence identity. Imported filesystem
dates do not establish original creation dates. Missing values are not zero bytes.

## Active native workstation commands

The immediate MVP runs from the independent Xplorer fork, not the phase-two
review application below. Its isolated launcher is:

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\xplorer-copilot-buildkit\xplorer-copilot" && pwsh -NoProfile -File scripts/start-intake.ps1
```

The launcher uses loopback port 5176, pinned Rust 1.91.1, one Cargo worker, and
process-local E: build/cache/temp/runtime paths. It does not start the marketplace,
a local model, or a corpus indexer. It refuses an unrecognized process occupying
its port. Native chat uses the remote Portkey route; credentials stay out of Vite.
The filesystem API remains explicitly configured through native
`INTAKE_FILESYSTEM_API_URL`, with its optional token. Browsing does not depend on
that service being configured.

**Verification boundary:** source tests, pinned native Cargo check, executable
build and native startup pass. Windows reports the Intake window responding,
its WebView profile is on E:, and duplicate-runtime launch is rejected. Automated
desktop interaction and live index integration remain unverified; this is not
a claim that the complete MVP has passed acceptance testing. See
`XPLORER-FIRST-2026-09-11.md` for the latest receipt.

For the first interactive check, use the top bar's **Split right** button and the
right rail's **AI Chat** button. **New Chat** in the top bar creates a chat file;
it is not the standalone assistant. The Preview/AI Chat header's **Preview + chat**
toggle displays both with a resizable divider. Each pane retains its own selection;
the active pane supplies chat context. Chat context is metadata-only, but an active
preview may read the selected file, including a remote mounted file.

Use the **left sidebar Search tab** for the combined index. The old right-rail
Content Search/tokenizer is not the new CocoIndex surface. Search remains explicitly
unconfigured until a dedicated Weaviate target and filesystem API are connected.

## Historical phase-two commands from Intake

**Storage prerequisite, owner order 2026-09-11:** development workload storage
belongs on E:, including temporary files, dependency/tool caches and build output.
The source directory alone does not enforce this. Before running commands below,
verify effective tool and child-process paths; do not resume native compilation
with default C: caches. E: is the selected destination, not the earlier suggested D:.
Insufficient E: capacity is a reason to report/coordinate cleanup, never to fall
back to C:. The native fork now has its own E: launcher and copied toolchain/cache;
existing shared C: caches were retained, not moved or deleted. The historical
phase-two commands below do not implicitly inherit the native launcher's setup.

```powershell
npm run test -- --maxWorkers=1
npm exec tsc -- --project tsconfig.app.json --noEmit
npm run dev -- --host 127.0.0.1
npm run backend:test
```

The dev server uses strict port 1420; if occupied, do not terminate another lane.
Tests are scoped to `src/` and exclude nested independent repositories. No command
above should start corpus ingestion. Do not launch backend imports or workers
just to verify the UI. Preserve build outputs rather than cleaning directories.

## Historical phase-two testable slice

Import `fixtures/recovery-inventory.csv`. It is synthetic metadata, not evidence.
Use its imported fields for size, date, store and hash sorting/search. Row titles
and generated cards are not document-content previews. The current search is a
local substring filter, not Weaviate or visual retrieval.

Select rows, filter/sort, and confirm the footer reports visible/hidden selection.
Adding a review tag makes the tag searchable. Grouping remains the existing simple
session overlay, not the completed nested-unit system. Closing/reloading loses
session annotations; durable review sessions and decision export are still open.

## Later integration backlog (not prerequisites for ordinary file operations)

1. Version shared source/representation/unit/assertion and search-result contracts.
2. Bound backend reads, parser memory and concurrency before real corpus runs.
3. Prove docking with Glide/preview and preserve independent pane state.
4. Implement CocoIndex's supported custom Weaviate target and query adapter.
5. Owner-approved small multimodal fixture and remote-provider capability probe.
6. Connect source-resolving previews, facets and neighborhood navigation.
7. Surreal relationship persistence and bounded agent investigation tools.
8. Human-approved operation manifests, stale-source checks and receipts before
   any physical reconstruction/move execution.

Use disjoint file ownership for concurrent lanes. One integrator owns contracts
and dependencies; workers must not change those independently. No corpus-wide
tests, cloud hydration or surprise model services. Record observed results and
unverified boundaries in dated receipts.
