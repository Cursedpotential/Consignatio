#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Turn native Google Docs/Sheets/Slides occurrence rows from pending_export into exported. Runs ON the VPS.

Inputs (run dir /data/consignatio/migrations/gdrive-copy-20260913):
  native-export-<acct>-idmap.tsv                       id, native path, office name, pdf name, mime, modtime  (gdrive_native_export_plan.py)
  native-export-<acct>-{office,pdf}.copyid-*.receipt.jsonl  {"status": ok|failed, "items": [dest names], "detail"}  (gdrive_copyid_driver.py)
  raw_duck.b2_objects                                   fresh listing — an export counts only if its object is on B2
Row per native (source gdrive/<acct>, scope '', path = native path, source_id = Drive id):
  exported        both the Office and the PDF objects are on B2; b2_key = Office key; metadata.pdf_key, metadata.export_receipts
  export_partial  exactly one of the two is on B2 (metadata says which)
  export_failed   neither; metadata.export_error = last receipt detail
Run after ALL export passes finish and after b2_content_catalog.sh has refreshed b2_objects.
Usage: python3 gdrive_native_exports_load.py <salemnet|salem85>
"""
import glob
import json
import os
import subprocess
import sys

RUN = "/data/consignatio/migrations/gdrive-copy-20260913"
PG = "fgz1n7useplhk0t91uk7k1aw"
B2_PREFIX = "consignatio/intake/raw-dedupe/v1/source-buckets/gdrive/"
CSV_OPTS = "with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')"

SQL = f"""
create temp table ne (id text, path text, office text, pdf text, mime text, modtime text, err text);
\\copy ne from '/tmp/ne_{{acct}}.tsv' {CSV_OPTS}
create temp table ne_out as
select n.*, o.key as office_key, p.key as pdf_key
from ne n
left join raw_duck.b2_objects o on o.key = '{B2_PREFIX}{{acct}}/' || n.office
left join raw_duck.b2_objects p on p.key = '{B2_PREFIX}{{acct}}/' || n.pdf;
insert into raw_duck.source_occurrences
  (source, scope, path, size, modtime, source_id, native_hash_kind, native_hash, md5, disposition, b2_key, matched_origin, metadata)
select 'gdrive/{{acct}}', '', path, 0, nullif(modtime,'')::timestamptz, id, null, null, null,
       case when office_key is not null and pdf_key is not null then 'exported'
            when office_key is not null or pdf_key is not null then 'export_partial' else 'export_failed' end,
       coalesce(office_key, pdf_key),
       'native_export',
       jsonb_build_object('native', true, 'mime', mime, 'office_key', office_key, 'pdf_key', pdf_key,
                          'export_error', nullif(err, ''), 'export_rule', 'unique -> <name>.<ext>; collision -> <name> [gdoc-<id8>].<ext>')
from ne_out
on conflict (source, scope, path, source_id) do update set
  modtime = excluded.modtime, disposition = excluded.disposition, b2_key = excluded.b2_key,
  matched_origin = excluded.matched_origin, metadata = raw_duck.source_occurrences.metadata || excluded.metadata, recorded_at = now();
select string_agg(d || '=' || n, ' ' order by d) from (
  select case when office_key is not null and pdf_key is not null then 'exported'
              when office_key is not null or pdf_key is not null then 'export_partial' else 'export_failed' end d, count(*) n
  from ne_out group by 1) s;
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
    errors: dict[str, str] = {}
    # receipts in time order (the stamp is in the filename): a later "ok" for an item clears its earlier failure
    for rf in sorted(glob.glob(f"{RUN}/native-export-{acct}-*.copyid-*.receipt.jsonl"), key=lambda p: p.split(".copyid-")[1]):
        for line in open(rf, encoding="utf-8"):
            rec = json.loads(line)
            for item in rec.get("items", []):
                if rec.get("status") == "failed":
                    errors[item] = rec.get("detail", "")[-300:]
                else:
                    errors.pop(item, None)
    rows = 0
    tsv = f"{RUN}/ne_{acct}.rows.tsv"
    with open(tsv, "w", encoding="utf-8", newline="\n") as fh:
        for line in open(f"{RUN}/native-export-{acct}-idmap.tsv", encoding="utf-8"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            fid, path, office, pdf, mime, modtime = parts[:6]
            err = errors.get(office) or errors.get(pdf) or ""
            fh.write("\t".join([fid, path, office, pdf, mime, modtime, err.replace("\t", " ").replace("\n", " ")]) + "\n")
            rows += 1
    ddl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_occurrences.sql")
    sh("docker", "cp", tsv, f"{PG}:/tmp/ne_{acct}.tsv")
    out = sh("docker", "exec", "-i", PG, "psql", "-U", "postgres", "-d", "casebible", "-At", "-v", "ON_ERROR_STOP=1",
             stdin=open(ddl, encoding="utf-8").read() + SQL.format(acct=acct))
    print(f"gdrive/{acct} natives={rows} " + " ".join(l for l in out.splitlines() if "=" in l))
    return 0


if __name__ == "__main__":
    sys.exit(main())
