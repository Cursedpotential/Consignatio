-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- elt_imessage_txt_v1 — iMessage/SMS text export ("Conversation: +1…" then "[YYYY-MM-DD hh:mm AM] Sender:")
-- -> event contract, DuckDB only (read_text + line grouping + RE2). Also covers imessage-exporter txt.
-- The bracket timestamp has no zone (phone local time) -> tz_status local_unknown_tz, sort_ts only.
with lines as (
  select generate_subscripts(l, 1) as ln, unnest(l) as line, conv
  from (select string_split(replace(content, chr(13), ''), chr(10)) as l,
               coalesce(nullif(regexp_extract(content, '^Conversation: *([^\n]*)', 1), ''),
                        regexp_extract('{{SRC}}', '([^/]+)\.[A-Za-z]+$', 1)) as conv
        from read_text('{{SRC}}'))
),
marked as (
  select *, regexp_extract(line, '^\[([0-9]{4}-[0-9]{2}-[0-9]{2}[^\]]*)\] *(.*?):\s*$', 1) as ts_raw,
            regexp_extract(line, '^\[([0-9]{4}-[0-9]{2}-[0-9]{2}[^\]]*)\] *(.*?):\s*$', 2) as who
  from lines
),
grouped as (
  select *, sum(case when ts_raw <> '' then 1 else 0 end) over (order by ln rows unbounded preceding) as msg_no
  from marked
),
msgs as (
  select msg_no,
    min(conv) as conv,
    max(ts_raw) filter (where ts_raw <> '') as ts_raw,
    max(who) filter (where ts_raw <> '') as who,
    min(ln) as ln,
    trim(array_to_string(array_agg(line order by ln) filter (where ts_raw = ''), chr(10))) as body
  from grouped where msg_no > 0 group by msg_no
)
select
  row_number() over (order by ln) - 1 as record_index,
  null::timestamptz as event_ts_utc,
  coalesce(try_strptime(ts_raw, '%Y-%m-%d %I:%M %p'), try_strptime(ts_raw, '%Y-%m-%d %H:%M:%S'),
           try_strptime(ts_raw, '%Y-%m-%d %I:%M:%S %p'), try_strptime(ts_raw, '%Y-%m-%d %H:%M')) as sort_ts,
  ts_raw as ts_original,
  'bracket_prefix(local,no_tz)' as ts_field,
  case when coalesce(try_strptime(ts_raw, '%Y-%m-%d %I:%M %p'), try_strptime(ts_raw, '%Y-%m-%d %H:%M:%S'),
                     try_strptime(ts_raw, '%Y-%m-%d %I:%M:%S %p'), try_strptime(ts_raw, '%Y-%m-%d %H:%M')) is null
       then 'unparsed' else 'local_unknown_tz' end as tz_status,
  'message' as event_kind,
  conv as conversation_id, conv as conversation_title,
  null::varchar[] as participants,
  case when lower(who) in ('me', 'owner', 'matt', 'matt salem') then 'owner' else who end as sender,
  case when lower(who) in ('me', 'owner', 'matt', 'matt salem') then [conv] else ['owner'] end as recipients,
  case when lower(who) in ('me', 'owner', 'matt', 'matt salem') then 'sent' else 'received' end as direction,
  right(regexp_replace(conv, '[^0-9]', '', 'g'), 10) as counterparty_phone,
  null::varchar as contact_name,
  body,
  null::varchar as attachments,
  null::varchar as member_path
from msgs where ts_raw is not null;
