-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Readable timeline in the catalog PG (casebible.raw_duck), so Metabase (tailnet) can show it tonight.
-- The loaded rows come from timeline_build.duckdb (events_dedup / event_provenance), piped in by load_pg.sh.
-- This is a read-copy for viewing; it is rebuilt by re-running load_pg.sh.
-- Why here as well as Surreal: surreal-intake hung twice under bulk INSERT on 2026-09-18 (see URGENT-TODO).
-- No person names in this file; the tags are computed upstream.

drop table if exists raw_duck.chat_events_20260918 cascade;
create table raw_duck.chat_events_20260918 (
  dedup_key text primary key, n_sources int, sort_ts timestamp, event_ts_utc timestamptz, tz_status text,
  ts_original text, ts_field text, source_format text, event_kind text, conversation_title text,
  conversation_id text, sender text, recipients text, participants text, direction text,
  counterparty_phone text, contact_name text, body text, attachments text,
  katrina_ref_type text, katrina_conf text, catrina_class text, daughter_conf text,
  custody_hit boolean, housing_hit boolean, vault_key text, catalog_rel text
);
drop table if exists raw_duck.chat_event_provenance_20260918;
create table raw_duck.chat_event_provenance_20260918 (
  dedup_key text, event_uid text, source_format text, extractor text, vault_key text, sha1 text,
  catalog_rel text, member_path text, record_index bigint, ts_original text, ts_field text
);
