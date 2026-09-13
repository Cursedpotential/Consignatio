#!/usr/bin/env python3
"""Flag likely PII in text; never creates a redacted file."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from _common import banner, write_json
LIMITS=['Detection is best-effort and will miss information or flag harmless text.','Never outputs a redacted file. Image/PDF layers require human visual verification; overlay-only redaction can be reversed.','Does not decide what current court rules require.']
PATS={'possible_ssn':r'\b\d{3}-\d{2}-\d{4}\b','possible_account':r'\b(?:\d[ -]?){9,18}\d\b','possible_dob':r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b','possible_driver_license':r'\b[A-Z]\d{12}\b','possible_address':r'\b\d{1,5}\s+[A-Za-z0-9 .-]+\s(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b'}
def main():
 p=argparse.ArgumentParser();p.add_argument('input_text');p.add_argument('--output');p.add_argument('--dry-run',action='store_true');a=p.parse_args();print(banner('redaction_helper.py',LIMITS));text=Path(a.input_text).read_text(encoding='utf-8',errors='replace')
 flags=[]
 for label,pat in PATS.items():
  for m in re.finditer(pat,text,re.I): flags.append({'type':label,'start':m.start(),'end':m.end(),'preview':'[flagged '+label+']'})
 # Conservative minor-name cue only; do not call it a determination.
 for m in re.finditer(r'\b(?:minor|child)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',text):flags.append({'type':'possible_minor_full_name','start':m.start(1),'end':m.end(1),'preview':'[flagged possible minor name]'})
 out={'tool':'redaction_helper.py','limitations':LIMITS,'dry_run':a.dry_run,'flags':flags,'human_verification_required':True,'redacted_file_created':False};write_json(a.output,out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
