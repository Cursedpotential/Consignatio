"""Byline: Codex | 2026-09-20. Add verified recovery outcomes without altering historical claims."""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

from io_utils import Postgres,records,sha256_file,write_records
from run import save_json,emit

SQL="""
CREATE TABLE IF NOT EXISTS raw_duck.recovered_artifacts_20260920 (
 generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
 artifact_id text NOT NULL, payload jsonb NOT NULL, PRIMARY KEY(generation_id,artifact_id),
 CHECK(payload->>'status'='recovered_verified'));
CREATE TABLE IF NOT EXISTS raw_duck.recovered_occurrences_20260920 (
 generation_id uuid NOT NULL,occurrence_id text NOT NULL,artifact_id text NOT NULL,
 PRIMARY KEY(generation_id,occurrence_id),
 FOREIGN KEY(generation_id,artifact_id) REFERENCES raw_duck.recovered_artifacts_20260920);
CREATE TABLE IF NOT EXISTS raw_duck.recovery_holds_20260920 (
 generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
 artifact_id text NOT NULL,payload jsonb NOT NULL,PRIMARY KEY(generation_id,artifact_id));
CREATE OR REPLACE VIEW catalog_reconcile.recovery_holds AS
 SELECT r.* FROM raw_duck.recovery_holds_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.recovered_artifacts AS
 SELECT r.generation_id,r.artifact_id,r.payload->>'local_path' AS recovered_path,
 r.payload->>'source_version_id' AS source_version_id,r.payload->>'source_key' AS source_key,
 (r.payload->>'size')::bigint AS size,r.payload->>'sha1' AS sha1,r.payload->>'sha256' AS sha256,
 r.payload->>'status' AS status,r.payload->>'bas_status' AS bas_status,r.payload AS receipt
 FROM raw_duck.recovered_artifacts_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.effective_recovery_worklist AS
 SELECT w.*,CASE WHEN w.kind='relink_historical_version' AND r.artifact_id IS NOT NULL THEN 'byte_recovery_complete'
 WHEN w.kind='native_export_linkage_conflict' AND n.id IS NOT NULL
 AND n.representations->'office'->>'state' IN ('visible_exact_path','visible_exact_elsewhere')
 AND n.representations->'pdf'->>'state' IN ('visible_exact_path','visible_exact_elsewhere') THEN 'export_linkage_reconciled'
 ELSE 'pending' END AS recovery_stage_status,
 r.artifact_id AS recovered_artifact_id,a.payload->>'local_path' AS recovered_path,
 'quality_and_bas_review_still_required'::text AS quality_boundary
 FROM catalog_reconcile.recovery_worklist w
 LEFT JOIN raw_duck.recovered_occurrences_20260920 r ON r.generation_id=w.generation_id
 AND r.occurrence_id=w.evidence->>'occurrence_id' AND w.kind='relink_historical_version'
 LEFT JOIN raw_duck.recovered_artifacts_20260920 a ON a.generation_id=r.generation_id AND a.artifact_id=r.artifact_id
 LEFT JOIN catalog_reconcile.native_exports n ON n.source=w.source
 AND n.provider_source_id=w.evidence->>'source_id' AND w.kind='native_export_linkage_conflict';
"""


def publish(root):
    root=Path(root);meta=json.loads((root/'recovered.json').read_text(encoding='utf-8'))
    if meta['failed'] or meta['verified']!=meta['planned']:raise ValueError('Batch recovery is incomplete')
    if sha256_file(root/'recovered.parquet')!=meta['results_sha256']:raise ValueError('Recovery receipts changed')
    downloaded=list(records(root/'recovered.parquet'));rows=[];holds=[]
    for r in downloaded:
        p=Path(r['local_path']);h1=hashlib.sha1();h256=hashlib.sha256()
        try:
            with p.open('rb') as f:
                for block in iter(lambda:f.read(1024*1024),b''):h1.update(block);h256.update(block)
            if p.stat().st_size!=r['size'] or h1.hexdigest()!=r['sha1'] or h256.hexdigest()!=r['sha256']:raise ValueError('Local recovered file failed independent read-back')
            rows.append({**r,'independent_disk_readback':'verified'})
        except (OSError,ValueError) as error:
            holds.append({**r,'status':'download_verified_disk_readback_held','hold_reason':type(error).__name__,
                          'local_errno':getattr(error,'errno',None),'next_step':'Retain B2 source; inspect protection/quality hold without bypassing it'})
    write_records(root/'disk_verified.parquet',rows)
    write_records(root/'disk_holds.parquet',holds)
    gen=meta['generation_id'];pg=Postgres()
    if (root/'published.json').exists():raise FileExistsError('Already published')
    with (root/'publish.stdout').open('x',encoding='utf-8') as out,(root/'publish.stderr').open('x',encoding='utf-8') as err:
        proc=subprocess.Popen(pg.command(writable=True),stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,encoding='utf-8')
        proc.stdin.write('BEGIN; SELECT pg_advisory_xact_lock(20260920,2);\n'+SQL)
        proc.stdin.write('COPY raw_duck.recovered_artifacts_20260920 FROM STDIN WITH (FORMAT CSV);\n')
        writer=csv.writer(proc.stdin,lineterminator='\n')
        for r in rows:writer.writerow([gen,r['artifact_id'],json.dumps(r,ensure_ascii=False)])
        proc.stdin.write('\\.\nCOPY raw_duck.recovered_occurrences_20260920 FROM STDIN WITH (FORMAT CSV);\n')
        for r in rows:
            for identity in r['occurrence_ids']:writer.writerow([gen,identity,r['artifact_id']])
        proc.stdin.write('\\.\nCOPY raw_duck.recovery_holds_20260920 FROM STDIN WITH (FORMAT CSV);\n')
        for r in holds:writer.writerow([gen,r['artifact_id'],json.dumps(r,ensure_ascii=False)])
        proc.stdin.write('\\.\nCOMMIT;\n');proc.stdin.close()
        if proc.wait(timeout=120):raise RuntimeError('Recovery publication failed; inspect receipt')
    counts=list(pg.rows("SELECT recovery_stage_status,count(*) AS items FROM catalog_reconcile.effective_recovery_worklist GROUP BY 1 ORDER BY 1"))
    actual=list(pg.rows('SELECT count(*) AS artifacts,sum(size) AS bytes FROM catalog_reconcile.recovered_artifacts'))[0]
    if actual['artifacts']!=len(rows) or actual['bytes']!=sum(r['size'] for r in rows):raise ValueError('Live recovery count mismatch')
    save_json(root/'published.json',{'generation_id':gen,'status':'verified_recovery_published','independent_local_hash_readback':True,
                                   'live_artifacts':actual,'work_stages':counts,'held_artifacts':len(holds),
                                   'held_occurrences':sum(len(r['occurrence_ids']) for r in holds)})
    emit('recovery_publication_verified',artifacts=actual,work_stages=counts)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--batch',required=True);publish(p.parse_args().batch)
