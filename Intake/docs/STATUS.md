# Implementation status

> _Byline: Codex · GPT-5 · 2026-08-30._

## Implemented in the first slice

- Product and authority-boundary documentation.
- React/Vite application shell.
- Glide Data Grid viewport using stable record IDs.
- Grid/Gallery mode switch.
- Shared sample review set modeled as an existing Immich album snapshot.
- Selection ledger and bulk group/tag actions.
- Source/Proposal/Human provenance rail.
- Storybook configuration and representative stories.
- Tauri host skeleton with an intentionally minimal command surface.
- Backend-job gateway contract with exact record scope and idempotency keys.
- Job-run panel with polling, progress, cancellation, terminal state, and receipts.
- Deterministic browser demo gateway plus opt-in `VITE_WORKBENCH_API_URL` HTTP gateway.
- Local JSON/CSV file import with guarded parsing and actionable validation errors.
- Pre-load schema tape showing inferred type, populated count, and sample per field.
- Imported structured objects projected into dynamic Glide columns with immutable
  source values and separate human annotations.
- User-selected row-title mapping and grid column visibility before import.
- Full source records remain visible in the provenance inspector even when fields
  are hidden from the grid.

## Next

- Saved import profiles and reusable field-mapping presets.
- IndexedDB review-session persistence.
- Undo/redo command history and signed operation receipts.
- Live Immich connector.
- Version-aware PhotoPrism connector.
- UIW opaque-source handoff.
- Registered local-tool manifests and streamed job output.
- Platform implementation of the `/jobs` HTTP contract and authentication.
- Real lazy thumbnail cache and original-byte acquisition.

Nothing in this first slice is production deployment proof or a live media/evidence
integration.

## Verification receipt — structured import slice, 2026-08-30

- `npm run test`: passed, 3 files / 10 tests.
- Parser tests cover quoted CSV commas and line breaks, wrapped JSON arrays,
  inferred columns, and immutable review-record projection.
- `npm run build`: passed, 281 modules transformed.
- `npm run build-storybook`: passed; the existing large-chunk warning remains.
- Source files are read through the browser File API; no upload or backend write
  occurs in this slice.

## Verification receipt — field mapping slice, 2026-08-30

- `npm run test`: passed, 3 files / 11 tests.
- `npm run build`: passed, 281 modules transformed.
- `npm run build-storybook`: passed; the existing large-chunk warning remains.
- Mapping tests prove the selected identifier field becomes the review-row title.

## Verification receipt — backend jobs slice, 2026-08-30

- `npm run test`: passed, 2 files / 7 tests.
- `npm run build`: passed, 279 modules transformed.
- `npm run build-storybook`: passed; the existing Storybook chunk-size warning remains.
- In-app browser visual verification was attempted twice but the local browser webview
  did not attach. No visual or live Platform execution claim is made for this slice.
- The unconfigured browser build uses the demo gateway. A real backend call requires
  `VITE_WORKBENCH_API_URL` and an implementation of `docs/BACKEND-JOBS.md`.

## Verification receipt — 2026-08-30

- `npm run test`: passed, 1 file / 3 tests.
- `npm run build`: passed, 276 modules transformed.
- `npm run build-storybook`: passed.
- Browser inspection: Grid and Gallery rendered with the approved Platform palette;
  selecting a picture updated the persistent selection ledger; bulk grouping assigned
  `G-000020` and updated the Human decision layer; no browser warnings or errors.
- `cargo check --manifest-path src-tauri/Cargo.toml`: blocked before compiling the
  application because the current Windows environment cannot find Microsoft
  `link.exe`. Rust/Cargo are installed; Visual Studio Build Tools with the Visual C++
  workload, or its activated developer environment, remains required for native proof.
