#!/usr/bin/env python3
"""
cb_manifest.py — Phase 1+2 for the Case Bible raw-ingest orchestrator.

Zero-download / zero-cost:
  Phase 1: fast-ingest r2:casebible-{raw,quarantine,sorted} into the catalog via
           `rclone ls` (flat LIST, ~1100 rows/sec; no --hash, no download).
  Phase 2: for each local source, list via `rclone ls` (filesystem metadata only,
           no hydration) or `rclone ls od:...` (OneDrive API, no hydration), then
           match by (name, size) against the catalog -> per-source new-to-add.

Dedup signal is name+size (no content hash) — a conservative estimator for the
GO/NO-GO manifest. True content-hash dedup (good-copy rule) is deferred to Phase 4.

Byline: Claude Code · GLM-5.2 · 2026-08-02
"""
import os, re, sys, csv, subprocess, sqlite3
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DB = os.environ.get("CBCAT_DB", "E:/AI_Workspace/casebible/casebible.duckdb")
RC_TIMEOUT = int(os.environ.get("CB_RC_TIMEOUT", "1800"))  # 30 min per rclone ls

R2_BUCKETS = ["casebible-raw", "casebible-quarantine", "casebible-sorted"]

# (label, rclone source spec, proposed raw prefix, transfer path, notes)
SOURCES = [
    ("D:\\Backup",                                 "D:/Backup",                                 "_backup_import/",         "devbox rclone -> R2",      "largest; D: read-only source"),
    ("C:\\Users\\matts\\OneDrive\\Case Bible",      "od:Case Bible",                             "_onedrive/case_bible/",   "VPS-side rclone (bypass devbox)", "BLOCKER: od: not on VPS yet; zero hydration via od: API"),
    ("F:\\Disk Drill",                              "F:/Disk Drill",                             "_diskdrill/",             "devbox rclone -> R2",      ""),
    ("D:\\google",                                  "D:/google",                                 "_google/",                "devbox rclone -> R2",      ""),
    ("D:\\fb",                                      "D:/fb",                                     "_fb/",                    "devbox rclone -> R2",      ""),
    ("D:\\context - Copy",                          "D:/context - Copy",                         "_d_context_copy/",        "devbox rclone -> R2",      ""),
    ("D:\\snap",                                    "D:/snap",                                   "_snap/",                  "devbox rclone -> R2",      ""),
    ("E:\\backup",                                  "E:/backup",                                 "_e_backup/",              "devbox rclone -> R2",      "byte-identical to J:\\Disk Drill (dup)"),
    ("J:\\Disk Drill",                              "J:/Disk Drill",                             "_j_diskdrill/",           "devbox rclone -> R2",      "byte-identical to E:\\backup (dup)"),
    ("J:\\docs",                                    "J:/docs",                                   "_j_docs/",                "devbox rclone -> R2",      ""),
    ("J:\\Evidence",                                "J:/Evidence",                               "_j_evidence/",            "devbox rclone -> R2",      ""),
    ("J:\\00_Documentation",                        "J:/00_Documentation",                       "_j_doc_00/",              "devbox rclone -> R2",      ""),
    ("J:\\03_Evidence_Analysis",                    "J:/03_Evidence_Analysis",                   "_j_evi_03/",              "devbox rclone -> R2",      ""),
    ("J:\\Case Bible BACKUP 2026-03-12",            "J:/Case Bible BACKUP 2026-03-12",           "_j_cb_backup_2026-03-12/","devbox rclone -> R2",      ""),
    ("J:\\Legal_Knowledge_Base_Obsidian",           "J:/Legal_Knowledge_Base_Obsidian",          "_j_lkb/",                 "devbox rclone -> R2",      ""),
]
# Excluded by owner decision: D:\casebible (byte-identical to E:\AI_Workspace\casebible scratch = working state),
#   J:\heic (empty), C:\Users\matts\.casebible, C:\Users\matts\casebible-recovery, E:\AI_Workspace\casebible (scratch).

CLASS_A_PER_M = 4.50  # R2 $/million Class-A ops; free tier 1M/month
FREE_TIER = 1_000_000

def run_rclone_ls(spec):
    """Stream `rclone ls <spec>`, yield (size:int, path:str). Zero-download for r2:; metadata-only for local/od:."""
    proc = subprocess.run(["rclone", "ls", spec], capture_output=True, text=True, timeout=RC_TIMEOUT)
    if proc.returncode != 0:
        sys.stderr.write(f"[WARN] rclone ls {spec} rc={proc.returncode}: {proc.stderr[-300:]}\n")
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        try:
            size = int(parts[0])
        except ValueError:
            continue
        yield size, parts[1]

def basename(p):
    return re.split(r"[\\/]", p)[-1]

def ext_of(p):
    m = re.search(r"\.([^./\\]+)$", p)
    return m.group(1).lower() if m else ""

def tier_of(p):
    return p.split("/", 1)[0] if "/" in p else ""

# ---- Phase 1: ingest R2 buckets ----
import duckdb
con = duckdb.connect(DB)
con.execute("""CREATE OR REPLACE TABLE r2_files (
  bucket VARCHAR, path VARCHAR, name VARCHAR, ext VARCHAR,
  size BIGINT, md5 VARCHAR, modtime TIMESTAMP, mimetype VARCHAR, tier VARCHAR)""")

