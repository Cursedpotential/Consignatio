#!/usr/bin/env python3
"""Create a read-only exhibit index and hashes after possession representation."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from _common import banner, write_json
LIMITS=['Does not assess admissibility, legality, authenticity, or privilege.','Does not alter originals; it only reads selected files.','Refuses processing absent the user representation that they are entitled to possess the files.']
def h(p):
 x=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):x.update(b)
 return x.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('paths',nargs='*');p.add_argument('--authorized-possessor',required=True);p.add_argument('--output');p.add_argument('--dry-run',action='store_true');a=p.parse_args();print(banner('exhibit_indexer.py',LIMITS))
 if a.authorized_possessor.strip().upper()!='YES': raise SystemExit('REFUSED: pass --authorized-possessor YES only if entitled to possess every file.')
 rows=[]; seen={}
 for i,s in enumerate(a.paths,1):
  f=Path(s); digest=None if a.dry_run else h(f); duplicate=seen.get(digest) if digest else None
  if digest:seen[digest]=f.name
  rows.append({'exhibit_number':i,'file_name':f.name,'path':str(f),'sha256':digest,'duplicate_of':duplicate,'foundation_checklist':['lawful possession represented','relevance/purpose','knowledge witness','authentication','hearsay path','privilege/confidentiality','redaction','native/original retained']})
 out={'tool':'exhibit_indexer.py','limitations':LIMITS,'dry_run':a.dry_run,'exhibits':rows};write_json(a.output,out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
