"""Byline: Codex | 2026-09-20. Exact message-multiset comparison; no source mutation."""
import collections
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path
from defusedxml import ElementTree
from io_utils import write_records, records, sha256_file
from run import save_json, now

BASE=Path('docs/receipts/source-recovery-2026-09-20')
OUT=BASE/'native-backup-containment-01'
EXE='C:/Users/matts/scoop/apps/rclone/current/rclone.exe'

class HashedReader:
    def __init__(self, stream):
        self.stream=stream;self.size=0;self.md5=hashlib.md5();self.sha256=hashlib.sha256()
    def read(self,n=-1):
        data=self.stream.read(n);self.size+=len(data);self.md5.update(data);self.sha256.update(data);return data

def canonical(element):
    attrs=dict(element.attrib)
    value=attrs.get('data')
    if value not in (None,'','null'):
        raw=value.encode('utf-8')
        attrs['data']={'encoding':'base64-attribute-utf8','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    return {'tag':element.tag,'attributes':attrs,'text':element.text if element.text and element.text.strip() else None,
            'children':[canonical(child) for child in element]}

def fingerprint(record):
    return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def scan(source, name, expected_md5, expected_size, metadata, remote=False):
    folder=OUT/name;folder.mkdir()
    if remote:
        before=subprocess.run([EXE,'lsjson',source,'--stat','--metadata','--hash'],capture_output=True,timeout=90)
        if before.returncode:raise RuntimeError('Source metadata unavailable')
        live_before=json.loads(before.stdout)
        proc=subprocess.Popen([EXE,'cat',source,'--contimeout','15s','--timeout','90s','--retries','1','--low-level-retries','1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stream=proc.stdout
    else:stream=Path(source).open('rb');live_before=None;proc=None
    reader=HashedReader(stream);root=None;root_attributes={};count=collections.Counter();failure=None;items=[]
    try:
        for event,element in ElementTree.iterparse(reader,events=('start','end')):
            if root is None and event=='start':root=element;root_attributes=dict(element.attrib)
            if event=='end' and element.tag in ('sms','mms'):
                node=canonical(element);items.append({'ordinal':len(items),'kind':element.tag,'fingerprint':fingerprint(node),'record':node})
                count[element.tag]+=1;element.clear();root.clear()
    except ElementTree.ParseError as exc:failure={'type':'ParseError','position':exc.position,'message':str(exc)}
    # Finish hashing the unchanged source even if XML parsing failed early.
    while reader.read(4*1024*1024):pass
    stream.close()
    if proc:
        error=proc.stderr.read();exit_code=proc.wait();proc.stderr.close()
        (folder/'transfer.log').write_bytes(error)
        if exit_code:raise RuntimeError('Read-only source stream failed')
        after=subprocess.run([EXE,'lsjson',source,'--stat','--metadata','--hash'],capture_output=True,timeout=90)
        live_after=json.loads(after.stdout) if after.returncode==0 else None
    else:live_after=None
    source_hash_verified=reader.size==expected_size and reader.md5.hexdigest()==expected_md5
    if not source_hash_verified:raise ValueError('Source identity changed')
    digest=reader.sha256.hexdigest()
    for row in items:row['backup_sha256']=digest
    write_records(folder/'messages.parquet',items)
    assessment={'name':name,'source':source,'source_metadata':metadata,'live_metadata_before':live_before,'live_metadata_after':live_after,
                'metadata_stable':live_before==live_after,'observed_at':now(),'size':reader.size,'md5':reader.md5.hexdigest(),'sha256':digest,
                'root_attributes':root_attributes,'counts':dict(count),'parse_error':failure,'declared_count_matches':len(items)==int(root_attributes.get('count',-1)),
                'message_fingerprints_sha256':sha256_file(folder/'messages.parquet'),'comparison_contract':'exact-tree-attributes-base64-sha256-v1',
                'scope':'All SMS/MMS attributes and nested part/address records; formatting-only inter-element whitespace ignored; backup-level metadata retained separately'}
    save_json(folder/'assessment.json',assessment)
    print(json.dumps({'backup':name,'counts':dict(count),'parse_error':failure,'declared_count_matches':assessment['declared_count_matches']}),flush=True)
    return assessment

def compare(old,new,old_counts,new_counts):
    missing=old_counts-new_counts
    eligible=all(x['parse_error'] is None and x['declared_count_matches'] and x['metadata_stable'] for x in (old,new))
    return {'older':old['name'],'retained':new['name'],'older_sha256':old['sha256'],'retained_sha256':new['sha256'],
            'older_message_count':sum(old_counts.values()),'retained_message_count':sum(new_counts.values()),
            'missing_record_instances':sum(missing.values()),'missing_fingerprints':dict(missing),
            'status':'skip_additional_binary_copy_proven_record_subset' if eligible and not missing else 'retain_separately_unproven_subset',
            'backup_metadata_retained':True,'retirement_status':'not_cleared','boundary':'Containment does not prove device-wide completeness; retained backup attachment gaps remain open.'}

def main():
    OUT.mkdir(exist_ok=False)
    current=json.loads((BASE/'native-r2-december-recovery/assessment.json').read_text(encoding='utf-8'))
    retained=scan(current['local_path'],'december-06',current['md5'],current['size'],current)
    selected=[]
    for index in (21,22,23):
        sample=json.loads((BASE/f'native-r2-01/samples/{index:03d}/result.json').read_text(encoding='utf-8'));r=sample['catalog']
        selected.append(('r2:'+r['bucket']+'/'+r['path'],r['name'].removesuffix('.xml'),r['md5'],r['size'],sample))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        older=list(pool.map(lambda args:scan(*args,remote=True),selected))
    base=collections.Counter(r['fingerprint'] for r in records(OUT/'december-06/messages.parquet'))
    results=[compare(a,retained,collections.Counter(r['fingerprint'] for r in records(OUT/a['name']/'messages.parquet')),base) for a in older]
    save_json(OUT/'containment.json',{'completed_at':now(),'retained':retained,'older':older,'comparisons':results})
    print(json.dumps({'comparisons':[{k:r[k] for k in ('older','older_message_count','retained_message_count','missing_record_instances','status')} for r in results]}),flush=True)

if __name__=='__main__':main()