print("=== PHASE 1: R2 fast-ingest (rclone ls, zero-download) ===", flush=True)
for b in R2_BUCKETS:
    n = 0; bytes_ = 0; zb = 0
    rows = []
    for size, path in run_rclone_ls(f"r2:{b}"):
        rows.append((b, path, basename(path), ext_of(path), size, None, None, None, tier_of(path)))
        n += 1; bytes_ += size
        if size == 0: zb += 1
        if len(rows) >= 20000:
            con.executemany("INSERT INTO r2_files VALUES (?,?,?,?,?,?,?,?,?)", rows); rows.clear()
    if rows:
        con.executemany("INSERT INTO r2_files VALUES (?,?,?,?,?,?,?,?,?)", rows)
    print(f"  {b}: {n} files, {bytes_/1e9:.2f} GB, zero_byte={zb}", flush=True)

print("\n=== catalog stats after ingest ===", flush=True)
for r in con.execute("SELECT bucket, count(*), round(sum(size)/1e9,2), count(*) FILTER(WHERE size=0) FROM r2_files GROUP BY bucket ORDER BY bucket").fetchall():
    print(f"  {r[0]}: {r[1]} files, {r[2]} GB, zero_byte={r[3]}", flush=True)

# ---- Phase 2: per-source dedup-aware manifest ----
print("\n=== PHASE 2: per-source dedup-aware manifest (name+size match, zero-download) ===", flush=True)
hdr = f"{'source':<48} {'prefix':<28} {'transfer':<32} {'files':>9} {'bytes_GB':>10} {'new':>9} {'new_GB':>9} {'zeroB':>7} {'classA_$':>9}"
print(hdr, flush=True)
print("-" * len(hdr), flush=True)

manifest_rows = []
for label, spec, prefix, transfer, notes in SOURCES:
    n = 0; bytes_ = 0; zb = 0; new_n = 0; new_b = 0
    cand_rows = []
    for size, path in run_rclone_ls(spec):
        cand_rows.append((path, basename(path), size))
        n += 1; bytes_ += size
        if size == 0: zb += 1
    if cand_rows:
        con.execute("DROP TABLE IF EXISTS cand; CREATE TEMP TABLE cand(path VARCHAR, name VARCHAR, size BIGINT)")
        con.executemany("INSERT INTO cand VALUES (?,?,?)", cand_rows)
        # match: in_corpus if any r2_files row has same (name, size)
        res = con.execute("""
          WITH m AS (
            SELECT c.size, EXISTS(SELECT 1 FROM r2_files r WHERE r.name=c.name AND r.size=c.size) AS inc
            FROM cand c)
          SELECT count(*), coalesce(sum(size),0),
                 count(*) FILTER(WHERE NOT inc), coalesce(sum(size) FILTER(WHERE NOT inc),0)
          FROM m""").fetchone()
        n_match = res[0]; bytes_match = res[1]; new_n = res[2]; new_b = res[3]
    new_gb = new_b / 1e9
    # Class-A $ for the NEW uploads only (1 PUT per new file). Conservative: free tier shared across run.
    class_a_ = (new_n / 1_000_000) * CLASS_A_PER_M
    print(f"{label[:48]:<48} {prefix:<28} {transfer[:32]:<32} {n:>9} {bytes_/1e9:>10.2f} {new_n:>9} {new_gb:>9.2f} {zb:>7} {class_a_:>9.2f}", flush=True)
    manifest_rows.append({
        "source": label, "spec": spec, "prefix": prefix, "transfer": transfer, "notes": notes,
        "files": n, "bytes": bytes_, "new_to_add": new_n, "new_bytes": new_b,
        "zero_byte": zb, "class_a_usd": round(class_a_, 4),
    })
    if notes:
        print(f"    NOTE: {notes}", flush=True)

# ---- summary ----
tot_files = sum(r["files"] for r in manifest_rows)
tot_bytes = sum(r["bytes"] for r in manifest_rows)
tot_new = sum(r["new_to_add"] for r in manifest_rows)
tot_new_b = sum(r["new_bytes"] for r in manifest_rows)
tot_zb = sum(r["zero_byte"] for r in manifest_rows)
print("-" * len(hdr), flush=True)
print(f"{'TOTAL (local sources)':<48} {'':<28} {'':<32} {tot_files:>9} {tot_bytes/1e9:>10.2f} {tot_new:>9} {tot_new_b/1e9:>9.2f} {tot_zb:>7} {(tot_new/1e6)*CLASS_A_PER_M:>9.2f}", flush=True)
print(f"\nFree-tier note: first 1M Class-A ops/month free; ${CLASS_A_PER_M}/M thereafter. Totals above assume no free tier remaining (conservative).", flush=True)
print(f"Zero-byte files (bad_zero_byte, Addendum 4): {tot_zb} across sources — to be flagged/skipped at ingest, never canonical.", flush=True)

# write manifest CSV (tool input for the eventual ingestion, NOT a report)
out_csv = "E:/AI_Workspace/casebible/ingest_manifest.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
    w.writeheader(); w.writerows(manifest_rows)
print(f"\nManifest CSV: {out_csv}", flush=True)
con.close()