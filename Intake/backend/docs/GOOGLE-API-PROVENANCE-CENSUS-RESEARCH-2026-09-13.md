> _Byline: Claude Code · research subagent · 2026-09-13_

# Google API provenance census — research findings

**Status:** RESEARCH, read-only. No authenticated Google API was called. No gcloud mutation, API enablement, credential, or token was touched.
**Feeds:** `SOURCE-METADATA-CAPTURE-AND-FORENSIC-PACKAGE-SPEC.md` §3 (census), §4 (receipt), §7/§7b (providers, account-level sources), §8 (open verification items).
**Accounts in scope:** consumer `@gmail.com` accounts (not Google Workspace).

## 0. Method and evidence levels

- **Discovery documents** were fetched unauthenticated on 2026-09-13/14 into the session scratchpad. They are the machine-readable source for schemas, methods, and scope strings.
  - drive v3 `20260904`, drive v2 `20260904`, driveactivity v2 `20260908`, drivelabels v2 `20260909`, admin reports_v1 `20260907`, vault v1 `20260905`, alertcenter v1beta1 `20260907`, dataportability v1 `20260910`, photoslibrary v1 `20260910`, photospicker v1 `20260910`, keep v1 `20260902`, workspaceevents v1 `20260906`, script v1 `20260830`, forms v1 `20260906`, tasks v1 `20260908`, fitness v1 `20260910`, health v4 `20260909`. Also fetched: people, gmail, calendar, docs, sheets, slides, youtube, chat, meet, cloudidentity, directory, and oauth2.
  - `drivemcp` Discovery returned **HTTP 403** ("unregistered callers"). It cannot be censused anonymously.
- **Official docs** (developers.google.com, support.google.com, knowledge.workspace.google.com) were read with WebFetch. Every claim below cites a URL.
- **Evidence levels used below:**
  - **VERIFIED-DISCOVERY**: read directly from a Discovery document.
  - **VERIFIED-DOC**: stated on an official Google page.
  - **INFERENCE**: reasoned from the two above. Stated as inference.
  - **UNVERIFIED**: not found in official sources. Needs a live check.
- Note that WebFetch returns a model summary of each page, not the raw page. Quotes are as returned. Re-read the page before quoting it in a legal filing.

---

## 1. Findings that change the spec (read first)

1. **The Data Portability API is not available to US users.** Google's help page lists only European countries and regions (EU/EEA states, Switzerland, UK). The United States is not listed. It also excludes work/school-managed accounts, users under 18, and Advanced Protection accounts.
   - Source: https://support.google.com/accounts/answer/14452558?hl=en (VERIFIED-DOC)
   - **Impact:** if the accounts are US-based, every `dataportability.*` census entry is `not_supported_for_account`, with the reason "region". It must not be `denied_scope`. Verify live once with `accessType.check` or `initiate` on a test user. **Takeout remains the only bulk path** for these products.
2. **Photos Library API cannot read an existing library.** Since 2025-03-31, `photoslibrary.readonly`, `photoslibrary.sharing`, and `photoslibrary` return 403. The Library API only sees app-created items.
   - Source: https://developers.google.com/photos/support/updates (VERIFIED-DOC)
   - The Picker API only returns items the user hand-picks in a session. Base URLs last 60 minutes. The `=d` download keeps EXIF **except location**.
   - Source: https://developers.google.com/photos/picker/guides/media-items (VERIFIED-DOC)
   - **Impact:** the Photos forensic package must be Takeout-sourced. The API can only corroborate hand-picked items, without GPS.
3. **Old binary revision bytes are mostly gone, and the revision list can be incomplete.**
   - Only **Keep Forever** blob revisions can be downloaded.
   - Purgeable revisions last about 30 days, or less once there are 100 non-pinned revisions.
   - `revisions.list` "might be incomplete" for heavily edited Docs/Sheets/Slides, and "the first revision returned may not be the oldest".
   - The Drive UI history "might be more complete" than the API.
   - Sources: https://developers.google.com/workspace/drive/api/guides/manage-revisions and https://developers.google.com/workspace/drive/api/guides/manage-downloads (VERIFIED-DOC)
   - **Impact:** §2 "bytes of every downloadable revision" is achievable, but "first revision date" is **not** a reliable oldest-date assertion. The receipt needs a `revision_list_possibly_truncated` flag for Docs-editor files.
4. **Drive `createdTime` / `modifiedTime` are client-settable, not server-observed.**
   - Discovery marks neither as Output-only. The `modifiedTime` description explicitly covers setting it. (VERIFIED-DISCOVERY)
   - Whether `createdTime` can be set on `files.create` is **UNVERIFIED live**. It is widely relied on by uploaders that preserve local dates.
   - **Impact:** in oldest-real-date grading these are *uploader assertions*. A Drive Activity `create` event timestamp is the server-observed anchor and should outrank them.
5. **Drive Activity has no "view" or "download" action type.** `ActionDetail` holds only create, edit, move, rename, delete, restore, permissionChange, comment, dlpChange, reference, settingsChange, and appliedLabelChange. (VERIFIED-DISCOVERY)
   - Its **history horizon is undocumented** (UNVERIFIED). Capture it now and store it, because nothing guarantees it will persist.
6. **Labels, Approvals, Admin Reports, Directory, Vault, Alert Center, Cloud Identity, and Keep are Workspace or organization features.** On consumer accounts they are `not_supported_for_account`, or empty (see §3).
7. **Every Drive scope that reaches all files is Restricted.** This covers `drive.readonly`, `drive.metadata.readonly`, `drive.activity(.readonly)`, and `drive.meet.readonly`. All Gmail read scopes are Restricted too.
   - Source: https://developers.google.com/workspace/drive/api/guides/api-specific-auth and https://developers.google.com/workspace/gmail/api/auth/scopes (VERIFIED-DOC)
   - The personal-use exception applies: "you are the only user of your app or … used by only a few users, all of whom are known personally to you."
   - Source: https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification (VERIFIED-DOC)
   - In **Testing** status, authorizations and refresh tokens **expire after 7 days**, with a 100-test-user cap.
   - Source: https://support.google.com/cloud/answer/15549945?hl=en (VERIFIED-DOC)
8. **Data Portability scopes cannot be mixed with any other scope in one authorization request.**
   - Source: https://developers.google.com/data-portability/user-guide/configure-oauth (VERIFIED-DOC)
   - This forces a dedicated shard (§6).
9. **Net-new provenance sources the spec does not list yet:**
   - Gmail: Drive share and comment notification emails, and attachments with Received headers.
   - People API: resolves Activity actor IDs to identities.
   - Calendar: event attachments by Drive `fileId`.
   - Forms: response timestamps.
   - YouTube Data API: `fileDetails.fileName` and `creationTime` of the original upload, plus `recordingDetails`.
   - Drive v2: a few fields v3 lacks (§3.2).

---

## 2. Summary table

Consumer column key: **Works**, **Partial**, **WS-only** (Workspace/org only), **Restricted-policy** (API exists but is policy-limited for this use), **Region** (geo-gated).

