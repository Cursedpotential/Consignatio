-- forensic-detection-commit.sql
-- Byline: Claude Code (PIPELINE lane) · Opus 4.8 · 2026-07-01
--
-- DURABLE committing run of the behavioral DETECTION RUNNER — the COMMIT
-- counterpart of the PASSED specs/forensic-detection-dryrun.sql. Same INSERT…SELECT
-- logic (set-based mirror of evidence/detection.py, literal subset), but it COMMITS
-- instead of ROLLBACK, writing the first durable analysis.pattern_finding output.
--
-- Court-safety is ENFORCED, not just asserted: an in-txn guard RAISEs (aborting the
-- whole commit, zero durable rows) if findings=0 OR any court-safety counter > 0.
-- So no unsafe row can ever land.
--
-- AUTHORIZATION: owner (matt) in-session "if the dry run goes well then continue"
-- (relayed by ORCHESTRATOR 2026-07-01), following the PASSED live rolled-back dry-run.
--   ssh ovh3 'docker exec -i <agno-postgres> psql -U ai -d ai -v ON_ERROR_STOP=1 -f -'
--
-- Undo (scoped, reversible):
--   DELETE FROM analysis.pattern_finding WHERE provenance_id = '<commit_run_id>';
--   DELETE FROM analysis.processing_run   WHERE run_id       = '<commit_run_id>';

\set ON_ERROR_STOP on
BEGIN;

-- 1) provenance run for this durable pass (status 'ok' = finished; CHECK set has no 'completed')
INSERT INTO analysis.processing_run
    (run_type, run_purpose, status, actor, tool_or_model,
     ran_local_only, cloud_exposure, human_review_requirement, replayable, started_at, finished_at)
VALUES ('pattern_analysis', 'detection commit (durable, literal subset)', 'ok',
        'forensic-detection-commit', 'sql literal-scan', true, false, true, true, now(), now())
RETURNING run_id AS commit_run_id \gset

\echo '--- committing detection run_id: ---'
\echo :commit_run_id

-- 2) literal findings: each normalized_record whose content contains a literal
--    pattern's phrase. Symmetric by construction — no party/speaker filter.
INSERT INTO analysis.pattern_finding
    (subject_type, subject_id, category_id, pattern_id, pattern_set_id, subcategory,
     detection_method, rule_name, matched_text, matched_pattern,
     bias_caution, authored_perspective, severity, score,
     requires_human_review, is_verified, review_status, safe_for_legal_use,
     data_tier, provenance_id)
SELECT 'message', nr.id, dp.category_id, dp.id, dp.pattern_set_id, dp.subcategory,
       'literal'::detection_method, dp.source,
       left(dp.pattern, 2000), left(dp.pattern, 2000),
       dp.bias_caution, dp.authored_perspective, dp.severity, dp.score,
       true, false, 'unreviewed'::review_state, false,
       'inferred'::evidence_tier, :'commit_run_id'
FROM analysis.detection_pattern dp
JOIN analysis.detection_pattern_set ps
     ON ps.id = dp.pattern_set_id AND ps.is_active
JOIN analysis.normalized_record nr
     ON nr.content ILIKE '%' || replace(replace(dp.pattern, '%', '\%'), '_', '\_') || '%'
WHERE dp.is_active
  AND dp.match_type = 'literal'
  AND length(dp.pattern) >= 4;

-- 3) COURT-SAFETY GUARD — abort the whole commit if 0 findings OR any unsafe row.
DO $guard$
DECLARE
  v_total int; v_legal int; v_review int; v_bias int; v_unrev int; v_tier int;
BEGIN
  SELECT count(*),
         count(*) FILTER (WHERE pf.safe_for_legal_use),
         count(*) FILTER (WHERE NOT pf.requires_human_review),
         count(*) FILTER (WHERE NOT pf.bias_caution),
         count(*) FILTER (WHERE pf.review_status <> 'unreviewed'),
         count(*) FILTER (WHERE pf.data_tier <> 'inferred')
    INTO v_total, v_legal, v_review, v_bias, v_unrev, v_tier
  FROM analysis.pattern_finding pf
  JOIN analysis.processing_run r ON r.run_id = pf.provenance_id
  WHERE r.actor = 'forensic-detection-commit';

  RAISE NOTICE 'court-safety guard: findings=% legal_leak=% review_bypass=% bias_off=% not_unreviewed=% wrong_tier=%',
    v_total, v_legal, v_review, v_bias, v_unrev, v_tier;

  IF v_total = 0 THEN
    RAISE EXCEPTION 'ABORT: 0 findings written — refusing to commit an empty run';
  END IF;
  IF (v_legal + v_review + v_bias + v_unrev + v_tier) > 0 THEN
    RAISE EXCEPTION 'ABORT: court-safety violation (legal=% review=% bias=% not_unreviewed=% tier=%) — nothing committed',
      v_legal, v_review, v_bias, v_unrev, v_tier;
  END IF;
END
$guard$;

-- 4) acceptance preview (must show all court-safety counters = 0)
\echo '--- commit acceptance (all court-safety counters must be 0) ---'
SELECT
    count(*)                                              AS findings_written,
    count(DISTINCT pf.subject_id)                         AS records_hit,
    count(DISTINCT pf.category_id)                        AS categories_hit,
    count(*) FILTER (WHERE pf.safe_for_legal_use)         AS legal_leak_MUST_BE_0,
    count(*) FILTER (WHERE NOT pf.requires_human_review)  AS review_bypass_MUST_BE_0,
    count(*) FILTER (WHERE NOT pf.bias_caution)           AS bias_off_MUST_BE_0,
    count(*) FILTER (WHERE pf.review_status <> 'unreviewed') AS not_unreviewed_MUST_BE_0,
    count(*) FILTER (WHERE pf.data_tier <> 'inferred')    AS wrong_tier_MUST_BE_0
FROM analysis.pattern_finding pf
JOIN analysis.processing_run r ON r.run_id = pf.provenance_id
WHERE r.actor = 'forensic-detection-commit';

COMMIT;
\echo '--- COMMITTED — durable rows written ---'
