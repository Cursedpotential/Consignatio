"""Byline: Codex | 2026-09-20. Build local SQL views over verified metadata Parquet."""
import argparse
import json
from pathlib import Path

import duckdb

from io_utils import sha256_file
from run import save_json


def create(root):
    root=Path(root).resolve()
    manifest=json.loads((root/'validated.json').read_text(encoding='utf-8'))
    if manifest['status']!='validated_metadata_reconciliation' or not all(manifest['checks'].values()):
        raise ValueError('Generation is not validated')
    for name,expected in manifest['files'].items():
        if sha256_file(root/name)!=expected:raise ValueError('Fingerprint differs: '+name)
    target=root/'catalog.duckdb'
    if target.exists():raise FileExistsError(target)
    connection=duckdb.connect(str(target))
    try:
        connection.execute('SET threads=2')
        connection.execute("SET memory_limit='1GB'")
        connection.execute("SET temp_directory="+sql_string(str(root/'duckdb-temp')))
        for name in ('object_versions','occurrence_links','r2_links','recovery_worklist','native_export_reconciliation','atomic_units','atomic_members','export_units','export_members','vault_units','source_observations','bas_candidates'):
            path=sql_string(str(root/(name+'.parquet')))
            connection.execute(f'CREATE VIEW {name}_raw AS SELECT record::JSON AS record FROM read_parquet({path})')
        connection.execute("""CREATE VIEW object_versions AS SELECT record->>'file_id' AS file_id,
          record->>'key' AS object_key,record->>'action' AS action,(record->>'size')::BIGINT AS size,
          record->>'sha1' AS sha1,(record->>'visible')::BOOLEAN AS visible,
          record->'metadata' AS source_metadata FROM object_versions_raw""")
        connection.execute("""CREATE VIEW occurrences AS SELECT record->>'occurrence_id' AS occurrence_id,
          record->>'source' AS source,record->>'state' AS availability,record->>'match_basis' AS match_basis,
          record->'source_record'->>'path' AS source_path,record->'source_record'->>'source_id' AS provider_source_id,
          record->'version_ids' AS version_ids,record->'source_record' AS source_record,
          record->'quality_flags' AS quality_flags,record->>'bas_status' AS bas_status,
          record->>'retirement_status' AS retirement_status FROM occurrence_links_raw""")
        connection.execute("""CREATE VIEW recovery_worklist AS SELECT record->>'item_id' AS item_id,
          record->>'kind' AS kind,record->>'source' AS source,record->>'priority' AS priority,
          record->>'reason' AS reason,record->>'next_step' AS next_step,record->'evidence' AS evidence,
          record->>'retirement_status' AS retirement_status FROM recovery_worklist_raw""")
        connection.execute("""CREATE VIEW r2_occurrences AS SELECT record->>'occurrence_id' AS occurrence_id,
          record->'source_record'->>'bucket' AS bucket,record->'source_record'->>'path' AS source_path,
          record->>'state' AS availability,record->>'match_basis' AS match_basis,
          record->'version_ids' AS version_ids,record->>'retirement_status' AS retirement_status,
          record->'source_record' AS source_record FROM r2_links_raw""")
        connection.execute("""CREATE VIEW visible_duplicate_identities AS SELECT sha1,size,count(*) AS physical_copies,
          (count(*)-1)*size AS repeated_bytes FROM object_versions
          WHERE visible AND action='upload' AND sha1 IS NOT NULL GROUP BY sha1,size HAVING count(*)>1""")
        connection.execute("""CREATE VIEW bas_candidates AS SELECT record->>'family_id' AS family_id,
          record->>'source' AS source,record->>'source_id' AS provider_source_id,
          record->'bas1_candidate' AS bas1_candidate,record->'bas2_candidate' AS bas2_candidate,
          record->>'status' AS status,record->'complementary_representations_to_review' AS complementary_representations_to_review
          FROM bas_candidates_raw""")
        connection.execute("""CREATE VIEW native_exports AS SELECT record->>'source' AS source,
          record->>'source_id' AS provider_source_id,record->>'native_path' AS source_path,
          record->'representations' AS representations,record->>'source_native_retained' AS source_native_retained
          FROM native_export_reconciliation_raw""")
        counts={name:connection.execute(f'SELECT count(*) FROM {name}').fetchone()[0]
                for name in ('object_versions','occurrences','r2_occurrences','recovery_worklist','visible_duplicate_identities')}
        if counts['occurrences']!=manifest['occurrence_rows'] or counts['recovery_worklist']!=manifest['work_items']:
            raise RuntimeError('SQL read-back conservation failed')
        connection.execute('CHECKPOINT')
    finally:connection.close()
    save_json(root/'lakehouse.json',{'byline':'Codex | 2026-09-20','generation_id':manifest['generation_id'],
                                  'database':str(target),'counts':counts,'status':'local_sql_readback_verified'})
    print(json.dumps(counts))


def sql_string(value):return "'"+value.replace("'","''")+"'"


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--generation',required=True)
    create(parser.parse_args().generation)
