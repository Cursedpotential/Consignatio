# Source metadata capture and forensic packages — feature specification

> _Byline: Claude Code · Opus 5 · 2026-09-13_

**Status:** SPECIFIED, not implemented. Owner direction 2026-09-13 23:26–23:32 EDT.
No code, API call, or credential change has been made for this feature.

## 1. What this feature is

This is a feature of **Intake**, the Consignatio Vault work surface. It is not a separate tool. It gives the
operator better access, more readable metadata, and more provenance for files that still live at a
provider (Google Drive first), now and later, without moving them.

Siblings in the connected-sources family (milestone M4):

| Sibling feature | Role |
|---|---|
| Source viewer (Filestash / OpenList) | Browse and open files where they live |
| Photo library snapshots (Immich / PhotoPrism) | Frozen album membership plus metadata |
| **Source metadata capture and forensic packages** (this spec) | Provider metadata, history, sharing, and comparison, selectable or complete |

It serves the organizing workflow **find → group → compare → decide → move**, and the stage where a file
becomes important: evidence promotion, tracing a source, proving provenance.

## 2. Two modes

### Mode A — Selective capture (flexible, GUI-driven)

The operator chooses which metadata items to pull. The choice is not a fixed script.

- **Field catalog panel:** a searchable tree of provider → resource → field, for example
  Drive → file → `sha256Checksum`, Drive → revisions → `lastModifyingUser`, and Drive → permissions → `role`.
- **Operations:** select, filter, add, subtract, and select a whole resource or a single field.
- **Profiles:** save a field choice under a name (for example "dedupe basics", "sharing audit",
  "chronology") and reuse, edit, or combine it.
- **Scope:** runs over any selection (single file, group, folder snapshot, or query result).
- **Estimate first:** before running, show the item count, the expected API calls, and whether any
  bytes would be downloaded or exported. Metadata-only is the default.
- **Results:** captured fields become grid columns, facets, and preview-pane tabs. Profiles and
  captures are versioned. Re-running appends a new observation and never overwrites the old one.

### Mode B — Forensic package (the full kitchen sink, complete and validated)

**Owner operating model (2026-09-14):** as files are selected as evidence, each one gets its evidence packet. The packet
is captured on demand from the source while the item still exists there. There is no bulk pre-capture of whole accounts.

The forensic package is triggered on a selection from the GUI. Intake suggests it when an item is flagged
important or queued for promotion.

- **Entire capture:** every item in the provider's capability census (§3), not just a large profile.
- **Validated complete:** the package carries a completeness receipt (§4). "Complete" is proven
  against the census, never asserted.
- **More if more exists:** when a later census finds fields or endpoints that the package lacks, the package
  is flagged `more_available` and a supplement capture adds a new immutable version.
- **Contents** (Drive; other providers map to their equivalents):
  - Raw API responses, byte for byte, for every call, with request parameters.
  - Normalized records derived from the raw responses. They never replace the raw responses.
  - The full file resource (every readable field), parents and derived paths, and shortcut targets.
  - Permissions, including inherited permissions and details, plus sharing and capability flags.
  - Every revision record, and the **bytes of every downloadable revision**.
  - Comments and replies, including resolved and deleted states where they are returned.
  - Drive Activity events for the item.
  - Labels and field values, `properties`, `appProperties`, and content restrictions.
  - Current content bytes, or for Google-native files **every export format the provider offers**.
    Exports are labeled derived representations.
  - Local SHA-256 (and BLAKE3) computed on the captured bytes and compared with every provider hash. A
    mismatch is recorded, never silently resolved.
  - **Capture context:** account identity, granted scopes, API and discovery-document revisions, tool
    version, and start/end timestamps.
  - **Integrity:** a hash of every artifact, a manifest hash, and immutability. Supplements are new
    versions, never edits.
- **Authority:** Intake builds the package. Custody and evidence promotion stay with Platform, which
  receives the package as provenance. A package is not a legal acceptance.

