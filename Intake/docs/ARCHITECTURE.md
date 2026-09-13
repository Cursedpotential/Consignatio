# Architecture

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: record three-system boundary | Context: explicit owner clarification -->

**Owner decision — 2026-09-12:** CCC means project-local CocoIndex Code indexes only. Intake is the multifaceted CocoIndex-based filesystem workstation, using Weaviate for advanced search and SurrealDB for relationships, with multimodal tools/libraries (OCR, STT, video transcription/processing, advanced SLM extraction/classification). Docstore is CocoIndex + SurrealDB for project documentation. Keep their apps, tracking state, locks, configuration and target ownership isolated; shared technology is not a shared runtime. This defines scope, not proof every feature is implemented.

See [CCC / Intake / Docstore boundaries](../../../SYSTEM-BOUNDARIES.md) for indexing eligibility, duplicate provenance and the human-agent organizing workflow.

> _Byline: Codex · GPT-5 · 2026-08-30._

## Runtime layers

```text
Tauri desktop host
├── React application
│   ├── Workbench shell
│   ├── Glide grid viewport
│   ├── media contact sheet
│   ├── provenance inspector
│   └── selection ledger
├── review-domain core
│   ├── immutable sources
│   ├── annotation overlays
│   ├── group hierarchy
│   ├── undoable commands
│   └── receipts
├── dataset adapters
│   ├── JSON / CSV
│   ├── DuckDB / IndexedDB
│   └── paged Platform queries
├── media connectors
│   ├── Immich
│   └── PhotoPrism
└── permissioned native commands
    ├── filesystem acquisition
    ├── registered scripts
    └── governed UIW handoff
```

## Ownership rules

Glide owns viewport rendering, cell interaction, keyboard navigation, and visible
selection. TanStack may own selected headless state and client-side row processing.
It must not materialize millions of full row objects merely to feed Glide. Large
datasets use an adapter that maps visible row indexes to stable record IDs.

The React UI can run in an ordinary browser for design and tests. Privileged file,
credential, network, and process operations exist only behind Tauri commands with
explicit capabilities.

## State flow

```text
SourceAdapter ──> immutable source records
                         │
ProposalAdapter ──> proposal overlay
                         │
CommandBus ───────> human annotation overlay ──> operation receipt
                         │
                         ├── Glide viewport
                         ├── Gallery viewport
                         └── Provenance rail
```

## Canonical boundary

Workbench state is a review-session projection. Platform PostgreSQL and governed
custody workflows remain canonical. An accepted Workbench operation can prepare an
intake request, but only the Platform workflow acquires bytes, previews the hash and
metadata, persists the decision, and promotes context to evidence.

## Tool runner boundary

Tools are registered by trusted manifests. A manifest fixes the executable,
argument schema, working-directory policy, allowed paths, network policy, timeout,
confirmation level, and receipt behavior. Imported data may populate typed argument
values; it can never select an executable or inject raw command text.

## Backend job boundary

The React/Vite interface invokes backend work through a `JobGateway`. A request
contains a fixed job kind, the review-set ID, an exact list of stable record IDs,
an idempotency key, and a request timestamp. The backend returns a durable run ID;
the Workbench polls that run and displays queued, running, succeeded, failed, or
cancelled state plus the final receipt.

`VITE_WORKBENCH_API_URL` selects the HTTP gateway. With no configured endpoint,
the browser and Storybook builds use the deterministic in-memory demo gateway.
The demo proves interaction only; it is not backend or workflow execution proof.

The concrete HTTP schema is documented in `BACKEND-JOBS.md`.
