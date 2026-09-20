---
title: Object Storage Preservation & Sorting Plan
status: owner-policy
tags: [consignatio, vault, policy, preservation, sorting, taxonomy, atomic-containers, dedupe, provenance, object-storage]
provenance:
  shared_by: owner, 2026-09-16 22:34 EDT, as F:/Users/matts/Downloads/Object-Storage-Preservation-and-Sorting-Plan.md (parent of the addendum shared 22:32)
  saved_by: "Claude Code · Fable 5.1 (session nifty-nash-6d261e)"
  saved_at: 2026-09-16T22:45:00-04:00
  addendum: 2026-09-16-recovery-recycle-recap-triage-and-canonicalization-addendum.md
  content: verbatim; only this front-matter block was added
---

*Prepared for Matt Salem · Structural migration and classification plan for a consolidated object-storage corpus. This is a logical organization model and execution protocol; it does not assume, require, or preserve any particular Google Drive behavior. No objects, prefixes, metadata, ACLs, retention settings, or versions are changed by this document.*

# Purpose and Operating Assumption

This plan is for a consolidated object-storage corpus assembled from cloud drives, Google Drive exports, device backups, local migrations, repositories, and other historical sources. The storage backend may be S3-compatible, cloud blob storage, a filesystem gateway, or a catalog layered across multiple buckets. The plan treats the corpus as an object set with source provenance, stable object identity, relative-path dependencies, optional object versions, and potentially duplicated source material.

Google Drive is only one possible source. Any Google-specific material remains classified as a **source package**, not as a special organizing principle for the entire archive. The same rules apply to exports from Microsoft, Apple, Meta, Android, browser profiles, chat platforms, local disks, NAS shares, Git repositories, recovery tools, and application backups.

The main rule is simple:

> Preserve source boundaries and internal relative paths first. Apply a useful working taxonomy only at the container level or through catalog metadata.

Do not flatten a source package, repository, backup image, application installation, media companion set, or matter-based record bundle merely because its contents could be distributed across more intuitive categories.

# Core Classification Model

Every top-level source prefix, collection root, or detected atomic container should receive metadata before any physical move or copy is considered.

| Field | Meaning | Example |
|---|---|---|
| `container_id` | Stable catalog identifier, never inferred from a mutable path | `ct_000184` |
| `source_system` | Origin system or migration source when known | `google_drive`, `onedrive`, `android`, `local_disk`, `unknown` |
| `source_account_or_device` | Optional account/device label, preferably an internal opaque ID | `gdrive_personal_01`, `pixel_7`, `win11_workstation` |
| `ingest_batch` | Consolidation or import batch identifier | `2026-09-15_migration_03` |
| `original_locator` | Original path, Drive ID, URI, or external identifier, retained verbatim where safe | `drive://...`, `C:\Users\...`, `s3://legacy/...` |
| `container_kind` | Classification from the taxonomy below | `source_export`, `repository`, `records_bundle` |
| `atomicity` | Whether its internal hierarchy must remain intact | `immutable`, `preserve_root`, `logical_collection`, `ordinary`, `unclear` |
| `integrity_status` | Hash/manifest and completeness state | `unverified`, `manifested`, `hash_verified`, `partial`, `corrupt_suspected` |
| `duplicate_status` | Duplicate relationship without deleting anything | `unknown`, `candidate`, `exact_duplicate`, `near_duplicate`, `canonical` |
| `sensitivity` | Access-handling classification | `standard`, `personal`, `confidential`, `restricted`, `credential_material` |
| `retention_status` | Keep/review/dispose decision state | `preserve`, `review`, `pending_dedup`, `legal_hold`, `retired` |
| `access_profile` | Intended working use, not a security guarantee by itself | `active`, `reference`, `cold_archive`, `quarantine` |

The canonical catalog record—not the current prefix—is the source of truth. A move or re-key operation changes a locator; it must not replace provenance, hashes, source identifiers, or the prior locator history.

# Destination Architecture

The categories below deliberately remove the numbered “preview” structure and avoid a Drive-oriented hierarchy. They separate **working material**, **preserved source packages**, **records**, **media**, **code**, and **review states** without implying that everything must be physically rearranged.

