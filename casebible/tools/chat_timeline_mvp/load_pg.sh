#!/bin/sh
# Byline: Claude Code · Opus 5 · 2026-09-18
# Copy the deduplicated timeline from the scratch DuckDB into casebible.raw_duck (read-copy for Metabase).
# Run on ovh-files from /data/probata/config/timeline-mvp/app.
set -e
PG=fgz1n7useplhk0t91uk7k1aw
W=/data/probata/volumes/timeline-mvp
docker exec -i $PG psql -U postgres -d casebible -v ON_ERROR_STOP=1 < pg_timeline_20260918.sql
dump() {
  docker run --rm -v $W:/work -v /data/probata/config/timeline-mvp/app:/app:ro chat-timeline-mvp:1 python /app/dump_csv.py "$1"
}
dump "select dedup_key, n_sources, sort_ts, event_ts_utc, tz_status, ts_original, ts_field, source_format, event_kind,
  conversation_title, conversation_id, sender, array_to_string(recipients, ' | '), array_to_string(participants, ' | '), direction,
  counterparty_phone, contact_name, replace(body, chr(0), ''), attachments, katrina_ref_type, katrina_conf, catrina_class, daughter_conf,
  custody_hit, housing_hit, vault_key, catalog_rel from events_dedup" \
 | docker exec -i $PG psql -U postgres -d casebible -v ON_ERROR_STOP=1 -c "\copy raw_duck.chat_events_20260918 from stdin with (format csv, header true)"
dump "select dedup_key, event_uid, source_format, extractor, vault_key, sha1, catalog_rel, member_path, record_index, ts_original, ts_field from event_provenance" \
 | docker exec -i $PG psql -U postgres -d casebible -v ON_ERROR_STOP=1 -c "\copy raw_duck.chat_event_provenance_20260918 from stdin with (format csv, header true)"
docker exec -i $PG psql -U postgres -d casebible -v ON_ERROR_STOP=1 < pg_timeline_views_20260918.sql
echo PG LOAD DONE
