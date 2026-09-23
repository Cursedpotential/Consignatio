#!/usr/bin/env python3
# Byline: Claude Code · Opus 5 · 2026-09-13
"""Read-only: which eligible migration survivors are already on B2, and what is still missing.

Inputs:
  - a fresh `rclone lsf -R` listing of b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets (key, size)
  - local casebible.duckdb `final_survivors` (eligible = integrity_status IS NULL and md5 present)
  - local casebible.duckdb `r2_files`, for the owner's R2 quarantine/onedrive folder subset
A survivor counts as present when its expected B2 key (source-buckets/<bucket>/<path>) exists with the same size.
Content-level presence for the owner's folder subset: some eligible survivor with the same (md5, size) is present.

Writes a summary plus a TSV of missing survivors next to the listing. Changes nothing in B2, R2 or the catalogs.
"""
import csv
import datetime as dt
import os
import subprocess
import sys

import duckdb

RCLONE = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"
CONFIG = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
B2_ROOT = "b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets"
DUCKDB = "E:/AI_Workspace/Projects/Propria/Consignatio/casebible/casebible.duckdb"
# Receipts moved into the repo 2026-09-15; was E:/AI_Workspace/_receipts/corruption-hunt/b2-presence
OUT_DIR = "E:/AI_Workspace/Projects/Propria/Consignatio/docs/receipts/corruption-hunt/b2-presence"
OWNER_QUARANTINE_FOLDERS = ["onedrive/Case Bible/", "onedrive/Case Bible BACKUP 2026-03-12/", "onedrive/no sync/", "onedrive/archive/"]


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    listing = os.path.join(OUT_DIR, f"{stamp}-b2-source-buckets-listing.tsv")
    cmd = [RCLONE, "lsf", B2_ROOT, "-R", "--files-only", "--format", "ps", "--separator", "\t",
           "--b2-encoding", "None", "--fast-list", "--config", CONFIG]
    with open(listing, "w", encoding="utf-8", newline="\n") as fh:
        proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    if proc.returncode != 0:
        print(f"ABORT: B2 listing failed: {proc.stderr.strip()[:300]}", file=sys.stderr)
        return 2

    con = duckdb.connect(DUCKDB, read_only=True)
    con.execute(f"""create temp table b2 as
        select column0 as key, try_cast(column1 as bigint) as size
        from read_csv('{listing}', delim=chr(9), header=false, quote='', all_varchar=true)""")
    con.execute("""create temp table surv as
        select bucket, path, size, md5, bucket || '/' || path as key
        from final_survivors where integrity_status is null and coalesce(md5, '') <> ''""")
    con.execute("create temp table present as select s.* from surv s join b2 on b2.key = s.key and b2.size = s.size")

    def one(sql, params=None):
        return con.execute(sql, params or []).fetchone()

    lines = [f"checked_at={dt.datetime.now().astimezone().isoformat()}",
             f"b2_objects_listed={one('select count(*) from b2')[0]}"]
    lines.append("bucket | eligible_survivors | present_on_b2 | missing | missing_GB")
    for bucket, total, present, missing_gb in con.execute("""
            select s.bucket, count(*), count(p.key), round(sum(case when p.key is null then s.size else 0 end) / 1e9, 1)
            from surv s left join present p on p.key = s.key group by s.bucket order by s.bucket""").fetchall():
        lines.append(f"{bucket} | {total} | {present} | {total - present} | {missing_gb}")
    lines.append(f"b2 objects not matching any eligible survivor key+size: "
                 f"{one('select count(*) from b2 where key not in (select key from present)')[0]}")

    lines.append("owner R2 quarantine folder | files | distinct_eligible_contents | contents_present_on_b2 | contents_missing | missing_GB")
    for folder in OWNER_QUARANTINE_FOLDERS:
        row = one("""with f as (
                select distinct md5, size from r2_files
                where bucket = 'casebible-quarantine' and starts_with(path, ?) and integrity_status is null and coalesce(md5, '') <> ''),
              p as (select distinct md5, size from present)
            select (select count(*) from r2_files where bucket = 'casebible-quarantine' and starts_with(path, ?)),
                   count(*), count(p.md5), count(*) - count(p.md5),
                   round(sum(case when p.md5 is null then f.size else 0 end) / 1e9, 1)
            from f left join p on p.md5 = f.md5 and p.size = f.size""", [folder, folder])
        lines.append(f"{folder} | {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")

    missing_path = os.path.join(OUT_DIR, f"{stamp}-survivors-missing-on-b2.tsv")
    con.execute(f"""copy (select s.bucket, s.path, s.size, s.md5 from surv s left join present p on p.key = s.key
                         where p.key is null order by s.bucket, s.path) to '{missing_path}' (header, delimiter '\t')""")
    lines.append(f"missing_list={missing_path}")
    report = "\n".join(lines)
    print(report)
    with open(os.path.join(OUT_DIR, f"{stamp}-summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(report + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
