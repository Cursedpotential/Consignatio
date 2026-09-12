# Guarded local/OneDrive → R2 `casebible-raw` sync — PLAN + DRY-RUN harness

> _Byline: Claude Code (🟦 SORT lane) · Opus 4.8 · 2026-07-01_ · **LOCAL ONLY**
> Pickup: BOARD 2026-07-01 RESUME — SORT owns "the guarded local-drives + OneDrive Case Bible → raw
> sync (DRY-RUN + junk exclude-list + md5 dedup-skip vs `D:\casebible\casebible.duckdb` + NEVER modify
> `D:\Backup`)."

## Goal
Pull any **new** content that lives on the local drives / OneDrive "Case Bible" but is **not yet in
R2 `casebible-raw`** up into `casebible-raw`, WITHOUT: re-uploading dupes, uploading software junk,
or ever mutating a source (esp. `D:\Backup`). Direction is one-way **local → raw**. Enrichment and the
raw→sorted type-first re-bucket then proceed as already built.

## The five guards (owner mandate)
| # | Guard | How it is enforced |
|---|---|---|
| 1 | **DRY-RUN first** | `cb_guarded_sync_dryrun.py` only *classifies*; it produces the exact ledger the transfer would consume. No `rclone copy` is emitted until owner sign-off. |
| 2 | **junk exclude-list** | Path/name patterns from the 2026-06-29 owner-approved software-junk rule: `node_modules/ site-packages/ __pycache__/ venv*/ .venv/ flet_env/ *.dist-info *.egg-info *.pyc/.pyo/.whl/.dll/.so`, the whole `text-generation-webui` install, `$RECYCLE.BIN`, `.tmp.driveupload/`. Marked `EXCLUDED`, never uploaded. |
| 3 | **md5 dedup-skip** | Each source file's md5 is checked against the R2 snapshot `casebible.duckdb → r2_files.md5` (277,417 distinct md5 over 590,560 objects). Hit ⇒ `DUP`, skipped. |
| 4 | **NEVER modify `D:\Backup`** | The harness opens every file `'rb'` only — it has **no** write/move/delete code path to any source. `D:\Backup` is scanned as a read-only *source* for NEW content; it is physically never written. (Also: the ledger refuses to write itself inside any source root.) |
| 5 | **CLOUD-PLACEHOLDER skip** (cost-aware, added 2026-07-01) | OneDrive Files-On-Demand online-only files are detected via Windows `st_file_attributes` (bits `OFFLINE 0x1000 \| RECALL_ON_OPEN 0x40000 \| RECALL_ON_DATA_ACCESS 0x400000`) — a **metadata-only** `os.stat`, no `open()` — and marked `DEFERRED_CLOUD` *without hashing*. Opening a placeholder would trigger OneDrive **hydration** (a bandwidth/billable re-pull the owner's cost-aware HARD RULE forbids doing blindly). `--hydrate-cloud` deliberately opts in to a full-content run. **This makes a full OneDrive dry-run safe to run unattended** — it can no longer accidentally re-pull the cloud. |

## Sources (read-only)
- `C:\Users\matts\OneDrive\Case Bible` — **178,499 files** (canonical working source; still read/write for
  the owner, but this sync only READS). **Real breakdown (metadata-only attribute scan, 2026-07-01, 28.5 s, $0):**
  **176,639 hydrated/local (150.94 GB)** + **1,860 cloud-only placeholders** (0 stat errors). The 1,860
  placeholders cluster in one Facebook-export photos/gifs dir. Guard 5 now classifies those 1,860 as
  `DEFERRED_CLOUD` **without** hydrating them, so a full dry-run reads only the 150.94 GB of already-local
  content (local disk I/O, $0 — no bandwidth). A deliberate `--hydrate-cloud` run is the only path that
  would download the 1,860 placeholders.
- `D:\Backup` — **READ-ONLY** source (never modified). Bounded 400-file smoke sample: **222 DUP / 178
  NEW / 51 DEFERRED_LARGE** → confirms much of Backup is already in raw; the dedup-skip is doing real work.
- Other local drives (`D:\`, `E:\` work areas) — **excluded by default** except explicit `--root`s the
  owner names, to avoid sweeping in the whole workspace / OS. **Do NOT** point a root at `D:\casebible`
  scaffold, `E:\AI_Workspace` repo, or any venv/build tree.

## Ledger statuses
`NEW` (candidate upload — the gated set) · `DUP` (md5 in R2, skip) · `EXCLUDED` (junk) ·
`READ_ERROR` (unreadable / un-hydrated placeholder) · `DEFERRED_LARGE` (over `--max-bytes`, not hashed
in this pass).

## Harness — `specs/cb_guarded_sync_dryrun.py` (read-only, VERIFIED 2026-07-01)
```
python cb_guarded_sync_dryrun.py --root "<dir>" [--root ...] \
       --duckdb "D:\casebible\casebible.duckdb" --out "<ledger.csv>" [--limit N] [--max-bytes N]
```
Verified 2026-07-01 pass 1 (output → `specs/guarded-sync-DRYRUN-smoketest.csv`):
- status/ sample: 4 NEW (correctly not-in-R2), R2 md5 set loaded = 277,417.
- `D:\Backup` bounded sample (limit 400, max-bytes 5 MB): NEW=178 · DUP=222 · DEFERRED_LARGE=51 ·
  READ_ERROR=0 · EXCLUDED=0. Ran in 9.5 s, `D:\Backup` untouched.

Verified 2026-07-01 pass 2 — **Guard 5 (cloud-placeholder skip)** (output →
`specs/guarded-sync-DRYRUN-cloudguard-smoketest.csv`): ran over the OneDrive FB-export inbox dir that holds
all 1,860 placeholders (+ its local files): **DUP=8,011 · DEFERRED_CLOUD=1,860 · NEW=0 · READ_ERROR=0 ·
EXCLUDED=0**, 98.5 s. `DEFERRED_CLOUD=1,860` exactly matches the pre-scan placeholder count ⇒ every
placeholder was detected and **skipped without opening** (no hydration). C: free-space delta over the run =
~33 MB = ambient OS noise (had the 1,860 hydrated, it would be far larger and `DEFERRED_CLOUD` would be 0).
DUP=8,011 also confirms this FB export is already fully in R2.

## Next reversible/local steps (no transfer)
1. Owner confirms the source root list (esp. whether `D:\Backup` + which OneDrive subtrees are in scope).
   **Hydration policy is now DECIDED by default:** Guard 5 skips online-only placeholders (no re-pull);
   a full-content run of those 1,860 is opt-in only (`--hydrate-cloud`). Remaining owner input = root scope + routing.
2. **Full DRY-RUN over OneDrive Case Bible is now safe to run unattended** ($0, local-only, ~150.94 GB of
   hashing, no bandwidth) → the complete `NEW` ledger with a real object-count + GB total. (Heavy/long but
   reversible; can run in background. Not fired this pass — queued as the next reversible step.)
3. Rescue/second-look pass on `EXCLUDED` (the junk classifier over-flags — proven twice; a different-LLM /
   human check before anything is dropped, mirroring the 2-LLM quarantine rule).

## GATED (queue to APPROVALS — do NOT run unattended)
- The actual **`rclone copy` of the `NEW` set → `r2:casebible-raw`** (billable Class-A puts; runs on
  **OVH-2** via Tailscale, remote `r2`, `/opt/casebible/rclone.conf` — the dev box can't reach R2). Must be
  preceded by the full dry-run's exact object-count + GB total for owner sign-off (cost-aware rule).
- Any OneDrive **mass hydration** (bandwidth cost) if a full-content hash of cloud-only files is required.
