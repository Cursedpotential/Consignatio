-- 0008-app-layer-adoptions-DRAFT.sql  (DRAFT — prod DDL, owner-gated, NOT applied)
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-03
--
-- Adopts the "good shape" from the extracted schemas/parsers/loose-archive sweeps
-- (see specs/drizzle-schemas-vs-live-DIFF.md + extracted-code-sweep-ADDENDUM.md +
--  loose-archive-sweep-MASTER.md). ADDITIVE ONLY — no drops, no data rewrites.
-- Everything derives conveniences the old per-platform schemas baked in as stored
-- columns; live keeps facts once + exposes conveniences as views.
--
-- search_path note: custom enums live in schema `ai`. This runs with ai on the
-- path; enum refs are unqualified (matches migrations 0005/0006).
--
-- Apply (owner's hand, same path as 0005/0006/0007):
--   ssh -i ~/.ssh/ovh ubuntu@100.119.96.29 "docker exec -i agentos-db-ipy7vrw61jjsw0ktou2qr20f-055743909530 psql -U ai -d ai -v ON_ERROR_STOP=1 -f -" < D:/casebible/casebible-coordination/specs/0008-app-layer-adoptions-DRAFT.sql
-- Undo: see the DROP block at the bottom (commented).

\set ON_ERROR_STOP on
SET search_path = analysis, public, ai;
BEGIN;

-- ===========================================================================
-- 1) analysis.format_resolver  (AI-derived field mappings for unknown formats)
--    ← schema_resolver.py cascade (exact→fuzzy→content→ai), md5[:12] signature.
--    Directly attacks XLSX / Snapchat-JSON / call-log parser gaps: resolve an
--    unknown export's columns once, store the mapping + how it was derived,
--    reuse + audit forever.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS analysis.format_resolver (
    id              uuid PRIMARY KEY DEFAULT uuidv7(),
    source_signature text NOT NULL,          -- md5(sorted lowercased source fields)[:12]
    source_label    text,                    -- e.g. 'sms-backup-restore-xml', 'snapchat-json'
    source_fields   jsonb NOT NULL,          -- verbatim source field list
    mappings        jsonb NOT NULL,          -- [{source_field,target_field,confidence,method}]
                                             -- method ∈ exact|fuzzy|content|ai|cached
    target_schema   text NOT NULL DEFAULT 'analysis.message',
    ai_model        text,                    -- model id if any mapping used method='ai'
    used_count      integer NOT NULL DEFAULT 0,
    review_status   review_state NOT NULL DEFAULT 'unreviewed',
    created_by      text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_signature, target_schema)
);
COMMENT ON TABLE analysis.format_resolver IS
  'AI-assisted field-mapping registry for unknown message-export formats. mappings[].method '
  'records HOW each field was resolved (exact/fuzzy/content/ai) — court-defensibility: a '
  'human can see which columns were deterministic vs model-inferred. Seed dict + cascade '
  'ported from schema_resolver.py.';

-- ===========================================================================
-- 2) message hint provenance + is_read
--    Live message has 6 *_hint columns but records neither WHY/WHEN/WHO(model).
--    is_read is forensically load-bearing (SMS read/unread, notice evidence).
-- ===========================================================================
ALTER TABLE analysis.message ADD COLUMN IF NOT EXISTS is_read boolean;
COMMENT ON COLUMN analysis.message.is_read IS
  'SMS/MMS read flag (SBV read=1/0; iMessage is_read). NULL = unknown/not-applicable.';
ALTER TABLE analysis.message ADD COLUMN IF NOT EXISTS hint_provenance jsonb;
COMMENT ON COLUMN analysis.message.hint_provenance IS
  'Provenance for the *_hint columns: {field: {model, at, method, reasoning}}. A model-assigned '
  'hint that cannot say why/when/what-model is not court-usable; this records it. NULL until any '
  'hint is set by an analysis pass.';

