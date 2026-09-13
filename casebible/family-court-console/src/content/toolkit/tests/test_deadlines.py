import json,subprocess,sys
from conftest import ROOT
def run(kind):
 r=subprocess.run([sys.executable,str(ROOT/'scripts/deadline_calculator.py'),'--trigger-date','2026-08-10','--kind',kind],capture_output=True,text=True);assert r.returncode==0
 return json.loads(r.stdout[r.stdout.index('{'):])
def test_referee_candidate_and_warning():
 d=run('referee-objection');assert d['result']['candidate_date']=='2026-08-31';assert 'CONFIRM WITH THE CLERK' in d['result']['warning']
def test_backward_local_motion_candidate():
 d=run('motion-before-hearing');assert d['result']['candidate_date']=='2026-08-03'
