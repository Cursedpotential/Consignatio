#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
cb_guarded_sync_dryrun.py  —  SORT lane guarded local/OneDrive -> R2 casebible-raw sync (DRY-RUN ONLY)
> Byline: Claude Code (SORT lane) · Opus 4.8 · 2026-07-01

WHAT THIS IS
  A READ-ONLY dry-run planner for the guarded sync of local drives + OneDrive "Case Bible"
  into R2 `casebible-raw`. It NEVER copies, moves, deletes, or writes to any source, and it
  NEVER touches R2. It only READS files to hash them and WRITES one dry-run ledger CSV to an
  owner-visible path. The actual upload is a GATED cloud transfer (owner sign-off + run on OVH-2
  rclone), never fired from here.

FIVE GUARDS (owner mandate, BOARD 2026-07-01)
  1. DRY-RUN            — this script only classifies; it produces the ledger the transfer would use.
  2. junk exclude-list  — path/name patterns that are software junk are marked EXCLUDED, never uploaded.
  3. md5 dedup-skip     — any file whose md5 already exists in the R2 snapshot (casebible.duckdb ->
                          r2_files.md5) is marked DUP and skipped (already in casebible-raw).
  4. NEVER modify D:\Backup — D:\Backup is a READ-ONLY source. This script opens files 'rb' only;
                          it has no write/move/delete path to any source at all. D:\Backup is scanned
                          for NEW-content candidates but is physically never written.
  5. CLOUD-PLACEHOLDER skip (cost-aware, added 2026-07-01) — OneDrive Files-On-Demand online-only files
                          are DETECTED via Windows file attributes (st_file_attributes; no open/read) and
                          marked DEFERRED_CLOUD *without hashing*. This prevents opening them, which would
                          trigger OneDrive HYDRATION (a billable / bandwidth re-pull the owner's cost-aware
                          rule forbids doing blindly). Use --hydrate-cloud to deliberately opt in (a full
                          content run that WILL download placeholders).

STATUS values in the ledger
  NEW            — not junk, md5 not in R2 -> candidate to upload (this is the gated transfer set).
  DUP            — md5 already in R2 snapshot -> skip.
  EXCLUDED       — matched the junk exclude-list -> never upload.
  DEFERRED_LARGE — over --max-bytes, not hashed this pass.
  DEFERRED_CLOUD — OneDrive online-only placeholder, not hydrated/hashed (unless --hydrate-cloud).
  READ_ERROR     — could not read/hash (permission, corrupt, etc.).

USAGE (all read-only)
  python cb_guarded_sync_dryrun.py --root "<dir>" [--root "<dir2>" ...] \
         --duckdb "D:\\casebible\\casebible.duckdb" \
         --out    "<ledger.csv>" [--limit N] [--max-bytes N] [--hydrate-cloud]
  --limit N        stop after N files (sampling / smoke test)
  --max-bytes N    skip hashing files larger than N bytes (avoid huge reads in a smoke run;
                   such files are recorded status=DEFERRED_LARGE, not hashed)
  --hydrate-cloud  OPT-IN: also hash OneDrive online-only placeholders (this DOWNLOADS them —
                   bandwidth cost). Default OFF: placeholders are DEFERRED_CLOUD, never hydrated.
