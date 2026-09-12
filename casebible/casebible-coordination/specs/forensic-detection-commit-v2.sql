-- forensic-detection-commit-v2.sql
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-01
--
-- TIGHTENED durable committing run of the behavioral DETECTION RUNNER.
-- Supersedes specs/forensic-detection-commit.sql (v1, never landed — classifier-blocked).
--
-- WHY v2 — the v1 scan included the 25 `markdown-transcript` normalized_record rows
-- (whole AI-chat transcripts, avg 161KB, ingested as single "messages"). Those are
-- CONTEXT corpus, NOT evidence (ADR ~0033 evidence-context boundary), and they
-- produced 908 of 1247 findings (73%) — mostly the scanner matching pattern-spec
-- phrase lists quoted inside research docs. v2 scopes the scan to REAL messaging
-- evidence only:
--     nr.source = 'imessage-html'          (1,918 records, avg 41 chars)
-- Measured expectation (read-only scope query 2026-07-01):
--     VARIANT A (this file): 339 findings / 276 records / 15 categories
--     (variant B len>=8: 115/96/11 — drops substance categories, NOT used;
--      variant C multi-word-only: 93/88/11 — higher precision, owner may prefer)
--
-- Court-safety guard identical to v1: in-txn RAISE aborts the whole commit
-- (zero durable rows) if findings=0 OR any court-safety counter > 0.
--
-- Run (owner's hand / live-approved prompt):
--   ssh -i ~/.ssh/ovh ubuntu@100.119.96.29 "docker exec -i agentos-db-ipy7vrw61jjsw0ktou2qr20f-055743909530 psql -U ai -d ai -v ON_ERROR_STOP=1 -f -" < D:/casebible/casebible-coordination/specs/forensic-detection-commit-v2.sql
--
-- Undo (scoped, reversible):
--   DELETE FROM analysis.pattern_finding WHERE provenance_id = '<commit_run_id>';
--   DELETE FROM analysis.processing_run   WHERE run_id       = '<commit_run_id>';

\set ON_ERROR_STOP on
BEGIN;

-- 1) provenance run for this durable pass
INSERT INTO analysis.processing_run
    (run_type, run_purpose, status, actor, tool_or_model,
     ran_local_only, cloud_exposure, human_review_requirement, replayable, started_at, finished_at)
VALUES ('pattern_analysis',
        'detection commit v2 (durable, literal subset, imessage-html evidence only — transcripts excluded per evidence-context boundary)',
        'ok', 'forensic-detection-commit-v2', 'sql literal-scan', true, false, true, true, now(), now())
RETURNING run_id AS commit_run_id \gset

\echo '--- committing detection run_id: ---'
\echo :commit_run_id

-- 2) literal findings over REAL MESSAGES ONLY. Symmetric by construction — no
--    party/speaker filter; both parties' messages hit identically.
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
  AND length(dp.pattern) >= 4
  AND nr.source = 'imessage-html';          -- v2: evidence-context boundary enforced

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
  WHERE r.actor = 'forensic-detection-commit-v2';

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

-- 4) acceptance (expect ~339 findings / 276 records / 15 categories; all counters 0)
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
WHERE r.actor = 'forensic-detection-commit-v2';

COMMIT;
\echo '--- COMMITTED — durable rows written ---'
