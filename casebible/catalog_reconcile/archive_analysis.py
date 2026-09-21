"""Byline: Codex | 2026-09-20. Preserve generated analysis, schemas and source references."""
import datetime
import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from io_utils import Postgres, write_records, sha256_file
from run import save_json, now

REPO=Path.cwd().resolve()
OUT=REPO/'docs/receipts/source-recovery-2026-09-20/native-platform-archive-01'
TABLES=['recovered_artifacts_20260920','recovered_occurrences_20260920','recovery_holds_20260920',
        'evidence_quality_20260920','missing_message_payloads_20260920','backup_manifests_20260920',
        'backup_message_records_20260920','backup_message_occurrences_20260920','backup_containment_20260920',
        'r2_candidate_preservation_20260920']

def main():
    if REPO.drive.upper()!='E:':raise ValueError('E drive required')
    OUT.mkdir(exist_ok=False);snapshot=OUT/'snapshot';snapshot.mkdir();pg=Postgres();exports={}
    for table in TABLES:
        n=write_records(snapshot/(table+'.parquet'),pg.rows('SELECT * FROM raw_duck.'+table));exports[table]=n
    names=','.join("'"+s+"'" for s in TABLES)
    write_records(snapshot/'columns.parquet',pg.rows("SELECT * FROM information_schema.columns WHERE table_schema='raw_duck' AND table_name IN ("+names+") ORDER BY table_name,ordinal_position"))
    write_records(snapshot/'constraints.parquet',pg.rows("SELECT c.relname AS table_name,con.conname,pg_get_constraintdef(con.oid,true) AS definition FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='raw_duck' AND c.relname IN ("+names+") ORDER BY c.relname,con.conname"))
    write_records(snapshot/'views.parquet',pg.rows("SELECT schemaname,viewname,definition FROM pg_views WHERE schemaname='catalog_reconcile' ORDER BY viewname"))
    write_records(snapshot/'extensions.parquet',pg.rows("SELECT extname,extversion FROM pg_extension WHERE extname IN ('pg_duckdb','plpgsql')"))
    shutil.copyfile(REPO/'docs/URGENT-TODO.md',snapshot/'URGENT-TODO-snapshot.md')
    roots=[REPO/'docs/receipts/catalog-reconciliation-2026-09-20',REPO/'docs/receipts/source-recovery-2026-09-20',REPO/'casebible/catalog_reconcile']
    paths=[];excluded=[]
    for root in roots:
        for path in root.rglob('*'):
            if not path.is_file() or path.is_relative_to(OUT):continue
            if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Artifact link leaves owned root')
            rel=path.relative_to(REPO).as_posix()
            historical='/batch-01/files/' in rel and path.name not in ('receipt.json','provenance.json')
            acquired_xml=path.suffix.lower()=='.xml' and any(s in rel for s in ('/native-calls-01/','/native-sms-01/','/native-r2-december-recovery/'))
            if historical or acquired_xml:
                entry={'path':rel,'size':path.stat().st_size,'reason':'Unchanged acquisition mirror; original B2 bytes/version references retained in companion receipts'}
                receipt=path.parent/'receipt.json'
                if receipt.exists():
                    r=json.loads(receipt.read_text(encoding='utf-8'));entry.update(sha256=r.get('sha256'),source_version_id=r.get('source_version_id'),receipt_path=receipt.relative_to(REPO).as_posix())
                else:entry['sha256']=sha256_file(path);entry['receipt_directory']=path.parent.relative_to(REPO).as_posix()
                excluded.append(entry);continue
            if '__pycache__' in path.parts:continue
            paths.append(path)
    paths.extend(p for p in snapshot.iterdir() if p.is_file())
    files=[{'path':p.relative_to(REPO).as_posix(),'size':p.stat().st_size,'sha256':sha256_file(p),'mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()} for p in sorted(paths)]
    inventory={'created_at':now(),'files':files,'original_binary_mirrors_referenced_not_duplicated':excluded,'postgres_exports':exports,
               'scope':'Generated analysis artifacts, private source observations, samples, code, receipts, failed attempts and reusable platform tables. Credentials/config files outside these owned roots are not included.',
               'limitations':['Source-system authenticity and court admissibility are not established by this archive','A held executable unavailable locally remains represented by its existing acquisition/source-version receipt']}
    save_json(OUT/'artifact-inventory.json',inventory)
    archive=OUT/'analysis-artifacts.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=3) as tar:
        for path in sorted(paths):tar.add(path,arcname=path.relative_to(REPO).as_posix(),recursive=False)
        tar.add(OUT/'artifact-inventory.json',arcname='preservation/artifact-inventory.json',recursive=False)
    expected={r['path']:r for r in files};expected['preservation/artifact-inventory.json']={'sha256':sha256_file(OUT/'artifact-inventory.json'),'size':(OUT/'artifact-inventory.json').stat().st_size}
    verified=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            if member.name in verified or member.name not in expected or not member.isfile():raise ValueError('Unexpected or duplicated archive member')
            h=hashlib.sha256();n=0
            with tar.extractfile(member) as stream:
                for b in iter(lambda:stream.read(1024*1024),b''):h.update(b);n+=len(b)
            if h.hexdigest()!=expected[member.name]['sha256'] or n!=expected[member.name]['size']:raise ValueError('Artifact changed during snapshot')
            verified.add(member.name)
    assert verified==set(expected)
    save_json(OUT/'archive-verified.json',{'verified_at':now(),'archive_sha256':sha256_file(archive),'archive_bytes':archive.stat().st_size,
              'member_files':len(verified),'source_mirrors_referenced':len(excluded),'all_member_hashes_verified':True,'postgres_exports':exports})
    print((OUT/'archive-verified.json').read_text(),flush=True)

if __name__=='__main__':main()
