from pathlib import Path
import json, yaml
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=['id','title','short_title','issuing_body','document_number','citation','authority_class','binding_status','jurisdiction','scope_note','official_url','alternate_urls','archive_url','publication_date','effective_date','last_amended_or_revised','date_accessed','last_verified','verified_by','verification_method','jurisdiction_confirmed_by','http_status','content_hash','superseded','superseding_authority','supersedes','related_authorities','update_frequency','watch_triggers','access_restrictions','copyright_note','reproduction_permitted','pin_cites','unresolved_issues','confidence']
def split(p):
 s=p.read_text(encoding='utf-8'); assert s.startswith('---\n'), p
 e=s.find('\n---\n',4); assert e>4,p
 return yaml.safe_load(s[4:e]),s[e+5:]
def docs():
 return [p for p in ROOT.rglob('*.md') if p.name not in {'SKILL.md','README.md','CHANGELOG.md','LIMITATIONS.md'}]
def ledger():return json.loads((ROOT/'ledger.json').read_text())
