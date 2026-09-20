# Source-preserving catalog reconciliation and recovery specification

Byline: Codex | 2026-09-20 | Owner direction: preserve the live catalog, correct it, find the best sources

## Outcome and boundary

The existing `casebible.raw_duck` catalog remains the source of historical facts.
An additive generation links those facts to observed B2 object versions and creates
an item-level recovery queue. The system must answer where an item came from,
which exact stored versions support it, what remains unverified, and what source
metadata could improve it. Existing merge/trunk decisions are claims to reassess.

The authorized first slice captures metadata, produces immutable Parquet snapshots,
provides SQL views, and publishes new dated metadata facts. It does not copy source
content, remove objects, hydrate cloud placeholders, change lifecycle rules, flatten
exports, run content indexing, or authorize R2 retirement.

## Identity and lineage contract

| Record | Required distinction |
|---|---|
| Source occurrence | Source/account, scope, provider ID, original path, original timestamps and complete available provider metadata |
| Physical object version | Bucket, exact key, provider file ID, action, size, algorithm-labelled hash, upload time, object metadata and visibility observation |
| Content identity | Algorithm plus digest plus size; missing or conflicting identities remain unresolved |
| Representation | Native item, exported Office/PDF, recovered carve, copy, thumbnail, conversion or other derivative; preserve its parent/source claim |
| Package | Atomic export/container root, manifest and member records; assess completeness without flattening |
| Assessment | Evidence-backed availability, provenance/quality flags, BAS candidates, reason and unresolved checks |

The same SHA does not erase separate occurrences. Path/size/mtime matching alone
is a lead, not exact-byte proof. Existing MD5-to-SHA1 bridges remain explicitly
catalog-derived evidence, distinguishable from direct B2 hash metadata. Reuse
existing SHA-256 ledgers before proposing new content hashing. Hashes establish
byte identity only within their algorithm's limits, not authenticity or metadata
completeness. No semantic-twin inference is made by this first slice.

## Generation and publication

1. Capture each selected live table using a read-only database session; retain
   its exact query, observed interval, row count and artifact SHA-256.
2. Capture current B2 names, all versions, hide/start markers, unfinished files
   and uploaded parts using metadata-only APIs. Retain every provider record.
3. Verify visible file IDs also exist in the all-version listing. Record observation
   windows; these listings and sequential table captures are not one atomic snapshot.
4. Resolve current-path, current-elsewhere, historical-version, conflicting and
   unresolved identities without selecting a retained copy by size.
5. Preserve native export ID maps, package membership and alternative historical
   routing claims. A disagreement is visible, never silently overwritten.
6. Require fingerprints, occurrence conservation, unique IDs and work-item
   conservation before publication. Load a generation in one PostgreSQL transaction.
7. Read back table counts and representative SQL results before reporting success.

The new dated `raw_duck.reconcile_*_20260920` tables hold immutable observations.
`catalog_reconcile` views select the most recently published validated generation.
Local Parquet is independently queryable through `catalog.duckdb` views. The live
catalog does not depend on that local DuckDB database. Historical captures remain.

## Quality buckets and BAS rules

Every claim carries evidence and an uncertainty state. Use these buckets only
when supported: source-native/original candidate, verified copy, derived/unverified,
orphaned derivative, malformed/partial, metadata-stripped/suspect, unknown. “Verified
copy” requires byte evidence plus a proven source link; an old integrity `ok` is not
proof of source-native status. The first slice reports flags and defaults to unknown
instead of inventing a definitive classification.

BAS #1 must be chosen using source occurrence proof, structural completeness,
metadata completeness, source-native representation and usable content. BAS #2 is
retained when it adds material provenance, timestamps, platform IDs, sidecars,
container context or content missing from #1. Both need a specific justification.
If either choice is unsupported, it remains unassessed. Larger byte count and
directory-name twins cannot decide BAS. Export/package boundaries are retained.

For possible byte twins, inspect embedded and occurrence metadata separately.
For semantic twins, preserve representations and do not equate resemblance with
identity. Recovered files with plausible signatures can still be over-carved,
zero-filled or partial; the restricted `recup_dir.N` scan cannot certify all recovery.

## Targeted recovery order

| Priority | Task | Evidence required before acquisition |
|---|---|---|
| 1 | Repair links to already retained historical B2 versions | Exact version ID, matching hash/size and source occurrence; no source re-pull |
| 2 | Reconcile native Google export maps and original file IDs | Source ID metadata, export receipts, Office/PDF identities and source availability |
| 3 | Investigate unresolved R2 identities | Existing SHA-256 ledger, exact B2 versions, original R2 metadata and package membership |
| 4 | Compare recovered copies with OD/GD/local originals | Original path/ID, timestamps, sidecars, EXIF inventory and structural-quality evidence |
| 5 | Verify atomic exports and complementary metadata | All members, manifests, sidecars and parent/container context |

Provider probes must be bounded and metadata-only. Google Drive uses explicit file
IDs in the two known accounts. OneDrive probes must not hydrate placeholders.
Local probes are restricted to named paths from the queue. Missing access is an
access limitation, not evidence of data loss. A provider capability census records
unavailable permissions/fields so partial metadata is never labelled complete.

No R2 item is safe to retire until exact B2 equivalence, occurrence metadata
preservation, required complementary material and package completeness are
demonstrated. This first generation explicitly clears zero retirements.

## Unverified historical outputs

`timeline_mvp` Parquet, `chat_events_20260918`, partial Weaviate projections,
Surreal relationship projections, prior trunk recommendations, recovery-integrity
statuses and prior deletion claims remain UNVERIFIED for canonical/BAS selection.
Their existence or row counts do not validate their provenance or completeness.
They may be linked as historical artifacts without promoting their conclusions.

## Acceptance and remaining work

First-slice acceptance: reproducible metadata capture, complete frozen occurrence
records, matching evidence linked to explicit versions, preserved package records,
an item-level recovery queue, queryable local/live views, and successful read-back.

Full source-quality acceptance is later and separate: metadata capability census,
targeted provider verification, representation lineage, structural validation,
evidence-backed BAS #1/#2 decisions and package-completeness checks. All unfinished
assessments remain explicit in the queue. No migration replaces historical facts.

## Verified query engine amendment

Byline: Codex | 2026-09-20 | Owner clarification: PostgreSQL is intended to have pg_duckdb

The live database has pg_duckdb 1.1.0 with embedded DuckDB v1.4.3, verified by
actual DuckDBScan execution over reconciliation facts. PostgreSQL remains the
authoritative catalog. Use transaction-local DuckDB execution for compatible
analytics; keep PostgreSQL-specific JSON views and transactional controls on their
supported native path. Do not force every application connection through DuckDB.
The local Parquet/DuckDB generation is an inspection and reproducibility artifact.
Direct server-side access to B2 Parquet remains a separate capability check; the
engine execution test does not claim that connection has been validated.