```text
catalog-root/

inbox-and-intake/
  unclassified/
  intake-manifests/
  pending-classification/
  failed-or-partial-ingest/

source-packages/
  cloud-service-exports/
  device-and-application-exports/
  messaging-and-social-exports/
  backup-sets-and-system-images/
  legacy-migrations/
  archive-files-and-bundles/

projects/
  software-and-services/
  data-ai-and-agents/
  infrastructure-and-automation/
  home-property-and-hardware/
  creative-and-production/
  research-workspaces/

code-and-repositories/
  active/
  archived/
  mirrors-and-vendor-snapshots/
  releases-and-build-artifacts/

records/
  financial-and-tax/
  property-insurance-and-construction/
  legal-and-case-materials/
  business-and-professional/
  personal-and-household/
  health-and-sensitive-personal/

knowledge-and-research/
  notes-and-writing/
  source-materials-and-reading/
  datasets-and-methods/
  document-collections/
  chat-and-agent-exports/
  reference-archives/

media/
  camera-and-device-originals/
  source-export-media/
  edited-and-derived/
  scans-and-documents/
  screenshots-and-captures/

review-and-control/
  duplicate-candidates/
  unclear-containers/
  incomplete-or-broken-projects/
  security-or-quarantine-artifacts/
  sensitive-exports/
  access-restricted/

manifests-and-audit/
  inventory-snapshots/
  path-and-key-history/
  checksums/
  duplicate-analysis/
  move-copy-and-restore-plans/
  policy-and-classification-decisions/
```

## Category intent

### `inbox-and-intake`
Newly consolidated material that has not yet received a durable classification. It is not a dumping ground: each object or prefix should have an ingest batch, observed source, original locator, and provisional status. Material should leave this area through metadata and a controlled promotion process, not by ad hoc drag-and-drop sorting.

### `source-packages`
Immutable or near-immutable captures from another system. This includes service exports, device exports, browser exports, application backups, disk snapshots, archive files, and migration payloads. Keep the source root, manifests, sidecars, timestamps, and internal hierarchy intact.

A Google Takeout folder belongs here as `source-packages/cloud-service-exports/google/...`, but so do OneDrive exports, Facebook downloads, Android backups, local disk images, iCloud exports, and app-specific export bundles. The category is source-neutral.

### `projects`
Human working collections whose internal files are not necessarily formal repositories but whose context matters: AI workflows, evidence engines, research environments, hardware/automation work, construction documentation, operational notes, and creative projects. A project may contain code, prompts, assets, notes, and generated outputs when those things are one working unit.

### `code-and-repositories`
Repository roots, source mirrors, vendor snapshots, releases, and build artifacts. Each repository root remains atomic. Do not distribute its `src`, tests, docs, configuration, `.git`, lockfiles, submodules, vendored dependencies, or local tools into category folders.

### `records`
Matter-based, account-based, and year-based records. Keep a records bundle together when it documents the same account, property, legal matter, tax year, claim, transaction sequence, or household event. Access control should be stronger here than in general working storage.

### `knowledge-and-research`
Reusable intellectual material: research sessions, source readings, datasets, methodologies, notes, prompts, chat exports, reference collections, and document-analysis outputs. Where a chat export, source documents, prompts, and synthesis outputs form one research thread, preserve them as a named document collection rather than scattering them by file extension.

### `media`
Original media, source-export media, edited derivatives, scans, and screenshots. Preserve photo/video sidecars and companion relationships. A source export containing media stays intact in `source-packages`; `media/source-export-media` may hold a **derived working copy** only when that is explicitly useful and its relationship to the preserved package is cataloged.

### `review-and-control`
Material that cannot safely be classified, deduplicated, or opened for routine access yet. This is a controlled status zone, not an archive destination. It includes recovery artifacts, partial exports, duplicate candidates, credential-bearing exports, potential quarantine artifacts, and access-restricted material.

### `manifests-and-audit`
Machine-readable inventory and decision records. Keep this separate from the corpus so it can document every ingest, transformation, physical relocation, checksum result, duplicate relationship, retention decision, and restoration path.

# Atomic-Container Rules

A container can be physically stored under one category while remaining discoverable through many catalog facets. Do not solve retrieval by splitting containers.

