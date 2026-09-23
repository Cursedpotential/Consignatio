---
title: The catalog is the source of truth across all chats
date: 2026-09-16
status: accepted
decided_by: owner (Matt Salem)
recorded_by: Claude Code · Fable 5.1
domains: [consignatio, intake, infra]
tags: [decision, owner-directive, catalog, lakehouse, raw-duck, consignatio, intake, b2, vault, docstore]
---

# Decision: the catalog is the source of truth across all chats

> _Byline: Claude Code · Fable 5.1 · 2026-09-16 08:37 EDT_

## Owner statements (verbatim, 2026-09-16)

- 07:48 EDT: "shouldn't it all be in the catalog? Like, isn't that the whole point of a lakehouse?"
- 07:48 EDT: "I'm failing to understand why we built a lakehouse if it still takes a fucking hour to scan something."
- 08:32 EDT: "enforce the catalog across all chats"

## Decision

PostgreSQL database `casebible`, schema `raw_duck`, on ovh-files (Coolify database
`fgz1n7useplhk0t91uk7k1aw`) is the single source of truth for what exists, where it
is, its size, its hashes and its provenance, across every Propria session and tool.

1. **Load first, then query.** Every listing of B2, R2, Google Drive, OneDrive or a
   local disk is loaded into a `raw_duck` table by a dated, tracked script under
   `Consignatio/casebible/tools/` before any question is asked of it.
2. **Never re-scan for an answerable question.** No bucket walk, no re-parse of a
   listing JSON, no `rclone lsjson` over a tree the catalog already holds. A scan that
   takes an hour is evidence the catalog was bypassed.
3. **No private copies of the truth.** Facts live in `raw_duck` tables; the
   human-readable side is `Consignatio/docs/receipts/`; the operational log is
   `Consignatio/docs/URGENT-TODO.md`. Scratchpads hold nothing anyone else needs.
4. **New facts land as catalog tables** (listings, hashes, plans, keep/delete lists,
   receipts): `raw_duck.<name>` plus the script that built it. A snapshot that is
   superseded by a later listing gets a new dated table; the old one is not overwritten.
5. **Ordering rule (07:04 EDT):** organization lands first; indexing and hashing come
   after, driven from the catalog, never as a precondition to see files.

## Tables in force on the decision date

`b2_objects` (intake layer, 530,070 objects / 2.769 TB, listed 2026-09-14 18:11 UTC),
`b2_content`, `source_occurrences`, `atomic_units` / `atomic_unit_members`,
`vault_units_v2`, `vault_place_v6` / `vault_mounts_v6` / `vault_copy_manifest_v6`,
`vault_objects` (fresh vault/v1 listing, 1,677,487 rows, md5 on 99.997% via
`vault_place_v6`, sha1 on 99.89% via `b2_objects`), `vault_twins_*` (twin-structure
analysis, 2026-09-16), `vault_keep_v6` (dedupe keep list, propria-79 lane).

## Enforcement

- Recorded as a HARD RULE in the owner's global `~/.claude/CLAUDE.md` (Workflow section)
  so every session loads it at start.
- Auto-memory `catalog-is-source-of-truth` in the Consignatio memory store.
- Broadcast at 08:33 EDT to the live sessions intake-23, intake-44, intake-5d, propria-68.
- This file is indexed by the Docstore pipeline (never hand-registered); the decision
  log row is written with `fn::decision_amend` after indexing.

## Consequences

- The vault twin analysis (2026-09-16) runs entirely against `raw_duck.vault_objects` and
  `vault_twins_dir_files`; the first attempt to re-walk B2 was stopped.
- Any tool that browses files (Spacedrive, Intake/Xplorer, a virtual filesystem such as
  JuiceFS / SeaweedFS) should be fed from the catalog rather than by walking storage.
