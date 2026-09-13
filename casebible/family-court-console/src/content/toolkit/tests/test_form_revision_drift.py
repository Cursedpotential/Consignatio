from conftest import ROOT,ledger

def test_objection_module_flags_local_packet_version_risk():
 p=ROOT/'references/genesee/objection-to-referee-recommendation.md';t=p.read_text().lower();assert 'form' in t and 'verify' in t and 'packet' in t

def test_form_source_has_revision_watch_trigger():
 rows=ledger();r=[x for x in rows if x['id']=='guidance-scao-forms'][0]
 triggers=' '.join(r['watch_triggers']) if isinstance(r['watch_triggers'],list) else r['watch_triggers']
 assert 'form' in triggers.lower()