| Container kind | Atomicity | Preservation rule | Typical evidence |
|---|---|---|---|
| Service or platform export | Immutable | Preserve the export root, manifests, indexes, sidecars, and internal tree unchanged | Export manifest, `start_here.html`, account export naming, provider metadata |
| Device backup or communications export | Immutable | Keep date-paired calls/messages, databases, attachments, indexes, and metadata together | Timestamped XML/JSON/SQLite, app export structure |
| Backup set, disk image, or app installation snapshot | Immutable | Move/copy only as a whole prefix; do not “clean” caches or split dependencies during preservation | Disk image, restore metadata, `.git`, environment files, bundled plugins |
| Software repository | Immutable | Preserve the repository root and relative structure; catalog it independently | `.git`, `package.json`, `pyproject.toml`, `Cargo.toml`, lockfiles, source/test layout |
| Media companion set | Preserve root | Keep original, RAW/JPEG/HEIC/video, JSON/XMP, thumbnails, and edit sidecars associated | Filename stems, XMP/JSON sidecars, camera naming |
| Records bundle | Preserve root | Retain by matter, account, case, property, or year; do not split by document extension | Statements, invoices, correspondence, supporting records |
| Project workspace | Preserve root | Keep code, prompts, notes, generated artifacts, and project-specific data together when context depends on them | README, task docs, workflow files, shared naming/timestamps |
| Archive file | Immutable | Treat ZIP, 7z, tar, WARC, PST, OST, disk images, and forensic containers as objects; do not unpack for filing | Archive extension, manifest, tool-specific metadata |
| Loose ordinary object | Ordinary | Classify through metadata or a controlled collection prefix | No package or dependency signature |
| Recovery/quarantine artifact | Unclear | Preserve without normalizing names, contents, or timestamps until reviewed | `$Folder...`, `FOUND.000`, quarantine naming, recovery-tool patterns |

## Rules that apply across sources

- Preserve original object keys or paths in metadata even after re-keying.
- Preserve object modification times, content type, source IDs, checksums, version IDs, and custom metadata when the backend supports them.
- Do not rename objects inside an atomic container.
- Do not infer duplicates from names, dates, folder names, or cloud-provider IDs alone.
- Do not merge two package roots merely because their internal filenames overlap.
- Do not delete a duplicate candidate as part of organization.
- Do not turn source exports into a general working-media or records tree; create a derivative collection only when needed and record its parent package.

# Object-Storage Mechanics

The old plan assumed folder moves. Object storage generally has prefixes rather than real directories, and a “move” is typically a copy to a new key followed by deletion of the original. That changes the safety model.

## Prefer logical organization first

For the consolidated corpus, favor a catalog/index layer with tags and stable IDs over mass physical rearrangement. A single preserved object can appear in multiple views without duplication:

- `container_kind=repository`
- `project=knowledge-platform`
- `source_system=google_drive`
- `ingest_batch=2026-09-15_migration_03`
- `sensitivity=confidential`
- `duplicate_status=candidate`
- `access_profile=cold_archive`

This gives you browse paths such as “all repositories,” “all family-court materials,” or “all Google-origin exports” without changing the object’s canonical preservation location.

## If physical re-keying is necessary

Treat every prefix move as a copy-verify-commit operation:

1. Freeze a source manifest: object key, size, version ID/ETag where meaningful, checksum, last-modified time, content type, custom metadata, ACL/policy state, and source container ID.
2. Write a destination plan that maps every source object key to exactly one destination key.
3. Copy, never rename in place. Preserve metadata explicitly; many object-store copy APIs replace metadata unless instructed otherwise.
4. Verify destination object count, byte total, checksum where supported, and container manifest completeness.
5. Preserve the source copy through a defined validation window or legal/retention policy.
6. Mark the catalog record as relocated only after verification.
7. Delete source keys only through a separately approved retention/dedup action, preferably with versioning, object lock, or recoverability enabled.

A “folder” move must be all-or-nothing from the catalog’s perspective. If 9,998 of 10,000 objects copy successfully, the container remains `partial`, and its source remains authoritative.

## Versioning and immutability

For source packages, records, legal material, backups, and credential-adjacent exports, use the strongest preservation controls available in the backend:

