"""Byline: Codex | 2026-09-20. Bounded source-binary and occurrence-metadata assessment."""
import configparser, hashlib, json, urllib.parse, urllib.request
from pathlib import Path
from io_utils import Postgres, B2, sha256_file
from probe_google import request_json, FIELDS
from run import save_json, now
from defusedxml import ElementTree

ROOT=Path('docs/receipts/source-recovery-2026-09-20/native-calls-01')
SHA1='92aa22d7f611dd5162332296e85293ae784e0e94'
SHA256='0091b447820470f6531be2bc54600d4c360c39dbd6bdc772f3c1c121b300d302'
SIZE=175073
CONFIG=Path.home()/'scoop/apps/rclone/current/rclone.conf'

def download(request,path):
    with urllib.request.urlopen(request,timeout=60) as response:
        data=response.read(SIZE+1)
        headers={k:v for k,v in response.headers.items() if k.lower() in ('content-type','content-length','last-modified','etag') or k.lower().startswith('x-bz-')}
    if len(data)!=SIZE or hashlib.sha1(data).hexdigest()!=SHA1 or hashlib.sha256(data).hexdigest()!=SHA256:
        raise ValueError('Source bytes differ from catalog identity; preserve separate follow-up required')
    with path.open('xb') as stream:stream.write(data)
    if sha256_file(path)!=SHA256:raise ValueError('Independent disk readback mismatch')
    return {'path':str(path.resolve()),'size':len(data),'sha1':SHA1,'sha256':SHA256,'response_metadata':headers,'observed_at':now()}

def main():
    if ROOT.resolve().drive.upper()!='E:':raise ValueError('E drive required')
    ROOT.mkdir(parents=True,exist_ok=False)
    pg=Postgres()
    rows=[r['payload'] for r in pg.rows("SELECT payload FROM raw_duck.reconcile_occurrences_20260920 WHERE generation_id='2c2ae40f-bc6a-43c6-83a7-f3d60319e4d3' AND payload->'source_record'->>'sha1'='"+SHA1+"' LIMIT 20")]
    if len(rows)!=3:raise ValueError('Expected exactly three recorded occurrences')
    save_json(ROOT/'catalog-occurrences.json',{'records':rows,'captured_at':now()})
    cfg=configparser.ConfigParser(interpolation=None);cfg.read(CONFIG)
    remote=cfg['gd_salemnet'];token=json.loads(remote['token'])
    fresh,error=request_json(urllib.request.Request('https://oauth2.googleapis.com/token',data=urllib.parse.urlencode({'client_id':remote['client_id'],'client_secret':remote['client_secret'],'refresh_token':token['refresh_token'],'grant_type':'refresh_token'}).encode()))
    if error:raise RuntimeError('Google authentication unavailable')
    auth={'Authorization':'Bearer '+fresh['access_token'],'Accept-Encoding':'identity'}
    results=[]
    for row in rows:
        source=row['source_record']
        if source['source']!='gdrive/salemnet':continue
        fid=source['source_id'];base='https://www.googleapis.com/drive/v3/files/'+urllib.parse.quote(fid,safe='')
        meta,error=request_json(urllib.request.Request(base+'?'+urllib.parse.urlencode({'fields':FIELDS,'supportsAllDrives':'true'}),headers=auth))
        if error:raise RuntimeError('Google source metadata unavailable')
        meta.pop('exportLinks',None)
        save_json(ROOT/(fid+'-metadata-before.json'),{'source_id':fid,'metadata':meta,'observed_at':now()})
        if meta.get('trashed') or int(meta.get('size',-1))!=SIZE or meta.get('sha256Checksum')!=SHA256:raise ValueError('Live metadata identity differs')
        binary=download(urllib.request.Request(base+'?alt=media&supportsAllDrives=true',headers=auth),ROOT/(fid+'.xml'))
        after,error=request_json(urllib.request.Request(base+'?'+urllib.parse.urlencode({'fields':'id,version,size,md5Checksum,sha1Checksum,sha256Checksum,modifiedTime','supportsAllDrives':'true'}),headers=auth))
        if error or any(after.get(k)!=meta.get(k) for k in after):raise ValueError('Source changed across acquisition')
        save_json(ROOT/(fid+'-metadata-after.json'),{'metadata':after,'observed_at':now()})
        results.append({'occurrence_id':row['occurrence_id'],'source_id':fid,'source':'gdrive/salemnet','metadata':meta,'binary':binary})
    b2=B2(CONFIG);vid=rows[0]['version_ids'][0]
    version=list(pg.rows("SELECT payload FROM raw_duck.reconcile_objects_20260920 WHERE generation_id='2c2ae40f-bc6a-43c6-83a7-f3d60319e4d3' AND id='"+vid+"'"))[0]['payload']
    binary=download(urllib.request.Request(b2.auth['downloadUrl']+'/b2api/v4/b2_download_file_by_id?'+urllib.parse.urlencode({'fileId':vid}),headers={'Authorization':b2.auth['authorizationToken'],'Accept-Encoding':'identity'}),ROOT/'b2-retained.xml')
    if binary['response_metadata'].get('X-Bz-File-Id',binary['response_metadata'].get('x-bz-file-id'))!=vid:raise ValueError('B2 version differs')
    tree=ElementTree.parse(ROOT/'b2-retained.xml');root=tree.getroot();children=list(root)
    xml={'root':root.tag,'root_attributes':root.attrib,'record_count':len(children),'child_tags':sorted({x.tag for x in children}),'attribute_names':sorted({k for x in children for k in x.attrib}),'declared_count_matches':str(len(children))==root.get('count')}
    save_json(ROOT/'assessment.json',{'observed_at':now(),'sources':results,'b2_version':version,'b2_binary':binary,'xml_structure':xml,'onedrive_status':'catalog_metadata_only_not_live_verified','bas_status':'candidate_pending_package_and_source_device_completeness','retirement_status':'not_cleared','boundary':'Matching bytes and well-formed backup do not prove completeness against the source device or authenticity of individual call records.'})
    print(json.dumps({'verified_binaries':len(results)+1,'size_each':SIZE,'sha256':SHA256,'xml_structure':xml,'source_properties':[{ 'id':r['source_id'],'properties':r['metadata'].get('properties'),'appProperties':r['metadata'].get('appProperties')} for r in results]},ensure_ascii=True))

if __name__=='__main__':main()
