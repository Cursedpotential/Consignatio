-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- elt_google_voice_html_v1 — Google Takeout "Voice/Calls" hChatLog HTML -> event contract, DuckDB only.
-- Engine: read_text + RE2 (the markup is a fixed microformat: div.message / abbr.dt / cite.sender / q).
-- Block "text" = SMS threads exported as chat logs; block "call" = placed/received/missed/voicemail pages.
-- Timestamps are ISO-8601 WITH offset in abbr@title, so these are utc_known.

-- @block text
select
  i - 1 as record_index,
  strptime(regexp_extract(chunk, '<abbr class="dt" title="([^"]+)"', 1), '%Y-%m-%dT%H:%M:%S.%f%z') as event_ts_utc,
  null::timestamp as sort_ts,
  regexp_extract(chunk, '<abbr class="dt" title="([^"]+)"', 1) as ts_original,
  'abbr.dt@title(ISO,offset)' as ts_field,
  case when regexp_extract(chunk, '<abbr class="dt" title="([^"]+)"', 1) <> '' then 'utc_known' else 'missing' end as tz_status,
  'message' as event_kind,
  conv as conversation_id, conv as conversation_title,
  null::varchar[] as participants,
  html_unescape(coalesce(nullif(regexp_extract(chunk, 'class="fn"[^>]*>([^<]*)</', 1), ''),
                         nullif(regexp_extract(chunk, '<abbr class="fn" title="[^"]*">([^<]*)</abbr>', 1), ''),
                         regexp_extract(chunk, 'href="tel:([^"]+)"', 1))) as sender,
  null::varchar[] as recipients,
  case when regexp_extract(chunk, 'class="fn"[^>]*>([^<]*)</', 1) = 'Me'
         or regexp_extract(chunk, '<abbr class="fn" title="[^"]*">([^<]*)</abbr>', 1) = 'Me' then 'sent' else 'received' end as direction,
  right(regexp_replace(regexp_extract(chunk, 'href="tel:([^"]+)"', 1), '[^0-9]', '', 'g'), 10) as counterparty_phone,
  null::varchar as contact_name,
  trim(html_unescape(regexp_replace(regexp_extract(chunk, '<q>(.*?)</q>', 1), '<[^>]*>', ' ', 'g'))) as body,
  nullif(to_json(regexp_extract_all(chunk, '<img src="([^"]+)"', 1))::varchar, '[]') as attachments,
  null::varchar as member_path
from (
  select generate_subscripts(parts, 1) as i, unnest(parts) as chunk, conv
  from (select string_split(content, '<div class="message">') as parts,
               trim(html_unescape(regexp_replace(regexp_extract(content, '<title>(.*?)</title>', 1), '\s+', ' ', 'g'))) as conv
        from read_text('{{SRC}}'))
)
where chunk like '%<abbr class="dt"%';

-- @block call
select
  0 as record_index,
  strptime(regexp_extract(content, 'class="published" title="([^"]+)"', 1), '%Y-%m-%dT%H:%M:%S.%f%z') as event_ts_utc,
  null::timestamp as sort_ts,
  regexp_extract(content, 'class="published" title="([^"]+)"', 1) as ts_original,
  'abbr.published@title(ISO,offset)' as ts_field,
  case when regexp_extract(content, 'class="published" title="([^"]+)"', 1) <> '' then 'utc_known' else 'missing' end as tz_status,
  'call' as event_kind,
  conv as conversation_id, conv as conversation_title,
  null::varchar[] as participants,
  html_unescape(coalesce(nullif(regexp_extract(content, 'class="fn"[^>]*>([^<]*)</', 1), ''),
                         regexp_extract(content, 'href="tel:([^"]+)"', 1))) as sender,
  null::varchar[] as recipients,
  lower(regexp_extract(conv, '(Placed|Received|Missed|Voicemail|Recorded)', 1)) as direction,
  right(regexp_replace(regexp_extract(content, 'href="tel:([^"]+)"', 1), '[^0-9]', '', 'g'), 10) as counterparty_phone,
  null::varchar as contact_name,
  trim(html_unescape(regexp_replace(
       coalesce(nullif(regexp_extract(content, 'class="full-text"[^>]*>(.*?)</span>', 1), ''),
                nullif(regexp_extract(content, '<div class="haudio">(.*?)</div>', 1), ''),
                conv), '<[^>]*>', ' ', 'g'))) as body,
  nullif(regexp_extract(content, 'class="duration" title="([^"]+)"', 1), '') as attachments,
  null::varchar as member_path
from (select content, trim(html_unescape(regexp_replace(regexp_extract(content, '<title>(.*?)</title>', 1), '\s+', ' ', 'g'))) as conv
      from read_text('{{SRC}}'))
where content not like '%<div class="message">%';
