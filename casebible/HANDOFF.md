# Case Bible — Handoff to Claude Code
**Date:** 2026-08-23 · **From:** Opus 5 (chat session, MCP tooling died mid-task)
**Owner:** Matt Salem — pro se father, Genesee County MI custody case

---

## 0. THE RULES (non-negotiable)

1. **Matt runs everything.** You write scripts, he executes. Never run destructive ops yourself.
2. **No hard deletes. Ever.** Quarantine only — move, never delete.
   **`.review_hold` is NOT a quarantine bin.** It holds IMPLEMENTED TODOs and HANDOFFS
   awaiting archiving. Do not dump junk, duplicates, or excluded content there.
   Use explicit self-describing prefixes instead, e.g.
   `casebible-quarantine/_isolated_credentials/`, `casebible-quarantine/_excluded/`,
   `casebible-quarantine/_retired/`, `casebible-quarantine/_snapshots/`.
3. **Never infer disposition from a name.** Not a bucket name, not a folder name, not a container
   name. Only the registry decides. This rule exists because it has already caused real damage.
4. **Nothing is lost.** Every scattered store gets loaded before anything is collapsed.
5. **Ask before creating files/artifacts.** Plan first, iterate, then build.
6. Case Bible = **INVENTORY ONLY** (what exists, where, hashed?, sorted?, moved by whom).
   The **platform** (Agno-MCP-Platform) handles evidence, parsing, custody chain, ingestion.

---

## 1. CURRENT TASK

