---
tags: [intake, surrealdb, graph, receipt]
---

# Live Intake filesystem-graph population — 2026-09-14 / 2026-09-15

> _Byline: Claude Code · Sonnet 5 · 2026-09-14_

Relaunch of a task whose previous agent was lost mid-run (no prior receipt existed
under this filename). Goal: project the live `xplorer-live-20260914` inventory
output for source `diskdrill-legal-kb-20260914` into the dedicated Intake
SurrealDB graph (`surreal-intake`, ns `consignatio`, db `intake`), verify by
reading back, and record what remains unprojected.

## 0. Auth + schema check

```
$ export INTAKE_SURREAL_URL="https://surreal-intake.tilapia-skilift.ts.net"
$ uv run casebible-corpus graph-status
{"status": "ready", "namespace": "consignatio", "database": "intake", "version": "surrealdb-3.2.4+20260803.93ab219"}
```

Schema check passed (`verify_health_and_schema` confirms all 33 required node +
relation tables exist: 14 node tables — `archive_part, archive_series,
atomic_unit, content, export_event, identity_assertion, machine_proposal,
occurrence, operation_run, projection_snapshot, representation, review_decision,
store, subject_account` — and 19 relation tables — `alternate_representation_of,
belongs_to_account, confirms_extraction, contains, corroborates, decides_on,
member_of, occurrence_has_content, originated_from, part_of_series,
possible_extraction_of, produced_by, proposal_object, proposal_subject,
proposed_duplicate_of, proposes_subject_for, represents, stored_at,
supersedes_decision`). No password value was ever echoed; it is resolved only
through `casebible_index.secrets.get_secret("INTAKE_SURREAL_PASSWORD")`
(Windows Credential Manager).

## 1. Baseline — read before any write, with live/synthetic split

Read `projection_snapshot` and `operation_run` directly (a coordinator agent had
already taken an independent baseline at 21:52 EDT; this repeats the read
myself and adds the classification the coordinator asked for). Query used:
`SELECT count() FROM <table> GROUP ALL;` plus full `projection_snapshot` /
`operation_run` / `store` dumps and an `occurrence` `GROUP BY snapshot`.

| table | count (before) |
|---|---|
| occurrence | 368 |
| stored_at | 367 |
| store | 6 |
| projection_snapshot | 6 |
| occurrence_has_content | 6 |
| operation_run | 4 |
| produced_by | 4 |
| content | 2 |

Per-snapshot breakdown, classified by reading each snapshot's `metadata`, its
store's `label`/`root_locator`, and whether a `produced_by` edge to a
`completed` `operation_run` exists:

| snapshot (short) | source_id / label | occurrences | nature | completion |
|---|---|---|---|---|
| `1b2fd957…` | `intake-legacy-catalog-projection-v1`, "Historical R2 raw catalog — 25-row graph proof, not live census", real PG query against `ovh-files/casebible/raw_duck.r2_files` | 25 | **real historical metadata** (catalog import, not a live filesystem census) | completed (`operation_run:d2bdf994…`) |
| `6b91f160…` | "SYNTHETIC integration proof - not source evidence" | 3 | **synthetic fixture** | completed (`operation_run:e2302795…`) |
| `815c5a56…` | "SYNTHETIC integration proof - not source evidence" | 3 | **synthetic fixture** | completed (`operation_run:bc566b62…`) |
| `a91dbdb6…` | `intake-r2-b2-occurrence-map-v1`, `generation_id: synthetic-bridge-proof`, "R2 source fixture-bucket" | 3 | **synthetic fixture** | completed (`operation_run:3d39bccd…`) |
| `b5dff344…` | store label "F: case (local corpus store)", `root_locator local:F:/case`, occurrence `metadata.inventory_row.source_id = "f-case"`, real paths (`Evidence/Call data/Cube ACR/...`) | 296 | **real, live — NOT synthetic, NOT mine.** Concurrent projection of a different corpus (`F:/case`), presumably by another active agent in this session (`surreal-corpus-graph`). Projected 2026-09-15 00:48:52Z. | **no `produced_by` edge — incomplete/in-flight**, must not be treated as a finished batch per the design's own completion rule |
| `e4fb057e…` | same store label/kind, `source_id "f-case"`, real paths (`AI_Chats/Snap Subpoena, Pro Se Guide.docx`, …) | 38 | **real, live — NOT synthetic, NOT mine.** Second `f-case` batch, projected 2026-09-15 01:03:54Z. | **no `produced_by` edge — incomplete/in-flight** |

