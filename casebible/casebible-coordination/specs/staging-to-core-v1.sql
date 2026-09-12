-- staging-to-core-v1.sql
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-02
--
-- STAGING → MESSAGING-CORE WRITER, v1 (pilot conversation imessage:+18108532989).
-- Maps the 1,918 analysis.normalized_record rows (source='imessage-html') into the
-- proper messaging core: analysis.conversation + analysis.message +
-- analysis.message_participant. The 25 markdown-transcript staging rows are NOT
-- touched (context corpus, not evidence — they stay out of the core).
--
-- Design facts honored (live DDL, 2026-07-02 introspection):
--   * message.id FK -> normalized_record(id): core row KEEPS the staging UUID (1:1 lineage).
--   * serial_number = parser attrs.sequence_number (verified unique, 0..1917, no nulls).
--   * external_id  = attrs.message_hash (H2 custody hash, verified unique) — satisfies
--     UNIQUE(conversation_id, external_id) and ties each core row to the custody chain.
--   * direction CHECK: role 'me' -> outbound, 'them' -> inbound.
--   * content_sha256 = sha256(content) computed fresh (pgcrypto); H2/chain hashes kept
--     in platform_attrs; full staging attrs preserved in raw_data.
--   * sender_entity_id / handles / phones left NULL — entity resolution is a later,
--     separately-gated phase (handle/phone FK into analysis.entity).
--   * conversation.source_artifact_id -> evidence.evidence_hash (verified: all 1,918
--     staging rows join the single H1 artifact).
--
-- SELF-VERIFYING: the in-txn guard RAISEs (aborting everything, zero durable rows)
-- unless messages=1918, serials unique, chain endpoints exactly 1+1, directions legal,
-- participants=3836, conversation.message_count consistent.
--
-- Undo (scoped, reversible):
--   DELETE FROM analysis.message_participant WHERE message_id IN (SELECT id FROM analysis.message WHERE conversation_id = '<conv_id>');  -- (cascades anyway)
--   DELETE FROM analysis.message      WHERE conversation_id = '<conv_id>';
--   DELETE FROM analysis.conversation WHERE id = '<conv_id>';
--   DELETE FROM analysis.processing_run WHERE run_id = '<core_run_id>';

\set ON_ERROR_STOP on
BEGIN;

-- 1) provenance
INSERT INTO analysis.processing_run
    (run_type, run_purpose, status, actor, tool_or_model,
     ran_local_only, cloud_exposure, human_review_requirement, replayable, started_at, finished_at)
VALUES ('message_parsing',
        'staging-to-core v1: promote 1918 imessage-html normalized_record rows into conversation/message/message_participant (pilot conversation imessage:+18108532989)',
        'ok', 'staging-to-core-v1', 'sql set-based writer', true, false, true, true, now(), now())
RETURNING run_id AS core_run_id \gset

\echo '--- core writer run_id: ---'
\echo :core_run_id

-- 2) conversation (one row; UNIQUE(platform, external_thread_key) makes reruns fail loudly, not dup)
INSERT INTO analysis.conversation
    (source_artifact_id, platform, external_thread_key, participants, participant_count,
     primary_participant, primary_participant_e164, is_group, started_at, ended_at,
     message_count, is_evidence, data_tier, review_status, platform_attrs, provenance_id)
SELECT nr.artifact_id, 'imessage', nr.conversation_id,
       jsonb_build_array('me', '+18108532989'), 2,
       '+18108532989', '+18108532989', false,
       min(nr.occurred_at), max(nr.occurred_at),
       count(*), true, 'extracted'::evidence_tier, 'unreviewed'::review_state,
       jsonb_build_object('source_format','imessage-html',
                          'ingest_pass','bestoffort-v2-2026-06-26',
                          'tz_basis','America/New_York','tz_verified',false,
                          'writer','staging-to-core-v1'),
       :'core_run_id'
FROM analysis.normalized_record nr
WHERE nr.source = 'imessage-html'
GROUP BY nr.artifact_id, nr.conversation_id
RETURNING id AS conv_id \gset

\echo '--- conversation id: ---'
\echo :conv_id

-- 3) messages: 1:1 promotion, id preserved from staging
INSERT INTO analysis.message
    (id, conversation_id, ts_utc, platform, external_id, serial_number,
     sender_raw, sender_e164, recipient_raw, recipient_e164, direction,
     message_type, raw_ts, tz, word_count, char_count, content_sha256,
     extraction_confidence, platform_attrs, raw_data)
OVERRIDING SYSTEM VALUE
SELECT nr.id, :'conv_id', nr.occurred_at, 'imessage',
       nr.attrs->>'message_hash',
       (nr.attrs->>'sequence_number')::bigint,
       CASE nr.role WHEN 'me' THEN 'me' ELSE '+18108532989' END,
       CASE nr.role WHEN 'me' THEN NULL ELSE '+18108532989' END,
       CASE nr.role WHEN 'me' THEN '+18108532989' ELSE 'me' END,
       CASE nr.role WHEN 'me' THEN '+18108532989' ELSE NULL END,
       CASE nr.role WHEN 'me' THEN 'outbound' WHEN 'them' THEN 'inbound' ELSE 'unknown' END,
       'text',
       nr.attrs->>'occurred_at_original',
       nr.attrs->>'tz_basis',
       CASE WHEN btrim(nr.content) = '' THEN 0
            ELSE array_length(regexp_split_to_array(btrim(nr.content), '\s+'), 1) END,
       length(nr.content),
       public.digest(convert_to(nr.content, 'UTF8'), 'sha256'),
       CASE WHEN (nr.attrs->>'provisional')::boolean THEN 0.8 ELSE 1.0 END,
       jsonb_build_object('message_hash', nr.attrs->>'message_hash',
                          'chain_entry_hash', nr.attrs->>'chain_entry_hash',
                          'chain_previous_hash', nr.attrs->>'chain_previous_hash',
                          'file_hash', nr.attrs->>'file_hash',
                          'parser', nr.attrs->>'parser'),
       nr.attrs
