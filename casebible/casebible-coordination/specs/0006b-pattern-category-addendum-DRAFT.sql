-- 0006b-pattern-category-addendum-DRAFT.sql  (prod DDL data seed, owner-directed)
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-03
--
-- Adds the 11 behavior_category rows found MISSING from the live 153-category seed
-- by the loose-archive pattern-gap diff (specs/loose-archive-sweep-MASTER.md).
-- Sources: Expanded Pattern Library.md (research-backed, cites Pomerantz 2021 /
-- Anderson & Leaper 1998) + RESEARCH_BEHAVIORAL_ANALYSIS.md module taxonomy.
--
-- SAFE/INERT: these are CATEGORIES only. Detection produces findings only where
-- analysis.detection_pattern rows reference a category — none exist for these yet,
-- so seeding them fires NOTHING until patterns are authored later (from app.py
-- ABUSE_PATTERNS corpus). is_enabled defaults true (0008) but is moot without patterns.
-- Additive, idempotent (ON CONFLICT DO NOTHING), reversible.
--
-- Apply: ssh ovh3 ... psql -f -  < this file

\set ON_ERROR_STOP on
SET search_path = analysis, public, ai;
BEGIN;

INSERT INTO analysis.behavior_category
    (category_id, label, description, polarity, default_severity, mcl_factors, is_case_specific, source, notes)
VALUES
  ('cycle_tension', 'Cycle of abuse: tension-building',
   'Tension-building phase markers preceding an incident (walking-on-eggshells, escalating criticism).',
   'negative', 5, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:expanded-pattern-library',
   'Temporal phase marker; only meaningful in sequence — pair with escalation over a finding span.'),
  ('cycle_honeymoon', 'Cycle of abuse: reconciliation/honeymoon',
   'Post-incident reconciliation/honeymoon phase (apologies, gifts, promises) used to reset the cycle.',
   'negative', 4, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:expanded-pattern-library',
   'Positive-surface content re-scored as manipulation via contradiction with the incident phase.'),
  ('escalation', 'Escalation over time',
   'Rising severity/frequency across a conversation span; the trend itself, not any single message.',
   'negative', 7, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:app.py-escalation_index',
   'Computed over a finding span via escalation_index (0008 finding.escalation_index).'),
  ('pronoun_ratio', 'Pronoun-ratio linguistic marker',
   'Statistical I-talk vs you-talk ratio (I-talk>=0.08 -> self-focus/narcissism signal; you-talk>=0.12 -> blame).',
   'linguistic_marker', 0, ARRAY['l']::mcl_factor[], false, 'sweep-2026-07-03:pronoun-ratio-analysis',
   'Aggregate statistical marker, not a phrase match; computed per author over a window.'),
  ('mirroring', 'Mirroring / agreement-bombing',
   'Excessive agreement and rapid interest-adoption to manufacture false compatibility (love-bomb tactic).',
   'negative', 5, ARRAY['j','k']::mcl_factor[], false, 'sweep-2026-07-03:expanded-pattern-library', NULL),
  ('premature_intimacy', 'Premature intimacy / rushing',
   'Accelerating intimacy/commitment faster than the relationship warrants (future-faking adjacent).',
   'negative', 5, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:expanded-pattern-library', NULL),
  ('boundary_testing', 'Boundary testing',
   'Probing stated limits with small violations to gauge/erode resistance before larger ones.',
   'negative', 6, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:expanded-pattern-library', NULL),
  ('boundary_violation', 'Boundary violation',
   'Overriding an explicitly stated boundary (contact, location, topic, physical).',
   'negative', 7, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:research-behavioral-analysis', NULL),
  ('guilt_trip', 'Guilt-tripping',
   'Inducing guilt/obligation to control behavior (after-all-I-do-for-you, victimhood narrative).',
   'negative', 6, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:research-behavioral-analysis', NULL),
  ('intermittent_reinforcement', 'Intermittent reinforcement',
   'Unpredictable alternation of reward and punishment/withdrawal (trauma-bonding mechanism).',
   'negative', 8, ARRAY['k']::mcl_factor[], false, 'sweep-2026-07-03:research-behavioral-analysis',
   'High severity: the mechanism behind trauma bonding; detect via reward/withdraw oscillation over a span.'),
  ('interruption', 'Interruption / conversational dominance',
   'Conversational interruption and floor-taking as a power-asymmetry marker (Anderson & Leaper 1998).',
   'linguistic_marker', 3, ARRAY['l']::mcl_factor[], false, 'sweep-2026-07-03:expanded-pattern-library',
   'Conversation-level marker; requires turn structure, not single-message text.')
ON CONFLICT (category_id) DO NOTHING;

\echo '--- 0006b acceptance (expect 11 present, total 164) ---'
SELECT count(*) FILTER (WHERE source LIKE 'sweep-2026-07-03%') AS seeded_this_pass,
       count(*) AS total_categories
FROM analysis.behavior_category;
SELECT category_id, polarity, default_severity, mcl_factors
FROM analysis.behavior_category WHERE source LIKE 'sweep-2026-07-03%' ORDER BY category_id;

COMMIT;
\echo '--- 0006b COMMITTED ---'

-- UNDO: DELETE FROM analysis.behavior_category WHERE source LIKE 'sweep-2026-07-03%';
