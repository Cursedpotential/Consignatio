"""Byline: Codex | 2026-09-20. Bounded, file-ID-only Google metadata probes."""
import argparse
import configparser
import datetime as dt
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from io_utils import records, write_records
from run import save_json

FIELDS='id,name,mimeType,createdTime,modifiedTime,version,trashed,parents,description,owners,size,md5Checksum,sha1Checksum,sha256Checksum,originalFilename,capabilities,imageMediaMetadata,videoMediaMetadata,properties,appProperties,spaces,driveId,headRevisionId,exportLinks'
ACCOUNTS={'gdrive/salemnet':'gd_salemnet','gdrive/salem85':'gd_salem85'}


def request_json(request):
    try:
        with urllib.request.urlopen(request,timeout=30) as response:return json.load(response),None
    except urllib.error.HTTPError as exc:
        # No response bodies, request headers, or credentials are logged.
        return None,{'http_status':exc.code,'state':'access_unavailable' if exc.code in (401,403) else 'not_visible_to_account' if exc.code==404 else 'provider_error'}
    except (urllib.error.URLError,TimeoutError):return None,{'state':'network_unavailable'}


def probe(generation,out,config,per_account=6,oldest=False):
    if not 1<=per_account<=10:raise ValueError('At most 10 native IDs per account')
    root=Path(generation);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    cfg=configparser.ConfigParser(interpolation=None);cfg.read(config)
    selected={source:[] for source in ACCOUNTS}
    source_rows=records(root/'native_export_maps.parquet')
    if oldest:source_rows=sorted(source_rows,key=lambda r:r.get('modtime') or '9999')
    for row in source_rows:
        source=row['source']
        if source in selected and len(selected[source])<per_account:selected[source].append(row)
    results=[];capabilities=[]
    for source,items in selected.items():
        remote=cfg[ACCOUNTS[source]];token=json.loads(remote.get('token','{}'))
        # Refresh in memory. Never persist tokens or rewrite rclone configuration.
        body=urllib.parse.urlencode({'client_id':remote.get('client_id',''),'client_secret':remote.get('client_secret',''),
                                    'refresh_token':token.get('refresh_token',''),'grant_type':'refresh_token'}).encode()
        fresh,error=request_json(urllib.request.Request('https://oauth2.googleapis.com/token',data=body))
        access=fresh.get('access_token') if fresh else None
        capabilities.append({'source':source,'auth_state':'available' if access else 'unavailable',
                             'metadata_scope':'explicit listed file IDs only','permissions_census':'not_requested',
                             'revisions_census':'not_requested','completeness':'partial','error':error})
        for item in items:
            observation={'source':source,'source_id':item['source_id'],'recorded_native_path':item['native_path'],
                         'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'content_read':False,
                         'bas_status':'not_assessed','retirement_status':'not_cleared'}
            if access:
                url='https://www.googleapis.com/drive/v3/files/'+urllib.parse.quote(item['source_id'],safe='')+'?'+urllib.parse.urlencode({'fields':FIELDS,'supportsAllDrives':'true'})
                metadata,error=request_json(urllib.request.Request(url,headers={'Authorization':'Bearer '+access}))
                if metadata:
                    metadata['export_mime_types']=sorted((metadata.pop('exportLinks',{}) or {}).keys())
                    observation.update(state='metadata_observed',metadata=metadata)
                else:observation.update(state=error['state'],error=error)
            else:observation.update(state='authentication_unavailable',error=error)
            results.append(observation)
    write_records(out/'google_metadata.parquet',results)
    summary={'byline':'Codex | 2026-09-20','requests_planned':len(results),'metadata_observed':sum(r['state']=='metadata_observed' for r in results),
             'capabilities':capabilities,'content_reads':0,'source_changes':0,'rclone_config_changes':0}
    save_json(out/'probe.json',summary);print(json.dumps(summary))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--generation',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--config',default=str(Path.home()/'scoop/apps/rclone/current/rclone.conf'))
    parser.add_argument('--oldest',action='store_true')
    args=parser.parse_args();probe(args.generation,args.output,args.config,oldest=args.oldest)
