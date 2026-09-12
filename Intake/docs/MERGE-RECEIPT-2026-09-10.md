# Directory and plan merge receipt

> Byline: Codex · 2026-09-10

Owner authorized combining the Workbench and CocoIndex application directories and appointed this lane lead developer.

## Changes

- Moved `E:\AI_Workspace\Projects\Propria\casebible\cocoindex-casebible` intact to `E:\AI_Workspace\Projects\Propria\casebible\workbench\backend` after checking resolved paths, absent destination, Git boundary and process command-line references.
- Preserved frontend source location, backend code/tests/environment/outputs and the enclosing Git repository. No compatibility junction was created; old directory references need the new path.
- Repaired the ignored virtual environment's editable source path, which still referenced the older `E:\AI_Workspace\casebible` location. Direct Python module invocation bypasses stale console executable launchers.
- Added Windows backend help/test/lint commands to the existing frontend package, a unified project index, merged specification, HTML overview with three SVG diagrams, and the nested atomic-unit contract.
- Updated current README/planning entry points. Historical receipts and generated data were retained rather than rewritten.

## Verification

- All 33 Git-tracked backend files exist at their mapped destination; zero missing.
- Backend CLI module help: passed from the new directory.
- Backend tests: 11 passed.
- Backend Ruff: all checks passed.
- Frontend tests: 3 files / 11 tests passed.
- HTML local-file link check: zero broken links.
- `git diff --check`: passed; only Git line-ending notices.

## Boundaries and remaining work

No full corpus run, inference call, source hydration, VPS provisioning or external service publication occurred in this merge. No files were deleted, staged or committed. Unrelated repository changes, including the pre-existing `viz/` deletions, were not modified.

Frontend build/native packaging and browser visual verification were not rerun in this merge. SVGs are static planning diagrams. Advanced nested-repository recognition is specified, not implemented by this change. Existing backend tests do not establish the complete new detector contract.

The HTML/specification merge resolves the old browser-only and backend-only plans into one desktop application. Runtime integrations for Weaviate/Surreal/B2/Portkey/Context Forge/Filestash/Whisper and Platform contract reconciliation remain on the unified checklist.
