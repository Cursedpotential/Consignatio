# Byline: Claude Code · Opus 5 · 2026-09-13
# Builds the zero-filled hold manifest (hash + size + location) from verified detector outputs. Read-only.
import csv, duckdb, glob, hashlib
OUT = "E:/AI_Workspace/_receipts/corruption-hunt"
con = duckdb.connect("E:/AI_Workspace/Projects/Propria/Consignatio/casebible/casebible.duckdb", read_only=True)
rows = []
for bucket, path, size, md5 in con.execute(f"""select r.bucket, r.path, r.size, r.md5 from r2_files r join
    read_csv('{OUT}/r2_all_zero_files.tsv', delim=chr(9), header=false, quote='', all_varchar=true) z
    on r.bucket = z.column0 and r.path = z.column1 and r.size = try_cast(z.column2 as bigint)""").fetchall():
    rows.append(("r2", bucket, path, size, "md5", md5))
listing = sorted(glob.glob(f"{OUT}/*-b2-salem-data-listing.tsv"))[-1]
b2sha = {}
with open(listing, encoding="utf-8") as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 4: b2sha[p[0]] = p[3].lower()
with open(f"{OUT}/b2_all_zero_objects.tsv", encoding="utf-8") as fh:
    for line in fh:
        k, s = line.rstrip("\n").split("\t"); rows.append(("b2", "salem-data", k, int(s), "sha1", b2sha[k]))
with open(f"{OUT}/gd_salemnet_zero_files.tsv", encoding="utf-8") as fh:
    for line in fh:
        p, s, md5, _ = line.rstrip("\n").split("\t"); rows.append(("gdrive", "gd_salemnet", p, int(s), "md5", md5))
bad = 0
for store, _, _, size, kind, h in rows:  # re-verify every hash is the all-zero hash for its size
    if size <= 64 * 1024 * 1024:
        if getattr(hashlib, kind)(bytes(size)).hexdigest() != h: bad += 1
with open(f"{OUT}/quarantine/zero_filled_hold_manifest.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["store", "container", "path", "size", "hash_kind", "hash", "reason"])
    for r in rows: w.writerow([*r, "all_zero_payload"])
from collections import Counter
print("hold rows", len(rows), Counter(r[0] for r in rows), "distinct (size,hash)", len({(r[3], r[5]) for r in rows}), "re-verify failures (<=64MB)", bad)
print("manifest", f"{OUT}/quarantine/zero_filled_hold_manifest.csv")
