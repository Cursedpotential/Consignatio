<!-- tags: catalog, raw_duck, audit, source-of-truth, identity, occurrence, dates, provenance, hashes, packages, state, cocoindex, build-1 -->
# Catalog model audit — PG `casebible`, schema `raw_duck` (ovh-files)

> _Byline: Claude Code · Opus 5 · 2026-09-18 23:00 EDT. Read-only: `information_schema`, `pg_class`, and aggregate SELECTs. Nothing was written to the catalog._
> Why: Codex review 22:52 EDT (`docs/transcripts/2026-09-18-codex-catalog-is-the-foundation-audit-first.md`). Build 1 must consume the existing catalog model, not invent one.
> Raw listings in this folder: `tables.txt` (143 relations, rows, size), `columns.txt` (every column), `occurrences_profile.txt` (per-source dates, hashes, metadata keys, dispositions).

## Verdict

The catalog is **rich but undocumented and spread across many tables**. The occurrence level holds names, paths, sources, dates, hashes and source metadata for 1.56 M occurrences. The gaps are: a documented model, one stable object ID, object-level dates, one agreed occurrence → vault-object link, and "selected for intake" state. It is not broken. The `key, size, sha1` table used for Build 1's first query is the thinnest table in it.

## The 11 questions

**1. What exists.** 143 relations: 137 tables and 6 views (`timeline_*_20260918`). **None carries a table comment.** Groups:
- core: `source_occurrences`, `vault_objects_20260916_r4` (+ `_r2`, `_r3`, `_post_*`), `vault_keep_v7`, `vault_delete_v7`, `vault_occ_v1`, `vault_content_v0`, `vault_place_v1…v6`, `b2_objects`, `b2_content`, `vault_objects`;
- packages and structure: `atomic_units`, `atomic_unit_members`, `export_units_v1`, `export_unit_members_v1`, `vault_units_v1/v2`, `vault_unit_roots`, `dir_manifests`, `tg_nodes`, `tg_files`, `tg_node_content`, `tg_edge_*`;
- classification and state: `enrichment`, `graded_selection`, `integrity_hold`, `corrupt_recovery`, `ai_chat_probe_20260918`, `recovery_*`;
- dated task tables: `intake_*_20260916/17`, `chat_*_20260918`, `vault_twins_*`;
- **~40 unlabeled scratch tables** whose purpose is not recorded in the database: `base`, `base2`, `dec4`, `decisions`, `junk`, `junk4`, `losers`, `t`, `frem`, `mcut`, `keyed`, `scored`, `scored2`, `scored4`, `survivors`, `survivors2`, `surv4`, `final_survivors`, `staged`, `remaining`, `resolved`, `cand`, `cube`, `paired`, `side`, `dated`, `media`, `mfolder`, `arch`, `ns_canonical`, `ns_unique`, `to_copy`, `copy_manifest`, `in_sorted`, `sorted_best`, `sorted_best4`, `superseded_in_sorted`, `rec_all`, `rec_surv`, `r2_inv`, `local_files`, `r2_files`.

**2. What each represents.** Only inferable from columns and from the tracked SQL under `casebible/tools/`; the database itself says nothing. The core meanings used below come from those scripts and from the 09-16/09-17 records.

**3. Object identity.** **There is no single catalog object ID.** Content is identified in parallel by: native `sha256` (local and Google Drive occurrences), `quickxor` (OneDrive), `md5` (most occurrences), B2 `sha1` (vault listings), and `canonical_key` (`vault_keep_v7`, `vault_occ_v1`, `vault_content_v0`, the key the 09-16 dedupe kept one copy under).

**4. Source occurrence.** `source_occurrences`: 1,557,432 rows, natural key `(source, scope, path, source_id)`, no surrogate occurrence ID. `intake_catalog_fs_20260917` (1,567,456) is the same occurrences with a primary key `rel` and a resolved current vault key.

**5. Current physical B2 inventory.** `vault_objects_20260916_r4`: 508,201 rows (minus 49 in `vault_onecopy_pilot_delete_20260916` = 508,152, verified equal to the live mount on 2026-09-16). Columns: **key, size, sha1 only; no dates.** Stale: `vault_objects` (1,659,651, pre-dedupe), `b2_objects` (530,070 with `listed_at`; same count as `intake_objects_20260916_before`, the pre-clean intake area).