-- ===========================================================================
-- 3) app settings + topic codes + conversation cluster code
--    Clustering config (timeGap/similarity) + human-readable cluster IDs.
--    ← conversation-segmentation.ts (2h / 0.6 / PLAT_YYMM_TOPIC_iii) +
--      topic_detector.py TOPIC_MAPPING.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS public.app_setting (
    key         text PRIMARY KEY,
    value       jsonb NOT NULL,
    value_type  text NOT NULL DEFAULT 'json',
    description text,
    updated_by  text,
    updated_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.app_setting IS 'Versionable key/value config (clustering thresholds, etc.).';

CREATE TABLE IF NOT EXISTS analysis.topic_code (
    code        varchar(6) PRIMARY KEY,      -- KAILAH, VISITS, SUBST, INFID, THREAT, GENRL...
    label       text NOT NULL,
    keywords    text[] NOT NULL DEFAULT '{}',
    mcl_factors mcl_factor[],
    is_case_specific boolean NOT NULL DEFAULT false,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE analysis.topic_code IS 'Human-readable conversation topic codes (6-char). Seed = topic_detector.py TOPIC_MAPPING.';

ALTER TABLE analysis.conversation ADD COLUMN IF NOT EXISTS cluster_code text;
ALTER TABLE analysis.conversation ADD COLUMN IF NOT EXISTS cluster_reason text
    CHECK (cluster_reason IS NULL OR cluster_reason IN ('time_gap','topic_change','entity_change','first_message'));
COMMENT ON COLUMN analysis.conversation.cluster_code IS
  'Human-readable cluster id PLAT_YYMM_TOPIC_iii (e.g. SMS_1905_KAILAH_001). cluster_reason = split cause.';

-- seed clustering thresholds + topic codes (idempotent)
INSERT INTO public.app_setting (key, value, value_type, description) VALUES
  ('clustering.time_gap_seconds', '7200', 'int', 'New cluster if gap > 2h (conversation-segmentation.ts)'),
  ('clustering.similarity_threshold', '0.6', 'float', 'New cluster if cosine < 0.6 vs previous message'),
  ('clustering.embedding_model', '"all-MiniLM-L6-v2"', 'string', '384-dim; run via Milvus lane, not BERTopic'),
  ('clustering.id_format', '"PLAT_YYMM_TOPIC_iii"', 'string', 'cluster_code scheme')
ON CONFLICT (key) DO NOTHING;

INSERT INTO analysis.topic_code (code, label, keywords, is_case_specific) VALUES
  ('KAILAH','Child (Kailah)', ARRAY['kailah','daughter','child','baby','kyla','kaila'], true),
  ('VISITS','Parenting time / custody', ARRAY['parenting','custody','visitation','visit','pickup','dropoff'], false),
  ('CALLS', 'Calls / contact', ARRAY['call','phone','contact','voicemail'], false),
  ('SCHOOL','School', ARRAY['school','teacher','daycare','class'], false),
  ('MONEY', 'Financial', ARRAY['money','financial','bills','rent','payment','support'], false),
  ('HEALTH','Medical / health', ARRAY['medical','doctor','hospital','medication','appointment'], false),
  ('SUBST', 'Substance', ARRAY['alcohol','drug','adderall','drunk','high','pills'], false),
  ('INFID', 'Infidelity', ARRAY['cheat','affair','infidelity','loyal','huckleberry'], true),
  ('THREAT','Threats', ARRAY['threat','hurt','kill','harm'], false),
  ('GENRL', 'General', ARRAY[]::text[], false)
ON CONFLICT (code) DO NOTHING;

-- ===========================================================================
-- 4) behavior_category enable/disable toggle
--    Live can only toggle per-pattern; category-level kill switches were the
--    lesson of the detection-noise review. ← analysisModules.isEnabled (0003).
-- ===========================================================================
ALTER TABLE analysis.behavior_category ADD COLUMN IF NOT EXISTS is_enabled boolean NOT NULL DEFAULT true;
COMMENT ON COLUMN analysis.behavior_category.is_enabled IS
  'Category-level detection kill switch. Detection runners MUST honor: skip patterns whose '
  'category.is_enabled = false. (detection.py + forensic-detection commit SQL to filter on this.)';

-- ===========================================================================
-- 5) HurtLex lexicon sync provenance
--    ← hurtlex-fetcher.ts hurtlexSyncStatus + pinned v1.2 + level knob.
-- ===========================================================================
CREATE TABLE IF NOT EXISTS analysis.lexicon_sync (
    id           uuid PRIMARY KEY DEFAULT uuidv7(),
    lexicon      text NOT NULL,               -- 'hurtlex'
    language     text NOT NULL DEFAULT 'en',
    version      text,                         -- pinned, e.g. '1.2'
    level        text CHECK (level IS NULL OR level IN ('conservative','inclusive')),
    source_url   text,
    source_commit text,
    status       text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','syncing','success','error')),
    term_count   integer,
    error_message text,
    pattern_set_id uuid REFERENCES analysis.detection_pattern_set(id),
    last_sync_at timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE analysis.lexicon_sync IS
  'External lexicon import provenance. HurtLex pinned v1.2 (valeriobasile/hurtlex); level '
  'conservative|inclusive; isCustom terms protected on resync (enforced in importer, not here).';

-- ===========================================================================
-- 6) tool_call_ledger.prompt_version  (enables the prompt-metrics view)
-- ===========================================================================
ALTER TABLE analysis.tool_call_ledger ADD COLUMN IF NOT EXISTS prompt_version text;
COMMENT ON COLUMN analysis.tool_call_ledger.prompt_version IS
  'public.prompt_registry.prompt_version used by this call — joins for prompt-performance rollup.';

