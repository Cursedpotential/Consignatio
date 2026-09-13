#!/usr/bin/env python3
"""Normalize events into a chronology; drafting aid only."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from _common import banner, write_json
LIMITS=['Tagging is a drafting aid, not a legal conclusion.','Does not decide credibility, admissibility, or best-interest findings.','Read-only input; synthetic/sample events should be clearly labeled.']
def main():
 p=argparse.ArgumentParser();p.add_argument('input_json');p.add_argument('--output');p.add_argument('--dry-run',action='store_true');a=p.parse_args();print(banner('chronology_builder.py',LIMITS))
 events=json.loads(Path(a.input_json).read_text()); required=['date','event','source_document']
 normalized=[]
 for i,e in enumerate(events,1):
  missing=[k for k in required if not e.get(k)]
  normalized.append({'sequence':i,'date':e.get('date'),'event':e.get('event'),'source_document':e.get('source_document'),'exhibit_number':e.get('exhibit_number'),'best_interest_factor':e.get('best_interest_factor'),'disputed':bool(e.get('disputed')),'corroboration':e.get('corroboration'),'missing_fields':missing})
 normalized.sort(key=lambda x:(x['date'] or '9999-99-99',x['sequence']))
 dates=[e['date'] for e in normalized if e['date']]; conflicts=[d for d in sorted(set(dates)) if sum(x['date']==d for x in normalized)>1]
 out={'tool':'chronology_builder.py','limitations':LIMITS,'dry_run':a.dry_run,'chronology':normalized,'top_12_trial_narrative':normalized[:12],'same_date_items_to_review':conflicts};write_json(a.output,out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
