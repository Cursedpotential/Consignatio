from conftest import ledger
def test_superseded_authorities_are_labeled():
 rows=ledger(); local=[r for r in rows if r['id']=='genesee-local-administrative-orders'][0]
 assert local['superseded']=='partial' and local['supersedes']
def test_no_known_superseded_source_claimed_current():
 for r in ledger():
  if r['superseded']=='yes': assert r['superseding_authority'] not in ('',None,'unknown — verification required')
