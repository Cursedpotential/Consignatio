# RESTART-0001 — Per-Source Raw Tables (DRAFT, not applied) · rev 2

**Changes this rev:** hash placement DECIDED = Option A · added `conversation_key` + `participants` to every source (raw thread grouping, per your note).

```sql
-- =====================================================================================
-- RESTART-0001 — PER-SOURCE RAW TABLES (the ONLY ingestion step)  · DRAFT, not applied
-- =====================================================================================
--  Clean restart. The old detection/normalized_record/enrichment schemes are DEAD.
--  This is deliverable 1: a raw table PER SOURCE. Ingestion does exactly three things
--  and NOTHING else:
--    1. Read the source file in ITS ENTIRETY — every field the parser extracts lands
--       here. Typed columns for the first-class fields; `raw` JSONB captures the
--       COMPLETE parser output so nothing is ever dropped (full-fidelity guarantee).
--    2. UUIDv7 per message (message_uuid).
--    3. The 3-LEVEL CUSTODY HASH (canon 2026-07-02):
--         H1  h1-rawbytes-v1  = sha256(raw file bytes)                         [per file]
--         H2  h2-canonical-v2 = sha256(utf8( file_hex |seq|role|occurred_at|content ))
--                               occurred_at = 'YYYY-MM-DD HH:MM:SS+00:00'      [per msg]
--         H3  h3-chain-v1     = sha256(ascii( prev_hex + h2_hex )); genesis prev = H1
--                               chain head sealed per-file in source_file_custody     [chain]
--  NO analysis. NO inference. NO normalization. NO chunking. Those are separate lanes /
--  later steps (a segment table will group message_uuids AFTER this — TBD).
--
--  HASH PLACEMENT — DECIDED: Option A (h1/h2/h3 as columns on the row). H2/H3 are a
--  property of the row's own bytes, computed once at ingest; on-row = self-verifying,
--  no join to walk the chain. File-level H1 + sealed chain head live in file_custody.
--  The JSON evidence sidecar is a downstream EXPORT artifact populated FROM these columns.
--
--  CONVERSATION GROUPING (owner req 2026-07-06): every message row carries a raw
--  `conversation_key` = the source-native thread identifier (NOT inference — it's in the
--  data) + `participants` (raw handle list, for group threads). A single SMS-B&R or
--  iMessage file may contain MANY conversations (esp. a backup from the other party's
--  phone): GROUP BY conversation_key separates them. Verbatim numbers/handles, no PII
--  redaction. Derivation per source noted on each table.
--  (superseded note; Option A shown below):
--    A) hashes as columns ON each source row (h1/h2/h3). Simple, 1:1 with the message.
--    B) a separate source.message_custody(message_uuid, h1, h2, h3, prev_uuid) table
--       (custody as its own lane). Commented at the bottom — flip if you prefer B.
--
--  Lane: schema `source` = the raw-evidence lane. One row = one message/record, verbatim.
--  Requires PG18 (uuidv7() native). Idempotent (IF NOT EXISTS). REVIEW BEFORE APPLYING.
-- =====================================================================================

CREATE SCHEMA IF NOT EXISTS source;

-- Per-FILE custody anchor (H1 + sealed chain head). One row per ingested file.
CREATE TABLE IF NOT EXISTS source.file_custody (
  file_uuid       uuid PRIMARY KEY DEFAULT uuidv7(),
  source_file     text NOT NULL,                    -- original path / object key
  source_platform text NOT NULL,                    -- imessage|sms|facebook|ai_chat|...
  h1_file         bytea NOT NULL CHECK (octet_length(h1_file)=32),   -- h1-rawbytes-v1
  chain_head      bytea CHECK (octet_length(chain_head)=32),         -- sealed final H3
  message_count   integer NOT NULL DEFAULT 0,
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (h1_file)                                   -- same bytes = same file (dedupe)
);

-- ---------------------------------------------------------------------------
-- Reusable per-message raw-lane columns (documented once; repeated per table):
--   message_uuid    uuid PK  (uuidv7)
--   file_uuid       -> source.file_custody
--   source_format   parser id ('imessage-html','imessage-txt','sms-xml',...)
--   sequence_number document order within the file  (H2 input; preserve order)
--   occurred_at     parsed timestamptz              (H2 input)
--   raw_timestamp   verbatim timestamp string as in the source
--   sender_label    verbatim sender as written in the source (NOT resolved identity)
--   role            'owner'|'other'|'user'|'assistant'|... (H2 input)
--   direction       inbound|outbound|unknown
--   content         verbatim message text           (H2 input; never edited)
--   raw             jsonb — COMPLETE parser output (full-fidelity backstop)
--   h2_message      bytea  h2-canonical-v2
--   h3_chain        bytea  h3-chain-v1 (nullable until chain built)
--   ingested_at     timestamptz
-- ---------------------------------------------------------------------------

-- ============================ iMessage ============================
CREATE TABLE IF NOT EXISTS source.imessage (
  message_uuid    uuid PRIMARY KEY DEFAULT uuidv7(),
  file_uuid       uuid NOT NULL REFERENCES source.file_custody(file_uuid),
  source_format   text NOT NULL,                    -- imessage-html | imessage-txt | imessage-pdf
  sequence_number bigint NOT NULL,
  occurred_at     timestamptz,
  raw_timestamp   text,
  sender_label    text,
  role            text,
  direction       text CHECK (direction IN ('inbound','outbound','unknown')),
  content         text NOT NULL DEFAULT '',
  conversation_key text,                            -- iMessage: chat_identifier / handle (the +1810… thread)
  participants     jsonb NOT NULL DEFAULT '[]'::jsonb,
  -- iMessage first-class fields (from the parser; everything also in `raw`)
  service         text,                             -- iMessage | SMS
  is_from_me      boolean,
  chat_identifier text,
  attachments     jsonb NOT NULL DEFAULT '[]'::jsonb,
  tapbacks        jsonb NOT NULL DEFAULT '[]'::jsonb,
  edited_history  jsonb NOT NULL DEFAULT '[]'::jsonb,
  read_receipts   jsonb NOT NULL DEFAULT '[]'::jsonb,
  reply_block     text,
  transcriptions  jsonb NOT NULL DEFAULT '[]'::jsonb,
  is_deleted      boolean NOT NULL DEFAULT false,
  is_reply        boolean NOT NULL DEFAULT false,
  is_call         boolean NOT NULL DEFAULT false,
  raw             jsonb NOT NULL DEFAULT '{}'::jsonb,
  h2_message      bytea NOT NULL CHECK (octet_length(h2_message)=32),
  h3_chain        bytea CHECK (octet_length(h3_chain)=32),
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (file_uuid, sequence_number)
);
CREATE INDEX IF NOT EXISTS ix_imsg_file ON source.imessage(file_uuid);
CREATE INDEX IF NOT EXISTS ix_imsg_time ON source.imessage(occurred_at);
CREATE INDEX IF NOT EXISTS ix_imsg_conv ON source.imessage(conversation_key);

-- ============================ SMS / MMS (SMS Backup & Restore XML) ============================
CREATE TABLE IF NOT EXISTS source.sms (
  message_uuid    uuid PRIMARY KEY DEFAULT uuidv7(),
  file_uuid       uuid NOT NULL REFERENCES source.file_custody(file_uuid),
  source_format   text NOT NULL DEFAULT 'sms-xml',
  sequence_number bigint NOT NULL,
  occurred_at     timestamptz,
  raw_timestamp   text,
  sender_label    text,
  role            text,
  direction       text CHECK (direction IN ('inbound','outbound','unknown')),
  content         text NOT NULL DEFAULT '',
  conversation_key text,                            -- SMS: the address (other party) = the conversation
  participants     jsonb NOT NULL DEFAULT '[]'::jsonb,  -- group MMS = all addresses
  channel         text,                             -- sms | mms
  address         text,                             -- phone number as in source (verbatim)
  contact_name    text,
  raw_type        text,                             -- original SMS/MMS type code
  mms_parts       jsonb NOT NULL DEFAULT '[]'::jsonb,
  raw             jsonb NOT NULL DEFAULT '{}'::jsonb,
  h2_message      bytea NOT NULL CHECK (octet_length(h2_message)=32),
  h3_chain        bytea CHECK (octet_length(h3_chain)=32),
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (file_uuid, sequence_number)
);
CREATE INDEX IF NOT EXISTS ix_sms_file ON source.sms(file_uuid);
CREATE INDEX IF NOT EXISTS ix_sms_time ON source.sms(occurred_at);
CREATE INDEX IF NOT EXISTS ix_sms_conv ON source.sms(conversation_key);

-- ============================ Phone calls (from the same XML; NOT messages) ============================
CREATE TABLE IF NOT EXISTS source.phone_call (
  call_uuid        uuid PRIMARY KEY DEFAULT uuidv7(),
  file_uuid        uuid NOT NULL REFERENCES source.file_custody(file_uuid),
  source_format    text NOT NULL DEFAULT 'sms-xml',
  sequence_number  bigint NOT NULL,
  occurred_at      timestamptz,
  raw_timestamp    text,
  address          text,
  contact_name     text,
  conversation_key text,                            -- = address (the other party)
  direction        text CHECK (direction IN ('inbound','outbound','unknown')),
  call_type        text,                            -- incoming|outgoing|missed|rejected|blocked|voicemail
  duration_seconds integer NOT NULL DEFAULT 0,
  blocked          boolean NOT NULL DEFAULT false,
  raw_type         text,
  forensic_flags   jsonb NOT NULL DEFAULT '[]'::jsonb,
  raw              jsonb NOT NULL DEFAULT '{}'::jsonb,
  h2_message       bytea NOT NULL CHECK (octet_length(h2_message)=32),
  h3_chain         bytea CHECK (octet_length(h3_chain)=32),
  ingested_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (file_uuid, sequence_number)
);
CREATE INDEX IF NOT EXISTS ix_call_file ON source.phone_call(file_uuid);

-- ============================ Facebook Messenger (HTML / JSON DYI) ============================
CREATE TABLE IF NOT EXISTS source.facebook (
  message_uuid    uuid PRIMARY KEY DEFAULT uuidv7(),
  file_uuid       uuid NOT NULL REFERENCES source.file_custody(file_uuid),
  source_format   text NOT NULL,                    -- facebook-html | facebook-json
  sequence_number bigint NOT NULL,
  occurred_at     timestamptz,
  raw_timestamp   text,
  sender_label    text,
  role            text,
  direction       text CHECK (direction IN ('inbound','outbound','unknown')),
  content         text NOT NULL DEFAULT '',
  conversation_key text,                            -- Facebook: thread id
  participants     jsonb NOT NULL DEFAULT '[]'::jsonb,
  thread          text,                             -- conversation/thread id
  msg_type        text,                             -- text | photo | video | audio | call | share
  reactions       jsonb NOT NULL DEFAULT '[]'::jsonb,
  raw             jsonb NOT NULL DEFAULT '{}'::jsonb,
  h2_message      bytea NOT NULL CHECK (octet_length(h2_message)=32),
  h3_chain        bytea CHECK (octet_length(h3_chain)=32),
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (file_uuid, sequence_number)
);
CREATE INDEX IF NOT EXISTS ix_fb_file ON source.facebook(file_uuid);
CREATE INDEX IF NOT EXISTS ix_fb_time ON source.facebook(occurred_at);
CREATE INDEX IF NOT EXISTS ix_fb_conv ON source.facebook(conversation_key);

-- ============================ Tabular messaging CSV (iMazing / AnyTrans / generic export) ============================
CREATE TABLE IF NOT EXISTS source.messaging_csv (
  message_uuid     uuid PRIMARY KEY DEFAULT uuidv7(),
  file_uuid        uuid NOT NULL REFERENCES source.file_custody(file_uuid),
  source_format    text NOT NULL DEFAULT 'messaging-csv',
  sequence_number  bigint NOT NULL,
  occurred_at      timestamptz,
  raw_timestamp    text,
  sender_label     text,
  role             text,
  direction        text CHECK (direction IN ('inbound','outbound','unknown')),
  content          text NOT NULL DEFAULT '',
  conversation_key text,                            -- CSV: chat_session / derived from participants
  participants     jsonb NOT NULL DEFAULT '[]'::jsonb,
  detected_service text,                            -- imessage | sms | generic (from `service` column)
  chat_session     text,
  raw_row          jsonb NOT NULL DEFAULT '{}'::jsonb,  -- EVERY original column, verbatim (forensic contract)
  raw              jsonb NOT NULL DEFAULT '{}'::jsonb,
  h2_message       bytea NOT NULL CHECK (octet_length(h2_message)=32),
  h3_chain         bytea CHECK (octet_length(h3_chain)=32),
  ingested_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (file_uuid, sequence_number)
);
CREATE INDEX IF NOT EXISTS ix_csv_file ON source.messaging_csv(file_uuid);

-- ============================ AI chat transcripts (ChatGPT / Claude / Gemini / Perplexity) ============================
CREATE TABLE IF NOT EXISTS source.ai_chat (
  message_uuid       uuid PRIMARY KEY DEFAULT uuidv7(),
  file_uuid          uuid NOT NULL REFERENCES source.file_custody(file_uuid),
  source_format      text NOT NULL,                 -- transcripts.chatgpt-official | ...claude-code | ...
  provider           text,                          -- chatgpt | claude | gemini | perplexity
  sequence_number    bigint NOT NULL,
  occurred_at        timestamptz,
  raw_timestamp      text,
  role               text,                           -- user | assistant | system | tool
  content            text NOT NULL DEFAULT '',
  content_type       text,                           -- text | code | ...
  conversation_key   text,                           -- = conversation_id (uniform grouping column)
  conversation_id    text,                           -- original export conversation id (deterministic)
  conversation_title text,
  model              text,
  raw                jsonb NOT NULL DEFAULT '{}'::jsonb,
  h2_message         bytea NOT NULL CHECK (octet_length(h2_message)=32),
  h3_chain           bytea CHECK (octet_length(h3_chain)=32),
  ingested_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (file_uuid, sequence_number)
);
CREATE INDEX IF NOT EXISTS ix_ai_file ON source.ai_chat(file_uuid);
CREATE INDEX IF NOT EXISTS ix_ai_conv ON source.ai_chat(conversation_id);

-- =====================================================================================
-- LATER (NOT this deliverable) — the segment/chunk table that groups message_uuids into
-- conversations (segmenter_configurable.py, 0.65 similarity + time-gap). Sketch only:
--   CREATE TABLE source.segment (segment_uuid uuid PK, source_platform text, ...);
--   CREATE TABLE source.segment_member (segment_uuid uuid, message_uuid uuid, ord int);
--
-- OPTION B (REJECTED — chose A). Kept for the record only:
--   CREATE TABLE source.message_custody (
--     message_uuid uuid PRIMARY KEY, file_uuid uuid NOT NULL REFERENCES source.file_custody,
--     prev_uuid uuid, h2_message bytea NOT NULL, h3_chain bytea,
--     hash_canon text NOT NULL DEFAULT 'h2-canonical-v2/h3-chain-v1');
--   -- and drop h2_message/h3_chain from the source tables above.
-- =====================================================================================
```