"""
import argparse, csv, hashlib, os, re, subprocess, sys, time

# --- OneDrive / Files-On-Demand placeholder attribute bits (Windows st_file_attributes) ---
# FILE_ATTRIBUTE_OFFLINE=0x1000, RECALL_ON_OPEN=0x40000, RECALL_ON_DATA_ACCESS=0x400000.
# Reading any of these via os.stat is metadata-only and does NOT hydrate; opening the file DATA does.
CLOUD_ATTR_MASK = 0x1000 | 0x40000 | 0x400000

# --- junk exclude-list (mirrors the 2026-06-29 owner-approved software-junk delete rule) ---
EXCLUDE_DIR_PARTS = {
    "node_modules", "site-packages", "__pycache__", ".venv", "venv", "venv313",
    "flet_env", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "$recycle.bin",
    ".tmp.driveupload", ".tmp.drivedownload",
}
EXCLUDE_DIR_REGEX = [
    re.compile(r"(^|.*[\\/])venv[^\\/]*$", re.I),
    re.compile(r".*\.dist-info$", re.I),
    re.compile(r".*\.egg-info$", re.I),
]
EXCLUDE_EXT = {".pyc", ".pyo", ".whl", ".dll", ".so", ".pdb", ".lib", ".obj"}
# whole-subtree junk (the text-generation-webui ML install family etc.)
EXCLUDE_PATH_SUBSTR = ["text-generation-webui"]

def is_excluded(path):
    low = path.lower()
    parts = re.split(r"[\\/]+", low)
    for p in parts:
        if p in EXCLUDE_DIR_PARTS:
            return True, f"dir:{p}"
        for rx in EXCLUDE_DIR_REGEX:
            if rx.match(p):
                return True, f"dirrx:{p}"
    _, ext = os.path.splitext(low)
    if ext in EXCLUDE_EXT:
        return True, f"ext:{ext}"
    for sub in EXCLUDE_PATH_SUBSTR:
        if sub in low:
            return True, f"subtree:{sub}"
    return False, ""

def load_r2_md5(duckdb_path):
    """Read the DISTINCT md5 set from casebible.duckdb -> r2_files via the duckdb CLI (read-only)."""
    cmd = ["duckdb", duckdb_path, "-noheader", "-list",
           "-c", "SELECT DISTINCT md5 FROM r2_files WHERE md5 IS NOT NULL;"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if out.returncode != 0:
        raise RuntimeError(f"duckdb md5 export failed: {out.stderr[:400]}")
    s = {ln.strip() for ln in out.stdout.splitlines() if ln.strip()}
    return s

def md5_of(path, bufsize=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:               # 'rb' ONLY — never opened for write
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--duckdb", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-bytes", type=int, default=0)
    ap.add_argument("--hydrate-cloud", action="store_true",
                    help="OPT-IN: hash OneDrive online-only placeholders (downloads them). Default: skip.")
    a = ap.parse_args()

    # HARD GUARD: refuse to write the ledger anywhere under a source root (no source mutation ever).
    out_abs = os.path.abspath(a.out)
    for r in a.root:
        if out_abs.lower().startswith(os.path.abspath(r).lower() + os.sep):
            print(f"REFUSING: --out {out_abs} is inside source root {r}", file=sys.stderr)
            return 2

    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] loading R2 md5 snapshot from {a.duckdb} ...")
    r2 = load_r2_md5(a.duckdb)
    print(f"  R2 snapshot distinct md5 = {len(r2):,}")

    counts = {"NEW": 0, "DUP": 0, "EXCLUDED": 0, "DEFERRED_LARGE": 0,
              "DEFERRED_CLOUD": 0, "READ_ERROR": 0}
    new_bytes = 0
    n = 0
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["status", "reason", "bytes", "md5", "source_root", "path"])
        for root in a.root:
            for dirpath, dirnames, filenames in os.walk(root):
                # prune excluded dirs in-place so we don't descend into junk
                keep = []
                for d in dirnames:
                    ex, _ = is_excluded(os.path.join(dirpath, d) + os.sep)
                    if not ex:
                        keep.append(d)
                dirnames[:] = keep
                for fn in filenames:
                    fp = os.path.join(dirpath, fn)
                    ex, why = is_excluded(fp)
                    if ex:
                        counts["EXCLUDED"] += 1
                        w.writerow(["EXCLUDED", why, "", "", root, fp])
                        continue
                    try:
                        st = os.stat(fp, follow_symlinks=False)   # metadata only — does NOT hydrate
                        sz = st.st_size
                    except OSError as e:
                        counts["READ_ERROR"] += 1
                        w.writerow(["READ_ERROR", f"stat:{e.__class__.__name__}", "", "", root, fp])
                        continue
                    # GUARD 5: OneDrive online-only placeholder -> DEFERRED_CLOUD, never hydrate (unless opted-in)
                    if (not a.hydrate_cloud) and (getattr(st, "st_file_attributes", 0) & CLOUD_ATTR_MASK):
                        counts["DEFERRED_CLOUD"] += 1
                        w.writerow(["DEFERRED_CLOUD", "onedrive-online-only", sz, "", root, fp])
                        continue
                    if a.max_bytes and sz > a.max_bytes:
                        counts["DEFERRED_LARGE"] += 1
                        w.writerow(["DEFERRED_LARGE", f">{a.max_bytes}", sz, "", root, fp])
                        continue
                    try:
                        m = md5_of(fp)
                    except OSError as e:
                        counts["READ_ERROR"] += 1
                        w.writerow(["READ_ERROR", f"read:{e.__class__.__name__}", sz, "", root, fp])
                        continue
                    if m in r2:
                        counts["DUP"] += 1
                        w.writerow(["DUP", "md5-in-r2", sz, m, root, fp])
                    else:
                        counts["NEW"] += 1
                        new_bytes += sz
                        w.writerow(["NEW", "not-in-r2", sz, m, root, fp])
                    n += 1
                    if a.limit and n >= a.limit:
                        break
                if a.limit and n >= a.limit:
                    break
            if a.limit and n >= a.limit:
                break

    dt = time.time() - t0
    print(f"[{time.strftime('%H:%M:%S')}] DRY-RUN complete in {dt:.1f}s. Ledger -> {a.out}")
    print("  " + " | ".join(f"{k}={v:,}" for k, v in counts.items()))
    print(f"  NEW candidate upload bytes = {new_bytes:,} (~{new_bytes/1e9:.3f} GB) -- GATED transfer, NOT run here")

if __name__ == "__main__":
    sys.exit(main())
