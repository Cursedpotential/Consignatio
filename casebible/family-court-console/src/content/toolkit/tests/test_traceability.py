import subprocess,sys
from conftest import ROOT
def test_traceability_has_no_orphans():
 r=subprocess.run([sys.executable,str(ROOT/'scripts/traceability_check.py'),str(ROOT)],capture_output=True,text=True)
 assert r.returncode==0, r.stdout+r.stderr
 assert '"ok": true' in r.stdout
