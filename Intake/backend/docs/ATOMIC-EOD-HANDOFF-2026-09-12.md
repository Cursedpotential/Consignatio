# Atomic boundaries for the concurrent EOD R2 to B2 migration

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: record latest coordinating-task clarification | Context: preserve every occurrence independently of hint overlays -->

Latest coordinating-task rule: inventory and retain every occurrence. Junk,
quarantine, dupe, to_be_deleted and review labels are untrusted provenance
assertions, not omission authority. Physical upload dedupe belongs to that task
and may use verified SHA-256 or its separately labeled, conflict-free historical
MD5+size-to-SHA256 bridge; no such bridge has been implemented or verified here.
The graph proof's bounded25-row selection is NOT an EOD migration filter.

Verified 2026-09-12 by the Intake graph task and read-only atomic-contract agent.
No detector, object copies, OneDrive access or B2 writes were performed here.
Destination and live counts below were supplied by coordinating task
`01a09338-1c1a-7212-beda-5ebe94fb3099`, not independently measured here.
Approved destination: `salem-data/consignatio/vault/v1/`.

## Exact inventory joins and freshness

PG18 `casebible-pg18`, database `casebible`:

- Full historical R2 source: `raw_duck.r2_files`, columns `bucket,path,name,ext,size,
  md5,modtime,mimetype,tier,_src_file,_loaded_at`. Enrich live manifest with a LEFT
  join on exact bucket + exact original object key. Preserve variants and unmatched
  live occurrences. Never join by basename; size/MD5 are corroboration, not current
  SHA-256 verification.
- Filtered hint index: `inventory.atomic_path_index`, primary key
  `(store,account_key,container,path,source_variant_key)`. R2 uses store=r2,
  account_key='', container=bucket. Index path replaces backslashes with slashes;
  retain the live original object key as the only execution key. Normalization is
  not guaranteed lossless for a cloud key.
- Index columns also include name,byte_size,md5,sha1,sha256,quickxor,mtime_text,
  source_row_count,source_refs,path_parts,indexed_at. source_variant_key is a
  metadata-derived MD5, NOT a content digest. Missing index membership means only
  that FB/Takeout/archive filters did not select that row.

| Bucket | Historical PG rows / bytes | Coordinating task live rows / bytes |
|---|---|---|
| raw | 492300 / 659705405305 | 492317 / 659706010728 |
| sorted | 345273 / 1182975421449 | 345416 / 1183027867533 |
| quarantine | 441983 / 1264680093538 | 441984 / 1264721565313 |

Live PG index counts: R2=592822; Google Drive=46837; OneDrive=0.
`inventory.atomic_detection_run`, `atomic_unit_candidate`, `takeout_archive_part`
and `atomic_identity_evidence` each have zero rows. Both monolithic detection runs
rolled back. There are no populated candidate memberships to join.

Future candidate joins are scoped by run/store/account/container and exact path
SEGMENTS. Do not reuse `LIKE root || '/%'` without escaping `_` and `%`.
Defined relationships: atomic_copy.candidate_id -> atomic_unit_candidate.id;
atomic_member.copy_id -> atomic_copy.id; atomic_group_copy(group_id,copy_id);
atomic_candidate_relation(from_candidate_id,to_candidate_id,relation_type);
takeout_archive_part.archive_candidate_id -> atomic_unit_candidate.id.

## Protected boundaries and uncertainty

- Only Facebook and Takeout directory names may provide broad boundary hints;
  include malformed/copy/numbered/deeply nested names. Missing start/index files
  does not disqualify an export. Non-FB/Takeout boundaries require structure.
- Preserve-whole FB export candidates include parent of your_facebook_activity.
  Broad FB/Takeout collection wrappers (FB DATA, FB Exports, Katrina FB Data,
  Facebook Data, bare facebook, timestamped meta-*, loose messages (N), Takeout
  Data/Data1, Google Takeout, google_takeout, Google Takeout Files and malformed
  variants) are protected controlled-consolidation parents, not approved best copies.
