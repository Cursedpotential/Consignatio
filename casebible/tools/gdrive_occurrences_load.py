#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Classify a Google Drive Tier-1 baseline against B2 truth, load occurrence rows, emit the copy-by-ID map.
Runs ON the VPS.

Input: tier1-baseline-<acct>.lsjson (rclone lsjson -R --files-only -M --hash, full Drive metadata, natives included).
Identity is the Drive file ID (paths are not unique: duplicate top-level folders). Disposition per file:
  native (Size -1)                                  -> pending_export   (joined to export receipts later)
  dev junk                                          -> junk_excluded
  own key gdrive/<acct>/<path> on B2, same sha1     -> copied            (size match when Drive has no sha1)
  (md5,size) in raw_duck.b2_content                 -> content_on_b2
  (md5,size) in raw_duck.graded_carriers            -> pending_carrier   (tranche still running; re-join later)
  otherwise                                         -> to_copy, b2_key = own key if free, else
                                                       "<name> [gdrive-<id8>].<ext>" (owner's native-export naming precedent)
The 2026-09-13 copies chose "known" by r2_files; this re-classifies everything against what is actually on B2.
Writes lists/gdrive-<acct>.to_copy.idmap.tsv (id<TAB>dest path relative to gdrive/<acct>) for gdrive_copyid_driver.py.

Usage: python3 gdrive_occurrences_load.py <salemnet|salem85>
"""
import csv
import json
import os
import re
import subprocess
import sys

RUN = "/data/consignatio/migrations/gdrive-copy-20260913"
PG = "fgz1n7useplhk0t91uk7k1aw"
B2_PREFIX = "consignatio/intake/raw-dedupe/v1/source-buckets/gdrive/"
JUNK = re.compile(r"(^|/)(node_modules|__pycache__|\.venv|venv|flet_env|site-packages|\.npm|\.cache|\.next)(/|$)|installer_files/(env|conda)/|\.dist-info/")
# PG CSV reads an empty unquoted field as NULL — every equality test on md5/sha1 below is written NULL-safe.
# Input rows are written by csv.writer (quoted only when a Drive name carries a tab/newline — Drive allows both;
# an unquoted TSV broke on such a name 2026-09-14) and read as real CSV; the OUTPUT idmap stays quote-free because
# gdrive_copyid_driver.py splits it on tabs.
CSV_IN = "with (format csv, delimiter E'\\t', quote '\"', escape '\"')"
CSV_OPTS = "with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')"

SQL = f"""
create temp table gd (path text, size bigint, modtime text, id text, md5 text, sha1 text, sha256 text, mime text, kind text, metadata text);
\\copy gd from '/tmp/gd_{{acct}}.tsv' {CSV_IN}
-- rclone's B2 backend encodes control characters in object names (tab -> U+2409 "␉", LF -> "␊", CR -> "␍");
-- Drive names may contain them, so the EXPECTED key on B2 is the translated name, while the copy driver is
-- handed the raw name (rclone encodes on write). Without this, such files matched nothing and stayed to_copy.
create temp table gd_out as
select g.*, translate(g.path, E'\\t\\n\\r', U&'\\2409\\240A\\240D') as b2name, own.key as own_key,
       (own.key is not null and ((coalesce(g.sha1,'') <> '' and own.sha1 = g.sha1) or (coalesce(g.sha1,'') = '' and own.size = g.size))) as own_matches,
       alt.key as alt_key,   -- a collision copy already placed at "<name> [gdrive-<id8>].<ext>"
       (alt.key is not null and ((coalesce(g.sha1,'') <> '' and alt.sha1 = g.sha1) or (coalesce(g.sha1,'') = '' and alt.size = g.size))) as alt_matches,
       b.b2_key as content_key, b.origin as content_origin, c.b2_key as carrier_key
from gd g
left join raw_duck.b2_objects own on own.key = '{B2_PREFIX}{{acct}}/' || translate(g.path, E'\\t\\n\\r', U&'\\2409\\240A\\240D')
left join raw_duck.b2_objects alt on alt.key = '{B2_PREFIX}{{acct}}/' || translate(regexp_replace(g.path, '(\\.[^./]+)?$', ' [gdrive-' || left(g.id, 8) || ']\\1'), E'\\t\\n\\r', U&'\\2409\\240A\\240D')
left join raw_duck.b2_content b on g.kind = 'real' and b.md5 = g.md5 and b.size = g.size
-- a carrier that is itself a dev-junk path was never copied to B2, so it cannot be "pending" (3 rows, 2026-09-14)
left join lateral (select b2_key from raw_duck.graded_carriers x where x.md5 = g.md5 and x.size = g.size
                   and x.path !~ '(^|/)(node_modules|__pycache__|\\.venv|venv|flet_env|site-packages|\\.npm|\\.cache|\\.next)(/|$)|installer_files/(env|conda)/|\\.dist-info/' limit 1) c
       on g.kind = 'real' and b.md5 is null;
create temp table gd_final as
select *,
  case when kind = 'native' then 'pending_export' when kind = 'junk' then 'junk_excluded'
       when own_matches or alt_matches then 'copied' when content_key is not null then 'content_on_b2'
       when carrier_key is not null then 'pending_carrier' else 'to_copy' end as disposition,
  case when kind = 'native' then null when kind = 'junk' then null
       when own_matches then own_key when alt_matches then alt_key when content_key is not null then content_key
       when carrier_key is not null then carrier_key
       when own_key is null then '{B2_PREFIX}{{acct}}/' || b2name
       else '{B2_PREFIX}{{acct}}/' || translate(regexp_replace(path, '(\\.[^./]+)?$', ' [gdrive-' || left(id, 8) || ']\\1'), E'\\t\\n\\r', U&'\\2409\\240A\\240D') end as b2_key,
  -- raw destination handed to the copy driver (rclone encodes control chars itself)
  case when own_key is null then path else regexp_replace(path, '(\\.[^./]+)?$', ' [gdrive-' || left(id, 8) || ']\\1') end as copy_dest
from gd_out;
insert into raw_duck.source_occurrences
  (source, scope, path, size, modtime, source_id, native_hash_kind, native_hash, md5, disposition, b2_key, matched_origin, metadata)
select 'gdrive/{{acct}}', '', path, greatest(size, 0), nullif(modtime,'')::timestamptz, id,
       case when sha256 <> '' then 'sha256' when sha1 <> '' then 'sha1' end, nullif(coalesce(nullif(sha256,''), sha1), ''), nullif(md5,''),
       disposition, b2_key,
       case when disposition = 'copied' then 'own_key_sha1' when disposition = 'content_on_b2' then content_origin
            when disposition = 'pending_carrier' then 'carrier_pending' end,
       jsonb_build_object('mime', mime, 'native', kind = 'native') || metadata::jsonb
from gd_final
on conflict (source, scope, path, source_id) do update set
  size = excluded.size, modtime = excluded.modtime, native_hash_kind = excluded.native_hash_kind, native_hash = excluded.native_hash,
  md5 = excluded.md5, b2_key = excluded.b2_key, matched_origin = excluded.matched_origin, metadata = excluded.metadata,
  disposition = case when raw_duck.source_occurrences.disposition = 'copied' and excluded.disposition = 'to_copy'
                          then 'copied'
                     when raw_duck.source_occurrences.disposition in ('exported','export_partial','export_failed')
                          and excluded.disposition = 'pending_export'
                          then raw_duck.source_occurrences.disposition   -- export receipts outrank a baseline re-load
                     else excluded.disposition end,
  recorded_at = now();
-- a multi-parent Drive file is listed once per path with id "fileID<TAB>parentID": copy the FILE once (first path);
-- its other paths become content_on_b2 at the next join (bytes once, every occurrence kept in the catalog)
\\copy (select distinct on (split_part(id, E'\\t', 1)) split_part(id, E'\\t', 1), copy_dest from gd_final where disposition = 'to_copy' order by split_part(id, E'\\t', 1), path) to '/tmp/gdrive-{{acct}}.to_copy.idmap.tsv' {CSV_OPTS}
select string_agg(disposition || '=' || n || ' (' || gb || ' GB)', ' ' order by disposition)
  from (select disposition, count(*) n, round(sum(greatest(size,0))/1e9, 2) gb from gd_final group by 1) s;
select 'collision_suffixed_keys=' || count(*) from gd_final where disposition = 'to_copy' and b2_key like '%[gdrive-%';
"""


def sh(*args: str, stdin: str | None = None) -> str:
    r = subprocess.run(args, input=stdin, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(args)[:120]}\n{r.stderr.strip()[-1500:]}")
    return r.stdout


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("salemnet", "salem85"):
        print(__doc__, file=sys.stderr)
        return 2
    acct = sys.argv[1]
    objs = json.load(open(f"{RUN}/tier1-baseline-{acct}.lsjson", encoding="utf-8"))
    tsv = f"{RUN}/gd_{acct}.rows.tsv"
    n = 0
    with open(tsv, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        for o in objs:
            if o.get("IsDir"):
                continue
            p, size = o["Path"], o.get("Size", 0)
            kind = "native" if size == -1 else "junk" if JUNK.search(p) else "real"
            h = o.get("Hashes") or {}
            meta = json.dumps(o.get("Metadata") or {}, ensure_ascii=False)
            w.writerow([p, str(size), o.get("ModTime", ""), o.get("ID", ""), (h.get("md5") or "").lower(),
                        (h.get("sha1") or "").lower(), (h.get("sha256") or "").lower(), o.get("MimeType", ""), kind, meta])
            n += 1
    ddl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_occurrences.sql")
    sh("docker", "cp", tsv, f"{PG}:/tmp/gd_{acct}.tsv")
    out = sh("docker", "exec", "-i", PG, "psql", "-U", "postgres", "-d", "casebible", "-At", "-v", "ON_ERROR_STOP=1",
             stdin=open(ddl, encoding="utf-8").read() + SQL.format(acct=acct))
    os.makedirs(f"{RUN}/lists", exist_ok=True)
    sh("docker", "cp", f"{PG}:/tmp/gdrive-{acct}.to_copy.idmap.tsv", f"{RUN}/lists/gdrive-{acct}.to_copy.idmap.tsv")
    lines = [l for l in out.splitlines() if "=" in l]
    print(f"gdrive/{acct}: files={n} " + " ".join(lines))
    print(f"copy map: {RUN}/lists/gdrive-{acct}.to_copy.idmap.tsv ({sum(1 for _ in open(f'{RUN}/lists/gdrive-{acct}.to_copy.idmap.tsv', encoding='utf-8'))} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
