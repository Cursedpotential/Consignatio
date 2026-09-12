-- 0006c-detection-patterns-new-cats-DRAFT.sql  (prod data seed, owner-directed)
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-03
--
-- Authors detection_pattern rows for the phrase-matchable subset of the 11
-- categories added in 0006b. Sources: app.py ABUSE_PATTERNS corpus (behavioral-
-- analyzer-complete.zip) + Expanded Pattern Library.md.
--
-- SCOPE DISCIPLINE (the detection-noise lesson): only 3 of the 11 new categories
-- are cleanly phrase-matchable with low false-positive risk — guilt_trip,
-- premature_intimacy, boundary_violation. The other 8 are COMPUTED/temporal/
-- statistical (escalation, cycle_tension, cycle_honeymoon, pronoun_ratio,
-- interruption, intermittent_reinforcement) or too context-dependent for safe
-- regex (mirroring, boundary_testing) — they stay pattern-less until a computed
-- detector is built. Fabricating regex for them would reproduce the over-firing
-- garbage. All patterns are multi-word/anchored, never bare common words.
--
-- bias_caution=true + authored_perspective='single_party_complainant' (mirrors
-- the existing 512 seed). Findings from these remain hypotheses behind the
-- court-safety review gate; category is_enabled=true but toggleable.

\set ON_ERROR_STOP on
SET search_path = analysis, public, ai;
BEGIN;

INSERT INTO analysis.detection_pattern
  (pattern_set_id, category_id, match_type, pattern, severity, score, mcl_factors,
   authored_perspective, bias_caution, is_case_specific, source, description)
SELECT ps.id, v.category_id, 'regex', v.pattern, v.severity, v.severity,
       v.mcl::mcl_factor[], 'single_party_complainant', true, false,
       'sweep-2026-07-03:app.py+expanded-pattern-library', v.descr
FROM analysis.detection_pattern_set ps,
(VALUES
  -- guilt_trip (sev 6, mcl k) — obligation/victimhood induction
  ('guilt_trip', 'after (everything|all) i(''ve| have) (done|did) for you', 6, '{k}', 'obligation appeal'),
  ('guilt_trip', 'i (gave up|sacrificed) (everything|so much|my life) for you', 7, '{k}', 'sacrifice framing'),
  ('guilt_trip', 'you(''d| would) be (nothing|lost|homeless) without me', 7, '{k}', 'dependency framing'),
  ('guilt_trip', 'how could you (do this|treat me) (to me|like this)', 6, '{k}', 'wounded appeal'),
  ('guilt_trip', 'after (all|everything) i(''ve| have) (sacrificed|put up with)', 6, '{k}', 'martyr framing'),
  ('guilt_trip', 'i(''m| am) the one (who|thats|that''s) (suffering|hurting|struggling)', 5, '{k}', 'victimhood narrative'),
  -- premature_intimacy (sev 5, mcl k) — accelerating commitment
  ('premature_intimacy', 'you(''re| are) my soulmate', 5, '{k}', 'soulmate framing'),
  ('premature_intimacy', 'we(''re| are) (meant to be|made for each other)', 5, '{k}', 'destiny framing'),
  ('premature_intimacy', 'i(''ve| have) never felt (this|like this) (way )?(about anyone )?before', 5, '{k}', 'uniqueness claim'),
  ('premature_intimacy', 'i can(''t| ?not) (live|imagine (my )?life) without you', 6, '{k}', 'dependency escalation'),
  ('premature_intimacy', 'no one (has ever|will ever) (understand|love|get) (me|you) (like )?(you|i) (do|will)', 5, '{k}', 'exclusivity bonding'),
  -- boundary_violation (sev 7, mcl k) — overriding a stated limit
  ('boundary_violation', 'you can(''t| ?not) (tell|stop) me (what to do)?', 7, '{k}', 'authority rejection'),
  ('boundary_violation', 'i(''ll| will) (do|say) (what|whatever) i want', 7, '{k}', 'limit override'),
  ('boundary_violation', 'i don(''t| ?not) (care|give a (fuck|shit)) what you (said|want|think)', 7, '{k}', 'dismissal of boundary'),
  ('boundary_violation', 'i(''m| am) (coming|showing up|going to be there) (whether|even if) you (like it or not|want|say)', 8, '{k}', 'physical boundary override')
) AS v(category_id, pattern, severity, mcl, descr)
WHERE ps.is_active
ON CONFLICT DO NOTHING;

\echo '--- 0006c acceptance ---'
SELECT category_id, count(*) AS patterns_added
FROM analysis.detection_pattern
WHERE source = 'sweep-2026-07-03:app.py+expanded-pattern-library'
GROUP BY category_id ORDER BY category_id;

COMMIT;
\echo '--- 0006c COMMITTED ---'

-- UNDO: DELETE FROM analysis.detection_pattern WHERE source='sweep-2026-07-03:app.py+expanded-pattern-library';
