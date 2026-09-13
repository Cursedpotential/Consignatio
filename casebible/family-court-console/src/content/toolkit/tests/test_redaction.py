import json,subprocess,sys
from conftest import ROOT
def test_flags_pii_without_creating_redacted_file(tmp_path):
 p=tmp_path/'synthetic.txt';p.write_text('Avery Rowan born 05/01/2018 SSN 123-45-6789 at 22 Oak Street')
 r=subprocess.run([sys.executable,str(ROOT/'scripts/redaction_helper.py'),str(p)],capture_output=True,text=True);assert r.returncode==0
 d=json.loads(r.stdout[r.stdout.index('{'):]);types={x['type'] for x in d['flags']};assert {'possible_ssn','possible_dob','possible_address'}<=types;assert not d['redacted_file_created']