## 3. Capability census — how "everything we can get" is defined

For each provider, a census is built **from the provider's own machine-readable API description at
capture time**. It is not a hand-written list.

| Provider | Census sources |
|---|---|
| Google Drive | Google API Discovery documents for Drive v3, Drive Activity v2, and Drive Labels. The census covers every readable field of every resource and every read method applicable to a file. |
| OneDrive / SharePoint | Microsoft Graph `$metadata` for `driveItem` and its navigation properties (versions, permissions, thumbnails, activities, analytics, and so on) |
| Google Photos and other Google services | Their Discovery documents. Account-type and API-policy limits are recorded as census entries. |
| Local filesystem, B2/S3 | Declared capability lists (stat fields, alternate streams, object headers, versions), in the same shape |

The census doubles as the Mode A field catalog, so both modes always offer the same universe of fields.

## 4. Completeness receipt

Every census entry receives exactly one status in the forensic package:

| Status | Meaning | Blocks COMPLETE? |
|---|---|---|
| `captured` | Value or response stored | no |
| `empty` | Provider returned nothing for this item | no |
| `not_applicable` | Does not apply, with a stated reason (for example, no checksum for a native Doc) | no |
| `not_supported_for_account` | Provider does not offer it for this account type, with a reason | no |
| `denied_scope` | Obtainable with a scope that was not granted | **yes** |
| `unavailable_error` | Call failed, throttled, or timed out | **yes** |

- The package is **COMPLETE** only when no entry is `denied_scope` or `unavailable_error`. Otherwise it is
  **PARTIAL**. The GUI lists the named gaps with a **Get more** action (retry, or request the missing
  scope).
- Re-running the census flags `more_available` on older packages when new entries appear.
- The receipt itself is hashed into the package manifest.

## 5. Provider contract (shared by every provider)

The contract builds on MASTER-TODO CBX-P10-001 (`sources/base.py`) and the plan's `ConnectorSnapshot`.

| Operation | Behavior |
|---|---|
| `census()` | Build or refresh the capability census and field catalog from provider schemas |
| `browse()` / `list()` | Paged listing with native IDs and change tokens, with no content reads |
| `capture(selection, field_selection)` | Mode A. Bounded, estimated, append-only observations |
| `capture_forensic(selection)` | Mode B. Full census capture plus the completeness receipt |
| `verify(package)` | Re-check artifact hashes, the manifest, and provider-hash agreement |

| Model | Required content |
|---|---|
| `FieldCatalog` | provider, census revision, resource/field tree, applicability rules, byte-reading flag |
| `CaptureProfile` | ID, name, selected catalog entries, version, creator |
| `CaptureResult` | selection manifest, profile version, per-field values plus raw-response references, observed time |
| `ForensicPackage` | item native ID, version, artifacts, capture context, manifest hash, predecessor version |
| `CompletenessReceipt` | census revision, per-entry status plus reason, overall COMPLETE/PARTIAL, gaps |

