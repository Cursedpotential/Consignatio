# Intake — unified application

> Byline: Codex · 2026-09-10

Project directory: `E:\AI_Workspace\Projects\Propria\Consignatio\Intake`.

**Current layout after owner relocation:** the Git/Vault project root is `Consignatio/`;
the application is `Intake/`, its backend is `Intake/backend/`, and original dedup,
metadata and vault-structure work is preserved in the sibling `casebible/` directory.
This verified layout supersedes the earlier location check below. Historical move
receipts retain the paths that applied when they were written.

## Owner naming and location decision

As of 2026-09-10, **Intake** is the name of the desktop work surface and its combined frontend/backend application. **Consignatio** is the Vault project, whose owner-designated location is `E:\AI_Workspace\Projects\Propria\Consignatio\`. Use “Vault” for the user-facing storage/project role and “Consignatio” for the project name and location.

Intake searches, reviews, classifies and prepares intake/organization operations over Vault sources. The Vault location is distinct from application code, runtime caches, provider state and generated search projections. Source acquisition and relocation still use their defined scope and receipts.

The designated Consignatio directory was not present at the time of this read-only location check. No vault data or application directories were moved for this naming update. The application source remains at the project directory above until its final source location is established. Existing Case Bible package IDs and `casebible-corpus` CLI names remain compatibility identifiers pending an explicit, tested naming migration; they do not change the Intake product name.

The owner appointed this development lane to lead the combined product and authorized directory consolidation. The existing frontend stays here; the complete former `cocoindex-casebible/` application is now `backend/`. No source files, environments or outputs were deleted. Git history remains in the enclosing Case Bible repository. Unrelated repository changes are untouched.

## Planning index

- [Visual plan and diagrams](../backend/docs/UNIFIED-WORKBENCH-PLAN.html)
- [Full merged feature list, priorities, development guide and TODO](../backend/docs/UNIFIED-WORKBENCH-PLAN.md)
- [Backend master TODO](../backend/docs/MASTER-TODO.md)
- [Detailed backend architecture](../backend/docs/CASEBIBLE-CORPUS-BACKEND-SYSTEM-DESIGN.html)
- [Document handling, deduplication, Filestash and classification](../backend/docs/DOCUMENT-HANDLING-AND-DEDUPE.md)
- [Nested atomic-unit contract](ATOMIC-UNITS.md)

## Commands

From this directory, `npm run test`, `npm run build`, and `npm run build-storybook` address the frontend. Windows commands `npm run backend:test`, `npm run backend:lint`, and `npm run backend:help` use the relocated backend interpreter directly. They do not index a corpus or start a service.

The moved virtual environment can contain absolute console-script and editable-install paths. Verification must check imports from `backend/src` and run the actual CLI module before claiming relocation works. Generated outputs can retain historical source/artifact paths; preserve them as receipts, not silently rewritten data. Fresh runtime configuration must use the new location and per-instance state.

## Ownership

Lead owns contracts, architecture, integration and backend delivery. Frontend work can be assigned under `src/`, `.storybook/` and `src-tauri/` after an explicit file scope is recorded. No separate frontend agent was launched as part of the directory move. Docstore, Platform custody, global memory tooling and `ccc` remain external lanes.

The earlier backend-only exclusions are superseded by the merged product plan. Existing runtime implementations remain partial; directory consolidation is not proof that remote integrations are operational.