- facebookuser_<id>, facebook_payments, facebook_accounts_center,
  apps_and_websites_off_of_facebook and FB_IMG_* stay members inside proper units.
  Outside a boundary, flag orphaned_export_fragment / investigate_orphan. They are
  not standalone migration units. The owner's eventual approximately twelve FB
  conversation selections remain unresolved; do not infer a machine omission list.
- Retain nested roots and nearest-parent relationships. Do not flatten or silently
  choose independent migration of inner archives/packages. Repository manifests
  can support structural hints, excluding dependency-tree manifest hits.
- Takeout subjects: matt.salemnet (critical), matt.salem85, caminstaller, salemnma,
  katrina95xo, katrinasalem95; additional/unknown accounts remain possible.
  ma.salemnet was corrected before insertion. Storage-provider account is not the
  Takeout subject. Profiles/subscriber/change-history/content can provide identity
  evidence; folder names never finalize it.
- Model subject -> export event -> original archive series -> part -> extracted
  trees. Retain original ZIP/TGZ parts and distinct export events. Overlap does not
  prove same account/set. Contiguous part numbering does not prove completeness.
- Strong-original-name hint only:
  `(?i)^takeout-([0-9]{8}T[0-9]{6}Z)-([0-9]+)-([0-9]{3})\.(zip|tgz|tar\.gz)$`.
  Nonstandard archives still qualify for investigation. Proposed series keys
  store|provider-account|container|timestamp|batch do not establish subject identity.
- Same normalized archive/extraction stem is possible_extraction_of, not confirmed
  lineage. Later reconstruction chooses a verified-good base plus missing members,
  with per-member provenance. Corrupt/recovery variants never silently replace it.

## Refined junk overlays

Verified tables (location join bucket,path; size/MD5 corroborate variants):

| Table | Rows | Meaning |
|---|---:|---|
| rootcsv.junk_scrub_report_final | 5767 | Final historical junk overlay, not stale earlier reports |
| rootcsv.tmp_restored_final | 141 | Explicit restoration overlay |
| rootcsv.isolated_credentials | 2 | Never ingest/index/embed credential exports |
| rootcsv.excluded | 1 | Explicit owner exclusion |

size and md5 columns are varchar. Final pattern counts: site-packages3551,
node_modules1827, pycache181, dotgit164, venv41, tmp3. Those three tmp rows are the
two isolated credential exports plus one explicit exclusion, NOT a general tmp rule.

No generic tmp/temp/junk/dupe/quarantine/to_be_deleted exclusion. In particular,
_backup_import/Documents/tmp/ is a protected evidence/chat-export cache;
.review_hold is TODO/handoff storage. Dependency/dotgit hints do not authorize
shredding a protected repository. Historical overlays are not final sorted-case
disposition. Exact-byte copy/dedup and occurrence manifests remain distinct from
later human sorting and acceptance.
Credential isolation governs sensitive processing; it must not silently erase
the occurrence from the migration inventory. Keep occurrence accounting distinct
from credential handling, model ingestion and physical-upload decisions.

## Concurrent ownership

In Consignatio/casebible: schema_atomic_units.sql is modified; detect_atomic_units_v2.sql
and stage_atomic_paths.sql are untracked. Their prior dirty edits have unknown
ownership; this continuation has not modified them. HANDOFF.md around lines406-505
records prior owner classifications/run state. cb_isolate.py is historical context
only, includes old paths/removal-command generation, and must not be executed.

Next detector work must use bounded store/rule transactions and receipts, not a
monolithic detector. Third SurrealDB consignatio/intake is a separate organization
graph, not a populated source for EOD memberships or downstream legal authority.

This handoff and the occurrence-map projection contract were delivered to the
coordinating R2-to-B2 task `01a09338-1c1a-7212-beda-5ebe94fb3099` after crash
recovery. Delivery did not transfer file ownership or authorize that task to write
SurrealDB.
