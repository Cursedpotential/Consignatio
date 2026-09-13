import subprocess,sys
from conftest import ledger,ROOT
def test_urls_are_official_or_explicitly_explained():
 for r in ledger():
  url=r['official_url']
  assert url is None or url.startswith('https://')
  if url is None: assert r['alternate_urls'] and r['unresolved_issues']
def test_url_checker_has_safe_dry_run():
 r=subprocess.run([sys.executable,str(ROOT/'scripts/citation_url_checker.py'),str(ROOT/'ledger.json'),'--dry-run'],capture_output=True,text=True)
 assert r.returncode==0 and 'LIMITATIONS' in r.stdout and '"planned": true' in r.stdout
