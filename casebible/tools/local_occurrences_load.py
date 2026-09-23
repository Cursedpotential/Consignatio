#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Load a local source's dedupe plan into raw_duck.source_occurrences. Runs ON the VPS.

Input: the <stamp>-<label>-plan.tsv written by local_source_dedupe_plan.py
       (path, size, md5, sha256, modtime, mime, class, b2_key) — scp it to the VPS first.
Mapping (class -> disposition):
  excluded_zero   -> zero_byte        (catalog only; owner: 0 bytes has no hash)
  on_b2           -> content_on_b2    (b2_key = where identical bytes already live)
  pending_carrier -> pending_carrier  (re-join after the graded tranches finish)
  new             -> copied   if the object already exists under its own key local/<src>/<path> in raw_duck.b2_objects
                     to_copy  otherwise
Usage: python3 local_occurrences_load.py <source> <plan.tsv>     e.g. local/F-case  /tmp/20260913-F_case-plan.tsv
Idempotent: upsert by (source, scope='', path). Read-only against B2; writes only the occurrence rows.
"""
import os
import subprocess
import sys

PG = "fgz1n7useplhk0t91uk7k1aw"
B2_PREFIX = "consignatio/intake/raw-dedupe/v1/source-buckets/"
# DuckDB's COPY writes RFC CSV with a tab delimiter: paths holding special characters arrive double-quoted.
# Parse it as CSV (quote '"') — reading it "raw" stored literal quotes in 9 F: paths on 2026-09-14.
CSV_OPTS = "with (format csv, delimiter E'\\t', quote '\"', escape '\"', header true)"
SQL = f"""
create temp table lp (path text, size bigint, md5 text, sha256 text, modtime text, mime text, class text, b2_key text);
\\copy lp from '/tmp/{{base}}' {CSV_OPTS}
-- rows this loader wrote earlier with the quoting bug (path begins with a literal double quote): ours, not evidence
delete from raw_duck.source_occurrences where source = '{{source}}' and scope = '' and path like '"%';
insert into raw_duck.source_occurrences
  (source, scope, path, size, modtime, source_id, native_hash_kind, native_hash, md5, disposition, b2_key, matched_origin, metadata)
select '{{source}}', '', lp.path, lp.size, nullif(lp.modtime,'')::timestamptz, '', 'sha256', nullif(lp.sha256,''), nullif(lp.md5,''),
       case lp.class when 'excluded_zero' then 'zero_byte' when 'junk_excluded' then 'junk_excluded'
            when 'on_b2' then 'content_on_b2' when 'pending_carrier' then 'pending_carrier'
            when 'new' then case when o.key is not null then 'copied' else 'to_copy' end end,
       case lp.class when 'new' then '{B2_PREFIX}{{source}}/' || lp.path when 'junk_excluded' then null else nullif(lp.b2_key,'') end,
       case lp.class when 'on_b2' then 'catalog' when 'pending_carrier' then 'carrier_pending' end,
       jsonb_build_object('mime', nullif(lp.mime,''))
from lp left join raw_duck.b2_objects o on lp.class = 'new' and o.key = '{B2_PREFIX}{{source}}/' || lp.path and o.size = lp.size
on conflict (source, scope, path, source_id) do update set
  size = excluded.size, modtime = excluded.modtime, native_hash = excluded.native_hash, md5 = excluded.md5,
  matched_origin = excluded.matched_origin, metadata = excluded.metadata,
  -- a file this pipeline copied stays 'copied' — it is on B2, whatever a re-plan now calls it (on_b2 because its
  -- own key entered b2_content; junk_excluded because the 2026-09-13 F: plan had no junk filter — those junk
  -- objects are the optional sweep in URGENT-TODO, not a catalog lie)
  disposition = case when raw_duck.source_occurrences.disposition = 'copied' then 'copied' else excluded.disposition end,
  b2_key = case when raw_duck.source_occurrences.disposition = 'copied' then raw_duck.source_occurrences.b2_key else excluded.b2_key end,
  recorded_at = now();
select disposition || '=' || count(*) || ' (' || coalesce(sum(size),0) || ' B)' from raw_duck.source_occurrences
 where source = '{{source}}' group by disposition order by disposition;
"""


def sh(*args: str, stdin: str | None = None) -> str:
    r = subprocess.run(args, input=stdin, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"FAILED {' '.join(args)[:120]}\n{r.stderr.strip()[-1200:]}")
    return r.stdout


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    source, plan = sys.argv[1], sys.argv[2]
    base = os.path.basename(plan)
    ddl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_occurrences.sql")
    sh("docker", "cp", plan, f"{PG}:/tmp/{base}")
    out = sh("docker", "exec", "-i", PG, "psql", "-U", "postgres", "-d", "casebible", "-At", "-v", "ON_ERROR_STOP=1",
             stdin=open(ddl, encoding="utf-8").read() + SQL.format(base=base, source=source.replace("'", "''")))
    print(f"{source}: " + " ".join(l for l in out.splitlines() if "=" in l))
    return 0


if __name__ == "__main__":
    sys.exit(main())
