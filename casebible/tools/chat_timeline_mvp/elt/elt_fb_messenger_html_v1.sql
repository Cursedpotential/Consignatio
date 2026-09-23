-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- elt_fb_messenger_html_v1 — Facebook/Messenger HTML export (message_N.html) -> event contract, DuckDB only.
-- Engine: read_text + RE2 over Meta's fixed obfuscated classes (verified on the 2024 and 2025 exports):
--   section/div class="_a6-g"            one message block
--   div class="_2ph_ _a6-h _a6-i"        sender name
--   div class="_2ph_ _a6-p"              content (may hold nested divs, links, attachment anchors)
--   div class="_3-94 _a6-o"              timestamp, e.g. "Aug 03, 2024 10:40:52pm"
-- The timestamp carries no zone; Meta writes the requester's local time (the export header states
-- UTC-04:00/-05:00 for this corpus), so it is read as America/Detroit and recorded as tz_inferred_local.
-- A JSON export of the same thread carries epoch MILLISECONDS, so second-precision HTML events do NOT
-- collapse onto their JSON twins; that is recorded, not hidden.
select
  i - 1 as record_index,
  case when ts_raw <> '' then strptime(ts_raw, '%b %d, %Y %I:%M:%S%p') at time zone 'America/Detroit' end as event_ts_utc,
  null::timestamp as sort_ts,
  ts_raw as ts_original,
  'div._3-94._a6-o(local,America/Detroit)' as ts_field,
  case when ts_raw <> '' then 'tz_inferred_local' else 'missing' end as tz_status,
  'message' as event_kind,
  conv as conversation_id, conv as conversation_title,
  null::varchar[] as participants,
  sender,
  null::varchar[] as recipients,
  null::varchar as direction,
  null::varchar as counterparty_phone,
  null::varchar as contact_name,
  body,
  nullif(to_json(regexp_extract_all(chunk, 'href="((?:your_facebook_activity|your_activity_across_facebook|messages)/[^"]*)"', 1))::varchar, '[]') as attachments,
  null::varchar as member_path
from (
  select i, chunk, conv,
    trim(html_unescape(regexp_extract(chunk, 'class="_2ph_ _a6-h _a6-i"[^>]*>(.*?)</div>', 1))) as sender,
    trim(regexp_extract(chunk, 'class="_3-94 _a6-o"[^>]*>([^<]*)<', 1)) as ts_raw,
    trim(regexp_replace(html_unescape(regexp_replace(
         regexp_extract(chunk, 'class="_2ph_ _a6-p"[^>]*>(.*?)<div class="_3-94 _a6-o"', 1),
         '<[^>]*>', ' ', 'g')), '\s+', ' ', 'g')) as body
  from (
    select generate_subscripts(parts, 1) as i, unnest(parts) as chunk, conv
    from (select string_split(content, 'class="_a6-g"') as parts,
                 trim(html_unescape(regexp_extract(content, 'class="_a70e">([^<]*)<', 1))) as conv
          from read_text('{{SRC}}'))
  )
)
where ts_raw <> '' or body <> '';