**6. Dates.** Available, each with a different meaning:
- `source_occurrences.modtime`: on every row. Contains known-bad values: minimum 1970-01-01 in 6 of 7 sources, maxima in 2042, 2060 and 2106.
- Google Drive `metadata.btime` (created) and `metadata.mtime`; OneDrive `metadata.ModTime`.
- `metadata.SMBR_BACKUP_DATE` on 121 SMS Backup & Restore files on Drive.
- `recorded_at` (when the catalog recorded the occurrence); `b2_objects.listed_at`.
- `graded_selection.date_trusted` (a per-file date-trust flag); `enrichment.date_start` / `date_end` (model-inferred, 15,106 rows).

**Not in the catalog:** B2 upload time, EXIF or media dates, archive-member timestamps, document-internal dates for the vault set.

**7. Source and provenance.** `source` is the device or account: `local/D-Backup` 890,091 · `onedrive` 323,183 · `local/F-Disk-Drill` 158,142 · `gdrive/salemnet` 127,291 · `local/F-case` 56,133 · `gdrive/salem85` 12,594 · `local/D-root` 22. Also `scope`, original `path`, `source_id`, `matched_origin`. Drive metadata adds `owner`, `permissions`, `labels`, `description`, `native`, `mime`. Some Drive files carry SMS Backup & Restore set properties (`SMBR_BACKUP_SET_ID`, `SMBR_RECORD_COUNT`, `SMBR_BACKUP_TYPE`) or Gmail save-to-PDF IDs.

**8. Hashes by level.**
- Occurrence level: `sha256` for local and Drive (1.23 M), `quickxor` for OneDrive, `md5` on most rows, `md5_proxy` for OneDrive.
- Vault-object level: B2 `sha1` only (r4); the stale `vault_objects` also had `md5`.
- There is **no sha256 on vault objects directly**; it comes through the occurrences.

**9. Packages and containers.** `atomic_units` (608) with `atomic_unit_members` (128,834 keys; unit type, service, export root, parent unit, content manifest); `export_units_v1` (542) with `export_unit_members_v1` (499,712); `vault_units_v1/v2`; `dir_manifests` (22,475); the tree graph `tg_*` (`tg_files` = 508,201, the same count as the current vault listing). **Open:** which of these were built on pre-dedupe keys. The 09-16 memory marks `vault_unit_roots` and the twins tables as stale; the rest is not verified.

**10. Classification and state.**
- `source_occurrences.disposition`: `content_on_b2` 1,259,641 · `copied` 202,202 · `junk_excluded` 56,847 · `zero_byte` 47,205 · `exported` 1,560 · `to_copy` 1.
- Other state columns and tables: `intake_catalog_fs_20260917.resolution`; `integrity_hold` (33,685, zero-fill detector); `corrupt_recovery`; `graded_selection` (`disposition`, `completeness`, `date_trusted`); `enrichment` (doc type, `is_conversation`, parties, relevance, proposed domain); `ai_chat_probe_20260918.probe_class`.
- **No "selected for intake" state exists.**

**11. Authority per fact, as recorded:**

| Fact | Authority | Record |
|---|---|---|
| what is on B2 now | newest `vault_objects_20260916_rN` minus pilot deletes | memory `vault-v1-current-listing-and-lineage-tables`, verified 09-16 |
| where a file was seen, its original path, name, dates, native hashes | `source_occurrences` | catalog decision 2026-09-16 |
| where a deleted copy went | `vault_delete_v7` ⋈ `vault_keep_v7` on `canonical_key` | same memory, 100 % resolved |
| occurrence → current vault key | **two routes, no recorded authority:** `intake_catalog_fs_20260917.vault_key` (one key per occurrence via sha1+size, same basename first) and `vault_occ_v1.canonical_key` → `vault_keep_v7.dest_key` (content level, every occurrence) | **open** |

## What this means for Build 1

- The descriptor handed to CocoIndex should be: the vault object (current key, size, sha1), plus **all** its occurrences with their own names, paths, sources, dates, hashes and metadata, plus package membership and state. The `key, size, sha1`-only query is withdrawn.
- `casebible/tools/vault_index_source_20260918.sql` (written, **not run**) uses the `intake_catalog_fs_20260917` route. That choice needs deciding first (question 11, open row). It stays unrun until then.
- Nothing in the catalog needs "fixing" for Build 1. What it needs is this model written down and one link route chosen.
