"""Byline: Codex | 2026-09-20. Explicit recovery of catalog-proven historical B2 bytes."""
import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from core import stable_id
from io_utils import B2, Postgres, records, sha256_file, write_records
from run import save_json, now, emit

GENERATION='2c2ae40f-bc6a-43c6-83a7-f3d60319e4d3'
FILTER=f"generation_id='{GENERATION}' AND payload->>'state'='historical_exact'"


def safe_name(key):
    name=re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', key.rsplit('/',1)[-1]).rstrip(' .')[:140]
    if not name or re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',name):name='recovered_'+name
    return name


def plan(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    pg=Postgres()
    links=[r['record'] for r in pg.rows(f'SELECT payload AS record FROM raw_duck.reconcile_occurrences_20260920 WHERE {FILTER}')]
    versions={r['record']['file_id']:r['record'] for r in pg.rows(f"SELECT b.payload AS record FROM raw_duck.reconcile_objects_20260920 b JOIN (SELECT DISTINCT jsonb_array_elements_text(payload->'version_ids') AS id FROM raw_duck.reconcile_occurrences_20260920 WHERE {FILTER}) x ON b.id=x.id WHERE b.generation_id='{GENERATION}'")}
    groups={}
    for row in links:
        source=row['source_record'];identity=(source['sha1'],int(source['size']))
        group=groups.setdefault(identity,{'occurrences':[],'ids':set(),'keys':collections.Counter()})
        group['occurrences'].append(row);group['ids'].update(row['version_ids']);group['keys'][source.get('vault_key')]+=1
    items=[]
    for (sha,size),group in sorted(groups.items()):
        candidates=[versions[i] for i in group['ids']]
        if any(v['sha1']!=sha or v['size']!=size or v['action']!='upload' or v['visible'] for v in candidates):raise ValueError('Historical recovery identity invariant failed')
        # Transport selection only; all alternate occurrence/version metadata is retained.
        selected=sorted(candidates,key=lambda v:(-group['keys'][v['key']],v['file_id']))[0]
        identity=stable_id('recovered_historical',sha,size)
        items.append({'artifact_id':identity,'sha1':sha,'size':size,'selected_version':selected,
                      'all_supported_versions':candidates,'occurrences':group['occurrences'],
                      'relative_path':'files/'+identity+'/'+safe_name(selected['key']),
                      'selection_basis':'recorded-path linkage, then stable ID; not a BAS decision'})
    total=sum(r['size'] for r in items)
    if not items or len(items)>400 or total>250_000_000:raise ValueError('Recovery exceeds this approved bounded batch')
    n=write_records(root/'plan.parquet',items)
    save_json(root/'plan.json',{'generation_id':GENERATION,'planned_at':now(),'identities':n,'occurrences':len(links),'bytes':total,
              'plan_sha256':sha256_file(root/'plan.parquet'),'source_mutations':0,'purpose':'Recover byte-verified historical copies; retain all occurrence metadata'})
    emit('recovery_planned',identities=n,occurrences=len(links),bytes=total)


def verify_headers(headers,item):
    if headers.get('X-Bz-File-Id')!=item['selected_version']['file_id']:raise ValueError('Response version ID differs')
    if int(headers.get('Content-Length','-1'))!=item['size']:raise ValueError('Response size differs')
    if (headers.get('X-Bz-Content-Sha1') or '').lower()!=item['sha1']:raise ValueError('Response SHA-1 differs')


def recover(root,config):
    root=Path(root).resolve()
    if root.drive.upper()!='E:':raise ValueError('Recovery output must stay on E:')
    meta=json.loads((root/'plan.json').read_text(encoding='utf-8'))
    if sha256_file(root/'plan.parquet')!=meta['plan_sha256']:raise ValueError('Recovery plan changed')
    items=list(records(root/'plan.parquet'))
    if (root/'recovered.json').exists() or (root/'started.json').exists():raise FileExistsError('Recovery already attempted; preserve it and create an explicit retry batch')
    if len(items)!=meta['identities'] or sum(r['size'] for r in items)!=meta['bytes']:raise ValueError('Recovery plan conservation failed')
    b2=B2(config)
    save_json(root/'started.json',{'started_at':now(),'generation_id':GENERATION,'plan_sha256':meta['plan_sha256'],'source_mutations':0})
    def one(item):
        target=root/item['relative_path']
        if not target.resolve().is_relative_to(root):raise ValueError('Recovery path escapes batch')
        target.parent.mkdir(parents=True,exist_ok=False)
        partial=target.with_name(target.name+'.partial')
        result={'artifact_id':item['artifact_id'],'source_version_id':item['selected_version']['file_id'],
                'source_key':item['selected_version']['key'],'expected_sha1':item['sha1'],'expected_size':item['size'],
                'occurrence_ids':[r['occurrence_id'] for r in item['occurrences']],
                'bas_status':'not_assessed','retirement_status':'not_cleared','started_at':now()}
        h1=hashlib.sha1();h256=hashlib.sha256();size=0
        try:
            url=b2.auth['downloadUrl']+'/b2api/v4/b2_download_file_by_id?'+urllib.parse.urlencode({'fileId':item['selected_version']['file_id']})
            request=urllib.request.Request(url,headers={'Authorization':b2.auth['authorizationToken'],'Accept-Encoding':'identity'})
            with urllib.request.urlopen(request,timeout=120) as response:
                if response.status!=200:raise ValueError('Expected complete-file response')
                verify_headers(response.headers,item)
                result['response_metadata']={k:v for k,v in response.headers.items() if k.lower().startswith('x-bz-') or k.lower() in ('content-type','content-length','content-disposition','content-encoding')}
                with partial.open('xb') as stream:
                    for block in iter(lambda:response.read(1024*1024),b''):
                        size+=len(block)
                        if size>item['size']:raise ValueError('Download exceeds planned size')
                        h1.update(block);h256.update(block);stream.write(block)
                    stream.flush();os.fsync(stream.fileno())
            if size!=item['size'] or h1.hexdigest()!=item['sha1']:raise ValueError('Recovered bytes do not match expected identity')
            if target.exists():raise FileExistsError('Recovery destination already exists')
            partial.rename(target)
            result.update(status='recovered_verified',local_path=str(target),size=size,sha1=h1.hexdigest(),sha256=h256.hexdigest())
        except Exception as exc:
            result.update(status='recovery_failed',error_type=type(exc).__name__,http_status=getattr(exc,'code',None),received_bytes=size)
        result['ended_at']=now()
        save_json(target.parent/'receipt.json',result)
        save_json(target.parent/'provenance.json',item)
        return result
    outcomes=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(one,item):item for item in items}
        for future in concurrent.futures.as_completed(futures):
            outcomes.append(future.result())
            if len(outcomes)%25==0:emit('recovery_progress',completed=len(outcomes),verified=sum(r['status']=='recovered_verified' for r in outcomes))
    write_records(root/'recovered.parquet',sorted(outcomes,key=lambda r:r['artifact_id']))
    good=[r for r in outcomes if r['status']=='recovered_verified']
    save_json(root/'recovered.json',{'generation_id':GENERATION,'ended_at':now(),'planned':len(items),'verified':len(good),
              'failed':len(outcomes)-len(good),'verified_bytes':sum(r['size'] for r in good),
              'verified_occurrences':sum(len(r['occurrence_ids']) for r in good),'source_mutations':0,'r2_retirements':0,
              'results_sha256':sha256_file(root/'recovered.parquet')})
    emit('recovery_complete',verified=len(good),failed=len(outcomes)-len(good),verified_bytes=sum(r['size'] for r in good))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=('plan','recover'));p.add_argument('--batch',required=True)
    p.add_argument('--config',default=str(Path.home()/'scoop/apps/rclone/current/rclone.conf'));a=p.parse_args()
    plan(a.batch) if a.operation=='plan' else recover(a.batch,a.config)