**Direct to source (owner hard rule 2026-09-14 00:14 EDT):** capture always talks to the provider's own API
(Drive API or rclone's native Drive backend, Graph, S3/B2 API, local filesystem). It **never** goes through an abstraction
layer: openlist, WebDAV gateways, Filestash, rclone mounts, or any viewer. Those layers are for everyday access by apps
that can't read the native storage. They hide or drop provider metadata and per-file lookups; openlist silently copied
0 of 22,565 files on 2026-09-13.

**Credential shards (owner constraint 2026-09-14):** the owner's Google accounts are consumer accounts, and a
single project/OAuth client cannot hold the full recommended scope set. Capture uses **several GCP projects, each
with a smaller scope bundle**. The contract must:
- map every census entry to the scope bundle (shard) able to read it, and route calls to that shard;
- record in the receipt which shard captured each entry;
- mark an entry `denied_scope` when no current shard holds its scope. This is fixable by adding a shard, and the GUI shows
  which bundle would cover it.
- mark an entry `not_supported_for_account` when Google does not offer it to consumer accounts at all. This is a
  permanent ceiling.
- state explicitly that COMPLETE means complete against the **consumer-account ceiling**, never the Workspace
  maximum.

Creating projects, OAuth clients and scope grants is an owner action. The app proposes bundles and never creates them.

**Identity:** the provider's native file ID is the occurrence identity. Provider and local hashes link it to
the same content at R2, B2, OneDrive, and local disks through the cross-store hash ledger. Every occurrence is
kept, and matching copies corroborate rather than collapse.

## 6. How it connects to Intake's existing features

| Feature area | Addition |
|---|---|
| Import & inspect | Each capture is a connector snapshot that opens through the DatasetAdapter |
| Search & sort | Facets such as owner, sharing, revision count, first-revision date, and shortcut, plus provider-hash search |
| Selection & organization | SelectionManifest over native IDs, plus frozen dated folder-membership snapshots |
| Review & history | Revisions, comments, and activity form each item's history timeline, with source, proposal, and human decision kept as separate layers |
| Documents & media | Metadata tabs and derived-export labels in the preview pane, plus side-by-side comparison |
| Dedupe & classification | Provider checksums enter the hash ledger with algorithm and scope provenance. First-revision, created, and activity dates enter oldest-real-date grading as date assertions. |

## 7. Provider rollout

1. Google Drive: CBX-P10-004.
2. OneDrive / SharePoint via Graph: CBX-P10-006 and CBX-P10-007.
3. Google Photos and other Google services under review.
4. Local filesystem and B2/S3 in the same contract shape.

## 7a. Census facts verified 2026-09-13 23:58 EDT (read-only, public discovery docs + local gcloud)

- Google Discovery directory: 314 preferred APIs. Drive-family and related candidates: `drive v3`,
  `driveactivity v2`, `drivelabels v2`, `admin reports_v1`, `vault`, `alertcenter`, `cloudidentity`,
  `dataportability v1`, `people`, `gmail`, `calendar`, `keep`, `tasks`, `docs`, `sheets`, `slides`,
  `forms`, `script`, `youtube`, `workspaceevents`. `photoslibrary` is not in the directory.
- Drive v3 (rev 20260904) has 54 schemas and 64 methods. Its read methods include `approvals.get/list` and
  `accessproposals.get/list` in addition to files, revisions, comments, replies, permissions, changes,
  drives and about. These two resources are not yet named in §2, and the census absorbs them automatically.
- Drive Activity v2 (rev 20260908) has a single `activity.query`. Drive Labels v2 (rev 20260909) has 26 methods.
- Data Portability v1 (rev 20260910) has 73 scopes covering chrome, maps, myactivity, youtube, play, nest, pixel, shopping and
  others. **No drive, photos or gmail groups** appeared in the scope list, so it is not a Drive provenance route
  (to be confirmed by the research doc).
- GCP project `drive-479520` has enabled docs, drive, driveactivity, drivelabels, drivemcp, gmail, people,
  photoslibrary, photospicker, picker and sheets. It is probably the OAuth-client project (unverified).
- Full applicability research: `GOOGLE-API-PROVENANCE-CENSUS-RESEARCH-2026-09-13.md` (in progress).

## 7c. What already exists for Drive, and research findings that change this spec (2026-09-14)

**Existing direct Drive access (owner ruling 00:08 EDT, relayed by the consignatio-d6 session):** Drive is reached
**directly through rclone on the VPS** (`RCLONE_CONFIG=/data/consignatio/secrets/rclone-gdrive.conf` →
`gd_salemnet:`, `gd_salem85:`, using rclone's own OAuth client with the `drive` scope). `rclone lsjson -R --files-only -M --hash`
lists metadata and hashes with no downloads. openlist is a viewer only.

**Already captured: the 2026-09-13 inventories** (~~`E:/AI_Workspace/_receipts/corruption-hunt/hashes/`~~ moved 2026-09-15 to `Consignatio/docs/receipts/corruption-hunt/hashes/`, copies in
`b2:salem-data/consignatio/intake/_system/source-inventories/20260913/`). Verified by reading the files on 2026-09-14:

| | gd_salemnet | gd_salem85 |
|---|---|---|
| Records | 125,763 | 12,562 |
| Top-level fields | Path, Name, Size, MimeType, ModTime, IsDir, ID, Hashes, Metadata | same |
| Hashes | md5 all; sha1/sha256 on 103,308 (≈22.4k md5-only) | md5 all; sha1/sha256 on 12,551 |
| Metadata present | btime, mtime, owner, starred, viewed-by-me, writers-can-share, copy-requires-writer-permission, content-type; custom properties `CACRFLNM` (674), `SMBR_BACKUP_*` (121), `description` (100), `save_to_pdf_*` (46) | same core fields; `CACRFLNM` (3,977), `description` (14) |
| **Not present** | **permissions, labels, revisions, comments, activity, native exports** | same |

**rclone Drive reach (flags verified in local `rclone help backend drive`, v1.74.4, 2026-09-14):**
- `--drive-metadata-permissions read` adds a `permissions` JSON array. On shared drives only non-inherited permissions are included.
- `--drive-metadata-labels read` adds `labels` (consumer accounts are expected to return empty; see research).
- `--drive-metadata-owner` controls `owner`.
- These are metadata-only listing flags. They add API calls per file and download nothing.
- **rclone does not expose revisions, comments/replies or Drive Activity.** Those need the Drive and Drive Activity APIs
  directly.
- **Native Google Docs/Sheets/Slides were excluded** from the 2026-09-13 inventories (`--drive-skip-gdocs`, per the
  consignatio-d6 session). They have no bytes or checksums and need an export pass (`--drive-export-formats`, or the API
  `files.export` for every offered format). Until an export runs, native Docs are neither inventoried nor copied
  to B2. **Owner 2026-09-14 01:47 EDT: all native Docs must be exported into the Vault in general, so they are searchable**.
  They are not only evidence-packet material. Skipping them was a mistake. A general export job is queued in
  `Consignatio/docs/URGENT-TODO.md`. Evidence packets additionally export every offered format per selected item (§2).
- **✅ Native export COMPLETE (2026-09-14 ~04:05 EDT).** 3,120/3,120 exports on B2. The one Google refusal succeeded on
  retry at 08:03 UTC. **Verified independently** (Claude Code · Opus 5, read-only PG): `raw_duck.source_occurrences` has
  32 (salem85) + 1,528 (salemnet) rows with disposition `exported`. Every row has `b2_key` (Office) and
  `metadata.pdf_key`, and 0 are missing from `raw_duck.b2_objects` (listing 2026-09-14 08:04:49 UTC). The catalog rows,
  not the idmaps, are the Intake input. Loader: `casebible/tools/gdrive_native_exports_load.py`.
- **Native export run history (2026-09-14 02:06 EDT, consignatio-d6):** unit
  `consignatio-gdrive-native-export-20260914`, Office + PDF, placed in the native file's own folder under
  `source-buckets/gdrive/<acct>/`. Naming: unique paths get `<name>.<ext>`; same-path groups and clashes get
  `<name> [gdoc-<id8>].<ext>` (salemnet 421 plain + 1,107 suffixed; salem85 26 + 6). Nothing is overwritten
  (`--immutable`). **Catalog inputs:** `/data/consignatio/migrations/gdrive-copy-20260913/native-export-<acct>-idmap.tsv`
  (driveId, native path, office name, pdf name, mime, modtime) and receipts
  `native-export-<acct>-{office,pdf}.copyid-*.receipt.jsonl`. These files are export receipts.
  **Canonical occurrence catalog (live 2026-09-14, PG `casebible` on ovh-files, reported by consignatio-d6):**
  `raw_duck.source_occurrences` has one row per source file across all sources: PK (source, scope, path), size, modtime,
  `source_id` (Drive/OneDrive ID), native hash kind and value, md5, `disposition` (content_on_b2 | pending_carrier | to_copy |
  copied | zero_byte | junk_excluded | pending_hash), `b2_key`, `matched_origin`, and provider `metadata` jsonb. There is also
  `raw_duck.b2_content` ((md5,size) → b2_key, 235,281 payloads), `raw_duck.b2_objects` and `raw_duck.graded_carriers`.
  The Intake census and catalog read these tables, not the raw ID maps. **Join rule:** "md5 in r2_files" ≠ "bytes on B2";
  always join through `b2_content`. Both Drives and D:\Backup load as their baseline and hash jobs finish.
- **Detecting native items in rclone listings** (reported by consignatio-d6, 2026-09-14): rclone reports native files
  under their *export* MIME type (docx/xlsx/pptx per `--drive-export-formats`) with `Size: -1`, not
  `application/vnd.google-apps.*`. Detect them with `Size == -1`. Reported counts: salemnet 1,528 (1,426 Docs, 100 Sheets,
  2 Slides; 1,407 under "Court & Legal Project"); salem85 32 (30 Docs, 2 Sheets).

**Two-tier capture (owner 2026-09-14 01:48 EDT):**
- **Tier 1, broad and cheap, for every file:** pull everything rclone can list, because listing is cheap and downloads
  nothing: `rclone lsjson -R --files-only -M --hash --drive-metadata-owner read --drive-metadata-permissions read
  --drive-metadata-labels read`, **without** `--drive-skip-gdocs`, direct from the source on the VPS. This supersedes
  the 2026-09-13 inventories as the baseline snapshot. The job is queued in `Consignatio/docs/URGENT-TODO.md`, and a dry-run
  estimate plus owner sign-off come first.
- **Tier 2, follow-up per item (evidence packets):** tooling to reach everything rclone cannot, using the **Google Cloud
  CLI** and direct APIs (revisions, comments/replies, Drive Activity, native exports in every format, People actor
  resolution, Gmail notifications). The tooling must be available when the owner decides to follow up on an item.
  State on 2026-09-14: local gcloud is signed in as matt.salemnet. The gadmin (Cloud CLI) MCP needs reconnecting
  with more permissions. Calling Drive/Activity APIs with gcloud credentials needs a login that grants those scopes
  (per shard, §5). Exact commands are UNVERIFIED.

These inventories are the first captured Mode A snapshots. Nothing listed as "not present" has been captured yet.
It is captured per item when the item is selected as evidence (§2). A salemnet wipe is on the owner's to-do list but
far off and not a driver for this feature (owner 2026-09-14 01:46 EDT).

**Research findings** (`GOOGLE-API-PROVENANCE-CENSUS-RESEARCH-2026-09-13.md`, subagent, public docs, some
entries UNVERIFIED):
- Drive `createdTime`/`modifiedTime` can be set by the uploading client, and btime/mtime inherit that. **Drive
  Activity's create/upload/copy event is the server-observed anchor** and outranks them in date grading.
- Revision bytes are downloadable only for keepForever revisions, and revision lists can be truncated for heavily edited
  Docs. The first revision's date is not proof of origin.
- Drive Activity has no view or download events, and its history horizon is undocumented.
- **No data for consumer accounts:** Drive Labels, Approvals (inferred), Admin Reports/Directory, Vault, Alert
  Center, Cloud Identity, and the Keep API. These census entries are `not_supported_for_account`.
- Photos Library API can only read app-created media since 2025-03-31. The Picker needs manual selection and strips GPS.
  The full Photos package is Takeout-only.
- Every full-reach Drive and Gmail read scope is **restricted**. Unverified testing-mode apps get 100 test users and
  7-day tokens. No documented per-project scope-count limit was found.
- **Sources to add to the census:** Gmail share and comment notification emails, People API (resolves Activity
  actors), Calendar event attachments pointing to Drive files, Forms response timestamps, YouTube `fileDetails`
  (original filename and creation time).
- Proposed scope bundles and live-check order: research doc §6–§7. The last check writes a test file and needs separate
  owner approval.

## 7b. Account-level provenance sources (owner 2026-09-14 00:00 EDT: "these are also important and that's a great find")

The feature captures **account-level** data as well as **file-level** data. Account data (activity, history, location,
devices) can corroborate or date what happened around a file or event.

> **⚠️ Correction 2026-09-14 00:20 EDT (Claude Code · Opus 5): region-gated.** Google's help page
> (support.google.com/accounts/answer/14452558, fetched 2026-09-14) lists availability only for EU countries,
> Switzerland and the United Kingdom. **US-associated accounts are not eligible.** For the owner's accounts every
> `dataportability.*` census entry is therefore `not_supported_for_account` (reason: region), not `denied_scope`.
> One `accessType.check` call per account would confirm this. Takeout remains the route for this data. Details:
> research doc §4. Also, when eligible, these scopes cannot be combined with other scopes in one consent,
> download URLs last 6 h and data 14 days.

- **First source: Data Portability API**, the programmatic Takeout for consumer accounts. Groups verified in its scope
  list: `myactivity` (search, maps, youtube, play, shopping, myadcenter), `chrome` (history, bookmarks,
  autofill, extensions, reading list, settings, dictionary), `maps` (starred/aliased places, commute, reviews,
  contributions, photos/videos, vehicle/EV profile), `mymaps`, `youtube` (channel, videos, playlists, comments,
  live chat, music, posts…), `play` (installs, library, devices, purchases…), `nest` (camera events/video,
  user, store), `pixel.device_data`, `shopping`, `order_reserve`, `saved`, `discover`, `search_ugc`,
  `searchnotifications`, `streetview`, `alerts`.
- **Same contract as file sources:** census from its discovery doc, Mode A group selection, and Mode B "all groups" with a
  completeness receipt per group (captured / empty / not_supported_for_account / denied_scope /
  unavailable_error). Archives stay sealed packages, and zips are kept alongside extracted contents.
- **Identity:** account plus group plus archive job, with capture context and hashes as in §2.
- **Not verified:** archive job lifetime and re-export windows, the consent model (one-time vs time-limited access),
  whether sensitive groups require app verification, and date ranges available per group.

## 8. Open verification items (not verified; verify live before relying on them)

- [ ] The Drive scopes needed for the full census (Drive read, Activity, Labels) and whether current grants
      cover them. This is an input to the hold CBX-H-006 / CBX-P10-005.
- [ ] Which Drive census entries differ between consumer and Workspace accounts. Admin audit and Reports
      data are believed to be Workspace-only.
- [ ] Revision byte availability and retention for uploaded binaries versus Google-native files.
- [ ] The current Google Photos API read scope for existing libraries. It is believed to have been restricted in
      2025, which may leave Picker or Takeout as the only paths.
- [ ] Graph activities and versions behavior on consumer OneDrive versus business accounts.

## 9. Acceptance gate (CBX-P10-GATE-FORENSIC)

- A real provider item produces a forensic package whose receipt lists every census entry with a status.
- A deliberately withheld scope yields PARTIAL with the gap named. After granting the scope, **Get more**
  produces a supplement version that reaches COMPLETE.
- A Mode A profile edit (add and subtract fields) changes the captured columns with no forensic side
  effects.
- `verify()` passes on the package, and a tampered artifact fails it.
- No source mutation, no token leakage, and test data purged after the run.
