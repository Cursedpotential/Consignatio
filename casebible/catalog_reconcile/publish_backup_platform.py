"""Byline: Codex | 2026-09-20. Persist reusable message and containment facts."""
import csv
import gzip
import io
import json
import subprocess
from pathlib import Path
from io_utils import Postgres, records, write_records, sha256_file
from run import save_json, now

ROOT=Path('docs/receipts/source-recovery-2026-09-20/native-backup-containment-01')

def main():
    result=json.loads((ROOT/'containment.json').read_text(encoding='utf-8'))
    assessments=[result['retained']]+result['older'];unique={};occurrences=[]
    for assessment in assessments:
        for row in records(ROOT/assessment['name']/'messages.parquet'):
            key=row['fingerprint'];record={'fingerprint':key,'kind':row['kind'],'record':row['record']}
            if key in unique and unique[key]!=record:raise ValueError('Fingerprint collision or record mismatch')
            unique[key]=record;occurrences.append((row['backup_sha256'],row['ordinal'],key))
    write_records(ROOT/'unique-message-records.parquet',unique.values())
    write_records(ROOT/'message-occurrences.parquet',({'backup_sha256':b,'ordinal':i,'fingerprint':f} for b,i,f in occurrences))
    schema="""BEGIN;
SET LOCAL lock_timeout='5s';
CREATE TABLE raw_duck.backup_manifests_20260920 (backup_sha256 text PRIMARY KEY, name text NOT NULL, sms_count bigint NOT NULL, mms_count bigint NOT NULL, payload jsonb NOT NULL);
CREATE TABLE raw_duck.backup_message_records_20260920 (fingerprint text PRIMARY KEY, kind text NOT NULL CHECK(kind IN ('sms','mms')), payload jsonb NOT NULL);
CREATE TABLE raw_duck.backup_message_occurrences_20260920 (backup_sha256 text REFERENCES raw_duck.backup_manifests_20260920, ordinal integer NOT NULL, fingerprint text REFERENCES raw_duck.backup_message_records_20260920, PRIMARY KEY(backup_sha256,ordinal));
CREATE TABLE raw_duck.backup_containment_20260920 (older_sha256 text REFERENCES raw_duck.backup_manifests_20260920, retained_sha256 text REFERENCES raw_duck.backup_manifests_20260920, status text NOT NULL, payload jsonb NOT NULL, PRIMARY KEY(older_sha256,retained_sha256));
"""
    artifact=ROOT/'platform-publication.sql.gz'
    with artifact.open('xb') as binary,gzip.GzipFile(fileobj=binary,mode='wb') as stream:
        stream.write(schema.encode())
        def copy(table,rows):
            stream.write(('COPY raw_duck.'+table+' FROM STDIN WITH (FORMAT CSV);\n').encode())
            for row in rows:
                buf=io.StringIO(newline='');csv.writer(buf,lineterminator='\n').writerow(row);stream.write(buf.getvalue().encode())
            stream.write(b'\\.\n')
        copy('backup_manifests_20260920',((r['sha256'],r['name'],r['counts'].get('sms',0),r['counts'].get('mms',0),json.dumps(r)) for r in assessments))
        copy('backup_message_records_20260920',((f,r['kind'],json.dumps(r['record'])) for f,r in unique.items()))
        copy('backup_message_occurrences_20260920',occurrences)
        copy('backup_containment_20260920',((r['older_sha256'],r['retained_sha256'],r['status'],json.dumps(r)) for r in result['comparisons']))
        for short in ('backup_manifests','backup_message_records','backup_message_occurrences','backup_containment'):
            stream.write(('CREATE VIEW catalog_reconcile.'+short+' AS SELECT * FROM raw_duck.'+short+'_20260920;\n').encode())
        stream.write(b'COMMIT;\n')
    pg=Postgres();proc=subprocess.Popen(pg.command(writable=True),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    with gzip.open(artifact,'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):proc.stdin.write(block)
    proc.stdin.close();output=proc.stdout.read();error=proc.stderr.read()
    if proc.wait():raise RuntimeError(error.decode(errors='replace')[:500])
    count=0
    for row in pg.rows('SELECT fingerprint,kind,payload FROM raw_duck.backup_message_records_20260920'):
        expected=unique[row['fingerprint']];assert row['kind']==expected['kind'] and row['payload']==expected['record'];count+=1
    assert count==len(unique)
    back={(r['backup_sha256'],r['ordinal'],r['fingerprint']) for r in pg.rows('SELECT * FROM raw_duck.backup_message_occurrences_20260920')}
    assert back==set(occurrences)
    assert {r['backup_sha256']:r['payload'] for r in pg.rows('SELECT backup_sha256,payload FROM raw_duck.backup_manifests_20260920')}=={r['sha256']:r for r in assessments}
    assert {r['older_sha256']:r['payload'] for r in pg.rows('SELECT older_sha256,payload FROM raw_duck.backup_containment_20260920')}=={r['older_sha256']:r for r in result['comparisons']}
    save_json(ROOT/'platform-published.json',{'verified_at':now(),'backups':len(assessments),'unique_record_fingerprints':len(unique),'message_occurrences':len(occurrences),'containment_comparisons':len(result['comparisons']),'all_rows_readback_equal':True,'publication_sha256':sha256_file(artifact)})
    print((ROOT/'platform-published.json').read_text())

if __name__=='__main__':main()
