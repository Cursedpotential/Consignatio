# Intake — application contract

Inherits `../AGENTS.md`. Read `AGENT_MEMORY.md` for task-specific context.

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
