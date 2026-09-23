---
title: Recovery, Recycle, and Data Recap Triage & Canonicalization Addendum
status: owner-policy
tags: [consignatio, vault, policy, recovery, recycle, recap, canonicalization, dedupe, provenance, addendum]
provenance:
  shared_by: owner, 2026-09-16 22:32 EDT, as F:/Users/matts/Downloads/Recovery-Recycle-Recap-Triage-and-Canonicalization-Addendum.md
  saved_by: "Claude Code · Fable 5.1 (session nifty-nash-6d261e)"
  saved_at: 2026-09-16T22:40:00-04:00
  parent: "Object Storage Preservation & Sorting Plan" (not yet in this repo as of saving)
  content: verbatim; only this front-matter block was added
  governs: recovery output (recup_dir, $Folder, FOUND.000, recovered, restored), recycle-bin/trash captures, recap/report files, duplicate candidates, canonical-copy selection
---

*Addendum to the Object Storage Preservation & Sorting Plan. Applies to data-recovery output, recycle-bin/restoration material, provider trash exports, recovered fragments, recap/summary files, migration leftovers, and apparent duplicates. This is a preservation and decision policy, not permission to delete, overwrite, normalize, or silently select a winner.*

# Purpose

Recovered, recycled, restored, and recap-derived material should not be mixed immediately into ordinary projects, records, media, or source packages. Some items can be identified with high confidence and linked back to an existing container; others are fragments whose origin, completeness, dates, or names cannot be trusted.

The correct first action is separation and evidence capture—not broad filing and not broad deduplication.

The governing objective is:

> Preserve every recoverable candidate and its provenance first; then identify the strongest canonical working copy without destroying alternatives, original timestamps, or recovery context.

A “best copy” is a catalog decision. It does **not** mean silently delete every other copy. For important materials—especially records, legal material, personal history, communications, source exports, repositories, or backups—the other copies remain preserved as variants, provenance sources, or corroborating artifacts until a distinct retention decision is approved.

# Add These Areas

Add these controlled prefixes beneath `review-and-control/`:

```text
review-and-control/
  recovery-and-restoration/
    recovered-containers/
    recovered-loose-objects/
    recycle-bin-and-trash-exports/
    restoration-staging/
    recovery-tool-artifacts/
    orphaned-sidecars-and-metadata/
    unresolved-fragments/

  recap-and-derived-inventories/
    provider-recaps-and-reports/
    migration-recaps/
    tool-generated-inventories/
    extraction-and-index-recaps/
    human-authored-summaries/

  duplicate-candidates/
    exact-content-candidates/
    container-overlap-candidates/
    version-and-revision-candidates/
    media-and-sidecar-candidates/
    unresolved-candidate-groups/

  canonicalization-review/
    ready-for-canonical-selection/
    conflicts-and-uncertain-lineage/
    date-anomalies/
    metadata-conflicts/
    restricted-or-high-impact/
```

These are not final destinations for all material. They are controlled staging and decision states.

# Classification Rules

## Recovery and data-recovery folders

Examples include names such as `$Folder...`, `FOUND.000`, `recup_dir`, `recovered`, `recovery`, `undelete`, `restored`, `lost+found`, `file recovery`, or output from forensic/recovery tools. The name alone does not prove the content is unimportant or corrupt.

Classify the **recovery output root** as:

```text
container_kind: recovery_output
atomicity: preserve_root
retention_status: review
access_profile: quarantine
integrity_status: unverified
```

Do not rename internal recovered objects merely to make them tidy. Recovery tools frequently produce synthetic folder names, altered paths, generic names, or recovered file names that are only hints. Preserve the recovered-root layout and capture its original recovery-tool path/identifier in metadata.

A recovered object may be promoted to a normal destination only after it has been linked to a known parent container, project, records bundle, media set, repository, or source package with sufficient evidence.

## Recycle-bin and trash material

Recycle-bin material is not the same thing as a recovery artifact. It can be a provider trash export, filesystem recycle-bin capture, cloud-trash restoration export, or files copied out before permanent purge.

Classify the root as:

```text
container_kind: recycle_or_trash_capture
atomicity: preserve_root
retention_status: review
access_profile: quarantine
```

Keep original deletion/restoration metadata when available, including:

- Provider/system source
- Original path/key/parent identifier
- Deleted-at time
- Restored-at time
- Deleting/restoring identity, if captured
- Recycle-bin entry ID, version ID, and source account/device
- Original object timestamps, size, content type, and checksums

Do not use deletion time as content-creation time. Do not overwrite original timestamps with restoration or ingestion times.

