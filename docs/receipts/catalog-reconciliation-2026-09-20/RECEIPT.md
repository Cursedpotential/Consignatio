# Catalog reconciliation: verified implementation receipt

Byline: Codex | 2026-09-20 | Generation: `2c2ae40f-bc6a-43c6-83a7-f3d60319e4d3`

The first additive reconciliation layer is live in PostgreSQL and queryable from local Parquet. This verifies metadata linkage and conservation, not universal source quality or deletion safety.

## Live result

- PostgreSQL: `ovh-files-ts`, database `casebible`, new dated `raw_duck.reconcile_*_20260920` facts and `catalog_reconcile` views.
- Local SQL: `generation-02/catalog.duckdb`, reading immutable metadata Parquet.
- New PostgreSQL metadata relations occupy 6,413,991,936 bytes including indexes. The host had approximately 20 GiB available after publication; future full generations need a storage budget.
- Existing catalog tables and all source content were retained. No source downloads, uploads, deletions, moves, lifecycle changes or content indexing occurred.
- 1,567,456 source occurrences and 1,279,556 R2 catalog occurrences preserved.
- 568,069 B2 version records; 146,246 item-level review tasks.
- 1,560 native Google source IDs mapped to 1,560 Office and 1,560 PDF representations, all found in visible B2 objects by hash and size.
- 24 native source IDs checked directly in the two known Google accounts: all accessible and not trashed. These are provisional source-native BAS #1 candidates; content completeness and original authorship are not proved.
- No BAS #2 decision or R2 retirement was cleared. Complementary representations remain preserved for review.

## Current B2 inventory

| Top-level prefix | Visible objects | Visible bytes |
|---|---:|---:|
| `consignatio` | 554,496 | 2,204,633,176,441 |
| `db_backups` | 24 | 27,119,210 |
| `infra-backups` | 6 | 13,493,889 |
| `_intake-engine-test-20260917` | 15 | 564,894 |
| `(root)` | 1 | 55,639 |
| `intake-catalog-added` | 11 | 0 |

Total: **554,553 objects / 2,204,674,410,073 bytes**.
Noncurrent uploaded versions: **6,749 / 10,563,715,232 bytes**. Hide markers: **6,760**. Unfinished large files: **7 files / 20 parts / 387,129,237 bytes**. All uploaded versions plus unfinished parts: **2,215,625,254,542 bytes**.

Hash/size groups with repeated visible storage: **40,479 groups**, **41,508 extra paths**, **30,260,018,805 repeated bytes**. These are physical-storage findings, not disposal instructions. Occurrence metadata remains independently important.

**Hash coverage limit:** 37 visible objects, totaling 337,987,455,100 bytes, lack a usable SHA-1 in B2 metadata. The repeated-byte figure covers supported SHA-1/size identities; it is not a complete dedupe certificate for those large objects. Existing MD5/version-ID and SHA-256 receipts remain recovery leads.

## PostgreSQL DuckDB engine

The live `casebible` database already has **pg_duckdb 1.1.0**, with embedded **DuckDB v1.4.3**. A read-only execution test produced `Custom Scan (DuckDBScan)` and the expected 12 native candidates in each Google account. No installation, restart or global configuration change was required.

