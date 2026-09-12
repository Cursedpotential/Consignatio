# Software-junk DELETE — review before execution

> _Byline: Claude Code · Opus 4.8 · 2026-06-29_ · **✅ EXECUTED 2026-06-29 (owner-approved).**
> Result: deleted **98,287 objects / 12.80 GiB freed** from `casebible-raw` (exit 0, 2m20s, via
> OVH-2 rclone `--files-from`). Verified: target subtrees = 0; Evidence (40,955), code source,
> `.obsidian` (3,012), `recup_dir.*` carve pile all intact.
> One-time owner-approved hard delete (exception to no-delete rule), **software junk only**.
> Bucket: **R2 `casebible-raw`** (from local catalog `casebible.duckdb` → `r2_files`).
> Full object list: `raw-software-junk-DELETE-manifest.csv` (98,287 rows, path,bytes).

## Totals
- **98,287 objects · 13.74 GB**
- 100% software artifacts (installs, venvs, deps, caches). **0 evidence/legal/takeout/entities.**
- ~12,800+ of your source files preserved (proof below).

## Directory tree to be deleted (rolled up)

```
casebible-raw/
├── _backup_import/
│   ├── text-generation-webui/        62,647 obj · 12.65 GB   ← whole ML app install (conda, site-packages, .pyc)
│   ├── Claude/  (Claude Extensions)  17,860 obj ·  0.35 GB   ← ONLY node_modules/__pycache__ inside extensions
│   ├── Projects/                      5,484 obj ·  0.37 GB   ← ONLY venv/site-packages/.dll inside your projects
│   ├── Case Bible/                      712 obj ·  0.04 GB   ← ONLY deps inside a Case Bible code copy
│   ├── Documents/                       152 obj ·  0.14 GB   ← ONLY deps/caches
│   └── (misc: applications, stray .pyc)   ~2 obj
├── _system_backup/
│   ├── venv313/                       9,452 obj ·  0.11 GB   ← Python venv
│   └── venv/                          1,327 obj ·  0.01 GB   ← Python venv
├── Archives/
│   └── _TECH_ASSETS/timeline_analyzer/flet_env/   641 obj · 0.07 GB   ← venv inside timeline project
└── General_Code_&_Repos/
    └── new_timeline_processor/ (deps)     9 obj            ← ONLY __pycache__/deps; source kept
```

## What is being deleted (rule)
Software artifacts only, matched by path:
`node_modules/`, `site-packages/`, `__pycache__/`, `.venv/` / `venv*` / `flet_env/`,
`*.dist-info/`, `*.egg-info/`, `*.pyc` / `*.pyo` / `*.whl`, the whole
`_backup_import/text-generation-webui/` install, and `_system_backup/venv*`.

## What is EXPLICITLY SPARED (NOT deleted)
- **All your source code** — every `.py/.js/.ts/.md/.json/.yaml/.sql/.sh/.ipynb` etc. in
  `Projects/`, `Claude/`, `General_Code_&_Repos/`, `Case Bible/`, `new_timeline_processor`,
  the timeline iterations, etc. (KEEP — code backup, per owner.)
- **`.obsidian/`** and vault config (KEEP — it's an Obsidian vault).
- **`recup_dir.*` / `photo_recovery`** — the PhotoRec carve pile (NOT software; separate
  content-classification task, handled later).
- **All Evidence / court / EXHIBIT / Takeout / Legal / Entities / INBOX** content.

## Safety proof (kept source counts, from catalog)
Projects 8,340 · Claude 3,360 · new_timeline_processor 591 · Timeline ETL 58 · Case Bible 50 ·
remembering-conversations 24 · markitdown 7 · … (15 code areas, all source retained).
Evidence-in-junk check = **0**.

## Execution method (staged, NOT yet run)
R2 not reachable from the dev box (public-IPv4 blackhole) → run on **OVH-2** via Tailscale,
using the existing rclone remote `r2` (`/opt/casebible/rclone.conf`). Two clean subtree purges
+ a manifest-driven delete for the scattered dep dirs:

```sh
# whole-install subtrees (safe, fast):
rclone purge  r2:casebible-raw/_backup_import/text-generation-webui
rclone purge  r2:casebible-raw/_system_backup/venv313
rclone purge  r2:casebible-raw/_system_backup/venv
# scattered dep dirs inside kept code → delete by manifest (--files-from):
rclone delete r2:casebible-raw --files-from raw-software-junk-DELETE-manifest.txt
```
Cost: ~98k R2 Class-A delete ops ≈ **$0.44**; frees 13.74 GB. **No deletes until owner signs off.**
