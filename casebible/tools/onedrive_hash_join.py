#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Join OneDrive inventory + server-side md5s against the content-on-B2 catalog; emit the copy list and
the occurrence rows. Runs ON the VPS.

Pipeline: onedrive_collision_plan.py (size split) -> launch_onedrive_hash.sh (md5 of the collision set)
-> THIS -> launch_onedrive_copy.sh -> `rclone check --download` -> THIS --mark-copied.

Rules applied (owner, 2026-09-13/14):
  - a file whose (md5,size) is in raw_duck.b2_content already has its bytes on B2 -> occurrence row only
    (matching r2_files is NOT enough: junk-filtered/held R2 rows never got a B2 carrier);
  - held rows have null md5, so a zero-filled copy can never match a good file;
  - dev junk (node_modules, __pycache__, .venv, ...) never rides to B2 -> junk_excluded;
  - 0-byte files have no hash -> zero_byte, catalog only;
  - everything else (new-by-size, or hashed but not on B2) -> to_copy; after a verified check -> copied.

Usage (on VPS):
  python3 onedrive_hash_join.py <scope>                 build lists + upsert occurrences
  python3 onedrive_hash_join.py <scope> --mark-copied   after `rclone check --download` passed: to_copy -> copied
Writes: <RUN>/lists/<scope>.copy.list, .matched.tsv, .unmatched.list, .join-summary.txt; rows in raw_duck.source_occurrences.
"""
import json
import os
import re
import subprocess
import sys

RUN = "/data/consignatio/migrations/onedrive-copy-20260914"
INV = "/data/consignatio/migrations/onedrive-inventory-20260913"
PG = "fgz1n7useplhk0t91uk7k1aw"
B2_PREFIX = "consignatio/intake/raw-dedupe/v1/source-buckets/onedrive/"
ROOT = {"AI_Space": "AI Space", "Case_Bible": "Case Bible", "Documents_CSV": "Documents/CSV",
        "Documents_Disk_Drill": "Documents/Disk Drill"}
JUNK = re.compile(r"(^|/)(node_modules|__pycache__|\.venv|venv|flet_env|site-packages|\.npm|\.cache|\.next)(/|$)|installer_files/(env|conda)/|\.dist-info/")
CSV_OPTS = "with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')"

SQL_JOIN = f"""
create temp table od_in (path text, size bigint, modtime text, source_id text, quickxor text, md5 text, kind text, metadata text);
\\copy od_in from '/tmp/{{scope}}.rows.tsv' {CSV_OPTS}
-- Proxy identity for unhashed collide rows (2026-09-14): the R2 onedrive backups hold the same files with md5.
-- basename + size + modtime-to-the-second (r2_files.modtime is naive US-Eastern local time, OneDrive's is UTC,
-- so -4h EDT / -5h EST) with exactly ONE distinct md5 counts as md5-by-proxy; held rows have md5 nulled, so a
-- zero-filled placeholder can never proxy-match. Recorded as matched_origin 'name_size_mtime:<origin>' and
-- metadata.md5_proxy — never written into the md5 column, which holds server-side hashes only.
create temp table od_proxy as
select i.path, min(r.md5) as md5_proxy
from od_in i
join raw_duck.r2_files r
  on r.name = regexp_replace(i.path, '^.*/', '') and r.size = i.size
 and r.modtime in ((nullif(i.modtime,'')::timestamptz at time zone 'UTC') - interval '4 hours',
                   (nullif(i.modtime,'')::timestamptz at time zone 'UTC') - interval '5 hours')
 and coalesce(r.md5, '') <> ''
where i.kind = 'collide' and i.md5 is null
group by i.path having count(distinct r.md5) = 1;
create temp table od_out as
select i.path, i.size, i.modtime, i.source_id, i.quickxor, i.md5,
       case when px.md5_proxy is not null then (i.metadata::jsonb || jsonb_build_object('md5_proxy', px.md5_proxy))::text else i.metadata end as metadata,
       case when i.kind = 'zero' then 'zero_byte'
            when i.kind = 'junk' then 'junk_excluded'
            when b.md5 is not null then 'content_on_b2'
            when c.md5 is not null then 'pending_carrier'   -- carrier still in a running tranche; re-join later
            when i.kind = 'collide' and i.md5 is null then 'pending_hash'
            else 'to_copy' end as disposition,
       case when b.md5 is not null then b.b2_key
            when c.md5 is not null then c.b2_key
            when i.kind in ('new','collide') then '{B2_PREFIX}' || '{{root}}' || '/' || i.path end as b2_key,
       case when b.md5 is not null then (case when i.md5 is null then 'name_size_mtime:' else '' end) || b.origin
            when c.md5 is not null then (case when i.md5 is null then 'name_size_mtime:' else '' end) || 'carrier_pending' end as matched_origin
from od_in i
left join od_proxy px on px.path = i.path
left join raw_duck.b2_content b on b.md5 = coalesce(i.md5, px.md5_proxy) and b.size = i.size and coalesce(i.md5, px.md5_proxy) is not null
left join lateral (select md5, b2_key from raw_duck.graded_carriers g where g.md5 = coalesce(i.md5, px.md5_proxy) and g.size = i.size limit 1) c
       on b.md5 is null and coalesce(i.md5, px.md5_proxy) is not null;
