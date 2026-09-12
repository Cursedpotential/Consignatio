-- 0009-human-label-workspace.sql  (prod DDL + populate, owner-directed)
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-03
--
-- The manual classification WORKFLOW backend. Owner tags every message (or a
-- selected group) with one OR MORE behavior labels → ground truth for pattern
-- refinement + small-model training. Front-end = NocoDB grid on this table
-- (multi-select labels field, bulk-edit selected rows). Distinct from the
-- approve/reject review gate — this is full manual classification.
--
-- One row per message (denormalized text so the grid is readable standalone).
-- labels text[] = multi-label (a message can be gaslighting AND blame_shifting).
-- A long/unnested VIEW feeds precision/recall scoring vs analysis.pattern_finding.
-- Additive, reversible (DROP at bottom). Pre-populated for the pilot conversation.

\set ON_ERROR_STOP on
SET search_path = analysis, public, ai;
BEGIN;

CREATE TABLE IF NOT EXISTS analysis.human_label (
    message_id     uuid PRIMARY KEY REFERENCES analysis.message(id) ON DELETE CASCADE,
    conversation_key text NOT NULL,
    seq            bigint NOT NULL,            -- serial_number: ordering + group-select
    occurred_at    timestamptz,
    who            text,                       -- ME / THEM
    message_text   text NOT NULL,              -- denormalized for standalone grid readability
    ai_flagged     text,                       -- the machine's guess (reference only, do not trust)
    ai_flag_count  integer NOT NULL DEFAULT 0,
    -- owner's classification --
    labels         text[] NOT NULL DEFAULT '{}',   -- multi-label; {} = untagged
    is_clean       boolean,                    -- true = explicitly nothing here (distinct from untagged)
    severity       integer CHECK (severity IS NULL OR (severity BETWEEN 0 AND 10)),
    notes          text,
    labeled_by     text,
    labeled_at     timestamptz,
    created_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE analysis.human_label IS
  'Manual classification workspace (NocoDB front-end). labels[] = owner multi-label ground truth. '
  'is_clean=true means reviewed-and-nothing (NOT the same as labels={} untagged). Feeds refinement + training.';

-- populate: every pilot-conversation message, with the machine guess for reference
INSERT INTO analysis.human_label
    (message_id, conversation_key, seq, occurred_at, who, message_text, ai_flagged, ai_flag_count)
SELECT m.id, c.external_thread_key, m.serial_number, m.ts_utc,
       CASE m.direction WHEN 'outbound' THEN 'ME' ELSE 'THEM' END,
       nr.content,
       f.ai_flagged, coalesce(f.ai_flag_count,0)
FROM analysis.message m
JOIN analysis.conversation c ON c.id = m.conversation_id
JOIN analysis.normalized_record nr ON nr.id = m.id
LEFT JOIN LATERAL (
    SELECT string_agg(DISTINCT dp.category_id::text, '; ' ORDER BY dp.category_id::text) AS ai_flagged,
           count(DISTINCT dp.category_id) AS ai_flag_count
    FROM analysis.detection_pattern dp
    WHERE dp.is_active AND (
         (dp.match_type='literal' AND length(dp.pattern)>=4
            AND nr.content ILIKE '%'||replace(replace(dp.pattern,'%','\%'),'_','\_')||'%')
      OR (dp.match_type='regex' AND nr.content ~* dp.pattern) )
) f ON true
WHERE c.external_thread_key = 'imessage:+18108532989'
ON CONFLICT (message_id) DO NOTHING;

-- long view: one row per (message, label) for scoring/training export
CREATE OR REPLACE VIEW analysis.vw_human_label_long AS
SELECT h.message_id, h.conversation_key, h.seq, h.occurred_at, h.who,
       h.message_text, label, h.severity, h.labeled_by, h.labeled_at
FROM analysis.human_label h
CROSS JOIN LATERAL unnest(
    CASE WHEN cardinality(h.labels) > 0 THEN h.labels
         WHEN h.is_clean THEN ARRAY['__CLEAN__']
         ELSE ARRAY[]::text[] END) AS label;
COMMENT ON VIEW analysis.vw_human_label_long IS
  'One row per (message,label). __CLEAN__ = explicitly-reviewed-nothing. Untagged messages absent. '
  'Join vs analysis.pattern_finding for precision/recall per category.';

-- labeling progress view (for the owner + a NocoDB dashboard)
CREATE OR REPLACE VIEW analysis.vw_labeling_progress AS
SELECT count(*) AS total_messages,
       count(*) FILTER (WHERE cardinality(labels) > 0 OR is_clean) AS labeled,
       count(*) FILTER (WHERE cardinality(labels) > 0) AS labeled_with_behavior,
       count(*) FILTER (WHERE is_clean) AS marked_clean,
       count(*) FILTER (WHERE cardinality(labels)=0 AND is_clean IS NOT TRUE) AS remaining,
       round(100.0 * count(*) FILTER (WHERE cardinality(labels) > 0 OR is_clean) / nullif(count(*),0), 1) AS pct_done
FROM analysis.human_label;

\echo '--- 0009 acceptance ---'
SELECT (SELECT count(*) FROM analysis.human_label) AS rows_populated,
       (SELECT total_messages FROM analysis.vw_labeling_progress) AS progress_total,
       (SELECT count(*) FROM analysis.human_label WHERE ai_flag_count>0) AS ai_flagged_ref;

COMMIT;
\echo '--- 0009 COMMITTED ---'

-- UNDO:
-- DROP VIEW IF EXISTS analysis.vw_labeling_progress, analysis.vw_human_label_long;
-- DROP TABLE IF EXISTS analysis.human_label;