## Data recap, summary, and report files

“Data recap” files need their own treatment because they are often metadata-rich but are not originals. They may be provider-generated inventories, migration reports, file lists, hash reports, export manifests, LLM summaries, human-authored notes, or tool-generated classification output.

Classify each recap by role:

| Recap type | Classification | Handling |
|---|---|---|
| Provider manifest or export index | `source_manifest` | Preserve with the source package; it can establish package completeness and original structure |
| Recovery-tool report | `recovery_report` | Preserve with its recovery-output root; it may be the only map back to lost paths or sectors |
| Migration/copy report | `migration_manifest` | Preserve in manifests-and-audit and link to the exact ingest batch and source/destination keys |
| Hash/checksum list | `integrity_manifest` | Preserve immutably; do not regenerate over it or treat a later hash file as the same artifact |
| Tool-generated inventory or extraction recap | `derived_inventory` | Keep as a reproducible derivative with tool/version/run metadata |
| Human-authored recap/notes | `human_summary` | Preserve as context; it is evidence of a person’s summary, not proof that the source corpus is complete or accurate |
| LLM-generated recap | `machine_summary` | Keep only as a labeled derivative; never let it replace source material, timestamps, or provenance |

A recap can be highly useful for classification, but it cannot be allowed to overwrite the original object’s facts. Record which source objects or container manifest it describes, its author/tool/version, and the time it was generated.

# Identification Before Filing

Recovered and recycled material should be processed through a confidence-gated routing sequence.

## High-confidence matches

A recovered object can be linked or promoted when multiple independent signals agree, for example:

- Exact content hash matches an object already cataloged.
- A provider object ID, file ID, inode/reference, archive member path, or recovery report identifies the source.
- The object has a matching internal format identifier plus matching size, stable timestamps, and a known parent context.
- A photo/video sidecar matches a media original by filename stem, embedded identifier, capture time, dimensions, and metadata.
- A repository file matches the expected relative path and commit/tree state inside a known repository root.

Even for an exact duplicate, retain the recovery occurrence as a provenance record:

```text
recovered_object_id -> exact_duplicate_of -> canonical_object_id
recovery_container_id -> recovered_from -> recovery_run_id
```

The recovered copy may be storage-deduplicated later, but its recovery relationship must remain queryable.

## Medium-confidence candidates

When content, metadata, or naming partly agrees but no strong identity match exists, keep the object or its containing prefix in `duplicate-candidates` or `recovery-and-restoration/unresolved-fragments`. Assign a candidate group and record the competing evidence. Do not automatically file it into the presumed project or records bundle.

## Low-confidence or conflicting material

If the filename is generic, timestamps conflict, the content is damaged, or the recovery path appears synthetic, keep it quarantined. Mark the uncertainty explicitly:

```text
lineage_confidence: low
parent_container_id: unknown
canonical_status: unresolved
integrity_status: partial | corrupt_suspected | unverified
```

# Canonical-Copy Selection

The canonical copy is the preferred **working reference** for retrieval, previews, derived processing, and routine access. It is not necessarily the only preserved copy, and it is not selected by filename alone.

## Required rule: earliest credible original time

When candidates represent the same logical file or record, favor the copy with the **earliest credible original timestamp**—including a creation, capture, authored, occurred, or source-record time—provided that timestamp is plausible and independently supported.

This implements the desired intent: preserve the copy that is closest to the original file/version, even if its current filename is bad, provided its metadata and content make the lineage more credible.

“Earliest” does not mean blindly accepting absurd clocks. Dates such as 1601, 1970, 1979/1980 defaults, 1989, 1189, a filesystem epoch placeholder, a timezone-conversion artifact, or a date inconsistent with the file format/device/account history are **date anomalies**, not proof of primacy.

## Selection hierarchy

Evaluate candidates in this order. A lower criterion must not defeat a higher one without an explicit review note.

| Priority | Decision factor | Why it matters |
|---|---|---|
| 1 | Original byte/content integrity | A damaged, truncated, or altered copy cannot outrank a complete original merely because its timestamp is earlier |
| 2 | Direct source identity and provenance | Source IDs, archive manifests, provider IDs, device/database identifiers, and recovery reports establish lineage better than names |
| 3 | Earliest **credible** original timestamp | Favors the copy nearest the original event/file state, not a later export, restore, edit, or ingest copy |
| 4 | Metadata richness and consistency | Retains the copy with original metadata, sidecars, embedded EXIF/XMP, headers, database fields, path evidence, or export manifests |
| 5 | Completeness of the logical set | A media original with its matching JSON/XMP, a record bundle with its attachments, or a repo root with configuration/history can outrank an isolated file |
| 6 | Fidelity to original representation | Original format beats a lossy conversion, rendered PDF, screenshot, flattened transcript, thumbnail, preview, or extracted text |
| 7 | Revision state and substantive content | If candidates are genuinely successive versions rather than duplicates, preserve them as versions; do not call the earliest one “best” merely because it is older |
| 8 | Filename/path quality | Useful as a weak signal and presentation choice only; never authoritative on its own |

