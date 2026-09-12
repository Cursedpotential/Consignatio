# Git repair after owner relocation

Final frontend verification: 3 test files / 11 tests passed. Initial broad discovery
picked up the nested independent Xplorer repository; `Intake/vitest.config.ts` now
restricts collection to Intake's `src` tests. Xplorer files were not modified.

> Byline: Codex · 2026-09-10

Verified repository root: `E:\AI_Workspace\Projects\Propria\Consignatio`.
Application: `Intake/`; corpus backend: `Intake/backend/`.
Original deduplication, metadata, manifests and vault structure: sibling `casebible/`.
The user's physical layout was preserved without further directory moves.

Git history and main branch were intact. The repair remapped existing index entries,
retaining their exact blob IDs and modes: 990 original Case Bible paths, 45 frontend
paths and 33 backend paths. Git reports all 1,068 as R100 exact renames. No new evidence
contents were staged; existing working-file edits remain unstaged. No commits or
pushes were performed. Twelve pre-existing viz deletions were left untouched.

The original index is backed up at
`.git/index.before-intake-rename-20260910T153441434505Z`.
The repair utility is `Intake/docs/repair_relocated_index.py`; its default is dry-run,
and it refuses to run over staged changes. It must not be reapplied to the current
staged migration.

Updated active repository guidance and relocated ignore rules, plus the ignored Python
editable-install path. Historical receipts retain old paths. The workbench package/CLI
identifiers are compatibility names; the product is Intake. Global app project shortcuts,
external workers and historical absolute paths were not rewritten by this repair.

Validation: Git resolves the new root; 1,068 exact renames; backup/output/nested-project
ignore checks pass; backend tests pass (11). Frontend test result is reported with the
delivery response. No database reads or corpus processing were used for this repair.
