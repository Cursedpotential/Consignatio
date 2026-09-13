from conftest import ROOT
PROHIBITED=['you should file','you will win','the judge will','this is legal advice']
DISCLAIMER='This package is legal **information**, not legal advice.'
def test_no_prohibited_advice_promises():
 for p in ROOT.rglob('*.md'):
  text=p.read_text(encoding='utf-8').lower()
  for phrase in PROHIBITED: assert phrase not in text, (p,phrase)
def test_required_disclaimer_is_present_in_user_material():
 assert 'This package is legal **information**, not legal advice.' in (ROOT/'cheatsheet/L1-pro-se-guide.md').read_text()