> **UPDATE 2026-08-27 (Claude Code · Fable 5, workspace lane):** Owner ruled 07:07 — **`casebible-pg18` (:5434) is the single
> home**; agentos-db is going away, so the `casebible` DB that the Aug-24/25 Claude Code lane built on agentos-db (:5432,
> now 36 tables: analysis / evidence / knowledge / llm_eval / media / ops / reference / working) is to be **consolidated INTO :5434 and
> verified**. Scripts written (Matt runs): `cb_consolidate_5432_to_5434.sh` (on ovh-files; --dry-run then --go; dumps, snapshots to
> r2:casebible-quarantine/_snapshots, restores in 3 sections, refuses if target already has those schemas) and
> `cb_verify_consolidation.py` (from the PC; count + md5-row-hash per table both sides; `--log` appends ops.migration_log).
> **CONSOLIDATION DONE 2026-08-27 21:59Z:** `cb_consolidate_5432_to_5434.sh --go` run on ovh-files (dump 40 MB, snapshot at
> `r2:casebible-quarantine/_snapshots/casebible_from_agentos_20260827T215859Z.dump`). `cb_verify_consolidation.py --log`: **36/36 tables
> identical by count + md5 row hash**, 36 rows appended to `ops.migration_log` on :5434, `catalog.od_manifest` untouched (1,869,794).
> All 11 extensions + the 4 immutability guard functions + 6 triggers present on :5434. The pre-created landing schemas
> (`raw_*`, `exports`, `gdrive`, `legacy_hashes`, `recovery`, `rootcsv`, `backups`, `analysis`) were EMPTY at that moment — Stage 1
> `--go` has still not loaded data. **Source on agentos-db left intact** (drop only on Matt's word). PG16 `analysis` migration in §4
> "Then 2." is now redundant: those 5 media tables already sit verified in `:5434/media.*` (enrichment 15,252 · faces 6,911 ·
> faces_scanned 7,121 · photos 7,121 · screenshots 3,113).
> **Stage 2 done:** `cb_prove.py` written and run read-only 17:47 → `cb_prove_report_20260827-174710.md`. Result: only
> `sorted_41621` (in_sorted → sorted_best) collapses; the other five families FAIL at least one check — see report. Step 4 (collapse)
> not started per owner ("??"). Note: an `llm-probe` service (ovh-files :8030) writes to `casebible.llm_eval` on :5432 — repoint after migration.
>
> **READINESS UPDATE 2026-08-29 (Codex):** the recorded Stage 1 dry run was not approval-ready: attached DuckDB/SQLite
> enumeration failed, dry-run could create schemas, the script embedded an admin password, same-stem CSV/Parquet files could collide,
> and `ignore_errors` dropped six legacy-hash paths containing `|`. `cb_load_raw.py` was repaired in place: libpq
> `service=casebible`, a dry-run that performs no PostgreSQL writes, `duckdb_tables()` enumeration, distinct same-stem tables, strict CSV reads,
> lossless legacy-line parsing, verification of the already-consolidated `media.*` tables, existing-table count verification, and
> nonzero exit on any failure. The two legacy files each contain exactly **590,560 physical rows**; 58 rows intentionally have blank
> MD5 values for large/unhashed files. The earlier “~900,000” expectation was stale. **Matt must rerun `--dry-run` and review its new
> receipt; `--go` remains unrun and blocked until that review.** Local-only source preflight passed without PostgreSQL access:
> 51 attached-DB tables / 16,166,939 rows; 33 CSV/Parquet tables / 1,681,622 rows; two legacy-hash tables / 1,181,120 rows; and
> GDrive / 125,719 rows — **19,155,400 prospective raw rows total**, before existing target tables are skipped.
>
> **STAGE 1 COMPLETE 2026-08-30 (Codex):** Owner explicitly directed the agent to run the real load. The first governed-role
> attempt proved `cb_agent` lacked landing-schema privileges and wrote zero tables. Granted only `USAGE, CREATE` on the ten raw
> landing schemas, then reran `cb_load_raw.py --go`. Final receipt: **87 tables / 19,155,400 rows loaded; zero load or count
> failures**. Independent live recount matched exactly: `raw_duck` 44 / 15,523,421; `raw_duck_d` 2 / 605,666; `raw_misc` 3 /
> 32,959; `raw_sqlite` 2 / 4,893; `recovery` 6 / 110,745; `exports` 12 / 213,454; `backups` 2 / 1,825; `rootcsv` 13 /
> 1,355,598; `legacy_hashes` 2 / 1,181,120; `gdrive` 1 / 125,719. `catalog.od_manifest` remained **1,869,794**. DuckDB's
> PostgreSQL adapter cannot issue schema comments, so the schema-owner connection applied all 11 authority comments directly;
> live verification confirmed all are present. No source row/file was moved, changed, collapsed, or deleted. Stage 3 has not run.

Consolidate **8 scattered databases / 59 tables** into ONE database, losing nothing, then
build a normalized inventory layer on top.

**Script is repaired; the prior dry run is stale and must be rerun. `--go` has NEVER been run.**

```powershell
cd E:\AI_Workspace\casebible
python cb_load_raw.py --dry-run     # writes nothing, reports what it would do
python cb_load_raw.py --go          # only after reading the dry-run output
```

### Before `--go`

```bash
# 1. Serve PG16 (else the analysis migration silently skips)
ssh ovh-files "sudo tailscale serve --bg --tcp 5433 tcp://172.18.0.3:5432"

# 2. Snapshot catalog (1.94M rows) — the script DETECTS damage, it cannot UNDO it
ssh ovh-files
docker exec fgz1n7useplhk0t91uk7k1aw pg_dump -U postgres -d casebible -n catalog -Fc -f /tmp/cat.dump
docker cp fgz1n7useplhk0t91uk7k1aw:/tmp/cat.dump /tmp/
rclone copy /tmp/cat.dump r2:casebible-quarantine/_snapshots/
```

### Watch for in the dry-run output
- `legacy_hashes.raw_sizehash` and `legacy_hashes.raw_hashes` should each be **590,560 rows**.
  Of those, 58 rows have blank MD5 values because the source files were not hashed; six paths contain literal `|` characters.
  Any lower count is data loss — investigate before `--go`.
- `rootcsv` globs loose `.csv` at the casebible root. If the count surprises, that's the point.

---

## 2. ENVIRONMENT (verified live 2026-08-23 — the plugin docs were WRONG, see §5)

### Hosts (renamed 2026-07-06; plugin docs still use old names)

| Old | Current | Tailnet IP | Role |
|---|---|---|---|
| IONOS | `ion-control` | 100.98.98.38 | Coolify control plane |
| ovh1 | `ovh-app` | 100.72.169.40 | agno / AgentOS |
| ovh2 | **`ovh-files`** | 100.91.190.107 | **Case Bible compute + all Postgres + Weaviate + n8n + neo4j + graphiti** |
| ovh3 | `ovh-data` | 100.119.96.29 | **DEAD 2026-08-12** (offline, not deleted, nothing stranded) |

Tailnet: `tilapia-skilift.ts.net` · SSH: `ssh ovh-files` (user `ubuntu`, key `~/.ssh/ovh`)

### Databases — THE TUNNEL IS DEAD, use Tailscale Serve

> **ACCESS CHANGE 2026-08-27 22:2x (owner order — "instead of env use pgcrypt"):** connect with libpq **`service=casebible`**
> (role `cb_agent`, :5434) — bootstrap files are `%APPDATA%\postgresql\.pg_service.conf`+`pgpass.conf` on the PC and
> `~/.pg_service.conf`+`~/.pgpass` on ovh-files. All provider/R2/infra credentials now live encrypted in **`ops.secret`**
> (`ops.secret_get('NVIDIA_API_KEY')` after `SET cb.master_key`; helper `cb_secrets.py`). The inline `postgres://…` URL below
> stays valid for admin only; scripts must stop scraping it. `~/.secrets/*.env` are a legacy mirror from this point.

```
:5433 -> 172.18.0.3:5432   casebible-db     PG16   rmj36da884vt5nzueh28mlng   RETIRING
:5434 -> 172.18.0.2:5432   casebible-pg18   PG18   fgz1n7useplhk0t91uk7k1aw   TARGET
:5432                      agentos-db       PG18   platform `ai` DB — NOT CASE BIBLE
```

```
postgresql://postgres:<REDACTED 2026-09-09: password lives in pgpass; use cb_secrets.connect()>@ovh-files.tilapia-skilift.ts.net:5434/casebible
```

**`100.91.190.107:5432` is the PLATFORM database (`ai`/`ai`), not Case Bible.** Pointing Case
Bible tooling at it is a real trap that already nearly happened.

`~/casebible/cb_refresh_dsn.sh` is **DEPRECATED** — it existed to chase a drifting container IP.
Serve + MagicDNS removes the need. Subnet routing to `172.18.0.0/16` is advertised and approved
but does NOT work (drops at the `ts-forward`/`DOCKER-FORWARD` hop). Use Serve.

Coolify DB resources **reject** `ports_mappings` and `custom_docker_run_options` (422). Only
`is_public`/`public_port` are settable and those bind `0.0.0.0` — do not use. Compose apps use
`ports: ['${BIND_IP:-127.0.0.1}:8081:8080']` + `BIND_IP` env var (that's how Weaviate did it).

### R2 (rclone remote `r2`, all live)
`casebible-raw` · `casebible-sorted` · `casebible-quarantine` · **`casebible-hash-ledger`** ·
`casebible-lakehouse` · `photos` · `milvus-memsearch` · `nexus` · `r2-explorer-bucket`

### rclone
Windows binary via scoop. Config at `C:\Users\matts\scoop\apps\rclone\current\rclone.conf`
(scoop moved it; the `%APPDATA%` copy is now stale — delete it).
Remotes: `od`, `od1`, `r2`, `b2`, `gd_net_rw`.

---

## 3. WHAT'S ALREADY DONE (do not redo)

- **Nothing is lost.** All 44,389 unique MD5s in `recovery_by_tree` (110,745 rows / 77.94 GB)
  confirmed present in R2. **Zero unrecoverable, zero single-copy-at-risk.**
- **OneDrive fully covered.** 208,811 unique MD5s in R2, **100% in `final_survivors`**, 98.8%
  physically in `casebible-sorted`. The 2,438-file gap is dev junk (`.py .dll .exe .apk`).
- **SHA-256 backfill COMPLETE** (2026-08-17): 909,343 hashed + 571,353 present, **141,457
  deferred (too large for Worker CPU)**, 40 failures. Records at
  `casebible-hash-ledger/sha256/v2/<xx>/<digest>/<ver>.json` carry **BOTH `digest` (sha256) and
  `md5Hash`** — this is the md5↔sha256 bridge.
- **Google Drive `matt.salemnet@gmail.com` enumerated**: 125,719 files / 1,602 GB, MD5 100%,
  SHA-256 82.1%. **51,086 unique MD5s are NEW** (not in R2), ~1 TB. Saved at
  `E:\AI_Workspace\casebible\gdrive\gd_net_rw.json`.
- **PG16/PG18 both on tailnet**, tunnel eliminated.
- **`casebible_pgdata`** (241 MB, exited container) probed — **fully superseded**, safe to retire.
- `ENVIRONMENT.md` in the plugin rewritten with a 17-item drift register.

---

## 4. WHAT'S LEFT

### THE MIGRATION: local files -> database

This is the core remaining job. Eight scattered stores + a pile of loose files become ONE
database, then a normalized inventory layer on top of it.

```
STAGE 1  LOAD RAW          cb_load_raw.py     DONE 2026-08-30 — 87 tables / 19,155,400 rows verified
STAGE 2  PROVE REDUNDANCY  cb_prove.py        DONE 2026-08-27 (read-only; one family passes)
STAGE 3  COLLAPSE          cb_collapse.py     NOT WRITTEN  (builds inventory.*)
STAGE 4  RECONCILE         (part of stage 3)  every source row must be traceable
```

#### Stage 1 - what lands where

| Schema | Source | Est. |
|---|---|---|
| `catalog` | **already on target - NEVER TOUCHED** | 1,941,580 |
| `raw_duck` | `E:/AI_Workspace/casebible/casebible.duckdb` (44 tables) | ~10.1M |
| `raw_duck_d` | `D:/casebible/casebible.duckdb` FOSSIL, preserved | 605,666 |
| `raw_misc` | merge-plan.duckdb + iterations_index.duckdb | 32,959 |
| `raw_sqlite` | `casebible_work.sqlite` (sort_map 4,878 / copy_log 15) | 4,893 |
| `recovery` | `recovery_by_tree/*.csv` | 110,745 |
| `exports` | `exports/*.csv` + `*.parquet` | ~190,000 |
| `backups` | `backups/*.parquet` | ? |
| `rootcsv` | loose `.csv` at casebible root | ? |
| `legacy_hashes` | `raw_sizehash.txt` + `raw_hashes.txt` (pipe-delimited) | **~900,000** |
| `gdrive` | `gdrive/gd_net_rw.json` | 125,719 |
| `analysis` | PG16 casebible-db - **PERMANENT HOME, not raw** | 35,268 |

**Every row is stamped `_src_file` + `_loaded_at`.** Every `raw_*` schema gets a
`COMMENT ON SCHEMA` reading *"WRITE-ONCE... SUPERSEDED BY inventory.*... DO NOT READ."*
That is what stops the loop (§6) restarting inside the consolidated DB.

**NOT loaded on purpose:** `.log`, `.sh`, `.py`, `.sql`, `.xlsx`, `od_case_bible.tsv`
(no path, no hash - owner dropped it).

#### Stage 2 - the six redundancy families

Identified by identical row counts inside `casebible.duckdb`:

| Rows | Tables | Widest |
|---|---|---|
| 987,529 | base, base2, scored, scored2, scored4, keyed | scored4 |
| 337,067 | survivors, surv4, final_survivors, junk4 | junk4 |
| 76,007 | mcut, media, mfolder, dated, resolved | resolved |
| 41,621 | sorted_best, sorted_best4, in_sorted | sorted_best |
| 1,281,563 | ns_unique, local_files | ns_unique |
| 1,260 | paired, cube | cube |

Three checks per family. **ALL must pass or that family does NOT collapse:**
1. key is 1:1 (`count(*) = count(distinct key)`) in both tables
2. anti-join on key returns 0 rows **in both directions**
3. every narrow column exists in the wide table AND
   `count(*) where narrow.col IS DISTINCT FROM wide.col = 0`

Output is a report Matt reads. No judgement calls, no "close enough".

#### Stage 3 - inventory.* (DDL at `E:/AI_Workspace/casebible/schema_inventory.sql`)

| Table | Answers | Fed by |
|---|---|---|
| `inventory.item` | what is it, **hashed?**, **sorted?** | r2_files, hash ledger, legacy_hashes, gd_net_rw, od_manifest |
| `inventory.location` | **where does it live** (N rows per item) | r2_files, local_files, od_manifest, gd_net_rw, recovery_by_tree, r2_manifest |
| `inventory.movement` | **who moved it, from where, to where, verified?** | od_ledger (9,743), sort_map (4,878), merge_plan (29,188), copy_log (15), copy_manifest |

`inventory.location` exists because `evidence.source` carries only ONE `r2_key`/`local_path`
per row. The same content lives in R2 **and** OneDrive **and** F:\case **and** GDrive at once.
It collapses back to `evidence.source` on handoff by picking the canonical location.

#### Stage 4 - reconcile (mandatory before anything is dropped)

Every source row must be traceable to an inventory row. Unaccounted rows are **listed, not
ignored**. `raw_*` schemas stay until Matt says drop. Only then:
`REVOKE SELECT ON ALL TABLES IN SCHEMA raw_duck FROM cb_agent`.

#### Hash join keys (this is the whole reason the migration works)

```
legacy_hashes.md5  ->  r2_files.md5  ->  hash-ledger md5Hash  ->  hash-ledger digest (sha256)
gd_net_rw          ->  sha256 + md5 + sha1 all provider-supplied
od_manifest        ->  quickxor ONLY - joins NOTHING else, path+size only
```

MD5 is the bridge that lets ~900k locally-hashed files inherit SHA-256 from the R2 ledger
without re-reading a single byte.

### Then

1. Run `cb_load_raw.py` (dry-run → go).
2. Verify `analysis.*`: `enrichment 15252 · photos 7121 · faces_scanned 7121 · faces 6911 ·
   screenshots 3113`. Then stop `casebible-db` in Coolify. **Leave the volume a week.**
3. **Diff `enrichment` columns**: E: DuckDB copy has **33**, PG16 has **32**. Resolve BEFORE
   PG16 goes away.

### Then
4. **`cb_prove.py`** (not yet written, read-only). Six suspected-redundant families in
   `casebible.duckdb`, identified by identical row counts:

   | Rows | Tables | Widest |
   |---|---|---|
   | 987,529 | base, base2, scored, scored2, scored4, keyed | scored4 |
   | 337,067 | survivors, surv4, final_survivors, junk4 | junk4 |
   | 76,007 | mcut, media, mfolder, dated, resolved | resolved |
   | 41,621 | sorted_best, sorted_best4, in_sorted | sorted_best |
   | 1,281,563 | ns_unique, local_files | ns_unique |
   | 1,260 | paired, cube | cube |

   Three checks per family, ALL must pass or it does not collapse:
   (a) key is 1:1 in both; (b) anti-join = 0 rows both directions; (c) every narrow column
   exists in the wide table and `count(*) where narrow.col IS DISTINCT FROM wide.col = 0`.

5. **`cb_collapse.py`** — build `inventory.item/location/movement` (DDL already written at
   `E:\AI_Workspace\casebible\schema_inventory.sql`). Then RECONCILE: every source row must be
   traceable to an inventory row; unaccounted rows listed, not ignored. `raw_*` stays until Matt
   says drop.

6. **`cb_pilot.py`** (written, `E:\AI_Workspace\casebible\pilot\`) — F:\case dry run.
   59,969 files / 46.6 GB, **zero junk dirs, zero zero-byte files, never ingested**.
   4 phases, hashing resumable. `F:\case` is **hydrated OneDrive** — expect high overlap.

7. **B2 is EMPTY** (30 objects / 38.7 MB). There is currently **ONE cloud copy** of 3.1 TB.
   R2 and B2 share **no common hash** (r2=md5, b2=sha1) so they cannot verify against each
   other — verification must route through a local manifest carrying md5+sha1+sha256.
   If Object Lock is enabled: **Governance mode + Legal Hold after verification**, never
   Compliance mode during ingest.

---

## 5. TRAPS — every one of these is verified, not theoretical

| # | Trap |
|---|---|
| 1 | **`casebible-quarantine` is NOT junk.** 745 GB, 98% classified CONTENT by `dec4`, holds the entire OneDrive corpus. Misclassified, then became canonical. |
| 2 | **`final_survivors` (337,067) violates `deduplication_spec.md`'s own anti-pattern** — hash+score flattening, no `duplicate_group_id`, 942,489 dropped rows unrecorded. Treat as a PROPOSAL, not a decision. |
| 3 | **`D:\casebible\casebible.duckdb` is a FOSSIL** (65 MB, 2026-06-23, `r2_files` = 2 cols / 590,560 rows). Live one is **`E:\AI_Workspace\casebible\casebible.duckdb`** (1,491 MB, 2026-08-13, 44 tables). ENVIRONMENT.md used to point at D:. |
| 4 | **`guarded-sync-NEW.csv` (176,344 rows) is WRONG** — computed against the D: fossil (277,417 md5 vs 337,067 actual). **Under-detects duplicates by ~60,000 keys.** Re-run against E:. |
| 5 | **`_SWEPT` / `_TO_BE_DELETED` / `_REVIEW_HOLD` contents do NOT match their names.** Half of `_TO_BE_DELETED` must NOT be deleted. Corrupt and missing files live in there. Only hashing resolves it. |
| 6 | **Milvus is RETIRED — Weaviate replaced it.** `tools/cb_vsearch.py` (pymilvus) is DEAD CODE. |
| 7 | **`docker ps -qf name=postgres` matches NOTHING** on ovh-files — Coolify uses hash names. Filter by image, not name. This silently no-ops scripts. |
| 8 | **Coolify status is unreliable.** It reports `horizon-swift-scratch-pg` as `exited:unhealthy`; `docker ps` shows it **running healthy**. Duplicate service/database registrations exist for the same container. |
| 9 | **`catalog.od_manifest`** (1,869,794 rows) is ~50% duplicated — same scans stored from both `manifests/local/` and `manifests/vps/`. 935,382 distinct paths. `quickxor` hash joins NOTHING else. |
| 10 | **No H3 custody chain exists yet** — `evidence.evidence_hash` is absent because nothing has been promoted. `cb-custody` is aspirational, not broken. Do NOT go on a rescue mission. |
| 11 | **AI chats ≠ communications.** `evidence.raw_ai_chat` vs `raw_imessage/raw_sms/raw_facebook`. `working.chat_*` (AI) vs `working.conversation`/`message` (comms). `is_conversation` is the WRONG discriminator — both read true. AI chat = **context, never evidence**; validation bar is "does it exist and parse", no custody. |
| 12 | **`C:\Users\matts\Downloads` is an ingest hazard** — contains live OAuth client secrets. Exclude credential patterns from any scan: `client_secret*.json`, `rclone.conf`, `.env`, `*credentials*.json`, `*token*.json`, `id_rsa`, `*.pem`, `*.pfx`, **`Chrome Passwords*.csv`**. |
| 13 | **THE `tmp` INCIDENT (2026-08-23) — the clearest proof of the standing rule.** The junk classifier used a bare `tmp` folder-name pattern. `_backup_import/Documents/tmp/` is an **evidence cache**, not scratch. 141 real files / **5.93 GB** were junk-flagged, including `WhatsApp Chat - Katrina Kinzel.zip`, `imessage export 8102689630 2023-2024`, `K- Timeline 3.json` (16.8 MB), `Kailah - Legacy Contact Access Key.pdf`, `location-history*.json` ×5, `+1 (810) 353-3592 2.pdf`, a medical record, and the full financial set (tenant ledger, loan agreement, CheckStubs ×6, Experian/TransUnion/Credit Karma). Flagged **purely because of the folder's name.** Corrected: use `junk_scrub_report_final.csv`, NEVER `junk_scrub_report.csv`. That folder also contains `_chat.txt` + `archive_browser.html` → it is an **ATOMIC UNIT**, do not shred it. |
| 14 | **`.review_hold` is NOT quarantine.** It is for IMPLEMENTED TODOs / HANDOFFS awaiting archiving. The `cb-quarantine` plugin skill and `case-bible-architect` both treat it as a junk bin — **they are wrong**. Fix the skill before running it. Excluded/isolated content goes to explicit prefixes (`_isolated_credentials/`, `_excluded/`, `_retired/`, `_snapshots/`). This is the same name-meaning drift as traps 1, 5 and 13. |

---

## 6. THE LOOP (why this mess exists — do not restart it)

```
Uncertainty about what exists → new scan → new store → stores disagree → MORE uncertainty ─┐
   ^──────────────────────────────────────────────────────────────────────────────────────┘
```

Evidence: `base→base2→scored→scored2→scored4→keyed` all exactly 987,529 rows (loop at table
level). `casebible-pg → casebible-db → casebible-pg18` (loop at DB level). `manifests/local/` +
`manifests/vps/` (loop at scan level).

**Consolidating LOCATION does not consolidate AUTHORITY.** `cb_load_raw.py` therefore:
- stamps `_src_file` + `_loaded_at` on **every row**
- writes `COMMENT ON SCHEMA` into the DB: *"WRITE-ONCE… SUPERSEDED BY inventory.*… DO NOT READ"*

After collapse is verified: `REVOKE SELECT ON ALL TABLES IN SCHEMA raw_duck FROM cb_agent`.
Enforce it, don't document it — documented rules have already failed here.

---

## 7. FILE MAP

```
E:\AI_Workspace\casebible\
  cb_load_raw.py          READY, NEVER RUN — step 1 of 3
  cb_prove.py             WRITTEN + RUN 2026-08-27 (read-only) — Stage 2; report cb_prove_report_*.md
  cb_consolidate_5432_to_5434.sh  WRITTEN 2026-08-27 — agentos-db casebible → :5434 (Matt runs on ovh-files)
  cb_verify_consolidation.py      WRITTEN 2026-08-27 — count+md5 proof, both sides
  schema_inventory.sql    READY — inventory.item / location / movement
  pilot\cb_pilot.py       READY — F:\case dry run, 4 phases
  casebible.duckdb        1,491 MB, 44 tables — CANONICAL
  casebible_work.sqlite   sort_map (4,878 = only old→new→domain provenance), copy_log
  merge-plan.duckdb       merge_plan 29,188
  iterations_index.duckdb table_defs 1,691 ← Matt's own meta-index of tables-over-time
  raw_sizehash.txt        80 MB, size|md5|relpath, ~900k rows — legacy MD5 corpus
  recovery_by_tree\*.csv  110,745 rows — RESTORE MAP (all recoverable)
  exports\                build_sort_map.sql (PACKAGE-aware sort = atomic units, reference impl)
                          normalized-messages-full.csv (canonical msg schema, UUIDv7)
                          message-core-full.csv (analysis.message + sha_prefix = H2 prototype)
                          labeling-workbook-*.csv (HITL gate, 1,918 msgs, already in platform)
                          _cats_for_dropdown.txt (164 tags, already in reference.behavior_category)
  gdrive\gd_net_rw.json   125,719 files, sha256+md5+sha1
```

**Plugin:** `C:\Users\matts\.claude\local-plugins\plugins\case-bible\`
(`ENVIRONMENT.md` corrected + drift register; `tools/`, `specs/`, `agents/`)

**Platform:** `E:\AI_Workspace\Projects\the-platform-workspace\Agno-MCP-Platform\sql\`
30 migrations + 445 KB baseline. **156 tables across `ai`/`analysis`/`evidence`/`ops`/`public`/
`reference`/`working`.** Schema is BUILT and nearly EMPTY (`evidence.file_node` = 0 rows).
Case Bible has the data; the platform has the shape. **This is a loading problem, not a schema
problem.** Do NOT design new evidence tables — they exist.

**cocoindex code search** (both repos, queryable via sqlite3, skip the `_vec` virtual tables):
`.cocoindex_code\target_sqlite.db` → `code_chunks_vec_auxiliary`
(`value00`=filename, `value01`=chunk text, `value02/03`=line range). 68,806 chunks.

---

## 8. OPEN QUESTIONS FOR MATT

1. `enrichment` 33 cols (DuckDB) vs 32 (PG16) — which column, which is right?
2. Google Drive accounts 2–4 — not yet authorized. OAuth client `drive-479520` exists,
   Desktop-app type, **still in Testing mode → refresh tokens expire in 7 days**. Publish to
   Production for durable tokens (accept the unverified-app warning once).
3. `od` vs `od1` — believed same account, unverified.
4. B2 as second cloud — confirm, then Object Lock (Governance + Legal Hold).
5. `casebible-pg18` is registered in Coolify as BOTH a service and a database. Check for a
   third `casebible*` volume before removing the exited service record.

---

## 9. ATOMIC GROUPING / TAKEOUT PROVENANCE RECEIPT — 2026-09-12

> _Byline: Codex · GPT-5 · 2026-09-12._

### Current location and product boundary

- The old `E:\AI_Workspace\casebible` route no longer exists. The live repository is
  `E:\AI_Workspace\Projects\Propria\Consignatio`; this legacy corpus lane is its
  `casebible\` subdirectory.
- Intake is the fully interactive, integrated human-and-AI chat/explorer workspace for the
  Case Bible organization system. The catalog/grouping SQL may continue in this adjacent legacy
  corpus lane; Intake can later present and operate on the review state without becoming a second
  source of truth.

### Owner-approved atomic-boundary classifications

1. Individually named Facebook export directories are atomic package candidates even when
   `start_here.html` or `index.html` is absent.
2. Messy Facebook parent directories (`FB DATA`, `FB Exports`, `Katrina FB Data`, `Facebook Data`,
   bare `facebook`, timestamped `meta-*`, and loose `messages (N)` trees) are
   **controlled-consolidation containers**. Protect the parent boundary while cleaning,
   reconstructing and deduplicating its contents; do not migrate the entire internal duplication
   unchanged.
3. Individually named Takeout directories (numbered, copied, timestamped and account-style names)
   are atomic package candidates.
4. Takeout collection parents (`Takeout Data`, `Takeout Data1`, `Google Takeout`,
   `google_takeout`, `Google Takeout Files`, including malformed names) are
   **controlled-consolidation containers**, not final canonical copies.
5. `facebookuser_<id>`, `facebook_payments`, `facebook_accounts_center`,
   `apps_and_websites_off_of_facebook`, and `FB_IMG_*` are ordinary members when contained by an
   approved Facebook unit. If found outside any approved unit, flag them as
   `orphaned_export_fragment` for owner investigation; do not promote them automatically.
6. Individual Facebook message threads are not migrated by default. Only the approximately twelve
   conversations later selected by the owner become standalone migration candidates.

### Takeout account and reconstruction rules

- Owner-supplied subject-account handles, kept distinct exactly as written:
  `matt.salemnet`, `matt.salem85`, `caminstaller`, `salemnma`, `katrina95xo`,
  `katrinasalem95`, plus explicit unknown/additional-account states.
- `matt.salemnet` is the largest known partition and one of the two most important evidence
  accounts. It is stored with `evidence_priority=critical`. The other top-two account is not yet
  identified; do not infer it.
- Do not confuse the storage-provider account with the subject account inside a Takeout.
- Folder names are hints only. Extracted Takeout identity should be supported by internal identity
  artifacts or content such as Google Account profile/subscriber/change-history records, repeated
  account-named files, Calendar/contact artifacts, or corroborating internal values.
- Model Takeout as: subject account -> export event -> original archive set -> archive part ->
  extracted/recombined trees. Do not merge accounts, export timestamps, archive batches or part
  numbers merely because names or contents overlap.
- Recovery is union-preserving: select a verified-good base tree, supplement genuinely missing
  members from other recovered copies, and retain per-member source provenance. Never let a
  zero-byte, truncated or corrupt recovery copy become canonical.
- Archive-to-extracted-tree relationships remain `possible_extraction_of` until hashes, manifests,
  or strong member comparisons prove them.

### Read-only archive census

| Store | ZIP/TGZ archives | In Takeout context | Takeout-named | Standard multipart names |
|---|---:|---:|---:|---:|
| Google Drive | 957 | 617 | 612 | 375 |
| OneDrive | 2,079 | 778 | 533 | 63 |
| R2 | 7,963 | 779 | 547 | 94 |

Observed standard multipart names reach at least part `678`. Many timestamp/batch series are
gapped or begin above part `001`; observed maxima are not proof of expected totals. Preserve each
part independently until completeness is established.

### Account-hint observations (paths, not export counts)

- `matt.salemnet`: R2 63,291 path hits / 46 archive hits; OneDrive 82,967 / 46; GDrive 476 / 0.
- `caminstaller`: R2 349; OneDrive 207; GDrive 115.
- `salemnma`: R2 13; OneDrive 310; GDrive 139.
- `katrina95xo`: R2 31; OneDrive 39; GDrive 6.
- `katrinasalem95`: R2 183; OneDrive 316; GDrive 33.
- `matt.salem85`: no path-name hit. It remains a known account awaiting internal-content evidence.

These counts are observations from manifest paths and can be heavily duplicated. They do not
assign an export to an account.

### Applied PostgreSQL schema

`schema_atomic_units.sql` was applied transactionally to Case Bible PG18 `:5434`. It now includes:

- `inventory.atomic_path_index`
- `inventory.atomic_detection_run`
- `inventory.atomic_unit_candidate`
- `inventory.atomic_copy`, `inventory.atomic_member`, `inventory.atomic_group`
- `inventory.takeout_subject_account`
- `inventory.atomic_identity_evidence`
- `inventory.takeout_archive_part`
- `inventory.atomic_candidate_relation`

The six supplied account handles were inserted. `matt.salemnet` is verified present as critical;
the mistaken `ma.salemnet` value was corrected before schema application and was never inserted.

### Execution state — exact boundary

- Two monolithic `atomic-boundary-v2` detection attempts were cancelled after approximately
  sixteen minutes each because their containment/account-evidence scans were operationally too
  expensive. Both ran inside single transactions and rolled back completely.
- Verified live after cancellation: `atomic_detection_run=0`, `atomic_unit_candidate=0`,
  `takeout_archive_part=0`, and `atomic_identity_evidence=0`. There is no partial detection result.
- The durable normalized path index was then started provider-by-provider:
  - R2 committed: **592,822 indexed path/metadata variants** representing 592,822 source rows.
  - Google Drive committed: **46,837 variants** representing 46,839 source rows.
  - OneDrive was still running when the owner directed the agent to record findings only. The
    exact PostgreSQL backend was cancelled; that OneDrive statement rolled back.
- `stage_atomic_paths.sql` is idempotent. It preserves same-path/different-size-or-hash variants and
  counts duplicate OneDrive scan rows rather than silently discarding their provenance.
- `detect_atomic_units_v2.sql` contains the approved rules but should **not be rerun monolithically**.
  Refactor it into store/rule-scoped phases that consume `inventory.atomic_path_index`, each with a
  timed receipt and independent transaction.
- No source object was opened, copied, moved or deleted. No canonical copy was selected. B2 remains
  untouched and no B2 transfer plan was created.