-- ===========================================================================
-- 7) finding SPAN + progression columns (multi-message pattern spans)
--    ← SMS zip messaging_behavior_patterns + 0003 patternMatches + app.py
--      escalation_index. Turns analysis.finding into a real span/progression row.
-- ===========================================================================
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS pattern_type text
    CHECK (pattern_type IS NULL OR pattern_type IN ('escalation','cycle','triggered_response','time_based','single'));
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS span_message_ids uuid[];
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS span_message_count integer;
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS span_start timestamptz;
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS span_end timestamptz;
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS severity_progression text
    CHECK (severity_progression IS NULL OR severity_progression IN ('escalating','stable','de_escalating'));
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS escalation_index numeric;  -- (2nd-half mean sev − 1st-half)/1st-half ×100
ALTER TABLE analysis.finding ADD COLUMN IF NOT EXISTS contradicts_finding_id uuid REFERENCES analysis.finding(id);
COMMENT ON COLUMN analysis.finding.escalation_index IS
  'app.py metric: (mean severity 2nd-half − 1st-half)/1st-half ×100 over time-sorted span.';
COMMENT ON COLUMN analysis.finding.contradicts_finding_id IS
  'Self-reference: this finding contradicts another (0003 patternMatches.contradictsWith).';

-- ===========================================================================
-- 8) convenience VIEWS (the "per-platform ergonomics" without stored dup columns)
--    behavior-flags view (one-click filters that RESPECT the review gate) +
--    per-platform typed views over platform_attrs.
-- ===========================================================================

-- 8a) behavior flags per message — hypothesis vs human-confirmed kept SEPARATE
CREATE OR REPLACE VIEW analysis.vw_message_behavior AS
SELECT m.id AS message_id, m.conversation_id, m.ts_utc, m.direction,
       m.has_behaviors, m.behavior_count, m.max_behavior_severity,
       count(pf.*)                                              AS finding_count,
       count(pf.*) FILTER (WHERE pf.review_status = 'approved') AS confirmed_count,
       bool_or(pf.category_id = 'threats')          AS flag_threat_hypothesis,
       bool_or(pf.category_id = 'threats' AND pf.review_status='approved') AS flag_threat_confirmed,
       bool_or(pf.category_id = 'gaslighting')       AS flag_gaslighting_hypothesis,
       bool_or(pf.category_id = 'minimizing')        AS flag_minimizing_hypothesis,
       bool_or(pf.category_id = 'blame_shifting')    AS flag_blame_hypothesis,
       array_agg(DISTINCT pf.category_id) FILTER (WHERE pf.category_id IS NOT NULL) AS categories
FROM analysis.message m
LEFT JOIN analysis.pattern_finding pf ON pf.subject_id = m.id AND pf.subject_type = 'message'
GROUP BY m.id, m.conversation_id, m.ts_utc, m.direction,
         m.has_behaviors, m.behavior_count, m.max_behavior_severity;
COMMENT ON VIEW analysis.vw_message_behavior IS
  'One-click behavior filters for UI. *_hypothesis = a finding exists (unreviewed OK); *_confirmed '
  '= human-approved only. Replaces the old containsThreat/Blame booleans WITHOUT bypassing the '
  'court-safety review gate.';

-- 8b) SMS-specific typed view (SBV fields living in platform_attrs)
CREATE OR REPLACE VIEW analysis.vw_message_sms AS
SELECT m.id AS message_id, m.conversation_id, m.ts_utc, m.direction, m.is_read,
       m.sender_e164, m.recipient_e164, m.delivery_status, m.status_code, m.is_blocked,
       m.platform_attrs->>'service_center' AS service_center,
       m.platform_attrs->>'sub_id'         AS sub_id,
       m.platform_attrs->>'contact_name'   AS contact_name,
       m.raw_ts, nr.content
FROM analysis.message m
LEFT JOIN analysis.normalized_record nr ON nr.id = m.id
WHERE m.platform = 'sms';
COMMENT ON VIEW analysis.vw_message_sms IS 'SMS-Backup&Restore fields as typed columns from platform_attrs.';

-- 8c) iMessage-specific typed view
CREATE OR REPLACE VIEW analysis.vw_message_imessage AS
SELECT m.id AS message_id, m.conversation_id, m.ts_utc, m.direction, m.is_read,
       m.external_id AS apple_guid,
       m.platform_attrs->>'service'        AS service,          -- iMessage vs SMS (if re-exported from chat.db)
       m.platform_attrs->>'date_read'      AS date_read,
       m.platform_attrs->>'date_edited'    AS date_edited,
       m.platform_attrs->>'thread_originator_guid' AS reply_to_guid,
       m.raw_ts, nr.content
