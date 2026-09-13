# Live graph projection proof — 2026-09-12

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: add completed populated restore proof | Context: final live verification -->

## Real writes and replay

Dedicated endpoint: https://surreal-intake.tilapia-skilift.ts.net,
namespace/database consignatio/intake, database-scoped intake_runtime account.
No object copies, B2 writes, source-object reads, corpus rescans or OneDrive access.

### Synthetic integration fixture

Generated three explicitly synthetic source files and native Parquet artifacts
under `E:/AI_Workspace/.tmp/intake-graph-live-20260912-02/` using
`scripts/graph_live_fixture.py`. No prior files overwritten.

Snapshot key:
`intake-inventory-projection-v1:2dae26992a0d92667f3892634a061f55a72ee970a39e5dd5837e5813ec93c173`.

Live apply and replay succeeded. Verified 3 occurrences, 1 store, 1 completion
edge; the hashed occurrence has 2 neighborhood edges (store + content). Explicit
null metadata keys survive the round trip. Two occurrences share one actual
SHA-256 identity; the deliberately unhashed occurrence has no content assertion.

The first fixture at `.../intake-graph-live-20260912-01/` is retained. Its snapshot
`intake-inventory-projection-v1:2937ae71168816b88094c66cd563b3781d66b0ba200f833c5a0c284ed454a3fd`
exposed an SDK defect: Python None is encoded as Surreal NONE, removing nested
metadata keys. First load returned completed, but strict replay correctly failed.
This is synthetic test data, not evidence, and was not silently repaired/deleted.

The serializer now binds explicit nulls with CBORSimpleValue(22), including CAS
expected documents. Source dictionaries and strict symmetric comparisons are
unchanged. Wire-level regression tests distinguish tag6 NONE from CBOR NULL.

### Historical cloud metadata

Read-only PG transaction exported 25 rows from raw_duck.r2_files, restricted to
historical R2 atomic-hint index membership. Exact bucket/path exclusions applied
for rootcsv.isolated_credentials and rootcsv.excluded. The query reads metadata
only and is recorded verbatim in the manifest. It does not run a detector.

Manifest: `E:/AI_Workspace/.tmp/intake-legacy-graph-20260912-01/manifest.json`.
SHA-256: `92d7e66371f8c557b0276c004be352ec09bec806193b46f9189689aec2d4558d`.
Source: ovh-files PG container fgz1n7useplhk0t91uk7k1aw, database casebible.
Script: `scripts/export_legacy_graph_probe.py`, read-only transaction +20s SQL timeout.

Snapshot key:
`intake-legacy-catalog-projection-v1:92d7e66371f8c557b0276c004be352ec09bec806193b46f9189689aec2d4558d`.

Live apply: 25 occurrences, 1 store, 0 new content records. Live replay instrumented
the query boundary: zero CREATE/UPDATE/UPSERT/RELATE statements. All 25 original
catalog-row dictionaries matched the input exactly, including nulls and original
keys. Verified 25 stored_at edges, 0 occurrence_has_content edges and 1 completion
edge for this snapshot.

MD5 remains historical metadata, not SHA-256 identity. Naive modtime stays original
text; no source timezone, nanosecond timestamp or symlink state is invented.
observed_at explicitly means catalog-import observation time, not source observation.
The historical catalog is NOT the current object census. Full corpus loading and
live manifest reconciliation remain open.

## Tests

Primary agent independently ran all 104 backend tests successfully with TEMP/TMP
on E:. Scoped Ruff passed for projection modules, probe scripts and related tests.
Existing Starlette/httpx deprecation warnings remain; they did not fail tests.

## Backup/restore follow-up

Populated native export succeeded:
`/data/consignatio/backups/surreal-intake/consignatio-intake-20260912T155132Z.surql`,
114329 bytes, SHA-256
`0e6d89ac5bee600c4504aa402c7ff5af3339c3e1c393a861ab60925a0addcf95`.

Checksum verification passed, but import into fresh
restore_drill_graph_20260912/restore_drill_graph_20260912 failed because an enforced
relationship referenced a projection_snapshot not imported yet. The original export
already contains OPTION IMPORT. This is the documented pre3.3.0 ordering defect;
schema-only restore previously could not reveal it. Live consignatio/intake was
not touched. Failed drill and original backup remain retained.

A dependency-ordered derived restore copy was implemented and deployed without
relaxing schema enforcement or replacing the original backup. The helper preserves
the complete multiset of 261 SQL statements, ordering normal records before
relations and resolving relation dependencies. Unknown syntax/cycles fail closed.
The pre3.3 ENFORCED import issue is also documented in the
[official SurrealDB reference](https://surrealdb.com/docs/reference/query-language/statements/define/table#using-enforced-to-ensure-that-related-records-exist).

Fresh restore into restore_drill_ordered_20260912/restore_drill_ordered_20260912
completed with no import errors and 33 tables. `scripts/verify_graph_restore.py`
compared every table's record count and SHA-256 of ordered logical records against
live consignatio/intake: zero mismatches. This includes all relation records,
not merely vertices/schema. Counts include 31 occurrences (25 historical +6
synthetic), 3 stores, 1 content, 31 stored_at, 4 occurrence_has_content and 3
produced_by edges; remaining empty tables were compared too. This proves small
populated-dataset restore, NOT full-corpus-scale recovery.

Derived artifact SHA-256:
`d9f79489aacb44dff520b94ba5779cf17dc2bcdc29410f6374b271dbcc2944fc`.
It and its ordering receipt are retained adjacent to the original backup, with
the fresh drill namespace/database in the filename. The previous restore script
is retained at `/data/consignatio/to_be_deleted/surreal-restore-pre-order-20260912/`.
Both failed and successful drill databases remain retained. Native exports include
user password hashes; treat entire exports as sensitive and never dump headers.

CLI: `python -m casebible_index.cli graph-project-catalog <manifest>` validates;
`--apply` explicitly writes historical observations. No transfer is started.

## Concurrent EOD lane

See [atomic-rule/table handoff](ATOMIC-EOD-HANDOFF-2026-09-12.md). That task owns
exact-byte copy/dedup, B2 and occurrence manifests. This task owns graph integration
and existing atomic-boundary contracts, not final sorting or evidence acceptance.
The atomic/graph contract and occurrence-map adapter instructions were delivered
to coordinating task `01a09338-1c1a-7212-beda-5ebe94fb3099` after crash recovery.
That message did not authorize transfer changes or graph writes by the other task.

## Migration occurrence-map alignment

Added an opt-in, hash-bound adapter for the concurrent migration's generated
occurrence-content-map JSONL. The migration builder produced a retained synthetic
generation at `E:/AI_Workspace/.tmp/intake-migration-bridge-20260912-01/`.
Live snapshot
`intake-r2-b2-occurrence-map-v1:96a5001340f030930c393bbf2738a2e6fd6f6e198f68cf15c020c7007ee758af`
contains three occurrences, one store, one verified content, three stored_at, two
content links and one completion edge. Replay issued zero writes. A `junk/` path
was retained normally. Held/unverified content has no exact-content edge.

See [occurrence-map contract](R2-B2-OCCURRENCE-GRAPH-CONTRACT-V1.md). No completed
real migration generation existed locally during this check; no transfer/B2 state
was mutated, and real-generation reconciliation remains open.
