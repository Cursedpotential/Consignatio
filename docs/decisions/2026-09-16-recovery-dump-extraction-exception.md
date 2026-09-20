---
title: Recovery-dump extraction exception to the Recovery/Recycle/Recap addendum
date: 2026-09-16
status: owner-decision
tags: [consignatio, vault, policy, decision, recovery, recup_dir, photorec, integrity, file-type, exception]
supersedes: none
relates_to:
  - docs/policy/2026-09-16-recovery-recycle-recap-triage-and-canonicalization-addendum.md
  - docs/policy/2026-09-16-object-storage-preservation-and-sorting-plan.md
---

> _Byline: Claude Code · Fable 5.1 · 2026-09-16 22:45 EDT. Owner decision, verbatim below; recorded as an explicit written exception rather than a silent break of the addendum's "preserve the recovered-root layout" rule._

## Owner decision (2026-09-16 22:43 EDT, verbatim)

> I actually want all of these fucking extracted. Into master directories based on file type. If you can extract more information from it, or if it's in a folder or something cool, keep it there, but otherwise, if it's just in a recap directory and it's just a dump, let's somehow segregate it. Can we also check for file integrity? Because a lot of those images don't even open.

## The rule as recorded

The addendum classifies every recovery-output root (`recup_dir.*`, `$Folder…`, `FOUND.000`, `recovered`, …) as `preserve_root` and forbids renaming its internal objects. **For recovery dumps whose internal layout carries no information beyond the tool run, that rule is replaced by this one:**

1. **Dump test.** A recovery folder is a *dump* when its files carry synthetic names (`f1234567.jpg`, `$R…`, `recup_dir.N/…`) and no meaningful sub-structure. PhotoRec output is the canonical case: 531 `recup_dir.*` folders in vault/v1 (192 at depth ≤ 3), 90,656 files / 46 GB by the 08:10 listing, to be recounted on the current listing.
2. **Keep in place when it carries information.** A recovered file stays where it is if (a) it sits in a folder whose name or siblings mean something (a real path fragment, a project, an export layout), or (b) it carries extractable identity of its own (EXIF/XMP capture data, document properties, embedded IDs, a matching sidecar). That identity is recorded and may promote the file to its real parent container per the addendum's high-confidence rules.
3. **Otherwise extract by type.** Dump files move into master type directories at the vault root using the existing Windows type-description naming already present there (`JPEG Images`, `PDF Documents`, `Movie Files (mp4)`, `HTML Files`, `ZIP archives`, `SQLite databases`, …); types without a folder get one in the same style (`PNG Images`, `Text Documents (txt)`, `GZIP Archives (gz)`, …). Exact-hash matches to an object already in the vault are **linked, not copied** (`exact_duplicate_of`), and the recovery occurrence is retained as provenance.
4. **Provenance survives the move.** Every extracted file keeps its original recovery key, recovery tool/run, and folder in the catalog (`source_occurrences` + the move manifest). The addendum's "why was this chosen" record applies.
5. **Integrity is checked before filing.** Every recovered file gets an `integrity_status` from a real content check, not a name or size: image decode (PIL `verify` + full load, dimensions, EXIF presence), PDF parse (page count), archive test (zip/gz/bz2/tar listing), audio/video probe (ffprobe stream + duration), SQLite `PRAGMA integrity_check`, text/HTML charset sanity, zero-fill and truncation detection. Files that fail go to `review-and-control/recovery-and-restoration/unresolved-fragments/<type>/` with the failure reason, not into the master type directories. Zero-filled payloads are `zero_filled`, never candidates.
6. **Nothing is deleted.** Extraction is copy-verify-commit; the recovery keys are retired only under the standing retire decision (validation window, then approved delete).

## Why

The addendum's preserve-root rule exists to keep recovery context that might map a fragment back to its origin. PhotoRec's `recup_dir.N/fNNNNNNN.ext` layout encodes nothing but carving order; keeping it preserves noise, and the owner's stated need is to *see and use* the recovered material, which requires it to be sorted by what it is and known to open.

## How to apply

- This exception applies to recovery dumps only. `$Folder…` trees from the Google restore, `Recovered Files`, `Triage/_recovered`, and any recovery folder with real names or structure are judged per rule 2 first; when in doubt, keep in place and record.
- The integrity check runs on the VPS reading from B2 (never on the desktop); results land in the catalog as a tracked table with tool, version, run id and reason per file.

## Amendment 2026-09-17 08:06 EDT (owner "yes")

> _Byline: Claude Code · Opus 5 · 2026-09-17_

Recovered program files, libraries, fonts, configs and source files (any generic `<EXT> Files` type or `No Extension`, i.e. types with no content checker: DLL, ELF, EXE, TTF, WOFF, JAR, JKS, PY, H, JAVA, INI, .a, …) go to their own `Software Fragments/<type>/` folder at the vault root, kept out of the photo and document type directories. Media, documents and data archives that merely lack a named type (CAF audio, XZ, 7z, RAR, or any file whose content sniffs as image/av/pdf/sqlite) stay with the type directories. Manifest: `raw_duck.recovery_manifest_20260917` (built by `casebible/tools/recovery_integrity_03_manifest.sql`).