| API | Consumer applicability | Net-new provenance value vs Drive `files` | Scopes (read) | Key limits |
|---|---|---|---|---|
| Drive v3 — files | Works | Baseline | `drive.readonly` (R), `drive.metadata.readonly` (R) | `createdTime`/`modifiedTime` client-settable; checksums only for blob files |
| Drive v3 — revisions | Works | **High**: per-revision user, time, md5, size, originalFilename, bytes | `drive.readonly` (R) | Blob bytes only if keepForever; 30 days / 100 purge; list may be truncated |
| Drive v3 — comments/replies | Works | Medium: author, created/modified, resolved, deleted, quoted content | `drive.readonly` (R) | Only non-purged comments |
| Drive v3 — permissions | Works | High: who has access, permissionDetails, expiration, pendingOwner | `drive.metadata.readonly` (R) | Current state only, no history |
| Drive v3 — changes | Works (future only) | Low retro, High ongoing | `drive.metadata.readonly` (R) | `getStartPageToken` = future changes only |
| Drive v3 — approvals | WS-only (INFERENCE) | Low on consumer (expected empty) | Drive scopes | `canStartApproval` false on ineligible edition |
| Drive v3 — accessproposals | Partial | Low: pending requests only | Drive scopes | Resolved proposals no longer listed |
| Drive v3 — listLabels / labelInfo | WS-only (INFERENCE) | None on consumer | `drive.readonly` (R) | Labels are a Workspace-edition feature |
| Drive v2 | Works | Low: `labels.viewed/restricted/hidden`, `ownerNames`, `userPermission`, comment `status`/`context` | same as v3 | Legacy; duplicates most v3 data |
| Drive Activity v2 | Works (INFERENCE + UNVERIFIED live) | **High**: server-observed create/upload/copy origin, moves, renames, permission changes, actors | `drive.activity.readonly` (R) | No view/download events; horizon undocumented |
| Drive Labels v2 | WS-only | None on consumer | `drive.labels.readonly` | Shared labels in closed beta |
| Admin SDK Reports | WS-only | None on consumer (would be highest: views/downloads/IP) | `admin.reports.audit.readonly` | 6-month Drive log retention even on Workspace |
| Admin SDK Directory | WS-only | None | `admin.directory.*` | — |
| Vault | WS-only | None | `ediscovery.readonly` | Workspace editions / add-on |
| Alert Center | WS-only | None | `apps.alerts` | Workspace admin + service account |
| Cloud Identity | Org-only | None | `cloud-identity.*` | Domain-managed identities |
| Data Portability | **Region** (not US); excludes managed, under-18, Advanced Protection | **High where available**: My Activity (ms timestamps, locationInfos), Chrome history (µs) | `dataportability.*` (mix of R and S); cannot mix with other scopes | 24h initiate window; URLs 6h; data 14d; testing 7d |
| Photos Library | Restricted-policy | None for existing library | only `*.appcreateddata`/`appendonly` remain | Legacy read scopes 403 since 2025-03-31 |
| Photos Picker | Partial | Low–Medium: `createTime` = capture time, camera make/model, EXIF minus location | `photospicker.mediaitems.readonly` | User must hand-pick; baseUrl 60 min |
| Google Picker (Drive picker) | Works | None (grants `drive.file` per file) | `drive.file` (NS) | UI selection only |
| People | Works | **Medium**: resolves Activity `people/…` actors; contact source `updateTime` | `contacts.readonly`, `contacts.other.readonly`, `userinfo.*` (classification UNVERIFIED) | Current state only |
| Gmail | Works | **High (indirect)**: share/comment notification emails, attachments, `internalDate`, raw headers | `gmail.readonly` (R) or `gmail.metadata` (R) | History IDs expire; mail deleted by user is gone |
| Calendar | Works | Medium: events with attachment `fileId`, created/updated, attendees | `calendar.readonly` / `calendar.events.readonly` (classification UNVERIFIED) | — |
| Keep | WS-only (enterprise, domain-wide delegation) | None via API | `keep.readonly` | Takeout only for consumers |
| Tasks | Works | Low | `tasks.readonly` | — |
| Docs / Sheets / Slides | Works | Low–Medium: suggestions, named ranges, developerMetadata; current state only | `documents.readonly` (S), `spreadsheets.readonly`, `presentations.readonly` | `revisionId` opaque, valid 24h, no history |
| Forms | Works | Medium for Forms files: response `createTime`, `lastSubmittedTime`, `respondentEmail` | `forms.body.readonly`, `forms.responses.readonly` | — |
| Apps Script | Works | Low: script processes (automation that may have touched files) | `script.processes`, `script.projects.readonly` | Process history retention UNVERIFIED |
| Workspace Events | Works (INFERENCE) | None retro; ongoing custody monitor | Drive scopes | **Future events only**; TTL 4h with payload / 7d without |
| Drive MCP server | Developer Preview | None (subset of v3) | `drive.readonly` (R) + `drive.file` | Discovery 403 anonymously; preview enrollment |
| YouTube Data v3 | Works | **Medium** for owned videos: original `fileName`, file `creationTime`, `recordingDate`, location | `youtube.readonly` | fileDetails owner-only |
| Fitness (Google Fit) | Restricted-policy | Low–Medium: location samples (if ever recorded) | `fitness.location.read` etc. | No new sign-ups since 2024-05-01; deprecated 2026 |
| Google Health API | Works (Fitbit / Pixel Watch) | Low | `googlehealth.*` (all Restricted) | Evolving; Fitbit Web API ends Sept 2026 |

R = Restricted, S = Sensitive, NS = Non-sensitive, per the official scope pages cited in each section.

---

## 3. Per-API sections

### 3.1 Drive API v3 (`drive`, rev 20260904)

**Returns (VERIFIED-DISCOVERY):**

- **File (63 props).** Provenance-relevant fields:
  - Dates: `createdTime`, `modifiedTime`, `modifiedByMeTime`, `viewedByMeTime`, `sharedWithMeTime`, `trashedTime` (shared drives only).
  - People: `owners`, `lastModifyingUser`, `sharingUser`, `trashingUser`.
  - Names: `originalFilename`, `name`.
  - Hashes: `md5Checksum`, `sha1Checksum`, `sha256Checksum` (blob files only, not Docs editors or shortcuts).
  - Location: `parents`, `driveId`, `spaces`, `shortcutDetails`.
  - Content: `headRevisionId`, `version`, `size`, `quotaBytesUsed`.
  - Media: `imageMediaMetadata` (camera make, model, lens, time, location, exposure…) and `videoMediaMetadata` (duration, height, width).
  - Sharing and restrictions: `permissions`, `permissionIds`, `hasAugmentedPermissions`, `inheritedPermissionsDisabled`, `shared`, `writersCanShare`, `copyRequiresWriterPermission`, `downloadRestrictions`, `contentRestrictions` (`restrictingUser`, `restrictionTime`, `reason`), `linkShareMetadata`.
  - Labels and properties: `labelInfo`, `properties`, `appProperties`.
  - Other: `capabilities` (46 flags including `canReadRevisions`), `exportLinks`, `resourceKey`, `clientEncryptionDetails`, `explicitlyTrashed`, `isAppAuthorized`, `description`, `starred`, `folderColorRgb`.
  - `contentHints` is "never populated in responses".
- **Revision:** `id`, `modifiedTime`, `lastModifyingUser` (only when a signed-in user made the change), `md5Checksum`, `size`, `originalFilename`, `mimeType`, `keepForever`, `exportLinks`, `published*`.
- **Permission:** `type`, `role`, `emailAddress`, `domain`, `displayName`, `expirationTime`, `deleted`, `pendingOwner`, `permissionDetails` (inherited, inheritedFrom), `view`, `allowFileDiscovery`, `inheritedPermissionsDisabled`.
- **Comment / Reply:** `author`, `createdTime`, `modifiedTime`, `content`, `htmlContent`, `quotedFileContent`, `anchor`, `resolved`, `deleted`, `mentionedEmailAddresses`, `assigneeEmailAddress`, reply `action` (resolve/reopen).
- **Approval:** `initiator`, `createTime`, `modifyTime`, `completeTime`, `dueTime`, `status`, `reviewerResponses`, `targetFileId`, `fileContentChangeBehavior`.
- **AccessProposal:** `requesterEmailAddress`, `recipientEmailAddress`, `requestMessage`, `rolesAndViews`, `createTime`.
- **Change:** `time`, `removed`, `file`, `changeType`.
- **Methods:** `files.export` is capped at 10 MB. `files.download` is a long-running operation (the only way to download Google Vids). Both are VERIFIED-DISCOVERY and manage-downloads doc.

