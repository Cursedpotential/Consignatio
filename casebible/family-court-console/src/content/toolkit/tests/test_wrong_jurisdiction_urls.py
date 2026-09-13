from conftest import ledger,ROOT

def test_no_florida_circuit7_source_is_accepted_as_genesee_authority():
 for r in ledger():
  urls=[r['official_url']]+r['alternate_urls']
  if any(u and 'circuit7.org' in u for u in urls):
   assert r['id']=='trap-florida-circuit7'
   assert 'florida' in r['jurisdiction'].lower()

def test_skill_warns_about_wrong_court_domain():
 s=(ROOT/'SKILL.md').read_text();assert 'circuit7.org' in s and 'Florida' in s
