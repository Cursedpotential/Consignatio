# R2 recovery: large XML and carved TXT leads

Byline: Codex | 2026-09-20 | Owner-directed read-only source search and targeted acquisition.

## Verified recovery

Acquired the unchanged `sms-20251206203434.xml` from `casebible-quarantine/onedrive/Case Bible/Evidence/SMS Backup and Restore/` in R2. The 1,327,221,655-byte local binary matches the catalog MD5 `7a89fe7a0975a5b81841667274b8fff1`. Independent local hashing produced SHA-256 `a0db30a47ca3bc2991d5d10c15991142e5070ecf8315bd4a7191aa4f2b20de76`. Before/after source metadata agreed.

Full XML parsing succeeds with exactly 2,135 SMS and 9,541 MMS records, matching the declared 11,676 messages. All 1,969 complete SMS records readable in the damaged January backup occur here with **every SMS attribute matching**. This file contains 166 additional unique SMS records. Its backup set and date differ from the January file; it is a complementary source, not the recovered exact January backup.

All 553 nonempty embedded payloads pass strict Base64 decoding, representing 983,096,133 decoded bytes. Decoded SHA-256 identities and original part/message attributes were recorded without writing decoded media or changing the backup. Media decoding, embedded EXIF/XMP completeness and original-source fidelity remain unverified.

There are 16 image parts without embedded data: ten declared HEIF and six JPEG. Their message timestamps, content IDs and filename fields are preserved as recovery targets. Exact filename searches in the R2 catalog returned no standalone hits. A catalog miss is not a live-source absence result.

Original binary, acquisition plan, metadata, full structural result, comparison, payload manifest, gap list and bundle hashes are under `native-r2-december-recovery/` (excluded from Git). Findings were added to `raw_duck.evidence_quality_20260920` as `native-r2-december-recovery`, visible through `catalog_reconcile.evidence_quality_assessments`; full JSON readback matched. Status: `structurally_valid_complement_with_attachment_gaps`. Retirement remains uncleared.

## Recovery and carved-file search

The catalog shortlist deliberately included recovery areas beyond `recup_dir.N`: `_backup_import`, recovered/PhotoRec paths, quarantine, and `f<number>` carved names. TXT/XML candidates used a 917,504-byte minimum (the damaged file's size), with bounded largest-first result sets of 200 general recovery and 150 carved candidates. These caps are not a full census and may omit smaller fragments.

Live header/tail sampling covered 24 selected candidate objects. Twenty-three have SMS-backup XML headers; ten sampled tails end with `</smses>`; eleven tails contain zero bytes. Neither a closing tag nor zero bytes alone decides whole-file integrity. Several carved XML files contain sampled SMS records matching the damaged backup.

Separate head/middle/tail sampling covered ten large carved TXT candidates. **All ten contain MMS opening tags in at least one sampled range.** Thus a TXT extension cannot exclude messaging evidence. None of those sampled ranges contained the target January backup-set ID or the four timestamps associated with the recovered December file's missing media. Unsampled content remains unresolved.

Candidate evidence and saved range bytes: `native-r2-01/samples/`, `native-r2-01/txt-samples/`, and `native-r2-01/sample-overlap.json`. Live source metadata before/after each sampled object agreed. No sampled fragment was repaired, silently concatenated, or promoted to a complete backup.

## Filename-search coverage

The catalog returned four paths for the associated call-backup timestamp and no SMS path. Nine R2 buckets were accessible to bucket enumeration. A live recursive names-and-sizes search is tracked in `native-r2-03/`; only its per-bucket successful result receipts and final `complete.json` establish completed coverage. Attempts `native-r2-01` and `native-r2-02` were interrupted while improving listing efficiency and are not absence evidence. No archive members are searched by object-key listing.

## Owner-required workflow

1. Search exact filenames and variants across the catalog and all relevant accessible live sources. Record completed, pending, unavailable and inaccessible sources separately.
2. Expand to differently named, carved and recovery files based on format, size, package context and embedded identifiers; include TXT files that may contain XML fragments. A filename miss must not end recovery.
3. Compare existing hashes, source IDs and metadata before targeted content reads. Preserve each occurrence and its original fields.
4. Acquire selected unchanged binaries with before/after source metadata and independent local hash checks. Keep all raw source material intact.
5. Validate complete structure, record counts and embedded payloads; compare records and metadata against known fragments and other occurrences. Preserve package/sidecar relationships.
6. Identify provisional BAS #1 and complementary #2 with reasons and limitations. Separate exact-byte identity, semantic record overlap, format validity, metadata completeness and original-source provenance.
7. Save positive findings and unresolved gaps to the catalog and recovery worklist. Never infer source absence from an incomplete search, or retire an occurrence merely because its bytes match.

## Outstanding work

The exact January backup and its complete 12,390 declared-message population have not been recovered. The December export is a verified complementary recovery with attachment gaps. Follow up the 16 missing media parts across other backups, source devices/provider occurrences and carved MMS fragments. Validate recovered media formats and metadata before selecting evidence originals. Complete the recorded live filename search; do not claim all R2 content was examined.

No remote object was altered, moved, uploaded or deleted. Local recovery artifacts and additive quality records were created. Docstore synchronization remains pending because the governed connector and CLI were unavailable earlier in this session; filesystem persistence and PostgreSQL verification are separate from document-store synchronization.


## Final live R2 filename coverage — completed

All nine accessible buckets completed successfully: casebible-raw, casebible-sorted, casebible-quarantine, casebible-hash-ledger, casebible-lakehouse, milvus-memsearch, nexus, photos, and r2-explorer-bucket. The listing returned 95,395 TXT/XML or timestamp-matching objects. Of these, 648 are at least 917,504 bytes; 405 have recovery-related path/name hints. These are physical object counts, not unique binary counts.

The exact January timestamp matches four call-backup paths and **no SMS filename**. A January 5 date-variant check over the text listings likewise returns only those four call paths. This establishes current live filename-search coverage, not absence of renamed, embedded or archived message data. Live receipts and listing fingerprints: `native-r2-03/verified-search-summary.json` and `complete.json`.