## Important distinction: duplicate versus revision

Do not select an old copy over a newer one if they are different substantive versions of a document, codebase, export, record, or data set.

- **Exact duplicate:** same bytes; choose one canonical working object based on provenance/metadata completeness, retain all occurrences as references.
- **Metadata-divergent duplicate:** same or equivalent content, but one occurrence has richer trusted provenance/metadata; select the richer/earlier-credible source as canonical and preserve the other metadata as an alternate observation.
- **Revision/version:** different content created over time; retain every version, establish a lineage chain if possible, and designate a working/latest version separately from the oldest/original version.
- **Near duplicate:** overlap without identity; retain until a human or rule-based review establishes the relationship.

# Timestamp Credibility Model

Store raw observed dates separately from normalized/selected dates. Never overwrite the source value.

```text
observed_timestamps[]:
  - value_raw
  - value_normalized
  - kind: created | modified | captured | authored | occurred | exported | deleted | restored | ingested | filesystem_birth | filesystem_modified
  - source: embedded_exif | xmp | provider_api | archive_manifest | filesystem | recovery_report | filename | user_note | parser
  - timezone_or_assumption
  - precision
  - credibility: high | medium | low | anomalous
  - anomaly_reason
```

## Credible-date signals

A timestamp is stronger when it is:

- Embedded in the original file format or device/application database.
- Corroborated by a provider export manifest, source object ID, message/database record, or companion sidecar.
- Consistent with related files, device history, account history, file format, or known event chronology.
- Earlier than export/restore/ingest times but not implausibly early.
- Repeated consistently across multiple independent captures.

## Weak or anomalous-date signals

Treat the following as weak until corroborated:

- Filename-only dates.
- Cloud upload, download, export, migration, restore, scan, or ingestion timestamps.
- Filesystem timestamps carried through an unknown copy operation.
- Default epochs or values known to arise from failed conversion, absent metadata, recovery tools, or archive extraction.
- Dates that predate the relevant device, account, application version, file format, or real-world context.
- Dates that differ wildly from all companion objects without a credible explanation.

If no credible original time exists, leave the canonical original date unset or `unknown`; retain all observed timestamp values rather than fabricating a replacement.

# Metadata-Rich Copy Rules

A wrong or generic filename does not disqualify a copy from becoming canonical. In recovery work, names are frequently the least trustworthy field.

Prefer a poorly named copy when it has substantially stronger evidence, such as:

- Original EXIF/XMP/IPTC or camera maker-note metadata.
- A matching JSON/XMP/AAE sidecar or provider metadata record.
- Original message identifiers, sender/recipient fields, database IDs, attachment references, and message timestamps.
- Original document properties, revision metadata, embedded authoring metadata, or structured XML.
- Archive membership, source package manifest membership, provider file IDs, historical path records, or recovery-tool mapping data.
- A complete set of dependent files rather than a lone rendered/exported object.
- A verified digest matching a known original or a trusted source manifest.

However, richer metadata must be assessed for authenticity and internal consistency. A later export can sometimes carry copied metadata, while an earlier recovered file can be truncated. The catalog should record **why** the canonical copy was chosen, not merely the result.

# Candidate-Group Record

Every deduplication or canonicalization decision should create a durable candidate-group record.

```text
candidate_group_id: cg_000427
logical_asset_type: document | photo | message_export | repository | backup | record_bundle | unknown
members:
  - object_or_container_id
  - locator
  - content_digest
  - size
  - observed_timestamps
  - source_system
  - metadata_completeness_score
  - integrity_status
  - lineage_confidence
relationship: exact_duplicate | metadata_variant | revision_chain | near_duplicate | unresolved
canonical_member_id: <nullable until reviewed>
canonical_reason:
  - verified complete bytes
  - provider manifest membership
  - earliest credible captured_at
  - matching sidecar preserved
  - original object ID retained
review_status: automated_candidate | human_reviewed | approved
reviewer_and_time: <nullable>
retention_of_noncanonical: preserve_variant | storage_dedup_link | cold_archive | pending_decision
```

