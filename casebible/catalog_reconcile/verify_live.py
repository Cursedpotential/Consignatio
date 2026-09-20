"""Byline: Codex | 2026-09-20. Read-only verification after atomic publication."""
import argparse
import json
from pathlib import Path

from io_utils import Postgres
from run import save_json


def verify(root):
    root=Path(root);pg=Postgres()
    expected=json.loads((root/'validated.json').read_text(encoding='utf-8'))
    published=json.loads((root/'published.json').read_text(encoding='utf-8'))
    if published['generation_id']!=expected['generation_id']:raise ValueError('Publication identity differs')
    def query(sql):return list(pg.rows(sql))
    result={'byline':'Codex | 2026-09-20','generation_id':expected['generation_id'],
      'current_generation':query('SELECT generation_id FROM catalog_reconcile.current_generation')[0]['generation_id'],
      'availability':query('SELECT * FROM catalog_reconcile.availability_summary ORDER BY source,availability'),
      'duplicates':query('SELECT count(*) AS identity_groups,sum(repeated_bytes) AS repeated_bytes FROM catalog_reconcile.visible_duplicate_identities')[0],
      'native_exports':query("SELECT count(*) AS native_items,count(*) FILTER (WHERE representations->'office'->>'state' IN ('visible_exact_path','visible_exact_elsewhere') AND representations->'pdf'->>'state' IN ('visible_exact_path','visible_exact_elsewhere')) AS both_visible FROM catalog_reconcile.native_exports")[0],
      'bas':query("SELECT count(*) AS candidates,count(*) FILTER (WHERE status<>'provisional_metadata_only' OR retirement_status<>'not_cleared') AS unexpected FROM catalog_reconcile.bas_candidates")[0],
      'retirement':query("SELECT count(*) FILTER (WHERE retirement_status<>'not_cleared') AS unexpected FROM catalog_reconcile.r2_occurrences")[0],
      'historical_links':query("SELECT count(*) AS missing FROM (SELECT DISTINCT jsonb_array_elements_text(version_ids) AS file_id FROM catalog_reconcile.occurrences WHERE availability='historical_exact') x LEFT JOIN catalog_reconcile.object_versions b ON b.file_id=x.file_id WHERE b.file_id IS NULL")[0]}
    local=json.loads((root/'triage-summary.json').read_text(encoding='utf-8'))
    result['checks']={'current_generation_identity':result['current_generation']==expected['generation_id'],
       'live_occurrence_conservation':sum(r['occurrence_rows'] for r in result['availability'])==expected['occurrence_rows'],
       'duplicate_groups_match_local':result['duplicates']['identity_groups']==local['duplicate_identities']['identity_groups'],
       'duplicate_bytes_match_local':result['duplicates']['repeated_bytes']==local['duplicate_identities']['repeated_bytes'],
       'native_map_conservation':result['native_exports']['native_items']==expected['native_maps'],
       'provisional_bas_conservation':result['bas']['candidates']==expected['provisional_bas1_candidates'],
       'no_unintended_bas_acceptance':result['bas']['unexpected']==0,
       'no_retirement_clearance':result['retirement']['unexpected']==0,
       'historical_links_resolve':result['historical_links']['missing']==0}
    save_json(root/'live-verification.json',result)
    print(json.dumps(result['checks']))
    if not all(result['checks'].values()):raise RuntimeError('Live verification failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--generation',required=True)
    verify(parser.parse_args().generation)