- Bucket/container versioning before re-keying or cleanup.
- Object-lock, WORM retention, or equivalent controls where the data merits it.
- Separate retention policies for active projects versus source packages.
- Lifecycle transitions to colder storage only after retrieval and restore behavior are tested.
- A replicated manifest and, where practical, a second storage location for high-value preservation packages.

Do not rely on ETags as cryptographic content hashes: multipart uploads and provider-specific implementations make them unsuitable for universal integrity verification. Store a separately calculated content digest such as SHA-256 or BLAKE3 in the manifest/catalog when byte-level validation matters.

# Deduplication Policy

Consolidation creates repeated material by design. The right outcome is not “one copy everywhere”; it is a recorded relationship between source packages and canonical blobs.

## Three distinct duplicate questions

| Question | Meaning | Safe response |
|---|---|---|
| Exact object duplicate | Same bytes, confirmed by content hash | Record the relationship; retain source-package provenance even if storage-level dedup is used |
| Duplicate container | Two package roots have matching manifests and equivalent object content | Keep both provenance records; select a canonical preservation copy only after comparison |
| Near duplicate | Overlapping export snapshots, parallel installs, edited media, or similar repositories | Keep both until their purpose and difference are understood |

## Recommended implementation

- Hash objects during ingest or in a dedicated verification job.
- Build a Merkle-style container manifest: sorted relative key, size, digest, and selected metadata for each object.
- Compare containers by manifest, not by display name or prefix.
- Store `canonical_container_id` and `duplicate_of_container_id` relationships in the catalog; do not encode the decision only in a suffix like `_dupe`.
- Where content-addressable storage is available, deduplicate the bytes below the catalog layer while preserving separate logical object and source-package records.
- Never deduplicate credential exports, legal records, backups, or security/quarantine artifacts solely to save storage without a retention and access-control review.

# Sensitive and Restricted Material

The consolidation corpus likely includes password exports, browser autofill CSVs, private communications, legal material, financial records, account exports, presigned links, device backups, and potentially security-tool artifacts. Those require a separate access policy from ordinary project data.

## Required handling

- Put plaintext password and autofill exports in `review-and-control/sensitive-exports` or a separate restricted bucket/container—not under normal records.
- Encrypt at rest using a distinct key or key policy where your platform supports it, and restrict read access to the smallest practical identity set.
- Avoid indexing secrets into full-text search, embeddings, logs, error traces, thumbnails, previews, or agent context by default.
- Scan filenames and extracted text for access tokens, signed URLs, API keys, private keys, cookies, and database credentials before broad indexing.
- Treat a file containing a presigned URL or secret-bearing filename as sensitive even if its object content is otherwise harmless.
- Preserve quarantine or recovery artifacts unchanged until you know their origin and intended treatment.
- Record access and materialization events for restricted packages, especially if agents, OCR, or content-extraction pipelines can read them.

# Suggested Catalog Facets

Use these as filters and virtual views rather than generating new physical category trees for every dimension.

| Facet | Example values |
|---|---|
| Source | Google Drive, OneDrive, local disk, Android, browser, GitHub, unknown migration |
| Ingest | Batch/date/tool/operator/checksum status |
| Structure | Source package, repository, backup, records bundle, media set, loose object |
| Work state | Active, reference, archived, review, quarantine |
| Subject | AI/data platform, home automation, property, family legal, financial, research, personal media |
| Sensitivity | Standard, personal, confidential, restricted, credential material |
| Integrity | Unverified, manifested, hash verified, partial, corrupt suspected |
| Duplicate state | Unknown, candidate, exact duplicate, near duplicate, canonical |
| Retention | Preserve, pending review, legal hold, cold archive, retirement candidate |

# Transition Plan

## Phase A — Stabilize and inventory

- Enable or confirm object versioning and preservation safeguards before any large copy/re-key operation.
- Snapshot current bucket/prefix listings and object metadata.
- Assign stable `container_id` values at detected roots before categorization.
- Generate per-container manifests and record an ingest/baseline timestamp.
- Identify objects that are too large, cold-tiered, locked, encrypted with unavailable keys, or partial before planning moves.

## Phase B — Classify without moving