FROM analysis.normalized_record nr
WHERE nr.source = 'imessage-html';

-- 4) chain links: prev/next + seconds-since-previous, ordered by parser sequence
WITH ordered AS (
  SELECT id,
         lag(id)  OVER w AS prev_id,
         lead(id) OVER w AS next_id,
         extract(epoch FROM ts_utc - lag(ts_utc) OVER w)::int AS dt
  FROM analysis.message
  WHERE conversation_id = :'conv_id'
  WINDOW w AS (ORDER BY serial_number)
)
UPDATE analysis.message m
SET prev_message_id = o.prev_id, next_message_id = o.next_id, time_since_prev_s = o.dt
FROM ordered o WHERE m.id = o.id;

-- 5) participants: from + to per message
INSERT INTO analysis.message_participant (message_id, participant_raw, participant_e164, role)
SELECT id, sender_raw, sender_e164, 'from'
FROM analysis.message WHERE conversation_id = :'conv_id'
UNION ALL
SELECT id, recipient_raw, recipient_e164, 'to'
FROM analysis.message WHERE conversation_id = :'conv_id';

-- 6) ACCEPTANCE GUARD — abort everything on any structural failure
DO $guard$
DECLARE
  v_msgs int; v_serials int; v_no_prev int; v_no_next int;
  v_badgap int; v_parts int; v_convs int; v_conv_count int; v_sha_bad int;
BEGIN
  SELECT count(*), count(DISTINCT serial_number),
         count(*) FILTER (WHERE prev_message_id IS NULL),
         count(*) FILTER (WHERE next_message_id IS NULL),
         count(*) FILTER (WHERE time_since_prev_s < 0),
         count(*) FILTER (WHERE content_sha256 IS NULL OR octet_length(content_sha256) <> 32)
    INTO v_msgs, v_serials, v_no_prev, v_no_next, v_badgap, v_sha_bad
  FROM analysis.message m
  JOIN analysis.conversation c ON c.id = m.conversation_id
  WHERE c.external_thread_key = 'imessage:+18108532989';

  SELECT count(*) INTO v_parts FROM analysis.message_participant mp
  JOIN analysis.message m ON m.id = mp.message_id
  JOIN analysis.conversation c ON c.id = m.conversation_id
  WHERE c.external_thread_key = 'imessage:+18108532989';

  SELECT count(*), max(message_count) INTO v_convs, v_conv_count
  FROM analysis.conversation WHERE external_thread_key = 'imessage:+18108532989';

  RAISE NOTICE 'acceptance: msgs=% serials=% chain_head=% chain_tail=% neg_gaps=% bad_sha=% parts=% convs=% conv.message_count=%',
    v_msgs, v_serials, v_no_prev, v_no_next, v_badgap, v_sha_bad, v_parts, v_convs, v_conv_count;

  IF v_msgs <> 1918 OR v_serials <> 1918 THEN
    RAISE EXCEPTION 'ABORT: expected 1918 messages with unique serials, got msgs=% serials=%', v_msgs, v_serials;
  END IF;
  IF v_no_prev <> 1 OR v_no_next <> 1 THEN
    RAISE EXCEPTION 'ABORT: chain endpoints wrong (heads=%, tails=%) — must be exactly 1 each', v_no_prev, v_no_next;
  END IF;
  IF v_badgap > 0 THEN
    RAISE EXCEPTION 'ABORT: % messages with negative time_since_prev_s (ordering broken)', v_badgap;
  END IF;
  IF v_sha_bad > 0 THEN
    RAISE EXCEPTION 'ABORT: % messages with missing/malformed content_sha256', v_sha_bad;
  END IF;
  IF v_parts <> 3836 THEN
    RAISE EXCEPTION 'ABORT: expected 3836 participant rows (2 x 1918), got %', v_parts;
  END IF;
  IF v_convs <> 1 OR v_conv_count <> 1918 THEN
    RAISE EXCEPTION 'ABORT: conversation row wrong (rows=%, message_count=%)', v_convs, v_conv_count;
  END IF;
END
$guard$;

-- 7) acceptance summary (visible output)
\echo '--- ACCEPTANCE SUMMARY ---'
SELECT c.external_thread_key, c.message_count,
       to_char(c.started_at,'YYYY-MM-DD') AS first_msg, to_char(c.ended_at,'YYYY-MM-DD') AS last_msg,
       (SELECT count(*) FROM analysis.message m WHERE m.conversation_id=c.id AND m.direction='outbound') AS outbound_me,
       (SELECT count(*) FROM analysis.message m WHERE m.conversation_id=c.id AND m.direction='inbound')  AS inbound_them,
       (SELECT count(*) FROM analysis.message_participant mp JOIN analysis.message m ON m.id=mp.message_id WHERE m.conversation_id=c.id) AS participant_rows
FROM analysis.conversation c WHERE c.external_thread_key='imessage:+18108532989';

COMMIT;
\echo '--- COMMITTED — messaging core populated ---'