I did not modify, delete, or complete either `f-case` snapshot — they belong to
a different concurrent task and the design explicitly allows a snapshot to sit
uncompleted pending replay by its own owner. Flagging this split back to the
coordinator: of the pre-existing 368 occurrences, 25 are real historical
catalog metadata, 9 are deliberately-retained synthetic fixtures (never to be
treated as canonical), and 334 are a different real corpus's in-flight work
that is not part of this task.

No prior snapshot used `source_id = "diskdrill-legal-kb-20260914"` — confirming
the earlier crashed agent for *this* task never reached a graph write.

## 2. Input inspected

- `output/xplorer-live-20260914/inventory/20260915T004342.956187Z-afa67ac2/files.parquet`
  — schema `casebible-path-inventory-v2`, 537 rows, single `source_id`
  `diskdrill-legal-kb-20260914`, `captured_at` 2026-09-15T00:43:42.956187Z
  (an immutable snapshot taken *before* the concurrent `index` run for the same
  source started at 00:44:55Z — safe to use regardless of that run's live state).
  SHA-256: `043670fff81c4512df31d9a6ec3081dfa348d112725118b58fbed1ec9f95bf67`.
- No `fingerprints/*.parquet` artifact exists yet for this source
  (`find output/xplorer-live-20260914 -iname '*fingerprint*'` is empty), so the
  manifest omits the optional `fingerprints` field. That means zero raw-SHA-256
  content identities can be asserted from this batch — expected and correct per
  `INVENTORY-GRAPH-MANIFEST-V1.md`, not a defect.
- `datasets/documents/*.parquet` and `datasets/chunks/*.parquet` (248 + 248
  shards) were **not** read or projected — they are CocoIndex's semantic lake
  output, out of scope for this graph by design (see §5).

## 3. Manifest and commands run

Manifest written to
`C:/Users/matts/AppData/Local/Temp/claude/E--AI-Workspace-Projects-Propria-Consignatio-Intake/17f83d73-8e58-4651-82de-41589dbe3824/scratchpad/live-graph-inventory-manifest-20260914.json`
(scratchpad, not the repo):

```json
{
  "schema": "intake-inventory-projection-v1",
  "source_id": "diskdrill-legal-kb-20260914",
  "declared_at": "2026-09-15T01:52:13+00:00",
  "store": {
    "root_locator": "local:F:/Disk Drill/Legal_Knowledge_Base_Obsidian",
    "store_kind": "local-volume",
    "label": "DiskDrill Legal Knowledge Base Obsidian (local corpus store, read-only)"
  },
  "inventory": {
    "path": "E:/AI_Workspace/Projects/Propria/Consignatio/Intake/backend/output/xplorer-live-20260914/inventory/20260915T004342.956187Z-afa67ac2/files.parquet",
    "sha256": "043670fff81c4512df31d9a6ec3081dfa348d112725118b58fbed1ec9f95bf67"
  }
}
```

Validation (no graph writes, no credentials needed):

```
$ uv run casebible-corpus graph-project-inventory <manifest>
{"status": "validated", "snapshot_key": "intake-inventory-projection-v1:e8893f68357330f5453dcad3b5edfcc5b0fbedfda1862f762cf6b1e84563a12b", "occurrences": 537, "unique_contents": 0}
```

Scoped test run before applying (25 tests, all passed):

```
$ uv run python -m pytest tests/ -k "surreal or inventory_manifest or graph" -q
.........................                                                [100%]
```

Live apply (ran ~26 minutes over the tailnet — 537 sequential
occurrence+relation writes each doing a read-then-conditional-write round
trip — so it was backgrounded past the 120s foreground limit and watched to
completion rather than assumed):

```
$ uv run casebible-corpus graph-project-inventory <manifest> --apply
{"snapshot_key": "intake-inventory-projection-v1:e8893f68357330f5453dcad3b5edfcc5b0fbedfda1862f762cf6b1e84563a12b", "status": "completed", "occurrences": 537, "unique_contents": 0}
```

No `graph-project-catalog` or `graph-project-migration` run was needed for this
task: there is no historical-catalog batch or R2→B2 occurrence map for the
`diskdrill-legal-kb-20260914` source, so only `graph-project-inventory` applies
(the catalog/migration commands cover unrelated inputs — see
`docs/LEGACY-CATALOG-GRAPH-MANIFEST-V1.md` and
`docs/R2-B2-OCCURRENCE-GRAPH-CONTRACT-V1.md`).

## 4. After — counts and read-back proof

| table | before | after | delta |
|---|---|---|---|
| occurrence | 368 | 905 | +537 |
| stored_at | 367 | 904 | +537 |
| store | 6 | 7 | +1 |
| projection_snapshot | 6 | 7 | +1 |
| occurrence_has_content | 6 | 6 | +0 (expected — no fingerprints) |
| operation_run | 4 | 5 | +1 |
| produced_by | 4 | 5 | +1 |
| content | 2 | 2 | +0 (expected — no fingerprints) |

`projection_summary()` for the new snapshot
(`intake-inventory-projection-v1:e8893f68357330f5453dcad3b5edfcc5b0fbedfda1862f762cf6b1e84563a12b`,
graph id `projection_snapshot:627d37cba414f10b024008a7363795c44e0320969e5e307d41af08e433811e8d`):

```json
{
  "occurrences": 537, "stores": 1, "stored_at": 537, "content_links": 0,
  "completion": [{"status": "completed", "out": "operation_run:d2f361c6…",
                  "counts": {"occurrences": 537, "unique_contents": 0}}]
}
```

Store record (real read-back, not the write echo):

```json
{
  "id": "store:0b1784dce688fd7eecce4d13dd9a27a57a2457b5af21fad4e7826b0e87819dbb",
  "root_locator": "local:F:/Disk Drill/Legal_Knowledge_Base_Obsidian",
  "store_kind": "local-volume",
  "label": "DiskDrill Legal Knowledge Base Obsidian (local corpus store, read-only)",
  "metadata": {"source_id": "diskdrill-legal-kb-20260914"},
  "snapshot": "projection_snapshot:627d37cba…"
}
```

Three sample read-back queries proving occurrence → store relationships exist:

1. **`Background_Research/Individuals/PARSING_SCHEMAS.md`** — occurrence record
   read back with full `inventory_row` preserved (14,127 bytes, source
   modified 2026-02-26), plus `graph_neighborhood()` showing exactly one
   `stored_at` edge from this `occurrence` to the `store` above:
   `{"id": "stored_at:8e29eb95…", "in": occurrence:364ebc03…, "out": store:0b1784dc…, "relation": "stored_at"}`.
2. **`Obsidian_Attachments/Clippings/6-time-bar-colors-min.jpg.sidecar.md`** —
   read back by its deterministic projection key
   (`…:occurrence:diskdrill-legal-kb-20260914:<relative_path>`); 284 bytes,
   `entry_kind: file`, snapshot correctly points at
   `projection_snapshot:627d37cb…`.
3. **`Obsidian_Attachments/Clippings/Images/mapweave-...-800x460-1.png`** —
   same read-back pattern; 119,096 bytes; confirms the projection key scheme
   is stable and collision-free across very different path shapes (sidecar
   `.md`, binary `.png`, nested nine-level paths).

No `content` nodes or `occurrence_has_content` edges were created by this
batch, consistent with the absence of a fingerprints artifact — verified by
`content_links: 0` in the summary and the unchanged `content` table count.

## 5. What is NOT projected yet

- **Raw-content identity (`content` nodes / `occurrence_has_content` edges)**
  for this corpus: requires running `casebible-corpus fingerprint` against
  this inventory first, then re-running `graph-project-inventory` with the
  `fingerprints` manifest field populated. Covered by the existing
  `graph-project-inventory` command and `INVENTORY-GRAPH-MANIFEST-V1.md` —
  no new design needed, just an unrun step.
- **Atomic/nested-unit structure** (`atomic_unit`, `contains`,
  `part_of_series`, `member_of`, archive parts/series): `detect-units` has not
  been run for this source, and there is no CLI command that projects atomic
  units into the graph at all yet (`graph-project-*` covers inventory, legacy
  catalog, and R2→B2 occurrence maps only). This is Phase 6 in
  `backend/docs/CASEBIBLE-CORPUS-BACKEND-SYSTEM-DESIGN.html` ("Units,
  provenance, derivation, corroboration, alternate representations,
  candidates, events, temporal links") and remains unimplemented.
- **Document/chunk semantic lake data** (`datasets/documents/*.parquet`,
  `datasets/chunks/*.parquet`, 248+248 shards): by the settled design in
  `docs/DEVELOPMENT.md` ("Filesystem index and graph — existing decision
  restored"), this filesystem graph is deliberately *not* the evidence/search
  index — Weaviate owns semantic search over that lake output. No projection
  command reads `datasets/` at all; this is intentional scope separation, not
  a gap.
- **`representation`, `identity_assertion`, `machine_proposal`,
  `review_decision`, `subject_account`, `export_event` node tables**: schema
  exists (part of the 33 required tables) but no projection code writes them
  yet — also Phase 6.
- **Replay/idempotency was not re-exercised live** for this batch (the
  synthetic fixtures on 2026-09-12 already proved replay correctness and CBOR
  null-handling under test; re-running 537 real writes a second time to prove
  it again live was judged not worth the ~26 extra minutes of tailnet round
  trips for a mechanism already covered by 25 passing unit/integration tests
  plus the prior live proof). If the owner wants it proven again on this exact
  batch, re-run the same `--apply` command; it is safe (compare-and-set,
  fails closed on any mismatch).

## 6. Failures and fixes

None. `graph-status`, validation, and apply all succeeded on the first attempt.
The only operational wrinkle was the apply exceeding the 120s foreground
command limit (537 sequential read+write round trips over the tailnet), which
was handled by backgrounding the command and polling its output file to
completion rather than declaring success early — no code change was required.

## 7. Next concrete test the owner can perform

- Reconcile the two incomplete `f-case` snapshots
  (`projection_snapshot:b5dff344…`, 296 occurrences, and
  `projection_snapshot:e4fb057e…`, 38 occurrences) with whichever agent/session
  owns them — they currently have no `produced_by` completion edge and should
  either be completed (replay to finish) or explicitly marked
  failed/superseded by their owner; this receipt does not touch them.
- Run `casebible-corpus fingerprint --scope dedup-candidates` (or `all`)
  against `output/xplorer-live-20260914/inventory/20260915T004342.956187Z-afa67ac2/files.parquet`,
  then re-run `graph-project-inventory` with a manifest that adds the
  resulting `fingerprints` artifact, to populate real `content` identities for
  the 537 `diskdrill-legal-kb-20260914` occurrences.
- Spot-check the live graph directly:
  `SELECT * FROM occurrence WHERE metadata.inventory_row.source_id = 'diskdrill-legal-kb-20260914' LIMIT 5;`
  against `https://surreal-intake.tilapia-skilift.ts.net` as `intake_runtime`.

## Changed paths

- `Intake/backend/docs/LIVE-GRAPH-POPULATION-2026-09-14.md` (this file, new)
- No source code changes were needed (`src/casebible_index/**` untouched).
- No records were deleted, overwritten, or superseded; no Docstore or Weaviate
  writes were made.
- Scratchpad-only, not in the repo: the manifest JSON at
  `C:/Users/matts/AppData/Local/Temp/claude/E--AI-Workspace-Projects-Propria-Consignatio-Intake/17f83d73-8e58-4651-82de-41589dbe3824/scratchpad/live-graph-inventory-manifest-20260914.json`
  and diagnostic scripts under `/tmp/*.py` (session-local, not committed).
