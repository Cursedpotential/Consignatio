-- forensic-detection-dryrun.sql
-- Byline: Claude Code (PIPELINE lane) · Opus 4.8 · 2026-07-01
--
-- Rolled-back proof that the behavioral DETECTION RUNNER's write path is
-- insertable against the LIVE applied schema (migrations 0005 + 0006).
-- Set-based mirror of evidence/detection.py: scans analysis.normalized_record
-- against the seeded analysis.detection_pattern (literal patterns) and writes
-- analysis.pattern_finding with the court-safe defaults, then ROLLS BACK.
--
-- GATED: this is a write-ATTEMPT against live ovh3 PG (db=ai) — rolled back, zero
-- durable rows, but still a prod-DB touch → run only under APPROVALS greenlight:
--   psql "$AGNO_PG_URL" -v ON_ERROR_STOP=1 -f forensic-detection-dryrun.sql
--
-- Expected: findings_written > 0, and ALL court-safety counters = 0
-- (no row escapes with safe_for_legal_use, no review bypass, no bias_caution off),
-- then ROLLBACK leaves pattern_finding exactly as it was.

\set ON_ERROR_STOP on
BEGIN;

-- 1) provenance run for this pass
WITH run AS (
    INSERT INTO analysis.processing_run
        (run_type, run_purpose, status, actor, tool_or_model,
         ran_local_only, cloud_exposure, human_review_requirement, replayable, started_at)
    VALUES ('pattern_analysis', 'detection dry-run (rolled back)', 'running',
            'forensic-detection-dryrun', 'sql literal-scan', true, false, true, true, now())
    RETURNING run_id
)
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
       'inferred'::evidence_tier, run.run_id
FROM analysis.detection_pattern dp
JOIN analysis.detection_pattern_set ps
     ON ps.id = dp.pattern_set_id AND ps.is_active
JOIN analysis.normalized_record nr
     ON nr.content ILIKE '%' || replace(replace(dp.pattern, '%', '\%'), '_', '\_') || '%'
CROSS JOIN run
WHERE dp.is_active
  AND dp.match_type = 'literal'
  AND length(dp.pattern) >= 4;

-- 3) acceptance — findings landed, and court-safety gates held on every row
\echo '--- detection dry-run acceptance (all court-safety counters must be 0) ---'
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
WHERE r.actor = 'forensic-detection-dryrun';

\echo '--- top categories by hit count (triage preview) ---'
SELECT pf.category_id, bc.polarity, count(*) AS hits
FROM analysis.pattern_finding pf
JOIN analysis.processing_run r  ON r.run_id = pf.provenance_id
JOIN analysis.behavior_category bc ON bc.category_id = pf.category_id
WHERE r.actor = 'forensic-detection-dryrun'
GROUP BY pf.category_id, bc.polarity
ORDER BY hits DESC
LIMIT 20;

-- 4) prove nothing is durable
ROLLBACK;
\echo '--- ROLLED BACK — zero durable rows written ---'
SELECT count(*) AS pattern_finding_rows_after_rollback FROM analysis.pattern_finding;
