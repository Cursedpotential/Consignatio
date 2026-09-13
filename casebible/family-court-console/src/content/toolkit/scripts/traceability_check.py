#!/usr/bin/env python3
"""Check Markdown source markers against the ledger without changing files."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from _common import banner, write_json
LIMITS=['Checks identifiers and simple bidirectional references, not legal accuracy.','Does not infer unstated legal support or validate a pinpoint against source text.']
PAT=re.compile(r'\[source:\s*([a-z0-9-]+)\s*\|\s*pin:\s*([^\]]+)\]',re.I)
def frontmatter(text):
 if not text.startswith('---\n'): return None
 end=text.find('\n---\n',4)
 return text[4:end] if end>=0 else None
def main():
 p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default='.');p.add_argument('--output');p.add_argument('--dry-run',action='store_true');a=p.parse_args();root=Path(a.root);print(banner('traceability_check.py',LIMITS))
 ledger=json.loads((root/'ledger.json').read_text()); ids={x['id'] for x in ledger}; used={}; errors=[]
 for f in root.rglob('*.md'):
  if f.name in {'README.md','SKILL.md','CHANGELOG.md','LIMITATIONS.md'}:continue
  rel=str(f.relative_to(root));text=f.read_text(encoding='utf-8');fm=frontmatter(text)
  if not fm:errors.append({'file':rel,'error':'missing frontmatter'});continue
  marks=PAT.findall(text)
  if not marks:errors.append({'file':rel,'error':'no traceability marker'})
  for sid,pin in marks:
   used.setdefault(sid,[]).append(rel)
   if sid not in ids:errors.append({'file':rel,'error':'unknown source id','source_id':sid,'pin':pin})
 for rec in ledger:
  deps=set(rec.get('dependent_files') or [])
  actual=set(used.get(rec['id'],[]))
  if actual and not actual.issubset(deps):errors.append({'source_id':rec['id'],'error':'ledger dependent_files missing references','missing':sorted(actual-deps)})
 out={'tool':'traceability_check.py','limitations':LIMITS,'dry_run':a.dry_run,'ok':not errors,'errors':errors,'source_ids_used':len(used),'ledger_source_ids':len(ids)};write_json(a.output,out);print(json.dumps(out,indent=2));raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
