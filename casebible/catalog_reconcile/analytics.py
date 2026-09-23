"""Byline: Codex | 2026-09-20. Named, read-only pg_duckdb catalog analytics."""
import argparse
import subprocess
import sys

from io_utils import Postgres


CURRENT="(SELECT generation_id FROM raw_duck.reconcile_generations_20260920 ORDER BY published_at DESC,generation_id DESC LIMIT 1)"
QUERIES={
 'availability':f"SELECT payload->>'source' AS source,payload->>'state' AS availability,count(*) AS occurrence_rows FROM raw_duck.reconcile_occurrences_20260920 WHERE generation_id={CURRENT} GROUP BY 1,2 ORDER BY 1,2",
 'native_candidates':f"SELECT payload->>'source' AS source,count(*) AS provisional_candidates FROM raw_duck.reconcile_bas_candidates_20260920 WHERE generation_id={CURRENT} GROUP BY 1 ORDER BY 1",
 'duplicate_totals':f"SELECT count(*) AS identity_groups,sum(copies-1) AS extra_paths,sum((copies-1)*size) AS repeated_bytes FROM (SELECT payload->>'sha1' AS sha1,(payload->>'size')::bigint AS size,count(*) AS copies FROM raw_duck.reconcile_objects_20260920 WHERE generation_id={CURRENT} AND (payload->>'visible')::boolean AND payload->>'action'='upload' AND payload->>'sha1' IS NOT NULL GROUP BY 1,2 HAVING count(*)>1) duplicates",
}


def execute(name,explain=False):
    # Transaction-local configuration; never enables external file access or installs extensions.
    sql="""BEGIN READ ONLY;
SET LOCAL duckdb.autoinstall_known_extensions=off;
SET LOCAL duckdb.autoload_known_extensions=off;
SET LOCAL duckdb.enable_external_access=off;
SET LOCAL duckdb.force_execution=on;
"""+("EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF) " if explain else "")+QUERIES[name]+";\nROLLBACK;"
    command=Postgres().command();command[-1]+=' --csv'
    result=subprocess.run(command,input=sql,capture_output=True,text=True,encoding='utf-8',timeout=650)
    if result.returncode:raise RuntimeError(result.stderr[:600])
    return result.stdout


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',choices=QUERIES);parser.add_argument('--explain',action='store_true')
    args=parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    print(execute(args.report,args.explain),end='')
