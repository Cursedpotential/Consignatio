---
scope: E:/AI_Workspace/Projects/Propria/Consignatio
status: current
verified_at: 2026-09-10
contains_secrets: false
---

# Consignatio — progressive project router

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: record three-system boundary | Context: explicit owner clarification -->

**Owner decision — 2026-09-12:** CCC means project-local CocoIndex Code indexes only. Intake is the multifaceted CocoIndex-based filesystem workstation, using Weaviate for advanced search and SurrealDB for relationships, with multimodal tools/libraries (OCR, STT, video transcription/processing, advanced SLM extraction/classification). Docstore is CocoIndex + SurrealDB for project documentation. Keep their apps, tracking state, locks, configuration and target ownership isolated; shared technology is not a shared runtime. This defines scope, not proof every feature is implemented.

See [CCC / Intake / Docstore boundaries](../SYSTEM-BOUNDARIES.md) for indexing eligibility, duplicate provenance and the human-agent organizing workflow.

This file routes context; it is not a transcript store or automatic memory job.
Load only the relevant lane. Parent routing is in `../AGENT_MEMORY.md`.

| Work | Read next |
|---|---|
| Intake application | `Intake/AGENTS.md`, `Intake/AGENT_MEMORY.md` |
| Original dedup, metadata, vault structure | Existing material under `casebible/`; inspect local instructions and exact files before changing them |
| Git relocation | `Intake/docs/GIT-RELOCATION-RECEIPT-2026-09-10.md` |
| Xplorer absorption | `Intake/docs/DEVELOPMENT.md`; child instructions before working inside either independent Xplorer repository |

Consignatio is the Vault project; Intake is its application. The original
`casebible/` work remains a sibling of Intake. Do not fold it into the frontend.
Docstore, Probata custody, global MemSearch and `ccc` are separate lanes.
Historical receipts preserve old paths; current run commands use this layout.
