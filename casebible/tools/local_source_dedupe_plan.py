#!/usr/bin/env python3
# Byline: Claude Code · Fable 5 · 2026-09-13 · revised Claude Code · Fable 5.1 · 2026-09-14 (match B2 truth, not r2_files)
"""Dedupe plan for a hashed local source (F:, D:\\Backup) against what is actually on B2.

Inputs:
  - one or more hash inventories (rclone lsjson --hash or local_hash_inventory.py: md5 + sha256 per file)
  - catalog exports pulled from PG casebible (b2_content_catalog.sql), default dir
    Consignatio/docs/receipts/corruption-hunt/catalog-exports-20260914/ (was E:/AI_Workspace/_receipts/… until 2026-09-15):
      b2_content.tsv          md5, size, b2_key   — payloads present on B2
      graded_carriers_keys.tsv md5, size, b2_key  — payloads the graded tranches will place on B2
      b2_objects.tsv          key, size           — fresh B2 listing of source-buckets/
  - the flattened SHA-256 ledger (digest, bucket, key, etag, size) — covers R2 objects whose md5 is
    empty in r2_files (multipart uploads) by mapping digest -> (bucket,key) -> mirrored B2 key

Classification (owner rules 2026-09-13/14: bytes once on B2, hash before transfer, zero-filled never a candidate):
  excluded_zero   0 bytes, or content is all zeros for its size
  on_b2           (md5,size) in b2_content, or sha256 in the ledger with its mirrored key in b2_objects
  pending_carrier (md5,size) in graded_carriers but not yet on B2 (raw/sorted tranche still running) — re-plan later
  new             everything else -> upload set (one carrier per distinct content; other paths recorded)

~~Old rule: known = sha256 in ledger OR (md5,size) in r2_files.~~ Superseded 2026-09-14: matching r2_files
called content "known" that never got a B2 carrier (junk-filtered / non-graded rows) — see URGENT-TODO.

Read-only. Writes <stamp>-<label>-plan.tsv (every file with its class) and <stamp>-<label>-upload.tsv next to the inventories.
"""
import argparse
import datetime as dt
import hashlib
import json
import os

import duckdb

# Receipts moved into the repo 2026-09-15 (owner: "under docs makes sense"); was E:/AI_Workspace/_receipts/corruption-hunt/
RECEIPTS = "E:/AI_Workspace/Projects/Propria/Consignatio/docs/receipts/corruption-hunt"
LEDGER = RECEIPTS + "/hashes/sha_ledger_flat.tsv.gz"
EXPORTS = RECEIPTS + "/catalog-exports-20260914"
B2_PREFIX = "consignatio/intake/raw-dedupe/v1/source-buckets/"


