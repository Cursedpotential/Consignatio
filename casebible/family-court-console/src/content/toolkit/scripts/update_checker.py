#!/usr/bin/env python3
"""Run URL checks and flag manifest staleness without modifying package sources."""
from __future__ import annotations
import argparse, datetime as dt, json, subprocess, sys
from pathlib import Path
from _common import banner, write_json
LIMITS=['Cannot detect unpublished local-practice changes and cannot replace calling the clerk.','Uses public URL reads only; no login, account access, or network writes.']
def main():
 p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default='.');p.add_argument('--output');p.add_argument('--dry-run',action='store_true');a=p.parse_args();root=Path(a.root);print(banner('update_checker.py',LIMITS))
 m=json.loads((root/'manifest.json').read_text()) if (root/'manifest.json').exists() else {}; expiry=m.get('expiry_date');expired=bool(expiry and dt.date.today().isoformat()>expiry)
 cmd=[sys.executable,str(root/'scripts/citation_url_checker.py'),str(root/'ledger.json'),'--dry-run'] if a.dry_run else [sys.executable,str(root/'scripts/citation_url_checker.py'),str(root/'ledger.json')]
 run=subprocess.run(cmd,capture_output=True,text=True);out={'tool':'update_checker.py','limitations':LIMITS,'dry_run':a.dry_run,'manifest_expiry_date':expiry,'expired':expired,'url_checker_exit_code':run.returncode,'url_checker_output':run.stdout,'stale_after_behavior':'Stop substantive use and re-verify official sources, forms, local orders, roster, and clerk instructions.'};write_json(a.output,out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
