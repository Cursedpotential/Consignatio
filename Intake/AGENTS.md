# Intake — application contract

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: record three-system boundary | Context: explicit owner clarification -->

**Owner decision — 2026-09-12:** CCC means project-local CocoIndex Code indexes only. Intake is the multifaceted CocoIndex-based filesystem workstation, using Weaviate for advanced search and SurrealDB for relationships, with multimodal tools/libraries (OCR, STT, video transcription/processing, advanced SLM extraction/classification). Docstore is CocoIndex + SurrealDB for project documentation. Keep their apps, tracking state, locks, configuration and target ownership isolated; shared technology is not a shared runtime. This defines scope, not proof every feature is implemented.

See [CCC / Intake / Docstore boundaries](../../SYSTEM-BOUNDARIES.md) for indexing eligibility, duplicate provenance and the human-agent organizing workflow.

Inherits `../AGENTS.md`. Read `AGENT_MEMORY.md` for task-specific context.

The organizing workflow is find → group → compare → decide → move, with a
selection-aware agent beside the human. Index readable unique content before
classification or evidence acceptance. Retain metadata/status for unknown,
unsupported, broken, empty and unhydrated entries without incidental hydration.
Exact copies may share content processing, but preserve every occurrence and its
provenance. Different formats, independent exports/devices and corroborating
copies stay distinguishable. Downstream exclusion does not require removal from
the organizing index. Deduplication never grants deletion authority.

- One React application and one Tauri host; backend stays in `backend/`.
- `src/app/` composes features. `src/features/` owns UI workflows. `src/domain/`
  holds framework-free identities and rules. External effects stay in adapters.
- Never directly connect the renderer to privileged database credentials.
- Source, machine proposal and human annotation remain separate. Review status
  is not legal acceptance or authorization to move/delete source files.
- CocoIndex remains the pipeline; Weaviate serves advanced vector search;
  SurrealDB serves the graph; Lance and Parquet are distinct lake outputs to B2.
- Xplorer is the immediate native file-manager implementation under
  `xplorer-copilot-buildkit/xplorer-copilot/`. Build and verify that desktop;
  the imported metadata review UI is phase two, not its replacement.
  Preserve the independent repository boundary, license and provenance.
- The filesystem CocoIndex app and its dedicated Surreal filesystem graph are
  separate from downstream evidence indexing/analysis and its database. Indexes
  assist ordinary browsing and organization; they are not approval prerequisites.
- Run frontend commands here, not at the Vault root. Keep tests scoped to this
  application's source so they do not recurse into independent child projects.
- Do not use `ccc` as this application's launch/index command. Keep instance
  identifiers, ports, state and worker limits explicit and isolated.
