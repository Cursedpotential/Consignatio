# Best-copy metadata reconciliation — 2026-09-13

## Owner contract

For a content group whose byte identity has been proven by SHA-256, the retained
payload/primary metadata donor and the canonical display filename are independent
decisions.

- The main retained representation is the healthy occurrence with the most
  complete trustworthy dates, EXIF, GPS, camera, provider, sidecar, and catalog
  metadata. A recovery-named occurrence can be the main representation.
- The canonical display/export filename is selected independently from credible
  original/native-name assertions. An obvious recovery or copy wrapper may be
  repaired, while every observed filename and path remains immutable provenance.
- The oldest trustworthy date is preferred. Every observed date remains an
  assertion with its source and interpretation; filesystem mtime, provider upload
  time, embedded EXIF time, filename-derived time, and content/event time are not
  conflated.
- Unresolved names or metadata are retained side by side in the resolution tables.
- Byte-different, corrupt, truncated, repaired, or near-duplicate objects are never
  auto-collapsed. They remain separate Case Bible review items.
- Embedded metadata is part of the bytes. If two claimed exact copies disagree on
  embedded EXIF/GPS/camera fields, the group is blocked until identity or extraction
  provenance is corrected. External sidecars and provider metadata may legitimately
  differ within one exact-byte group and are retained as separate assertions.

## Safety state

- `consignatio-pg18-r2-to-b2-raw-dedupe-20260912-v2.service` remains stopped and
  was read back as `inactive/dead`, `Result=success`, `ExecMainStatus=0`.
- No R2 or B2 payload was deleted, moved, renamed, overwritten, or recopied by this
  reconciliation.
- The two interrupted SHA-ledger partials were moved, never deleted, into
  `/data/consignatio/migrations/r2-to-b2/to_be_deleted/best-copy-resume-partials-20260913/`.
- The metadata-only SHA export completed at 256/256 partitions, 256 receipts, and
  zero partials. It read the existing SHA ledger and did not read corpus bytes.

## Existing database sources used

The new catalog uses the existing databases and fills their missing coverage from
PG18. It does not treat `raw_duck.r2_files` as the entire database.

| Source | Current observed coverage |
|---|---:|
| PG18 `raw_duck.r2_files` | 1,279,556 R2 occurrences / 337,067 MD5+size candidates |
| PG18 `catalog.od_manifest` | 1,868,827 OneDrive observations |
| PG18 `gdrive.gd_net_rw` | 125,719 Google Drive observations |
| PG18 `raw_duck.local_files` | 1,281,361 local-file observations |
| PG18 `inventory.atomic_path_index` | 640,219 normalized R2/GDrive path variants |
| PG18 recovery tables and root recovery map | preserved in the `recovery_links` shard |
| PG18 media/photo/screenshot/face metadata | 32,608 exported assertions |
| Existing R2 SHA-256 ledger | 338,318 metadata-rich SHA records |
| `D:/casebible/casebible.duckdb` | 590,560 hash/path rows; 15,106 enrichment rows |
| `D:/casebible/iterations_index.duckdb` | 2,080 iteration rows; 1,691 table definitions |
| `D:/casebible/merge-plan.duckdb` | 29,188 merge-plan rows |
| `D:/casebible/casebible_work.sqlite` | 4,878 sort decisions; 15 copy-log rows |
| `E:/e.efu` | 548,478 July-25 pre-merge E-drive baseline entries; historical provenance only |
| `C:/Users/matts/OneDrive/Desktop/export.csv` | 10,075 current report rows / 411 folders / 1,901 duplicate-marked rows |

The OneDrive desktop report's `Match %` field is retained as a tool assertion. It
does not authorize byte deduplication without the SHA identity gate.

## Immutable PG18 export receipt

Nine CSV-gzip shards were exported from PG18 through `COPY TO STDOUT`. Their
uncompressed CSV total is approximately 1.86 GB. Every shard has a SHA-256 receipt
under the ignored runtime directory
`runtime/best-copy-20260913/pg18-full/`. The source tables were not changed.

The SHA-ledger metadata shard is
`runtime/best-copy-20260913/sha256_metadata.csv.gz`: 338,318 records,
236,601,342 uncompressed bytes, SHA-256
`182b512865be5d517db7a23766af087f479847719ae805804f76a30272f71b71`.
It preserves source filename, path, bucket, byte size, MD5, SHA-256, custom mtime,
source upload time, source version, ETag, content type, storage class, computation,
and the raw custom/HTTP metadata objects.

## DuckDB catalog and code

- Branch: `codex/r2-b2-best-copy-20260913`.
- Metadata-resolution implementation commit: `eca84bd`.
- The builder has append-only metadata assertions and resolutions; it selects the
  primary metadata donor independently from the filename donor, rejects sentinel
  dates, preserves competing assertions, blocks embedded-metadata conflicts, and
  exports the complete side-by-side resolution.
- The source exporters and DuckDB build tool live under
  `casebible/r2-b2-migration-codex/tools/`. Generated databases, CSVs, receipts, and
  indexes stay ignored and never enter Git.
- The first standalone DuckDB resolution build was rejected during review because
  it materialized several sources without importing their field assertions and it
  treated historical path-plus-size matches as stronger identity evidence than they
  are. The partial database and WAL were preserved under `to_be_deleted`; they are
  not an accepted manifest. The corrected build must feed source assertions through
  the tested ledger resolver instead of maintaining a second selection algorithm.

## Source-by-source delta passes

The historical catalogs are baselines. Fresh change detection will run in bounded
source passes with a separate snapshot ID, timestamp, row count, and manifest hash:

1. R2/B2 transfer and metadata delta.
2. D: current consolidated local-corpus metadata/hash delta.
3. E: inventory the small post-merge residual and compare it with D. Use `E:/e.efu`
   only to retain pre-merge path/date provenance; do not recreate historical E copies.
4. F: metadata/hash delta.
5. J: metadata/hash delta.
6. OneDrive provider delta through `od:` and `od1:` without hydrating placeholders.
7. Google Drive provider deltas for `gd_salemnet:`, `gd_salem85:`, `gd_salemnma:`,
   and `gd_caminstaller85:`.

No pass may delete a source, infer equality from a filename or similarity score,
or hide a byte-different version. Hashing and deep metadata extraction can be
resumed independently per source; unresolved work remains visible to the Case
Bible review surface.

## Remaining live gates

- Replace the rejected standalone DuckDB selection SQL with an import/export layer
  around the migration ledger's tested assertion and resolution engine, then record
  exact group/change/review counts.
- Import the PG18, SHA ledger, D catalogs, historical E EFU, OneDrive report, and
  provider assertions into the migration ledger without promoting path/size matches
  to exact identity. Run resolution against the full frozen SHA identity set.
- Compare the new payload donors and filename/date donors with
  `raw_duck.final_survivors`, including already-copied B2 staging objects.
- Run a bounded fresh source delta per drive/provider. D is the current consolidated
  local source. The July E: EFU is historical after the E-to-D merge, and neither it
  nor the June/July D: catalogs can prove September freshness.
- Existing PG18 photo tables preserve filename-derived and filesystem dates, but no
  complete corpus-wide EXIF/GPS/camera extraction table was found. Reuse existing
  enrichment first; extract missing embedded metadata once per unique healthy byte
  identity and keep byte-different versions in Case Bible review.
- Do not resume the R2-to-B2 transfer until the new manifest, side-by-side metadata
  export, and read-back gate pass.
