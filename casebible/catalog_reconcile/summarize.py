"""Byline: Codex | 2026-09-20. Reproducible metadata-only triage totals."""
import argparse
import collections
import json
from pathlib import Path

import duckdb

from io_utils import records
from run import save_json


def summarize(root,output_name='triage-summary.json'):
    root=Path(root)
    con=duckdb.connect(str(root/'catalog.duckdb'),read_only=True)
    con.execute('SET threads=2');con.execute("SET memory_limit='1GB'")
    def query(sql):
        result=con.execute(sql);keys=[r[0] for r in result.description]
        return [dict(zip(keys,row)) for row in result.fetchall()]
    result={'byline':'Codex | 2026-09-20','visible':query("SELECT count(*) objects,sum(size) bytes FROM object_versions WHERE visible AND action='upload'")[0],
            'top_prefixes':query("SELECT CASE WHEN strpos(object_key,'/')=0 THEN '(root)' ELSE split_part(object_key,'/',1) END prefix,count(*) objects,sum(size) bytes FROM object_versions WHERE visible AND action='upload' GROUP BY 1 ORDER BY bytes DESC"),
            'consignatio_prefixes':query("SELECT split_part(object_key,'/',2) prefix,count(*) objects,sum(size) bytes FROM object_versions WHERE visible AND action='upload' AND object_key LIKE 'consignatio/%' GROUP BY 1 ORDER BY bytes DESC"),
            'versions':query("SELECT action,visible,count(*) records,sum(size) bytes FROM object_versions GROUP BY 1,2 ORDER BY 1,2"),
            'duplicate_identities':query('SELECT count(*) AS identity_groups,sum(physical_copies) physical_copies,sum(physical_copies-1) extra_paths,sum(repeated_bytes) repeated_bytes FROM visible_duplicate_identities')[0],
            'availability':query('SELECT source,availability,count(*) AS occurrence_rows FROM occurrences GROUP BY 1,2 ORDER BY 1,2'),
            'worklist':query('SELECT kind,priority,count(*) items FROM recovery_worklist GROUP BY 1,2 ORDER BY 1,2'),
            'r2':query('SELECT bucket,availability,count(*) AS occurrence_rows FROM r2_occurrences GROUP BY 1,2 ORDER BY 1,2')}
    containers=query("SELECT CASE WHEN strpos(substr(object_key,length('consignatio/vault/v1/')+1),'/')=0 THEN '(root files)' ELSE split_part(object_key,'/',4) END container,count(*) objects,sum(size) bytes FROM object_versions WHERE visible AND action='upload' AND object_key LIKE 'consignatio/vault/v1/%' GROUP BY 1 ORDER BY bytes DESC")
    result['vault_containers']=containers
    result['vault_directory_prefixes']=sum(r['container']!='(root files)' for r in containers)
    unfinished=list(records(root/'unfinished.parquet'))
    result['unfinished']={'files':len(unfinished),'parts':sum(len(r['parts']) for r in unfinished),
                          'bytes':sum(p['contentLength'] for r in unfinished for p in r['parts'])}
    native=collections.Counter()
    for r in records(root/'native_export_reconciliation.parquet'):
        for kind,value in r['representations'].items():native[(kind,value['state'])]+=1
    result['native_exports']=[{'representation':k[0],'availability':k[1],'items':v} for k,v in sorted(native.items())]
    result['retirement_cleared']=0
    if Path(output_name).name!=output_name:raise ValueError('Output must be a filename')
    save_json(root/output_name,result)
    con.close()
    print(json.dumps({k:result[k] for k in ('visible','duplicate_identities','unfinished','native_exports')},default=str))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--generation',required=True)
    parser.add_argument('--output-name',default='triage-summary.json')
    args=parser.parse_args();summarize(args.generation,args.output_name)