FROM analysis.message m
LEFT JOIN analysis.normalized_record nr ON nr.id = m.id
WHERE m.platform = 'imessage';
COMMENT ON VIEW analysis.vw_message_imessage IS
  'iMessage typed view. date_read/date_edited/service/reply_to_guid populate only after a '
  'chat.db re-export (current HTML export lacks them — see extracted-code-sweep-ADDENDUM.md §4).';

-- 8d) prompt-performance rollup (view, not columns — no DDL risk)
CREATE OR REPLACE VIEW public.vw_prompt_performance AS
SELECT pr.prompt_name, pr.prompt_version,
       count(l.*)                                        AS uses,
       avg(l.runtime_ms)::numeric(10,1)                  AS avg_runtime_ms,
       sum(l.cost_estimate)                              AS total_cost,
       count(*) FILTER (WHERE l.errors IS NOT NULL)      AS error_count
FROM public.prompt_registry pr
LEFT JOIN analysis.tool_call_ledger l ON l.prompt_version = pr.prompt_version
GROUP BY pr.prompt_name, pr.prompt_version;

-- 8e) LLM cost rollup by tool/day (view)
CREATE OR REPLACE VIEW public.vw_llm_cost_rollup AS
SELECT date_trunc('day', created_at) AS day, tool_name, tool_category,
       count(*) AS calls, sum(cost_estimate) AS total_cost, sum(runtime_ms) AS total_ms
FROM analysis.tool_call_ledger
GROUP BY 1,2,3 ORDER BY 1 DESC, total_cost DESC NULLS LAST;

-- ===========================================================================
-- 9) acceptance
-- ===========================================================================
\echo '--- 0008 acceptance ---'
SELECT
  (SELECT count(*) FROM analysis.topic_code)                                        AS topic_codes,
  (SELECT count(*) FROM public.app_setting WHERE key LIKE 'clustering.%')           AS clustering_settings,
  (SELECT count(*) FROM information_schema.columns
     WHERE table_schema='analysis' AND table_name='finding'
       AND column_name IN ('pattern_type','span_message_ids','escalation_index','contradicts_finding_id')) AS finding_span_cols,
  (SELECT count(*) FROM information_schema.columns
     WHERE table_schema='analysis' AND table_name='message' AND column_name IN ('is_read','hint_provenance')) AS message_new_cols,
  (SELECT count(*) FROM information_schema.tables
     WHERE table_schema IN ('analysis','public')
       AND table_name IN ('format_resolver','topic_code','app_setting','lexicon_sync'))                  AS new_tables,
  (SELECT count(*) FROM information_schema.views
     WHERE table_schema IN ('analysis','public')
       AND table_name IN ('vw_message_behavior','vw_message_sms','vw_message_imessage','vw_prompt_performance','vw_llm_cost_rollup')) AS new_views;
-- expect: topic_codes=10, clustering_settings=4, finding_span_cols=4, message_new_cols=2, new_tables=4, new_views=5

COMMIT;
\echo '--- 0008 COMMITTED ---'

-- ===========================================================================
-- UNDO (run manually if needed)
-- ===========================================================================
-- DROP VIEW IF EXISTS public.vw_llm_cost_rollup, public.vw_prompt_performance,
--   analysis.vw_message_imessage, analysis.vw_message_sms, analysis.vw_message_behavior;
-- ALTER TABLE analysis.finding DROP COLUMN IF EXISTS pattern_type, DROP COLUMN IF EXISTS span_message_ids,
--   DROP COLUMN IF EXISTS span_message_count, DROP COLUMN IF EXISTS span_start, DROP COLUMN IF EXISTS span_end,
--   DROP COLUMN IF EXISTS severity_progression, DROP COLUMN IF EXISTS escalation_index, DROP COLUMN IF EXISTS contradicts_finding_id;
-- ALTER TABLE analysis.tool_call_ledger DROP COLUMN IF EXISTS prompt_version;
-- ALTER TABLE analysis.behavior_category DROP COLUMN IF EXISTS is_enabled;
-- ALTER TABLE analysis.conversation DROP COLUMN IF EXISTS cluster_code, DROP COLUMN IF EXISTS cluster_reason;
-- ALTER TABLE analysis.message DROP COLUMN IF EXISTS is_read, DROP COLUMN IF EXISTS hint_provenance;
-- DROP TABLE IF EXISTS analysis.lexicon_sync, analysis.topic_code, analysis.format_resolver, public.app_setting;
