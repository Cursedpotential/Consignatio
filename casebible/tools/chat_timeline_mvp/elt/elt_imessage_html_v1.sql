-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- elt_imessage_html_v1 — the bubble-style iMessage export pages in the vault ("index.html" per number:
-- div.bubble.from-me / .from-them followed by div.meta "Sender - YYYY-MM-DD hh:mm AM") -> event contract.
-- Engine: read_text + RE2. Timestamps are phone-local with no zone -> local_unknown_tz.
select
  i - 1 as record_index,
  null::timestamptz as event_ts_utc,
  coalesce(try_strptime(ts_raw, '%Y-%m-%d %I:%M %p'), try_strptime(ts_raw, '%Y-%m-%d %H:%M'),
           try_strptime(ts_raw, '%Y-%m-%d %I:%M:%S %p')) as sort_ts,
  ts_raw as ts_original,
  'div.meta(local,no_tz)' as ts_field,
  case when coalesce(try_strptime(ts_raw, '%Y-%m-%d %I:%M %p'), try_strptime(ts_raw, '%Y-%m-%d %H:%M'),
                     try_strptime(ts_raw, '%Y-%m-%d %I:%M:%S %p')) is null then 'unparsed' else 'local_unknown_tz' end as tz_status,
  'message' as event_kind,
  conv as conversation_id, conv as conversation_title,
  null::varchar[] as participants,
  case when lower(who) in ('me', 'owner', 'matt', 'matt salem') then 'owner' else who end as sender,
  case when lower(who) in ('me', 'owner', 'matt', 'matt salem') then [conv] else ['owner'] end as recipients,
  case when chunk like ' from-me%' then 'sent' else 'received' end as direction,
  right(regexp_replace(conv, '[^0-9]', '', 'g'), 10) as counterparty_phone,
  null::varchar as contact_name,
  body,
  nullif(to_json(regexp_extract_all(chunk, 'class=.attachment-img. src=.([^''"]+).', 1))::varchar, '[]') as attachments,
  null::varchar as member_path
from (
  select i, chunk, conv,
    trim(regexp_replace(regexp_extract(chunk, '^[^>]*>(.*?)</div>', 1), '<[^>]*>', ' ', 'g')) as body_raw,
    trim(html_unescape(regexp_replace(regexp_extract(chunk, '^[^>]*>(.*?)</div>', 1), '<[^>]*>', ' ', 'g'))) as body,
    trim(regexp_extract(chunk, 'class=.meta.>(.*?) - [0-9]{4}-', 1)) as who,
    trim(regexp_extract(chunk, 'class=.meta.>.*? - ([0-9]{4}-[0-9]{2}-[0-9]{2} [^<]*)</div>', 1)) as ts_raw
  from (
    select generate_subscripts(parts, 1) as i, unnest(parts) as chunk, conv
    from (select string_split(content, '<div class=''bubble') as parts,
                 trim(html_unescape(regexp_extract(content, '<title>(.*?)</title>', 1))) as conv
          from read_text('{{SRC}}'))
  )
)
where ts_raw <> '' or body <> '';