def load_inventory(path: str):
    rows = []
    with open(path, encoding="utf-8") as fh:
        head = fh.read(1)
        fh.seek(0)
        objs = json.load(fh) if head == "[" else (json.loads(l) for l in fh if l.strip())
        for o in objs:
            if "error" in o or o.get("IsDir"):
                continue
            h = o.get("Hashes") or {}
            rows.append((o["Path"], o["Size"], (h.get("md5") or "").lower(), (h.get("sha256") or "").lower(),
                         o.get("ModTime", ""), (o.get("MimeType") or "")))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("label", help="source label, e.g. D_Backup")
    parser.add_argument("inventories", nargs="+", help="hash inventory files (lsjson array or JSONL)")
    parser.add_argument("--root", required=True, help="source root the inventory paths are relative to, e.g. D:/Backup")
    parser.add_argument("--exports", default=EXPORTS, help="catalog export dir (b2_content/graded_carriers_keys/b2_objects TSVs)")
    args = parser.parse_args()

    # later inventories win per path, and a row WITH a hash beats one without (2026-09-14: 191 D:\Backup rows whose
    # md5 was empty in the 09-13 rclone inventory were grouped as "one content per size" and left behind)
    by_path: dict[str, tuple] = {}
    for inv in args.inventories:
        for r in load_inventory(inv):
            prev = by_path.get(r[0])
            if prev is None or (not prev[2] and r[2]) or (r[2] and prev[2]):
                by_path[r[0]] = r
    rows = list(by_path.values())
    print(f"{args.label}: inventory files={len(rows)} (rows without md5: {sum(1 for r in rows if not r[2])})")

    zero_md5 = {}
    chunk = bytes(64 * 1024 * 1024)
    haser = hashlib.md5(); fed = 0
    for size in sorted({r[1] for r in rows if 0 < r[1] <= 4 * 1024**3}):
        while fed < size:
            n = min(len(chunk), size - fed)
            haser.update(chunk if n == len(chunk) else chunk[:n]); fed += n
        zero_md5[size] = haser.copy().hexdigest()

    con = duckdb.connect()
    con.execute("create temp table src(path varchar, size bigint, md5 varchar, sha256 varchar, modtime varchar, mime varchar)")
    con.executemany("insert into src values (?,?,?,?,?,?)", rows)
    con.execute("create temp table zero(size bigint, md5 varchar)")
    con.executemany("insert into zero values (?, ?)", list(zero_md5.items()))
    ex = args.exports.replace("\\", "/")
    tsv = "delim=chr(9), header=false, quote='', escape='', all_varchar=true"
    con.execute(f"create temp table b2c as select lower(column0) md5, cast(column1 as bigint) size, column2 b2_key from read_csv('{ex}/b2_content.tsv', {tsv})")
    con.execute(f"create temp table carr as select lower(column0) md5, cast(column1 as bigint) size, column2 b2_key from read_csv('{ex}/graded_carriers_keys.tsv', {tsv})")
    con.execute(f"create temp table b2o as select column0 as okey, cast(column1 as bigint) size from read_csv('{ex}/b2_objects.tsv', {tsv})")
    con.execute(f"""create temp table ledger as
        select lower(column0) digest, '{B2_PREFIX}' || column1 || '/' || column2 as b2_key, try_cast(column4 as bigint) size
        from read_csv('{LEDGER}', {tsv})""")

    con.execute("""create temp table plan as select s.*,
        (s.size = 0 or exists (select 1 from zero z where z.size = s.size and z.md5 = s.md5)) as excluded_zero,
        coalesce((select b2_key from b2c b where b.md5 = s.md5 and b.size = s.size and s.md5 <> '' limit 1),
                 (select l.b2_key from ledger l join b2o o on o.okey = l.b2_key and o.size = l.size
                   where l.digest = s.sha256 and s.sha256 <> '' limit 1)) as on_b2_key,
        (select b2_key from carr c where c.md5 = s.md5 and c.size = s.size and s.md5 <> '' limit 1) as pending_key
        from src s""")
    # dev junk never rides to B2 (owner rule); a carrier that is itself a junk path was never copied, so it
    # cannot be "pending" — such a file is new unless its own path is junk too (added 2026-09-14)
    junk_re = r"(^|/)(node_modules|__pycache__|\.venv|venv|flet_env|site-packages|\.npm|\.cache|\.next)(/|$)|installer_files/(env|conda)/|\.dist-info/"
    con.execute(f"""create temp table classed as select *,
        case when excluded_zero then 'excluded_zero'
             when regexp_matches(path, '{junk_re}') then 'junk_excluded'
             when on_b2_key is not null then 'on_b2'
             when pending_key is not null and not regexp_matches(pending_key, '{junk_re}') then 'pending_carrier'
             else 'new' end as class from plan""")
    for cls, n, gb in con.execute("select class, count(*), round(coalesce(sum(size),0)/1e9, 2) from classed group by 1 order by 1").fetchall():
        print(f"  {cls:16s} files={n:>9,} GB={gb}")
    dnew, new_n = con.execute("select count(distinct (md5, size)), count(*) from classed where class = 'new'").fetchone()

    out_dir = os.path.dirname(os.path.abspath(args.inventories[0])).replace("\\", "/")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    plan_tsv = f"{out_dir}/{stamp}-{args.label}-plan.tsv"
    upload = f"{out_dir}/{stamp}-{args.label}-upload.tsv"
    con.execute(f"copy (select path, size, md5, sha256, modtime, mime, class, coalesce(on_b2_key, pending_key) as b2_key from classed order by path) to '{plan_tsv}' (header, delimiter '\t')")
    con.execute(f"""copy (select path, size, md5, sha256, modtime, mime from
                    (select *, row_number() over (partition by md5, size order by path) rn from classed where class = 'new')
                    where rn = 1 order by path) to '{upload}' (header, delimiter '\t')""")
    print(f"plan: {plan_tsv}")
    print(f"upload list: {upload} (carrier payloads for {dnew} contents; {new_n - dnew} additional same-content paths recorded in the plan)")
    print(f"root={args.root}")
    return 0


if __name__ == "__main__":
    main()