- Apply `container_kind`, `atomicity`, `source_system`, `sensitivity`, and `retention_status` metadata.
- Create virtual views or catalog queries for the proposed categories.
- Identify all source-package roots, repositories, backup sets, records bundles, media companion sets, and unclear artifacts.
- Send uncertain material to `review-and-control` logically; do not rename ambiguous roots or normalize recovery/quarantine names.

## Phase C — Verify duplicates and relationships

- Hash and manifest duplicate candidates in batches.
- Compare source-package and repository roots at the container level.
- Mark exact duplicates, overlap relationships, and canonical candidates in the catalog.
- Keep all original source packages until a dedicated retention decision is approved.

## Phase D — Controlled physical normalization

Only if physical prefix normalization materially improves operations:

- Re-key one low-risk, non-atomic collection first.
- Use copy-verify-commit with a durable source-to-destination manifest.
- Preserve relative paths below each atomic root.
- Test restore, listing, search, presigned access, lifecycle behavior, and application references after the pilot.
- Promote the pattern incrementally; never run a blind global folder move across the corpus.

## Phase E — Build working derivatives

- Create explicit derived collections for active media, extracted documents, searchable text, embeddings, OCR, previews, or project workspaces.
- Attach `derived_from_container_id` and `derived_from_object_digest` to every derivative.
- Keep derived artifacts disposable and regenerable where possible; keep source packages and records authoritative.

# Examples

## Example: cloud export

A folder that originated as Google Takeout, OneDrive export, Facebook download, or a vendor data export is classified as:

```text
container_kind: source_export
atomicity: immutable
access_profile: cold_archive
integrity_status: manifested
source_system: <actual provider>
```

Its canonical storage prefix can be:

```text
source-packages/cloud-service-exports/<source-system>/<source-account-or-opaque-id>/<export-date-or-ingest-batch>/<container-id>/
```

The internal export tree remains untouched. If media from it is useful in a working photo library, create a derived media view or copy with provenance, rather than dismantling the export.

## Example: repository or application install

A ComfyUI installation, AI tool, MCP server, workspace tool, or other source project is classified as a repository or application snapshot. The parent collection may be organized under `code-and-repositories/active` or `projects/data-ai-and-agents`, but each project root retains all relative files, including `.git`, lockfiles, configuration, custom nodes, scripts, local documentation, and vendor-specific directories.

## Example: records and credential exports

Tax records, property records, legal matter folders, and financial documents can be classified by matter/year under `records`. Browser-password CSVs, autofill dumps, session material, private keys, and signed-link artifacts do **not** travel with those records; they stay restricted until you decide whether they need retention, secure vault import, rotation, or disposal.

# Acceptance Criteria

The organization is successful when:

- Every ingested object has a known source or a declared `unknown` provenance state.
- Every atomic container has a stable ID, manifest, and preservation classification.
- No internal path of a repository, source export, backup, archive, or records bundle has been split merely for taxonomy.
- The catalog can answer “where did this come from?”, “what container does it belong to?”, “is it verified?”, “is it duplicated?”, “who may access it?”, and “what derived artifacts came from it?”
- Physical moves have complete source-to-destination manifests and verified object counts/bytes/checksums.
- Duplicate candidates are recorded rather than silently removed.
- Sensitive material is excluded from general indexing and protected by an explicit access model.
- A low-risk restore test has proven that the archive is operational, not merely well labeled.

# What Changed From the Drive Plan

- Removed all numbered category prefixes and the old numbered preview hierarchy.
- Replaced Google Drive as the organizing assumption with source-neutral object-storage concepts: object keys, prefixes, immutable packages, catalog metadata, versioning, manifests, and copy-verify-commit re-keying.
- Kept Google-origin exports only as one source type under `source-packages`, alongside every other cloud, device, application, and local migration source.
- Replaced “folder move” language with safe object-store mechanics, including metadata preservation, version-aware rollback, checksum verification, and partial-copy handling.
- Added a catalog-first model so one preserved object can be discoverable across multiple categories without destructive physical reorganization.
- Expanded duplicate handling from name-based cleanup to content, container-manifest, provenance, and canonicalization relationships.
- Added explicit handling for lifecycle tiers, object locking, secrets exposure through indexing, derived artifacts, and access-restricted data.