The reason must be legible enough that you can later answer: “Why did the system call this one the canonical copy?”

# Special Cases

## Media

For photos and videos, the canonical original is normally the highest-fidelity original file with credible capture metadata and intact sidecars. A newer edited JPEG, social-media download, thumbnail, or rendered preview is a derivative, not a replacement.

If a badly named `.HEIC`, `.DNG`, or original video has correct embedded capture metadata and a matching JSON/XMP sidecar, it should generally outrank a nicely named later copy lacking those facts. Preserve both, but mark the original as canonical and the later copy as derived/exported where supported.

## Documents and records

For records, preserve the earliest credible original or source-issued copy, but do not discard later revisions, annotations, signed versions, scanned copies, delivery copies, or related attachments. The canonical “original” and the canonical “current/operative” document may be different records and should be represented separately.

## Repositories and project folders

Do not dedupe repositories based on filenames or a subset of source files. Use tree manifests, commit history, remotes, lockfiles, configuration, and project context. A later repository may be the active working version; an earlier copy may be the earliest preserved snapshot. Keep both roles explicit rather than forcing one winner.

## Exports and backups

Two exports may contain many of the same objects but represent distinct captures at different times. Preserve each export root as a separate immutable source package. You may construct an object-level dedup map or canonical content store underneath it, but do not erase the fact that an object appeared in multiple exports.

## Recycle-bin restores

A restored copy may have a later restore or provider-modified date. That does not make it newer in substance than the original. Keep deletion/restoration events as provenance events, not as replacement original timestamps.

# Automation Boundaries

Automation may:

- Separate known recovery/recycle/recap roots into the controlled review areas.
- Generate manifests, hashes, metadata extracts, and candidate groups.
- Identify exact byte duplicates.
- Flag default epochs, implausible calendar values, timestamp conflicts, missing sidecars, or truncated files.
- Propose canonical ranking with recorded reasons and confidence.
- Auto-link high-confidence exact duplicates while preserving both occurrences and provenance.

Automation must not, without a separately approved policy:

- Delete recovered, recycle-bin, recap, or duplicate-candidate material.
- Overwrite an original timestamp with inferred, filename-derived, current, export, or ingest time.
- Rename the internal contents of recovery output.
- Collapse source-package provenance into a single surviving path.
- Promote a low-confidence recovery artifact into legal records, a project, or a source package.
- Treat an LLM summary/recap as an authoritative source or a replacement for raw data.
- Decide high-impact conflicts involving records, communications, credentials, repositories, backups, or potentially evidentiary material.

# Workflow

1. **Quarantine by origin.** Route recovery, recycle-bin, restoration, and recap roots to their controlled staging prefixes; preserve their internal tree and related reports.
2. **Capture baseline facts.** Record source path/key, recovery tool/provider, ingest batch, object metadata, timestamps as observed, checksums, and container membership.
3. **Detect type and dependencies.** Identify archives, repository roots, backup sets, media/sidecar sets, records bundles, exported databases, manifests, and loose fragments.
4. **Create candidate groups.** Compare content hashes first, then container manifests, embedded IDs, sidecars, structured metadata, and context.
5. **Rank—not delete.** Use the canonical selection hierarchy, emphasizing complete bytes, provenance, earliest credible original time, and metadata richness.
6. **Require review where necessary.** Hold anomalies, revisions, conflicting timestamps, incomplete objects, sensitive items, and uncertain lineage for review.
7. **Promote by link, not amnesia.** When an item is filed under a normal category, retain a backlink to the recovery/recycle/recap origin and candidate group.
8. **Retain alternatives.** Preserve noncanonical variants at least through a defined validation/retention window; storage-level deduplication is preferable to logical deletion where feasible.

# Acceptance Criteria

This addendum is implemented when:

- Recovery, recycle-bin, restoration, and recap material is separately identifiable and not casually mixed into ordinary collections.
- Every recovered/recycled item retains its recovery/provider provenance and observed timestamps.
- Recap files are classified as manifests, reports, inventories, human summaries, or machine summaries rather than treated as raw originals.
- Every canonical selection has a recorded candidate group, evidence basis, and review state.
- “Earliest timestamp” means earliest **credible original** time, not an epoch placeholder, malformed date, filename guess, export date, or current ingest time.
- A richly evidenced original can win even when its filename is poor, while a corrupt or incomplete file cannot win merely for being older.
- Revisions remain revisions; the system does not incorrectly deduplicate meaningful historical versions.
- No alternate copy is deleted simply because another member is marked canonical.
