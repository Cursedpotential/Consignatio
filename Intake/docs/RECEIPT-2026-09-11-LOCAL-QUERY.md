# Local metadata query and selection receipt

## Implemented

- Verified the previously interrupted frontend restructure with 12 baseline tests.
- Added framework-free metadata query and visible-selection functions.
- Wired local filename/size/imported-field sorting and direction controls into
  the existing review surface. Unknown values sort last in both directions.
- Search includes imported keys/values, source references and checksums, human
  tags/notes/status, and proposal tags. It does not mutate source values.
- Recomputed grid selection from IDs after filtering/sorting; edits to visible
  rows preserve hidden selections. Clear explicitly clears the entire selection.
- Fixed missing source-reference handling in grid cells.
- Added synthetic eight-row inventory covering seven store labels and candidate
  alternate formats/archive/sidecars/zero-byte/unavailable cases.
- Added the missing development guide and durable owner priority/handler gate.

## Verification

`npm run test -- --maxWorkers=1`: 4 files, 19 tests passed on 2026-09-11.
Includes query/source immutability, numeric and natural ordering, imported metadata,
unknown size, overlays, and ID-based hidden-selection behavior.

`npm exec tsc -- --project tsconfig.app.json --noEmit`: passed, exit 0.
`npm exec vite -- build --outDir dist/verification-20260911-local-query --emptyOutDir false`:
passed, 282 modules; output isolated without cleaning older build artifacts.
`git diff --check -- src backend/docs/MASTER-TODO.md docs`: passed.

This receipt does not establish browser interaction, packaged native execution,
remote indexing, Weaviate, Surreal, actual file previews or multi-pane operation.
No evidence reads, cloud hydration, new handlers, services, installs or commits.
The prior staged relocation and unrelated changes were preserved.
