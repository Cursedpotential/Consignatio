#!/usr/bin/env python3
"""Read-only URL status checker; respects ordinary HTTP failures and does not evade blocks."""
from __future__ import annotations
import argparse, hashlib, html, json, re, sys, urllib.error, urllib.request
from pathlib import Path
from _common import banner, write_json
LIMITS=['Cannot judge legal correctness or currentness from a 200 response.','Cannot see paywalled/login content and marks blocked/failed requests; it does not bypass robots, CDNs, or access controls.']
def title_from(data):
    text=data.decode('utf-8','replace')[:200000]
    m=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S)
    return html.unescape(re.sub(r'\s+',' ',m.group(1))).strip() if m else None
def fetch(url, timeout):
    req=urllib.request.Request(url,headers={'User-Agent':'GeneseeToolkitURLCheck/1.0 (+read-only)'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            data=r.read(2_000_000); final=r.geturl(); status=getattr(r,'status',200)
            return {'url':url,'status':status,'final_url':final,'redirected':final!=url,'title':title_from(data),'content_hash':hashlib.sha256(data).hexdigest(),'error':None}
    except urllib.error.HTTPError as e:
        return {'url':url,'status':e.code,'final_url':url,'redirected':False,'title':None,'content_hash':None,'error':'http_error'}
    except Exception as e:
        label='blocked' if any(x in str(e).lower() for x in ['robot','forbidden','403']) else type(e).__name__
        return {'url':url,'status':None,'final_url':url,'redirected':False,'title':None,'content_hash':None,'error':label}
def main():
 p=argparse.ArgumentParser(description='Check ledger URLs without modifying sources.');p.add_argument('ledger',nargs='?',default='ledger.json');p.add_argument('--output');p.add_argument('--timeout',type=int,default=12);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
 print(banner('citation_url_checker.py',LIMITS))
 records=json.loads(Path(a.ledger).read_text())
 results=[]; cache={}
 for rec in records:
  urls=[]
  for u in [rec.get('official_url')]+(rec.get('alternate_urls') or []):
   if u and u not in urls: urls.append(u)
  for url in urls:
   if a.dry_run:
    r={'source_id':rec['id'],'url':url,'planned':True}
   else:
    used_cache=url in cache
    if not used_cache: cache[url]=fetch(url,a.timeout)
    r=dict(cache[url]); r['cache_reused']=used_cache
   if not a.dry_run:
    r['source_id']=rec['id']; r['changed_since_last_verified']=bool(rec.get('content_hash') not in [None,'','not retained; run scripts/citation_url_checker.py'] and r.get('content_hash')!=rec.get('content_hash'))
   results.append(r)
 output={'tool':'citation_url_checker.py','limitations':LIMITS,'dry_run':a.dry_run,'results':results}
 write_json(a.output,output); print(json.dumps(output,indent=2))
if __name__=='__main__': main()
