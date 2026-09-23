# Source recovery and metadata completeness assessment

Byline: Codex | 2026-09-20 | Owner-directed recovery and reconciliation.

## Verified result: one call-backup family

The original bytes of `calls-20260105063120.xml` were acquired separately from two explicit Google Drive file IDs and the retained B2 version. All three independently reread local binaries are 175,073 bytes and share SHA-256 `0091b447820470f6531be2bc54600d4c360c39dbd6bdc772f3c1c121b300d302`. Google provider metadata was captured before and after acquisition; version, checksums, size and modification time remained stable.

The XML parses using a parser that prohibits unsafe entity handling. It contains 557 call records, matching its declared count. Its root declares a full backup, backup set `da011db8-c7df-4dba-a19f-c2a187fe0a29`, and backup date `1767612680184`. These are observed application declarations, not proof of device-wide completeness or authorship.

| Occurrence | Evidence observed | Assessment |
|---|---|---|
| Google ID `1kgp20C5VMVpRxxYFntnO2Jn5JX0u0joE` | Created January 6, 2026; live application properties preserve backup set, date, type and 557-record count, agreeing with the XML | Provisional BAS #1 source occurrence for this exact backup family |
| Google ID `1x7EUmG-_FIjmVYqfUAI10zEVlfNpsV_t` | Created May 31, 2026; identical binary, application properties absent | Verified byte copy; retain its occurrence record |
| OneDrive occurrence | Existing catalog preserves independent provider ID, source path, creator/modifier identities and January 6 timestamps | Provisional complementary-source lead; live provider and binary verification outstanding |
| Retained B2 occurrence | Downloaded exact version and verified identical bytes; fileInfo retains only `src_last_modified_millis` | Verified storage copy; B2 metadata alone does not preserve the Google application properties |

The preferred evidence unit is the unchanged binary **plus occurrence metadata, source identifiers, acquisition records, and package relationships**. Do not inject recovered metadata into the original file. Sidecars remain separate, hashed records. No occurrence is approved for retirement, and no source has been certified court-ready.

Private supporting artifacts: `native-calls-01/assessment.json`, catalog occurrence snapshot, before/after provider metadata, and three unchanged XML binaries. This directory is excluded from Git. Acquisition source: `casebible/catalog_reconcile/assess_call_backup.py`.

## Earlier historical-version availability recovery

The bounded B2 historical batch transferred 324 identities totaling 177,412,387 bytes. Independent disk verification and live publication succeeded for **323 artifacts / 177,343,779 bytes**, representing 1,449 historical occurrence work items. One 68,608-byte `sniffpass.exe` acquisition is on a Windows Defender hold and is not counted as available or a BAS candidate. No protection bypass or execution was performed.

The live effective worklist also reconciles 1,560 existing native Office/PDF export links. Those links do not establish native-document fidelity or replace the source-native representation. There are 143,237 remaining pending work items in that generation. The historical batch largely contains application assets/cache material; its recovery is availability work, not an evidence-quality assessment.

Proof: `batch-01/published.json`, per-item receipts, independent disk verification records, and `catalog_reconcile.recovered_artifacts`, `recovery_holds`, and `effective_recovery_worklist` in PostgreSQL.

## Required evidence-quality recovery order

1. Messaging, call backups, email and evidentiary media: connect original provider/device IDs, preserve native files and adjacent manifests/sidecars, and compare embedded metadata without rewriting the bytes.
2. For photos/video, compare format integrity, dimensions/duration, EXIF/IPTC/XMP, capture time/timezone, camera identifiers, GPS where present, original filenames, and export sidecars. A larger file, successful decoder, or identical hash is not sufficient to select an occurrence.
3. Link whole Google Takeout, Facebook, Snapchat and other export roots as packages. Determine missing parts and sidecars before selecting a package as complete. Do not flatten exports.
4. Verify the OneDrive complementary occurrence for the assessed call backup and identify associated SMS/backup-set artifacts. Completeness against the source phone remains unresolved.
5. Extend recovery-area checks beyond `recup_dir.N`, including photo_recovery, other recovered trees and zero-fill quarantine. Revisit retained copies from the reported 16,400-image deletion using receipts and original-source metadata.
6. Reconcile R2 using exact identity plus preserved occurrence metadata. Quarantined/no-hash records are unresolved claims, not automatically missing or suitable for restoration. No R2 retirement is cleared.

For each assessed family, record BAS #1, complementary #2, the precise reason, missing metadata, unresolved conflicts, source/package scope, and the verification boundary. Do not conflate an application export with a source-device original. Semantic similarity is a relationship, not a deduplication decision.

## Open limitations

The SHA-256 historical ledger capture at `ledger-01` failed JSON parsing and is incomplete/unvalidated; it has not been published or used to resolve identities. Broader multimedia metadata completeness, OneDrive live verification, source-device completeness, and original-package recovery remain outstanding. Previous timeline, Weaviate and Surreal derived outputs remain UNVERIFIED. pg_duckdb is already installed and verified in the live database; it does not resolve these provenance gaps.

Remote operations in this phase were metadata reads and explicitly bounded file downloads. No remote object was modified, removed, moved, or uploaded. The new local acquisition and additive catalog records preserve the earlier catalog facts.


## Confirmed incomplete SMS companion — priority recovery target

Byline: Codex | 2026-09-20.

The live Google source `1GFuKXgAXQ92XvXQIyTdlBxcUqezGI59g`, named `sms-20260105063120.xml`, was acquired unchanged and independently reread. Its 917,504 bytes match the catalog and provider SHA-256 `1569dbdf3fd0c6b8eb464e4304a18e1e291e7af998256d14c4c960911040338e`. Provider version/checksum/size/modification fields were stable before and after acquisition.

**The file is structurally incomplete despite this successful hash check.** The XML header declares 12,390 messages and the same backup set/date as the assessed calls file. Only 1,969 complete SMS/MMS elements parse before an unclosed token at line 1,978, column 2. The closing `smses` tag is absent; no zero bytes were found. This does not establish the content or availability of the remaining declared messages. Do not accept this occurrence as a complete backup or repair/overwrite it in place.

The provider currently exposes one revision of the same size and MD5; no pagination cursor was returned. That observation does not establish whether other deleted revisions or copies once existed. A bounded catalog filename search finds only this SMS occurrence alongside three call-backup occurrences. Search old OD/GD/local/R2 backups using the exact backup set ID and timestamp, allowing renamed files and archives, then validate any candidate against its own complete structure and message identifiers. Adjacent backups may complement this file but must not be silently substituted as the same backup.

Private proof is under `native-sms-01/`: binary, before/after provider metadata, parse result, structure detail, provider revision listing and related catalog records. This finding makes the whole associated backup package incomplete; the call file remains a structurally valid component candidate, not a complete package BAS.

Docstore registration for this new receipt and TODO amendment is pending: the governed connector is unavailable, and the existing control CLI also failed. Local artifacts are saved; store synchronization is not claimed.
