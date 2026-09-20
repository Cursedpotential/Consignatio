-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Shared target table for every elt_ai_*_v1 template (the "same contract as a parser" rule,
-- owner 2026-09-04 18:14 EDT: "the exact same contract, just a different method of getting there").
--
-- Every template INSERTs rows shaped exactly like this. Provenance columns are bound by the
-- driver from the catalog; the template never invents them.
--   event_ts_utc  NULL whenever the source carries no usable timestamp. NEVER synthesised.
--   tz_status     utc_known | utc_from_offset | utc_from_named_zone | local_no_tz | missing | unparsed
--   catalog_modtime_hint  the catalog's file modtime. A HINT for ordering only, never an event time.

create table if not exists ai_turns (
  vault_key            VARCHAR,
  sha1                 VARCHAR,
  catalog_path         VARCHAR,
  zip_member_path      VARCHAR,
  catalog_modtime_hint TIMESTAMPTZ,
  extractor            VARCHAR,
  ingest_run_id        VARCHAR,
  service              VARCHAR,
  source_format        VARCHAR,
  conversation_id      VARCHAR,
  conversation_title   VARCHAR,
  turn_index           BIGINT,
  speaker              VARCHAR,
  role_raw             VARCHAR,
  body                 VARCHAR,
  event_ts_utc         TIMESTAMPTZ,
  ts_original          VARCHAR,
  tz_status            VARCHAR
);

create table if not exists ai_elt_attempts (
  ingest_run_id VARCHAR, template VARCHAR, vault_key VARCHAR, zip_member_path VARCHAR,
  sha1 VARCHAR, rows_out BIGINT, status VARCHAR, detail VARCHAR, ran_at TIMESTAMPTZ
);