`casebible/catalog_reconcile/analytics.py` provides named analytics queries with transaction-local DuckDB execution. PostgreSQL remains the authoritative store. The local DuckDB file is an additional inspection artifact. Direct B2/Parquet access from the server has not yet been certified. Some PostgreSQL-specific JSON functions require the native PostgreSQL path; this is why execution is selected per analytics session rather than forced globally. See the [version-matched pg_duckdb functions documentation](https://github.com/duckdb/pg_duckdb/blob/v1.1.0/docs/functions.md).

## Coverage

| Source occurrence availability | Rows |
|---|---:|
| `historical_exact` | 1,450 |
| `no_usable_identity` | 73,318 |
| `visible_exact_elsewhere` | 4 |
| `visible_exact_path` | 1,492,684 |

The 1,450 historical matches retain exact B2 version IDs. They must not be mistaken for missing source bytes. The no-usable-identity bucket includes native Google items and old exclusions; it is not a loss count. Native/export representation links live separately in `native_exports`.

| R2 catalog linkage | Rows |
|---|---:|
| `historical_catalog_link` | 937 |
| `unresolved` | 28,069 |
| `visible_catalog_link` | 1,250,550 |

R2 links use the recorded MD5/SHA1 bridge or exact recorded B2 version IDs with matching key/size. R2 was not re-inventoried live in this slice. Original occurrence metadata and package completeness still require review.

## Recovery worklist

| Task | Priority | Items |
|---|---|---:|
| `native_export_linkage_conflict` | high | 1,560 |
| `native_source_metadata_check` | high | 1,560 |
| `package_completeness` | high | 608 |
| `r2_identity_review` | review | 29,006 |
| `recovery_quality_and_provenance` | high | 3,041 |
| `recovery_quality_and_provenance` | review | 37,263 |
| `relink_historical_version` | high | 1,450 |
| `unresolved_occurrence` | review | 71,758 |

Full item-level evidence is in `generation-02/recovery_worklist.csv` and Parquet, and in the live `recovery_worklist` view. Multiple tasks can refer to one artifact; these counts are not unique files.

## Provenance and quality

| Bucket | Evidence and limitation |
|---|---|
| Source-native/original candidate | 24 live Google native observations support provisional native representation candidates; original authorship and content quality remain unverified. |
| Verified copy | Byte-link evidence is recorded separately from provenance. No blanket copy-quality approval was issued. |
| Derived/unverified | 3,120 mapped Office/PDF export representations have visible B2 identities; native source equivalence is not inferred. Timeline and search projections remain UNVERIFIED. |
| Orphaned derivative | No derivative is declared orphaned from an absent direct link alone; parent/source relationships require further checks. |
| Malformed/partial | Legacy recovery manifest has 861 fail and 2,180 unsupported entries, all queued for review. These are historical claims, not new content tests. |
| Metadata-stripped/suspect | Thin local metadata and anomalous dates are flags. Missing catalog metadata is not proof that embedded file metadata was stripped. |
| Unknown | Unresolved identities, untested structure, unsupported formats and incomplete provider metadata remain explicit. |

Preserved package metadata: 608 atomic roots / 128,834 membership records; 542 export units / 499,712 membership records; 711 vault units. The 40,304 recovery records and 33,685 integrity holds are also frozen in Parquet. The old limited recovery scan and largest-trunk proposals do not establish BAS.

## Historical artifacts: UNVERIFIED

- `timeline_mvp_20260918`: two payloads plus directory marker; 101,009,949 visible bytes. No content read or canonical acceptance.
- `chat_events_20260918` and related provenance tables: retained historical outputs; row counts are in the exact catalog inventory.
- Weaviate and Surreal outputs: historical projections, not completeness or source-quality authorities. This publication does not rebuild or certify them.
- Prior twin merge decisions, restricted recovery-quality conclusions and reported recovery-image deletions remain unverified as retention decisions.

## Verification and limits

- 10 safety tests passed, including replacement versions, missing hash/size, occurrence preservation, duplicate version rejection and disallowed B2 APIs.
- PostgreSQL schema compiled in a rollback-only transaction before publication.
- Capture fingerprints, unique identities, row conservation and visible-to-version coverage passed.
- Publication was atomic; every new table count was read back. Additional live view checks are recorded in `live-verification.json`.
- The detailed live availability aggregation matched the generation counts. The operational summary now reads those validated counts; its read-back took approximately one second including SSH. A dedicated availability lookup index supports targeted occurrence review.
- Exact pre-publication counts for 238 user tables/views and 2,305 catalog fields are preserved. Two DuckDB extension tables are excluded from exact-count scope.
- PostgreSQL captures and paginated B2 listings have observation windows; they are not a cross-provider atomic snapshot.
- Initial `generation-01` timed out during its first export and remains preserved but unpublishable.
- Google probes cover 24 named IDs, not all 1,560 natives. Permissions/revision histories were not enumerated. No new OD/local/R2 content acquisition occurred.

## Next recovery work

Use the recorded source IDs and version links to finish metadata capability checks, compare original timestamps/EXIF/sidecars/container context, resolve R2 identities using existing SHA-256 receipts, and assess package completeness. Only then make evidence-backed BAS #1/#2 decisions or propose acquisitions. All R2 retirement statuses remain `not_cleared`.

## Artifacts

- Specification: `SPEC.md`; current Docstore record IDs are retained in the registration receipt.
- Implementation and read-only query examples: `casebible/catalog_reconcile/`.
- Private reproducible observations, hashes, inventories and receipts: `generation-02/`.
- Live Google metadata observations and capability limits: `probe-01/`, `probe-02/`.
