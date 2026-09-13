import json
from conftest import ROOT,ledger

def test_completed_audit_artifacts_are_packaged_and_traceable():
 report=ROOT/'references/audit/deep-research-source-audit-2026-08-09.md'
 raw=ROOT/'references/audit/deep-research-source-ledger-2026-08-09.json'
 assert report.is_file() and raw.is_file()
 assert len(json.loads(raw.read_text())['sources'])==74
 rows={r['id']:r for r in ledger()}
 assert 'audit-deep-research-source-audit-2026-08-09' in rows
 assert 'mifile-available-courts' in rows
 assert 'references/audit/audit-mifile-nonlisting.md' in rows['mifile-available-courts']['dependent_files']

def test_blocked_primary_sources_have_explicit_limits():
 rows={r['id']:r for r in ledger()}
 for sid in ['mcr-current-compilation','mre-consolidated','foc-68-objection','mcsf-2025-manual']:
  r=rows[sid]
  assert 'robot' in str(r['http_status']).lower() or 'block' in str(r['http_status']).lower()
  assert r['unresolved_issues']
 assert rows['mcsf-2025-supplement']['official_url'] is None