**Consumer applicability:**

- **Works:** files, revisions, comments/replies, permissions, changes, about, apps, and export/download.
- **Approvals: likely empty.** `canStartApproval` is false when "Your Google Workspace edition is ineligible" (https://developers.google.com/workspace/drive/api/guides/approvals). Consumer eligibility is not stated, so this is INFERENCE and should be verified with `approvals.list` on one file.
- **Access proposals: pending only.** "The resolved access proposal is no longer returned through the `list` method." They can't be created via the API (https://developers.google.com/workspace/drive/api/guides/pending-access). Consumer availability is not stated (UNVERIFIED).
- **Labels: expect empty `labelInfo`** on consumer accounts. See §3.3.

**Scopes (https://developers.google.com/workspace/drive/api/guides/api-specific-auth, VERIFIED-DOC):**

- `drive.readonly`: **Restricted**. Bytes, revisions, and exports.
- `drive.metadata.readonly`: **Restricted**. Metadata only, no bytes.
- `drive.apps.readonly`: Sensitive. The `apps` resource and v2 `openWithLinks`.
- `drive.meet.readonly`: Restricted. Meet-created files only.
- `drive.file`: Non-sensitive. Only files the app created or the user opened with the app (via Picker).
- `drive.photos.readonly`: in Discovery, but not in the scope table (the legacy Google Photos folder in Drive). Treat as inert (UNVERIFIED).

**History and retention (VERIFIED-DOC, manage-revisions / manage-downloads):**

- Purgeable revisions are "typically preserved for 30 days". They can be purged earlier after 100 non-pinned revisions.
- Up to 200 Keep Forever revisions are allowed.
- "You can only download blob file content revisions that are marked as 'Keep Forever'." So for uploaded binaries, only the head revision plus pinned revisions yield bytes. Other revision records are metadata-only.
  - **UNVERIFIED live:** whether `revisions.get?alt=media` on a non-pinned binary revision still inside its 30-day window returns bytes. The doc says no.
- Docs editor files: earlier revisions are exported by using `revisions.get` to generate an export link (`exportLinks`). This is documented as a browser flow. Whether those links work with a bearer token and for all revisions is **UNVERIFIED**.
- The revision list may omit old revisions of Docs editor files.
- `changes.getStartPageToken` "Gets the starting pageToken for listing future changes". There is no retroactive change log (VERIFIED-DISCOVERY).

**Net-new vs `files`:** revisions, permissions detail, comments, and approvals/proposals are all net-new resources. `files` alone is only the current snapshot.

### 3.2 Drive API v2 (`drive` v2, rev 20260904) — completeness cross-check

The Discovery diff shows these fields exist only in v2 (VERIFIED-DISCOVERY):

- **File:**
  - Renames of v3 fields: `createdDate`, `modifiedDate`, `lastViewedByMeDate`, `sharedWithMeDate`, `trashedDate`, `fileSize`, `title`.
  - New in v2: `labels{starred, restricted, trashed, modified, hidden, viewed}`, `markedViewedByMeDate` (deprecated), `ownerNames`, `lastModifyingUserName`, `userPermission`, `openWithLinks` (needs `drive.apps.readonly`), `alternateLink`, `embedLink`, `downloadUrl`, `selfLink`, `indexableText`, `thumbnail`, `copyable`, `editable`, `shareable`, `appDataContents`.
- **Revision:** `pinned` (same as keepForever), `downloadUrl`, `lastModifyingUserName`, `fileSize`.
- **Permission:** `additionalRoles` (for example commenter), `withLink`, `authKey`, `expirationDate`, `name`, `value`.
- **Comment:** `status`, `context`, `fileTitle`.
- **Change:** `deleted`, `modificationDate`.
- **Assessment:** mostly duplicates. `labels.viewed`, `labels.modified`, `labels.hidden`, and `additionalRoles` are the only possibly distinct signals.
- **Recommendation:** include a v2 `files.get` raw response in Mode B as a cheap supplement, marked `derived_duplicate` where it matches v3.

### 3.3 Drive Labels API v2 (`drivelabels`, rev 20260909)

- **Returns:** label definitions (fields, options, lifecycle, `labelType` SHARED/ADMIN/GOOGLE_APP), label permissions, locks, `users.getCapabilities`, and `limits.getLabel`. Applied values on files come from Drive v3 `files.listLabels` and `labelInfo`. (VERIFIED-DISCOVERY)
- **Consumer: WS-only.**
  - Supported editions listed: Frontline, Business Standard/Plus, Enterprise, Education Standard/Plus, Essentials, and G Suite Business (support.google.com/a/answer/9292382, via search summary). Admin labels need "an account administrator with the Manage Labels privilege".
  - "Shared labels are only available in a closed beta that isn't currently accepting new customers" (https://developers.google.com/workspace/drive/labels/guides/overview, VERIFIED-DOC).
  - Non-Workspace users *can* read labels applied by a Workspace org to a file shared with them, if granted READER on the label. That is INFERENCE from the overview.
- **Scopes (VERIFIED-DISCOVERY):** `drive.labels.readonly`, `drive.labels`, `drive.admin.labels(.readonly)`. Classification not found (UNVERIFIED).
- **Receipt:** `not_supported_for_account` (reason: no Workspace edition). Still call `files.listLabels` once per file. An empty result is `empty`, which proves the absence.

### 3.4 Drive Activity API v2 (`driveactivity`, rev 20260908)

- **Returns (VERIFIED-DISCOVERY).** `activity.query` accepts `itemName` or `ancestorName` (a whole folder tree), `filter` (time, `detail.action_detail_case`), and `consolidationStrategy` (none/legacy). Each `DriveActivity` carries:
  - `primaryActionDetail`, `actions[]`, `actors[]`, `targets[]`, and `timestamp` or `timeRange`.
  - Actor types: `user` (knownUser with `personName` as `people/ID` and `isCurrentUser`, deletedUser, unknownUser), `anonymous`, `impersonation`, `system`, `administrator`.
  - `Create`: `new`, `upload` ("originated externally and was uploaded"), or `copy.originalObject` (**source-file lineage**).
  - `Move`: `addedParents`/`removedParents`. `Rename`: `oldTitle`/`newTitle`. `PermissionChange`: `addedPermissions`/`removedPermissions`.
  - `Delete`/`Restore` type, `Comment` (post, assignment, suggestion, mentionedUsers), `DataLeakPreventionChange`, `ApplicationReference`, `SettingsChange.restrictionChanges`, `AppliedLabelChange`.
  - Targets are `DriveItem` with owner, title, and mimeType, or a `fileComment`.
- **No view or download action type exists** in `ActionDetail`.
- **Consumer:** not documented as Workspace-only. Visibility rule: reported "depends on whether the change, or information about the change, is visible to the authenticated user" (https://developers.google.com/workspace/drive/activity/v2). Consumer behavior is INFERENCE; verify live on one file.
- **Scopes:** `drive.activity.readonly` (**Restricted**, api-specific-auth page).
- **History/retention:** **UNDOCUMENTED.** The query reference only shows filter syntax, with an example date in 2016. Mark horizon **UNVERIFIED**. Live probe: `activity.query` on the oldest file in each account, with `consolidationStrategy.none`, and record the earliest event.
- **Net-new vs `files`:** **high.**
  - Server-observed creation time and origin (upload vs new vs copy-of-X).
  - Full move and rename lineage.
  - Permission-change history, and deleted-user actors.
  - These are exactly the date and provenance assertions `files` cannot give.

### 3.5 Admin SDK — Reports (`admin` reports_v1) and Directory (`admin` directory_v1)

- **Returns (VERIFIED-DISCOVERY):**
  - `activities.list` / `watch` covers applicationName values including `drive`, `login`, `token`, `takeout`, `user_accounts`, `gmail`, `calendar`, `meet`, `keep`, `vault`, `chrome`, `chrome_sync`, and others. The Drive audit log includes views, downloads, and IPs.
  - Usage reports: `userUsageReport`, `customerUsageReports`, `entityUsageReports`.
- **Consumer: WS-only.**
  - The Reports API accesses "information about the Google Workspace activities of your users" (https://developers.google.com/workspace/admin/reports/v1/get-start/overview).
  - The retention page states that Gmail/Drive entries "are relevant for Workspace only" (https://knowledge.workspace.google.com/admin/reports/data-retention-and-lag-times).
  - Directory manages domain users and groups.
- **Scopes:** `admin.reports.audit.readonly`, `admin.reports.usage.readonly`.
- **Retention (VERIFIED-DOC, Workspace):** Drive log events 6 months; admin/user log events 6 months; usage 6 or 15 months; lag from near real time to 1–3 days.
- **Receipt:** `not_supported_for_account` (reason: consumer account, no Workspace customer). Record that this is the *only* API that would expose view/download/IP events, so their absence is structural.
- **Note:** project `silver-fiber-499419-k8` has `admin` enabled. Enabling does not create eligibility (INFERENCE).

### 3.6 Vault (`vault` v1)

- **Returns:** matters, holds, exports (corpus DRIVE, MAIL, GROUPS, HANGOUTS_CHAT, VOICE, CALENDAR, GEMINI), `DriveExportOptions.includeAccessInfo`, and saved queries. (VERIFIED-DISCOVERY)
- **Consumer: WS-only.** Vault is "an information governance and eDiscovery tool for Google Workspace", available in specific editions or as an add-on (https://knowledge.workspace.google.com/vault/getting-started/vault-overview).
- **Scopes:** `ediscovery.readonly`.

### 3.7 Alert Center (`alertcenter` v1beta1)

- **Returns:** security alerts, alert metadata, and feedback. (VERIFIED-DISCOVERY)
- **Consumer: WS-only.** "Available to all Google Workspace customers"; it needs domain admin and a service account (https://developers.google.com/workspace/admin/alertcenter/guides).
- **Scope:** `apps.alerts`.

### 3.8 Cloud Identity (`cloudidentity` v1)

- **Returns:** groups, memberships, devices, device users, and policies.
- **Consumer: org-only.** It is framed as replacing personal Gmail accounts with managed identities (https://docs.cloud.google.com/identity/docs/overview).
- **Net-new:** none for consumer accounts.

### 3.9 Data Portability API — see dedicated §4.

### 3.10 Google Photos — Library, Picker, and Google Picker

- **Library API (`photoslibrary` v1).**
  - Still in Discovery with six scopes, but the three broad read scopes are removed.
  - Only `photoslibrary.appendonly`, `photoslibrary.readonly.appcreateddata`, and `photoslibrary.edit.appcreateddata` remain. Legacy calls get "403 PERMISSION_DENIED after March 31, 2025" (https://developers.google.com/photos/support/updates, https://developers.google.com/photos/overview/authorization).
  - MediaItem fields (if reachable): `filename`, `mediaMetadata.creationTime`, photo camera/exposure data, video fps/status, `contributorInfo`, `description`.
  - **Receipt for existing library:** `not_supported_for_account` (reason: API policy 2025-03-31).
- **Picker API (`photospicker` v1).**
  - Sessions are created, then the user picks in the Google Photos UI; then `mediaItems.list`.
  - `PickedMediaItem`: `id`, `createTime` ("when the media item was created (not when it was uploaded)"), `type`, `mediaFile{mimeType, filename, baseUrl, mediaFileMetadata{width, height, cameraMake, cameraModel, photoMetadata{focalLength, apertureFNumber, isoEquivalent, exposureTime}, videoMetadata{fps, processingStatus}}}` (VERIFIED-DISCOVERY and the reference page).
  - Base URLs last 60 minutes. `=d` download retains "all the Exif metadata except the location metadata" (VERIFIED-DOC).
  - Scope: `photospicker.mediaitems.readonly`. Photos apps must "pass the OAuth verification review". The sensitivity class was not found (UNVERIFIED).
  - No album membership, no sharing, no upload time, no GPS, no description.
- **Google Picker (`picker`).** A Drive file-selection UI. It grants `drive.file` access to picked files. No metadata beyond Drive v3.
- **Net-new:** Picker gives capture time and camera model for hand-picked items. **GPS, albums, sharing, and edit history remain Takeout-only.**

### 3.11 People API (`people` v1)

- **Returns:**
  - `Person` has 38 fields, including `metadata.sources[]` with `type`, `id`, and `updateTime` ("Last update timestamp of this source").
  - `otherContacts` (auto-saved correspondents), `contactGroups`, and `people.get` for `people/ID`.
  - Sources: VERIFIED-DISCOVERY and https://developers.google.com/people/api/rest/v1/people/get.
- **Consumer:** works.
- **Scopes:** `contacts.readonly`, `contacts.other.readonly`, `userinfo.email`/`profile`, `user.*.read`. Classification not found on the fetched page (**UNVERIFIED**; contacts scopes are believed Sensitive).
- **Net-new:** resolves Drive Activity `knownUser.personName` values (`people/…`) and Comment/Revision user objects into stable identities. `otherContacts` shows who the account has corresponded with. Contact `updateTime` dates a contact record.

### 3.12 Gmail API (`gmail` v1)

- **Returns:**
  - `Message{id, threadId, labelIds, snippet, historyId, internalDate, sizeEstimate, payload (headers, parts, attachments), raw (RFC 2822), classificationLabelValues}`.
  - Also threads, labels, history, settings, and drafts. (VERIFIED-DISCOVERY)
- **Consumer:** works.
- **Scopes (https://developers.google.com/workspace/gmail/api/auth/scopes):** `gmail.readonly` **Restricted**; `gmail.metadata` **Restricted** (headers and labels, no body).
- **History:**
  - `history.list` needs a recent `startHistoryId`; out-of-date IDs typically return 404 (VERIFIED-DISCOVERY).
  - Messages persist until the user deletes them. Trash auto-empties after 30 days (UNVERIFIED, general Gmail behavior).
- **Net-new (INFERENCE, high value):**
  - Drive sends email for shares ("X shared a document with you"), comments, mentions, and access requests. These emails are durable, server-dated, independent records of sharing events, possibly older than Drive Activity keeps.
  - Attachments give byte copies with SMTP `Received` chains and `Date` headers, which corroborate a file's existence at a date.
  - Link Gmail attachments to Drive items by hash through the cross-store ledger.

### 3.13 Calendar API (`calendar` v3)

- **Returns:** `Event{created, updated, creator, organizer, attendees, attachments[{fileId, fileUrl, title, mimeType}], iCalUID, sequence, recurrence, location, source, conferenceData, eventType, …}`. (VERIFIED-DISCOVERY)
- **Consumer:** works.
- **Scopes:** `calendar.readonly`, `calendar.events.readonly`, `calendar.events.owned.readonly`. The classification table was not returned by the fetched page (**UNVERIFIED**; believed Sensitive). Source: https://developers.google.com/workspace/calendar/api/auth.
- **Net-new:** attachment `fileId` links Drive files to dated events and attendees. `created`/`updated`/`sequence` date the event record. Custody-relevant for scheduling evidence.

### 3.14 Keep API (`keep` v1)

- **Returns:** `Note{name, title, body, attachments, permissions, createTime, updateTime, trashTime, trashed}`, plus `media.download`. (VERIFIED-DISCOVERY)
- **Consumer: WS-only.**
  - The Discovery description says "used in an enterprise environment".
  - The guide says it enables "enterprise administrators to manage Google Keep notes" via domain-wide delegation (https://developers.google.com/workspace/keep/api/guides).
- **Scopes:** `keep.readonly`.
- **Receipt:** `not_supported_for_account`. Consumer Keep notes are **Takeout-only**.

### 3.15 Tasks API (`tasks` v1)

- **Returns:** task lists and tasks (updated, due, completed, notes, links).
- **Consumer:** works.
- **Scope:** `tasks.readonly`.
- **Net-new:** low. Dated to-do records only.

### 3.16 Docs / Sheets / Slides / Forms

- **Docs (`docs` v1).**
  - `Document{title, body, tabs, headers, footers, footnotes, namedRanges, inlineObjects, positionedObjects, suggestedDocumentStyleChanges, …, revisionId}`.
  - `documents.get` takes `suggestionsViewMode` and `includeTabsContent`. Suggestion state schemas exist.
  - `revisionId` "is not a sequential number but an opaque string … only guaranteed to be valid for 24 hours". It is populated only with edit access. (VERIFIED-DISCOVERY)
  - Scopes: `documents.readonly` **Sensitive**; `drive.readonly` Restricted (https://developers.google.com/workspace/docs/api/auth).
- **Sheets (`sheets` v4):** `Spreadsheet{properties, sheets, namedRanges, developerMetadata, dataSources, dataSourceSchedules}`. Scope: `spreadsheets.readonly`.
- **Slides (`slides` v1):** `Presentation{slides, layouts, masters, notesMaster, revisionId, …}`. Scope: `presentations.readonly`.
- **Forms (`forms` v1):** `Form{info, items, settings, publishSettings, linkedSheetId, revisionId}` and `FormResponse{responseId, createTime, lastSubmittedTime, respondentEmail, answers, totalScore}`. Scopes: `forms.body.readonly`, `forms.responses.readonly`.
- **Consumer:** all work.
- **History:** none. Current state only. Historical content comes only from Drive revisions and exports.
- **Net-new:**
  - Docs: structural suggestions (pending edits not visible in exports) and embedded object IDs.
  - Sheets: `developerMetadata`.
  - Forms: **response timestamps and respondent emails** (high for any Form in evidence).

### 3.17 Apps Script API (`script` v1)

- **Returns:** `processes.list` / `listScriptProcesses` ("information about processes made by or on behalf of a user, such as process type and current status"), plus project content, versions, deployments, and metrics. (VERIFIED-DISCOVERY)
- **Consumer:** works.
- **Scopes:** `script.processes`, `script.projects.readonly`, `script.metrics`.
- **Retention of process history:** UNVERIFIED.
- **Net-new:** low. It can show that automation, not a human, ran against the account. That context matters when an Activity actor is the user but the action was scripted.

### 3.18 Google Workspace Events API (`workspaceevents` v1)

- **Returns:** subscriptions delivering Drive events (files added, moved, edited or revision uploaded, trashed/untrashed; comments, replies, access proposals, approvals), plus Chat and Meet events, via Pub/Sub.
  - Sources: https://developers.google.com/workspace/events and https://developers.google.com/workspace/events/guides/events-drive.
  - Drive events reached GA in 2026 per the release notes (https://developers.google.com/workspace/events/release-notes). That came from a search summary, so the page text is **UNVERIFIED**.
- **Consumer:** "events for resources where the user has access through their Google Workspace account or Google Account" (INFERENCE: consumer supported).
- **Scopes:** Drive scopes from `drive.file` up to `drive.readonly`.
- **Limits:** future events only. TTL "Up to 4 hours" with resource data, "Up to 7 days" without.
- **Net-new:** none retroactively. For ongoing monitoring after capture, it is a server-pushed, timestamped change feed. It complements `changes.watch` and `files.watch`.

### 3.19 Drive MCP server (`drivemcp`)

- "Available as part of the Google Workspace Developer Preview Program".
- Scopes: `drive.readonly` and `drive.file`.
- Tools: `copy_file`, `create_file`, `download_file_content`, `get_file_metadata`, `get_file_permissions`, `list_recent_files`, `read_file_content`, `search_files`.
- Source: https://developers.google.com/workspace/drive/api/guides/configure-mcp-server (VERIFIED-DOC).
- Discovery is 403 anonymously.
- **Net-new:** none; it is a subset of v3. `read_file_content` may return a text rendering (derived). Exclude it from the census except as a derived-representation source. It also carries write tools (`copy_file`, `create_file`), which conflicts with the no-source-mutation gate.

### 3.20 Other related Google APIs found in the directory

- **YouTube Data API v3.**
  - For videos the account owns: `fileDetails{fileName, creationTime, fileSize, container, videoStreams, audioStreams, durationMs}` and `recordingDetails{recordingDate, location, locationDescription}` (VERIFIED-DISCOVERY).
  - Scope: `youtube.readonly`. Consumer: works.
  - **Net-new:** original upload filename and file creation time for any evidence uploaded as private/unlisted YouTube video.
- **Fitness API (Google Fit).**
  - Includes `fitness.location.read` and activity/sleep scopes (VERIFIED-DISCOVERY).
  - "As of May 1, 2024, developers cannot sign up to use these APIs"; "will be deprecated in 2026" (https://developers.google.com/fit).
  - **Restricted-policy.** A new project probably cannot onboard (UNVERIFIED for projects already enabled). Takeout "Fit" is the path.
- **Google Health API (`health` v4).**
  - Fitbit and Pixel Watch data. "All Google Health API scopes are categorized as Restricted". It is evolving, and the Fitbit Web API is discontinued September 2026 (https://developers.google.com/health/about).
  - Low custody value unless a wearable was in use.
- **youtubeAnalytics / youtubereporting, chat, meet, classroom, groupssettings, licensing:** not file-provenance relevant for consumer accounts. Chat and Meet REST APIs are Workspace-oriented (UNVERIFIED for consumer).
- **oauth2 v2 / tokeninfo:** capture context. It records the granted scopes and the account email at capture time, which the spec's §2 capture context needs.

---

## 4. Data Portability API — dedicated section (`dataportability` v1, rev 20260910)

### 4.1 Methods (VERIFIED-DISCOVERY and https://developers.google.com/data-portability/user-guide/methods)

- **`portabilityArchive.initiate`:** `resources[]` (1:1 with scopes), optional `startTime`/`endTime`. Returns a job ID and `accessType`.
  - Google recommends one resource group per call.
  - "You should initiate the portability archive within 24 hours of user authorization."
- **`archiveJobs.getPortabilityArchiveState`:** `state`, `urls[]` (signed Cloud Storage URLs), `startTime`, `exportTime`.
  - "The signed URLs expire after six hours, and the data is available for 14 days."
- **`archiveJobs.retry`:** "A failed job can be retried up to three times."
- **`archiveJobs.cancel`:** only for `IN_PROGRESS` time-based jobs.
- **`accessType.check`:** reports `oneTimeResources` vs `timeBasedResources` for a token before starting.
- **`authorization.reset`:** "Revokes all user-granted OAuth scopes". It allows re-initiating a resource group that was used before.
  - An internal `ResetAuthorization` "is called 14 days after the first `InitiatePortabilityArchive` call" (the one-time access lifecycle).

### 4.2 Consent and access model (https://developers.google.com/data-portability/user-guide/time-based)

- The user picks **once, 30 days, or 180 days** at consent.
- Time-based access allows one export per resource set **every 24 hours**. An early retry returns `RESOURCE_EXHAUSTED` / `RESOURCE_EXHAUSTED_TIME_BASED`, with "You can initiate another export after …".
- `refresh_token_expires_in` is 2592000 s (30 d) or 15552000 s (180 d). **Testing publishing status: always 7 days** regardless of the choice.
- Renewal is possible up to 90 days before expiry (search summary of the same page; release notes say a "6-month renewal window"). The exact rule is **UNVERIFIED**.
- **Time filter** (`startTime`/`endTime`) is supported **only** for `myactivity.youtube`, `myactivity.maps`, `myactivity.search`, `myactivity.myadcenter`, `myactivity.shopping`, `myactivity.play`, and `chrome.history`. Mixing them with unsupported scopes gives `INVALID_ARGUMENT` (https://developers.google.com/data-portability/user-guide/time-filter).
- DP scopes "can't be mixed with other scopes (such as, …userinfo.email)" in the same request (https://developers.google.com/data-portability/user-guide/configure-oauth).

### 4.3 Consumer applicability and verification

- **Region-gated. The US is not included.** The listed availability covers Austria through the United Kingdom (EU states, Switzerland, UK). The page says 31 countries/regions; the summary returned 29 names, so re-read the page for the exact list. It is unavailable for managed work/school accounts, users under 18, and Advanced Protection (https://support.google.com/accounts/answer/14452558?hl=en).
  - **If the owner's accounts are US-registered, this whole API is unavailable.**
  - **UNVERIFIED:** whether eligibility follows account country, IP, or both. Probe live with one `accessType.check` from a test-user token.
- **Verification:** apps need identity verification, a privacy policy, a use description, and a demo video. Restricted scopes add a security assessment. Re-verification is annual (https://developers.google.com/data-portability/user-guide/overview).
- **Policy:** the allowed purpose is "allowing users to move, copy, or transfer user data". Use is limited to features "visible and prominent in the requesting application's user interface" (https://developers.google.com/data-portability/policy).
  - A personal forensic-archiving app fits "copy/transfer" (INFERENCE). Whether the personal-use verification exception covers DP scopes is **UNVERIFIED**.

### 4.4 Every resource group and scope

Classification is from https://developers.google.com/data-portability/user-guide/scopes (VERIFIED-DOC). R = Restricted, S = Sensitive. "TF" means the time filter is supported.

| Group | Scope suffix (`…/auth/dataportability.`) | Class | Archive contents (schema reference) |
|---|---|---|---|
| Alerts | `alerts.subscriptions` | S | Google Alerts subscriptions |
| Business messaging | `businessmessaging.conversations` | R | Messages with businesses. **Doc-only: not in Discovery scope list** |
| Chrome | `chrome.autofill` | R | Addresses and more (JSON), no timestamps |
| Chrome | `chrome.bookmarks` | R | Bookmarks (HTML), no timestamps |
| Chrome | `chrome.dictionary` | S | CSV |
| Chrome | `chrome.extensions` | S | JSON |
| Chrome | `chrome.history` | R | **History JSON, timestamps in microseconds, TF** |
| Chrome | `chrome.reading_list` | S | HTML |
| Chrome | `chrome.settings` | S | JSON |
| Discover | `discover.follows`, `discover.likes`, `discover.not_interested` | S | Discover feed interactions |
| Fitbit | `fitbit.device_events` | R | Fitbit device events. **Doc-only: not in Discovery scope list** |
| Maps | `maps.aliased_places` | R | Labeled places (Home, Work…), name, address, latlng |
| Maps | `maps.commute_routes` | R | Pinned trips, place visits, travel mode, coordinates |
| Maps | `maps.commute_settings` | S | Commute mode preferences |
| Maps | `maps.ev_profile` | S | EV connector prefs |
| Maps | `maps.factual_contributions` | S | Place edits, geocodes, created timestamp |
| Maps | `maps.offering_contributions` | S | Suggested edits with timestamp |
| Maps | `maps.photos_videos` | S | **Media + JSON with `creationTime`, `photoTakenTime`, `geoDataExif` (lat/lon/alt)** |
| Maps | `maps.questions_answers` | S | Q&A text |
| Maps | `maps.reviews` | S | Reviews/reports with `report_time` |
| Maps | `maps.starred_places` | R | Saved places with coordinates |
| Maps | `maps.vehicle_profile` | S | Vehicle make/model |
| My Activity | `myactivity.maps` | R | **Activity records, TF** |
| My Activity | `myactivity.myadcenter` | S | Activity records, TF |
| My Activity | `myactivity.play` | R | Activity records, TF |
| My Activity | `myactivity.search` | R | **Activity records, TF** |
| My Activity | `myactivity.shopping` | R | Activity records, TF |
| My Activity | `myactivity.youtube` | R | **Activity records (watch/search), TF** |
| My Maps | `mymaps.maps` | R | Maps created in My Maps |
| Nest | `nest.camera_event`, `nest.camera_feature`, `nest.camera_video`, `nest.store`, `nest.user` | UNVERIFIED | **Discovery-only: not in the doc scope table.** Nest camera events and video would be high value if present |
| Order & reserve | `order_reserve.purchases_reservations` | S | Food purchases and reservations |
| Pixel | `pixel.device_data` | UNVERIFIED | **Discovery-only.** Pixel telemetry |
| Play | `play.devices`, `grouping`, `installs`, `library`, `playpoints`, `promotions`, `redemptions`, `subscriptions`, `usersettings` | S | Play Store records (installs dated per device) |
| Play | `play.purchases` | R | Purchases |
| Saved | `saved.collections` | S | Saved links, images, places |
| Search UGC | `search_ugc.comments`, `search_ugc.media.{reviews_and_stars, streaming_video_providers, thumbs, watched}` | S | Search/Google TV contributions |
| Search notifications | `searchnotifications.settings`, `searchnotifications.subscriptions` | S | Search app notification prefs |
| Shopping | `shopping.addresses`, `shopping.reviews` | S | Shipping addresses, product reviews |
| Street View | `streetview.imagery` | S | Uploaded Street View images/videos |
| YouTube | `youtube.private_videos` | R | **Videos CSV + original-format media + MP4; Video Create/Publish Timestamp** |
| YouTube | `youtube.unlisted_videos`, `youtube.public_videos` | S | Same shape as private |
| YouTube | `youtube.channel` | R | Channel CSV, images |
| YouTube | `youtube.private_playlists`, `unlisted_playlists`, `public_playlists` | S | Playlist create/update timestamps |
| YouTube | `youtube.comments`, `live_chat`, `posts`, `clips`, `music`, `playable`, `shopping`, `subscriptions` | S | CSV (+ audio for music); message/post/clip timestamps |
| YouTube | `youtube.conversations` | UNVERIFIED | **Discovery-only.** Messages, "Message Create Timestamp (UTC)" per the schema page |

- **Drift note:** Discovery lists 73 scopes. The doc table lists 67 rows.
  - Doc-only: `businessmessaging.conversations`, `fitbit.device_events`.
  - Discovery-only: `nest.*` (5), `pixel.device_data`, `youtube.conversations`.
  - The census must take the **Discovery** list as authoritative for what exists, and record doc drift.
- **My Activity record fields (all six groups, identical):**
  - `header`, `title`, `titleUrl`, `subtitles`, `description`, `time` (millisecond RFC 3339, "when the user did the activity"), `products`, `details`, `activityControls`, `locationInfos` ("location(s) associated with this activity"), `imageFile`, `audioFiles`, `attachedFiles`.
  - Formats: HTML/JSON, plus JPEG/PNG/WEBP/MPEG/CSV attachments.
  - Source: https://developers.google.com/data-portability/schema-reference/my_activity.
  - **`myactivity.maps` is Maps *activity* (searches, directions, views), not Timeline.** `locationInfos` is per-activity context. Its exact shape (coarse area vs lat/lng, and source such as "From your device") is **UNVERIFIED**.
- **Chrome schema:** https://developers.google.com/data-portability/schema-reference/chrome. Encrypted Chrome sync data is exported as "cannot be exported" markers.
- **Maps schema:** https://developers.google.com/data-portability/schema-reference/maps. "No Location History or Timeline data."
- **YouTube schema:** https://developers.google.com/data-portability/schema-reference/youtube.

### 4.5 What it does NOT cover that Takeout does (and other API routes)

| Takeout product | In Data Portability? | Other API route |
|---|---|---|
| Drive | No | Drive v3/v2/Activity (§3.1–3.4) |
| Photos | No | Picker only (hand-picked, no GPS); Library API blocked |
| Gmail | No | Gmail API (Restricted), full parity including raw |
| Contacts | No | People API |
| Calendar | No | Calendar API |
| Keep | No | None for consumers (Keep API is enterprise) |
| Tasks | No | Tasks API |
| Timeline / Location History | No | **None.** Timeline is now on-device, with optional encrypted backup and in-app export (`location-history.json`) (https://support.google.com/maps/answer/14169818, https://support.google.com/maps/answer/6258979). Whether Takeout still includes it is **UNVERIFIED** |
| Voice | No | None (no consumer Voice API found in the directory) |
| Fit | No | Fitness API (closed to new sign-ups, deprecated 2026) |
| Chat / Hangouts | No | Chat API is Workspace-oriented (UNVERIFIED for consumer) |
| Google Account / access log activity, devices | No | None |
| Blogger, Messages backup, Android device backup, Assistant | Only via My Activity where logged | None found |

- Supporting search summary (developers.google.com/data-portability): DP covers "Chrome, Maps, Play, Search, Shopping, YouTube". Gmail, Drive, and Photos are Takeout-only in the DP sense.
- The full Takeout product list could not be fetched (it requires sign-in; support page 3024190 lists only examples). **UNVERIFIED.**

### 4.6 Value for dating and corroborating events (custody evidence)

- **High, where available:**
  - `myactivity.search` / `maps` / `youtube`: millisecond-timestamped, server-logged user actions, some with `locationInfos`. They corroborate "where/what was the user doing at time T".
  - `chrome.history`: microsecond visit times.
  - `maps.photos_videos`: `photoTakenTime` plus EXIF GPS for Maps uploads.
  - `youtube.*_videos`: original media bytes plus create/publish timestamps.
  - `nest.camera_*` (if real): camera events and video.
- **Evidentiary shape:** exports arrive as a Google-produced archive with signed URLs. Hash the archive on download and record the job ID, `exportTime`, and URL expiry as capture context. This yields a strong chain of custody (INFERENCE).
- **Caveats:**
  - Region gating likely blocks the owner's accounts.
  - My Activity only holds what activity controls and auto-delete retained.
  - One-time tokens self-reset after 14 days, so archives must be pulled within the 14-day data window.

---

## 5. Not obtainable via any API (for honest receipt entries)

**Structurally absent for consumer accounts:**

- File **view and download events**, **IP addresses**, and **device/client identifiers** for Drive (Admin Reports only, Workspace only, 6-month retention).
- Revision **bytes** for purged or non-pinned binary revisions. Revision records omitted from long Docs histories. UI-only history detail.
- Resolved **access proposals**.
- Any change log before the capture's own `getStartPageToken`.
- Google Photos library-wide metadata: **GPS, album membership, sharing, upload time, edits, descriptions**. Takeout only.
- **Keep notes** (Takeout only). **Timeline/Location History** (device export only; Takeout status UNVERIFIED). **Voice**, **Fit** (API closed to new sign-ups), consumer **Chat/Hangouts** (UNVERIFIED).
- **All Data Portability groups**, if the account region is outside the listed European countries (Takeout covers most of them).
- Drive Labels, Approvals (INFERENCE), Vault holds, and Alert Center alerts: no data exists for consumer accounts.

**Never exposed by Google at all (INFERENCE from the schemas):**

- The original local filesystem timestamps of an uploaded file. Only what the uploader sent as `createdTime`/`modifiedTime`, or EXIF, survives.
- The uploading device, app version, or network.
- Permanently deleted files (after trash purge), and their Activity once gone (UNVERIFIED).
- Other apps' `appDataFolder` contents (for example phone-app backups in Drive). `drive.appdata` only reaches the calling app's own folder.

---

## 6. Proposed scope bundles (shards) across multiple GCP projects

**Ground rules found:**

- **DP scopes cannot share an authorization request with any other scope.** DP needs its own client/request (VERIFIED-DOC). A separate project is not stated as required (UNVERIFIED), but it is cleanest.
- **Testing status:** max **100 test users per project**, and **7-day** authorization/refresh-token expiry (https://support.google.com/cloud/answer/15549945). Four accounts fit easily.
- An unverified app shows the "unverified app" screen. The broader unverified-app cap is "100 new users in total" (https://support.google.com/cloud/answer/7454865).
- Restricted-scope verification exceptions: personal use, "development, testing, or staging". Verification is per project (https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification).
- **No documented per-project limit on scope count was found (UNVERIFIED).** The owner's statement that one client "can't be granted the full recommended set" matches no rule found in the fetched docs. It may be a consent-screen UI, verification, or granular-consent effect. Record it as an observed constraint.
- Google's granular consent lets a user untick individual scopes. The receipt must read the *granted* scopes (tokeninfo), not the requested ones (INFERENCE from spec §2).

| Shard | APIs to enable | Scopes (read-only) | Class | Unlocks census entries |
|---|---|---|---|---|
| **S1 Drive core metadata** | drive | `drive.metadata.readonly` | R | files (all fields), permissions, revisions metadata, comments/replies, changes, approvals, accessproposals, listLabels, about, v2 files/revisions/permissions/comments |
| **S2 Drive bytes** | drive | `drive.readonly` | R | files.get alt=media, export (all formats), download LRO, revision bytes (keepForever), revision exportLinks; supersedes S1 if one Drive shard is allowed |
| **S3 Drive history** | driveactivity, drivelabels | `drive.activity.readonly`, `drive.labels.readonly` | R / UNVERIFIED | Activity (create origin, moves, renames, permission changes, actors); Labels definitions (expected not_supported) |
| **S4 Identity resolution** | people, oauth2 | `contacts.readonly`, `contacts.other.readonly`, `userinfo.email`, `openid` | S (UNVERIFIED) / NS | Actor `people/ID` resolution, otherContacts, capture context (account email, granted scopes) |
| **S5 Mail corroboration** | gmail | `gmail.readonly` (or `gmail.metadata` if bodies are excluded) | R | Drive share/comment notification emails, attachments, headers, internalDate |
| **S6 Calendar/Tasks/Forms/Docs structure** | calendar, tasks, forms, docs, sheets, slides | `calendar.readonly`, `tasks.readonly`, `forms.body.readonly`, `forms.responses.readonly`, `documents.readonly`, `spreadsheets.readonly`, `presentations.readonly` | S (docs verified; others UNVERIFIED) | Event attachments, form responses, suggestions/named ranges/developerMetadata |
| **S7 Photos** | photospicker, picker | `photospicker.mediaitems.readonly` (+ `drive.file` for the Drive picker) | UNVERIFIED / NS | Hand-picked Photos items (capture time, camera, EXIF minus GPS) |
| **S8 YouTube** | youtube | `youtube.readonly` | UNVERIFIED | Owned-video fileDetails and recordingDetails |
| **S9 Automation context** | script | `script.processes`, `script.projects.readonly` | UNVERIFIED | Script process history |
| **DP-A My Activity** (own client, DP-only request) | dataportability | `myactivity.search`, `myactivity.maps`, `myactivity.youtube`, `myactivity.play`, `myactivity.shopping`, `myactivity.myadcenter` | R / S | Time-filterable activity archives (keep TF-capable groups together; add `chrome.history` here too) |
| **DP-B Chrome** | dataportability | `chrome.history` (TF), `chrome.bookmarks`, `chrome.autofill`, `chrome.reading_list`, `chrome.extensions`, `chrome.settings`, `chrome.dictionary` | R / S | Browsing chronology; do not mix TF and non-TF groups in one time-filtered call |
| **DP-C Maps** | dataportability | `maps.*` (11), `mymaps.maps`, `streetview.imagery` | R / S | Labeled/starred places, commute routes, Maps photos with GPS |
| **DP-D YouTube** | dataportability | `youtube.*` (17) | R / S | Private/unlisted video media, messages, posts, comments |
| **DP-E Devices & home** | dataportability | `nest.*`, `pixel.device_data`, `fitbit.device_events`, `play.devices`, `play.installs` | UNVERIFIED / R / S | Camera events/video, device telemetry, app installs by device |
| **DP-F Commerce & misc** | dataportability | `play.*` (rest), `shopping.*`, `order_reserve.*`, `saved.collections`, `discover.*`, `search_ugc.*`, `searchnotifications.*`, `alerts.subscriptions`, `businessmessaging.conversations` | R / S | Purchases, saved items, reviews |
| **N/A (do not request)** | admin, vault, alertcenter, cloudidentity, keep, drivemcp, photoslibrary read, fitness | — | — | Receipt: `not_supported_for_account` with the reasons in §3 |

**Shard notes:**

- **S1 vs S2:** `drive.readonly` is a superset for reads. If a single Drive shard is possible, use S2 alone. If the owner wants a metadata-only default (spec §2 Mode A), keep S1 as the default client and S2 for Mode B byte capture.
- **All DP shards** depend on region eligibility (§4.3). Probe one before building DP-B to DP-F.
- **Testing-mode tokens expire in 7 days on every shard.** Mode B "Get more" must plan for re-consent.

---

## 7. Recommended live verification (cheapest first, owner-authorized only)

1. `accessType.check` with a DP-A test-user token on one account. This settles region eligibility.
2. `activity.query` (`consolidationStrategy.none`) on the oldest known Drive file. This establishes the Activity history horizon.
3. `revisions.list` plus `revisions.get?alt=media` on one binary file with a non-pinned revision under 30 days old. It checks the keepForever-only download rule.
4. A revision `exportLinks` fetch with a bearer token on one Doc. It checks per-revision native export.
5. `approvals.list`, `accessproposals.list`, and `files.listLabels` on one consumer file. These confirm empty vs error.
6. `files.create` in a scratch folder with an explicit `createdTime`, then purge. This confirms whether createdTime is client-settable. It writes to the source account, so the owner must approve it separately.

## 8. Sources

**Discovery** (unauthenticated; revisions in §0):

- https://www.googleapis.com/discovery/v1/apis/drive/v3/rest
- https://www.googleapis.com/discovery/v1/apis/drive/v2/rest
- https://driveactivity.googleapis.com/$discovery/rest?version=v2
- https://drivelabels.googleapis.com/$discovery/rest?version=v2
- https://admin.googleapis.com/$discovery/rest?version=reports_v1
- https://vault.googleapis.com/$discovery/rest?version=v1
- https://alertcenter.googleapis.com/$discovery/rest?version=v1beta1
- https://dataportability.googleapis.com/$discovery/rest?version=v1
- https://photoslibrary.googleapis.com/$discovery/rest?version=v1
- https://photospicker.googleapis.com/$discovery/rest?version=v1
- https://keep.googleapis.com/$discovery/rest?version=v1
- https://workspaceevents.googleapis.com/$discovery/rest?version=v1
- https://script.googleapis.com/$discovery/rest?version=v1
- https://forms.googleapis.com/$discovery/rest?version=v1
- https://tasks.googleapis.com/$discovery/rest?version=v1
- https://fitness.googleapis.com/$discovery/rest?version=v1
- https://health.googleapis.com/$discovery/rest?version=v4
- people, gmail, calendar, docs, sheets, slides, and youtube equivalents
- https://www.googleapis.com/discovery/v1/apis

**Docs:**

- Drive
  - https://developers.google.com/workspace/drive/api/guides/api-specific-auth
  - https://developers.google.com/workspace/drive/api/guides/manage-revisions
  - https://developers.google.com/workspace/drive/api/guides/manage-downloads
  - https://developers.google.com/workspace/drive/api/guides/approvals
  - https://developers.google.com/workspace/drive/api/guides/pending-access
  - https://developers.google.com/workspace/drive/api/guides/configure-mcp-server
  - https://developers.google.com/workspace/drive/api/guides/events-overview
- Drive Activity and Labels
  - https://developers.google.com/workspace/drive/activity/v2
  - https://developers.google.com/workspace/drive/activity/v2/reference/rest/v2/activity/query
  - https://developers.google.com/workspace/drive/labels/guides/overview
  - https://support.google.com/a/answer/9292382 (via search summary)
- Admin, Vault, Alert Center, Cloud Identity
  - https://developers.google.com/workspace/admin/reports/v1/get-start/overview
  - https://knowledge.workspace.google.com/admin/reports/data-retention-and-lag-times
  - https://knowledge.workspace.google.com/vault/getting-started/vault-overview
  - https://developers.google.com/workspace/admin/alertcenter/guides
  - https://docs.cloud.google.com/identity/docs/overview
- Keep, Gmail, Calendar, Docs, People
  - https://developers.google.com/workspace/keep/api/guides
  - https://developers.google.com/workspace/gmail/api/auth/scopes
  - https://developers.google.com/workspace/calendar/api/auth
  - https://developers.google.com/workspace/docs/api/auth
  - https://developers.google.com/people/api/rest/v1/people/get
- Workspace Events
  - https://developers.google.com/workspace/events
  - https://developers.google.com/workspace/events/guides/events-drive
  - https://developers.google.com/workspace/events/release-notes (search summary)
- Photos
  - https://developers.google.com/photos/support/updates
  - https://developers.google.com/photos/overview/authorization
  - https://developers.google.com/photos/picker/guides/media-items
  - https://developers.google.com/photos/picker/reference/rest/v1/mediaItems
- Data Portability
  - https://developers.google.com/data-portability/user-guide/overview
  - https://developers.google.com/data-portability/user-guide/time-based
  - https://developers.google.com/data-portability/user-guide/methods
  - https://developers.google.com/data-portability/user-guide/time-filter
  - https://developers.google.com/data-portability/user-guide/scopes
  - https://developers.google.com/data-portability/user-guide/configure-oauth
  - https://developers.google.com/data-portability/docs/release-notes
  - https://developers.google.com/data-portability/policy
  - https://developers.google.com/data-portability/schema-reference
  - https://developers.google.com/data-portability/schema-reference/my_activity
  - https://developers.google.com/data-portability/schema-reference/chrome
  - https://developers.google.com/data-portability/schema-reference/maps
  - https://developers.google.com/data-portability/schema-reference/youtube
  - https://support.google.com/accounts/answer/14452558?hl=en
  - https://support.google.com/cloud/answer/14659903?hl=en
- OAuth and verification
  - https://support.google.com/cloud/answer/15549945?hl=en
  - https://support.google.com/cloud/answer/7454865?hl=en
  - https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification
- Takeout and Maps Timeline
  - https://support.google.com/accounts/answer/3024190?hl=en
  - https://support.google.com/maps/answer/14169818?hl=en
  - https://support.google.com/maps/answer/6258979?hl=en
- Fit and Health
  - https://developers.google.com/fit
  - https://developers.google.com/health/about
