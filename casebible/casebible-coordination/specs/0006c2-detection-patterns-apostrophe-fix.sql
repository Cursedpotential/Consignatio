-- 0006c2-detection-patterns-apostrophe-fix.sql
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-03
--
-- FIX for 0006c: the dry-run positive-control test showed the patterns required
-- literal apostrophes (can't, don't, I'm) and so MISSED apostrophe-dropped texts
-- (cant, dont, im) — false negatives. Real SMS/iMessage constantly omit
-- apostrophes. Rewrite all 15 with the seed convention: optional apostrophe `'?`.
-- Reversible: deletes the 0006c rows and reinserts corrected ones under a new source tag.

\set ON_ERROR_STOP on
SET search_path = analysis, public, ai;
BEGIN;

DELETE FROM analysis.detection_pattern
WHERE source = 'sweep-2026-07-03:app.py+expanded-pattern-library';

INSERT INTO analysis.detection_pattern
  (pattern_set_id, category_id, match_type, pattern, severity, score, mcl_factors,
   authored_perspective, bias_caution, is_case_specific, source, description)
SELECT ps.id, v.category_id, 'regex', v.pattern, v.severity, v.severity,
       v.mcl::mcl_factor[], 'single_party_complainant', true, false,
       'sweep-2026-07-03:app.py+expanded-pattern-library:v2', v.descr
FROM analysis.detection_pattern_set ps,
(VALUES
  -- guilt_trip
  ('guilt_trip', 'after (everything|all) i''?(ve| have) (done|did) for you', 6, '{k}', 'obligation appeal'),
  ('guilt_trip', 'i (gave up|sacrificed) (everything|so much|my life) for you', 7, '{k}', 'sacrifice framing'),
  ('guilt_trip', 'you''?(d| would) be (nothing|lost|homeless) without me', 7, '{k}', 'dependency framing'),
  ('guilt_trip', 'how could you (do this|treat me) (to me|like this)', 6, '{k}', 'wounded appeal'),
  ('guilt_trip', 'after (all|everything) i''?(ve| have) (sacrificed|put up with)', 6, '{k}', 'martyr framing'),
  ('guilt_trip', 'i''?m the one (who|thats|that''?s) (suffering|hurting|struggling)', 5, '{k}', 'victimhood narrative'),
  -- premature_intimacy
  ('premature_intimacy', 'you''?re my soulmate', 5, '{k}', 'soulmate framing'),
  ('premature_intimacy', 'we''?re (meant to be|made for each other)', 5, '{k}', 'destiny framing'),
  ('premature_intimacy', 'i''?(ve| have) never felt (this|like this) (way )?(about anyone )?before', 5, '{k}', 'uniqueness claim'),
  ('premature_intimacy', 'i can''?(t| ?not) (live|imagine (my )?life) without you', 6, '{k}', 'dependency escalation'),
  ('premature_intimacy', 'no one (has ever|will ever) (understand|love|get) (me|you)', 5, '{k}', 'exclusivity bonding'),
  -- boundary_violation
  ('boundary_violation', 'you can''?(t| ?not) (tell|stop) me', 7, '{k}', 'authority rejection'),
  ('boundary_violation', 'i''?(ll| will) (do|say) (what|whatever) i want', 7, '{k}', 'limit override'),
  ('boundary_violation', 'i don''?(t| ?not) (care|give a (fuck|shit)) what you (said|want|think)', 7, '{k}', 'dismissal of boundary'),
  ('boundary_violation', 'i''?m (coming|showing up|going to be there) (whether|even if) you (like it or not|want|say)', 8, '{k}', 'physical boundary override')
) AS v(category_id, pattern, severity, mcl, descr)
WHERE ps.is_active;

\echo '--- 0006c2 acceptance ---'
SELECT category_id, count(*) FROM analysis.detection_pattern
WHERE source = 'sweep-2026-07-03:app.py+expanded-pattern-library:v2'
GROUP BY category_id ORDER BY category_id;

COMMIT;
\echo '--- 0006c2 COMMITTED ---'
-- UNDO: DELETE FROM analysis.detection_pattern WHERE source LIKE 'sweep-2026-07-03:app.py%';
