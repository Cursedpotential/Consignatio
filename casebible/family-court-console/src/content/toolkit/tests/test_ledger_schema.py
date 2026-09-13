from conftest import docs,split,SCHEMA,ledger

def test_every_resource_has_complete_schema_and_url_gate():
 ids=[]
 for p in docs():
  fm,_=split(p); assert set(SCHEMA).issubset(fm),p
  assert fm['id'] and fm['title'] and fm['authority_class'] and fm['binding_status'],p
  assert fm['official_url'] or (fm['alternate_urls'] and fm['unresolved_issues']),p
  ids.append(fm['id'])
 assert len(ids)==len(set(ids))

def test_ledger_has_one_row_per_resource_and_preserves_audit_sources():
 rows=ledger(); resource_rows=[x for x in rows if x.get('file_path')]
 assert len(resource_rows)==len(docs())
 assert {x['file_path'] for x in resource_rows}=={str(p.relative_to(__import__('conftest').ROOT)) for p in docs()}
 assert all(set(SCHEMA).issubset(x) for x in rows)
 audit_rows=[x for x in rows if x.get('source_origin')=='deep-research audit 2026-08-09']
 assert len(audit_rows)==74
 assert all(x.get('source_file')=='references/audit/deep-research-source-ledger-2026-08-09.json' for x in audit_rows)
