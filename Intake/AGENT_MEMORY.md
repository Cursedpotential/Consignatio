# Intake — progressive context router

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: record three-system boundary | Context: explicit owner clarification -->

**Owner decision — 2026-09-12:** CCC means project-local CocoIndex Code indexes only. Intake is the multifaceted CocoIndex-based filesystem workstation, using Weaviate for advanced search and SurrealDB for relationships, with multimodal tools/libraries (OCR, STT, video transcription/processing, advanced SLM extraction/classification). Docstore is CocoIndex + SurrealDB for project documentation. Keep their apps, tracking state, locks, configuration and target ownership isolated; shared technology is not a shared runtime. This defines scope, not proof every feature is implemented.

See [CCC / Intake / Docstore boundaries](../../SYSTEM-BOUNDARIES.md) for indexing eligibility, duplicate provenance and the human-agent organizing workflow.

| Task | Read |
|---|---|
| Resume after 2026-09-11 model/usage handoff | `docs/HANDOFF-2026-09-11-INTAKE-NATIVE-AND-INDEX.md` — native desktop running; Weaviate8082 settled, old8081 retired; exact next live proof |
| Start development, commands, module boundaries | `docs/DEVELOPMENT.md` |
| Immediate file-manager work and native bootstrap | `docs/XPLORER-FIRST-2026-09-11.md`; native fork's local instructions |
| Settled filesystem graph vs evidence separation | `docs/DEVELOPMENT.md`, section "Filesystem index and graph"; original cookbook row `meeting_notes_to_surrealdb_graph` in the system-design HTML |
| Full product expectations and priorities | `backend/docs/UNIFIED-WORKBENCH-PLAN.md`, `backend/docs/MASTER-TODO.md` |
| Visual plan | `backend/docs/UNIFIED-WORKBENCH-PLAN.html` |
| Nested atomic units | `docs/ATOMIC-UNITS.md` |
| Document handling and dedup | `backend/docs/DOCUMENT-HANDLING-AND-DEDUPE.md` |
| Current structure and integration boundaries | `docs/UNIFIED-PROJECT.md` |

Load exact relevant files, not the entire plan collection for every change.
Run receipts are in `docs/`. Source/evidence data does not belong in this router.
