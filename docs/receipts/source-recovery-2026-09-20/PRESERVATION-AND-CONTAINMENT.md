# Missing payloads, backup containment and R2 preservation

Byline: Codex | 2026-09-20 | Owner-directed recovery and platform-data preservation.

## Missing payload table

Sixteen image parts in the December 6 backup lack embedded payload data. The table preserves raw epoch milliseconds, UTC and America/New_York times, original MMS attributes, part attributes, filenames and content IDs. These are recorded MMS timestamps, not independently authenticated capture times. Names retain their original `.jpg` suffix even when the recorded type is HEIF.

Live view: `catalog_reconcile.missing_message_payloads`. Machine-readable files: `native-payload-worklist-01/missing-payloads.csv` and `.json`. All 16 database rows were read back and matched.

| Recorded time, New York (EDT) | Filename | Recorded content type | Status |
|---|---|---|---|
| 2025-08-29T14:07:21-04:00 | image000000_11449.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11451.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11453.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11455.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11457.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11459.jpg | image/jpeg | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11461.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11463.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:07:21-04:00 | image000000_11465.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:11:36-04:00 | image000000_11469.jpg | image/jpeg | Missing embedded payload |
| 2025-08-29T14:11:36-04:00 | image000000_11471.jpg | image/jpeg | Missing embedded payload |
| 2025-08-29T14:11:36-04:00 | image000000_11473.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:11:36-04:00 | image000000_11475.jpg | image/heif | Missing embedded payload |
| 2025-08-29T14:11:36-04:00 | image000000_11477.jpg | image/jpeg | Missing embedded payload |
| 2025-09-02T11:18:05-04:00 | image_1_11604.jpg | image/jpeg | Missing embedded payload |
| 2025-09-02T15:19:54-04:00 | 0cc8129e-94df-4_11608.jpg | image/jpeg | Missing embedded payload |

## Exact backup-containment decisions

| Backup | SMS | MMS | Total | Exact records absent from December 6 | Additional-copy decision |
|---|---:|---:|---:|---:|---|
| November 26 | 2,110 | 9,079 | 11,189 | 2 MMS | Retain complementary occurrence |
| December 3 | 2,135 | 9,536 | 11,671 | 0 | Skip another binary copy; preserve backup provenance |
| December 4 | 2,135 | 9,536 | 11,671 | 0 | Skip another binary copy; preserve backup provenance |
| December 6 | 2,135 | 9,541 | 11,676 | — | Retain as fuller backup for this family |

All four streamed/local binaries matched expected sizes and MD5, parsed fully, matched their declared counts and had stable source metadata where remotely read. Comparison includes all SMS/MMS attributes, nested addresses and parts, and hashes of exact Base64 attribute values; formatting-only inter-element whitespace is ignored. Duplicate message multiplicities are preserved. Backup-level metadata remains separate and retained. The November exceptions have no same-timestamp MMS candidate in December 6 and must not be dropped merely because November is smaller.

Six targeted retention tests passed, including duplicate multiplicity, metadata/payload differences, malformed input and source-change holds. The retained December backup still has 16 attachment gaps; containment is not a claim of complete device history or a recovered exact January backup.

## Reusable platform records

Four backup manifests, 11,678 unique exact message records, 46,207 backup-message occurrences and three containment comparisons were published and fully compared with database readback. Views are `catalog_reconcile.backup_manifests`, `backup_message_records`, `backup_message_occurrences` and `backup_containment`. Parquet snapshots, the comparison contract, original backup metadata and the reproducible publication stream are under `native-backup-containment-01/`. Nothing is represented only by a prose count.

## R2 candidate preservation

All 648 large TXT/XML candidate occurrences from the completed nine-bucket search were reconciled. For 627, live R2 MD5 and size matched the preserved catalog linkage; all 186 referenced B2 versions were checked live for current version ID, size and available provider hash. Source metadata was captured for every one. Eighteen initially unhashed R2 sources were fully streamed on the VPS to compute MD5, SHA-1 and SHA-256 without storing their binaries there; all 18 matched current B2 copies by SHA-1 and size.

A newly cataloged Nexus occurrence of the December backup matched the same existing content. Two identical Nexus test-fixture occurrences were not covered by the current catalog. One 3,839,897-byte binary was preserved in B2, retaining both occurrences and their metadata, and fully read back to verify SHA-256 `72640c6c2995d7dd89ce01e5757f7ee5ccc5af2945f1faadefc60339b77c9a55`. It is explicitly a **derived test fixture, UNVERIFIED**: it contains 60 parsed records, does not match its declared count, and is not promoted to evidence.

Result: 646 existing-B2 occurrences plus two occurrences represented by one new B2 binary. No additional copies of the older December iterations were uploaded. Existing B2 copies were not deleted. `catalog_reconcile.r2_candidate_preservation` holds all 648 source-to-B2 preservation records; all JSON rows matched readback. This verifies this candidate batch, not retirement of every object in all R2 buckets. No R2 object was deleted or altered.

## Durable artifact preservation

The owner requires all generated counts, comparisons, receipts, queries, code and source observations to remain usable later. They are retained locally and in PostgreSQL; the B2 analysis archive and its inventory are recorded separately under `native-platform-archive-01/`. Its verified completion receipt, rather than this document alone, establishes successful cloud preservation. Original binary mirrors that are already held in B2 are represented by source/version references rather than duplicated inside the analysis archive. Raw header/tail samples remain archived with byte offsets and hashes. Incomplete attempts remain labeled incomplete and are not evidence of successful searches.

The historical SHA-256 ledger was recovered successfully on the second attempt: 338,318 records across 256 partitions, every partition hash checked. Blank NDJSON lines were counted and skipped; malformed records still fail. This is preserved historical receipt evidence, not a fresh hash of every current source.

Docstore synchronization remains pending due the unavailable governed connection; it does not invalidate independently verified PostgreSQL or B2 facts. No indexing/embedding job was started.