insert into raw_duck.source_occurrences
  (source, scope, path, size, modtime, source_id, native_hash_kind, native_hash, md5, disposition, b2_key, matched_origin, metadata)
select 'onedrive', '{{root}}', path, size, nullif(modtime,'')::timestamptz, coalesce(source_id,''), 'quickxor', quickxor, md5,
       disposition, b2_key, matched_origin, metadata::jsonb
from od_out
on conflict (source, scope, path, source_id) do update set
  size = excluded.size, modtime = excluded.modtime, source_id = excluded.source_id, native_hash = excluded.native_hash,
  md5 = excluded.md5, b2_key = excluded.b2_key, matched_origin = excluded.matched_origin, metadata = excluded.metadata,
  -- a file this pipeline copied stays 'copied' (after a copy its own key is in b2_content, so a re-join says content_on_b2)
  disposition = case when raw_duck.source_occurrences.disposition = 'copied' and excluded.disposition in ('to_copy','content_on_b2')
                     then 'copied' else excluded.disposition end,
  recorded_at = now();
\\copy (select path, md5, size, b2_key, matched_origin from od_out where disposition = 'content_on_b2' order by path) to '/tmp/{{scope}}.matched.tsv' {CSV_OPTS}
\\copy (select path from od_out where disposition = 'to_copy' order by path) to '/tmp/{{scope}}.copy.list' {CSV_OPTS}
\\copy (select path from od_out where disposition = 'to_copy' and md5 is not null order by path) to '/tmp/{{scope}}.unmatched.list' {CSV_OPTS}
\\copy (select path from od_out where disposition = 'pending_hash' order by path) to '/tmp/{{scope}}.hash.list' {CSV_OPTS}
select 'proxy_matched=' || count(*) from od_proxy;
select string_agg(disposition || '=' || n, ' ' order by disposition) from (select disposition, count(*) n from od_out group by 1) s;
select 'to_copy_bytes=' || coalesce(sum(size),0) from od_out where disposition = 'to_copy';
"""

SQL_MARK = """
update raw_duck.source_occurrences set disposition = 'copied', recorded_at = now()
where source = 'onedrive' and scope = '{root}' and disposition = 'to_copy';
select 'copied_now=' || count(*) from raw_duck.source_occurrences where source = 'onedrive' and scope = '{root}' and disposition = 'copied';
"""


def sh(*args: str, stdin: str | None = None) -> str:
    r = subprocess.run(args, input=stdin, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(args)[:120]}\n{r.stderr.strip()[-1200:]}")
    return r.stdout


def psql(sql: str) -> str:
    return sh("docker", "exec", "-i", PG, "psql", "-U", "postgres", "-d", "casebible", "-At", "-v", "ON_ERROR_STOP=1", stdin=sql)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ROOT:
        print(__doc__, file=sys.stderr)
        return 2
    scope, root = sys.argv[1], ROOT[sys.argv[1]]
    ddl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_occurrences.sql")
    psql(open(ddl, encoding="utf-8").read())
    if "--mark-copied" in sys.argv:
        print(psql(SQL_MARK.format(root=root.replace("'", "''"))).strip())
        return 0

    md5 = {}
    for fn in (f"{RUN}/hashes/{scope}.md5", f"{RUN}/hashes/{scope}.md5.part"):
        if os.path.exists(fn):
            for line in open(fn, encoding="utf-8"):
                line = line.rstrip("\n")
                if len(line) > 34:
                    md5[line[34:]] = line[:32]
    known = {int(l) for l in open(f"{RUN}/known_sizes_r2.txt", encoding="utf-8") if l.strip()}
    objs = json.load(open(f"{INV}/{scope}.lsjson", encoding="utf-8"))
    rows_tsv = f"{RUN}/hashes/{scope}.rows.tsv"
    with open(rows_tsv, "w", encoding="utf-8", newline="\n") as fh:
        for o in objs:
            if o.get("IsDir"):
                continue
            p, size = o["Path"], o["Size"]
            kind = ("zero" if size == 0 else "junk" if JUNK.search(p) else "collide" if size in known else "new")
            meta = json.dumps({k: v for k, v in o.items() if k not in ("Path", "Name", "Size", "IsDir", "Hashes", "ID")}, ensure_ascii=False)
            fh.write("\t".join([p, str(size), o.get("ModTime", ""), o.get("ID", ""), (o.get("Hashes") or {}).get("quickxor", ""),
                                md5.get(p, ""), kind, meta]) + "\n")
    sh("docker", "cp", rows_tsv, f"{PG}:/tmp/{scope}.rows.tsv")
    out = psql(SQL_JOIN.format(scope=scope, root=root.replace("'", "''")))
    for name in ("matched.tsv", "copy.list", "unmatched.list", "hash.list"):
        sh("docker", "cp", f"{PG}:/tmp/{scope}.{name}", f"{RUN}/lists/{scope}.{name}")
    summary = f"{scope}: {' '.join(out.split())} hashed_available={len(md5)}"
    open(f"{RUN}/lists/{scope}.join-summary.txt", "w", encoding="utf-8").write(summary + "\n")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
