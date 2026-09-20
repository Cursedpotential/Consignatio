-- Byline: Claude Code · Opus 5 · 2026-09-18
-- elt_ai_chat_memo_txt_v1 -- "Chat Memo - All Conversations" exporter (.txt)
-- Layout (verified against the real file on 2026-09-18):
--   # Chat Memo - All Conversations / Export Time: / Total Conversations: N
--   ==== separator ====
--   Title: ... / URL: https://chatgpt.com/c/<id> / Platform: ... / Created: ... / Messages: N
--   User: [YYYY-MM-DD HH:MM:SS]        <- marker line carries ONLY the label + timestamp
--   <body lines>
--   AI: [YYYY-MM-DD HH:MM:SS]
--   <body lines>
-- Per-message timestamps are LOCAL wall-clock with no zone: kept verbatim in ts_original,
-- event_ts_utc stays NULL, tz_status = 'local_no_tz'. Nothing is re-zoned or invented.

insert into ai_turns
with f as (select content from read_text(getvariable('src'))),
lines as (
  select generate_subscripts(a, 1) as ln, unnest(a) as line
  from (select str_split(replace(content, chr(13), ''), chr(10)) as a from f)
),
marked as (
  select ln, line,
    case when regexp_matches(line, '^(?:User|AI|Assistant|Human|You)[ \t]*:[ \t]*(\[|$)', 'i')
         then lower(regexp_extract(line, '^(User|AI|Assistant|Human|You)[ \t]*:', 1, 'i')) end as spk,
    nullif(regexp_extract(line, '^(?:User|AI|Assistant|Human|You)[ \t]*:[ \t]*\[([^\]]{0,48})\]', 1, 'i'), '') as ts_raw,
    case when line like 'Title: %' then trim(substr(line, 8)) end as title_val,
    case when line like 'URL: %'   then trim(substr(line, 6)) end as url_val,
    regexp_matches(line, '^(?:Title|URL|Platform|Created|Messages|Export Time|Total Conversations)[ \t]*:') as is_meta,
    regexp_matches(line, '^(?:=+|-{10,}|#+ Chat Memo)') as is_sep
  from lines
),
convd as (
  select *, sum(case when title_val is not null then 1 else 0 end)
              over (order by ln rows between unbounded preceding and current row) as conv_no
  from marked
),
convmeta as (
  select conv_no, max(title_val) as title, max(url_val) as url
  from convd where conv_no > 0 group by conv_no
),
grp as (
  select *, sum(case when spk is not null then 1 else 0 end)
              over (order by ln rows between unbounded preceding and current row) as turn_no
  from convd
),
turns as (
  select turn_no,
         max(case when spk is not null then conv_no end) as conv_no,
         max(spk) as spk_raw,
         min(ln)  as first_ln,
         max(case when spk is not null then ts_raw end) as ts_original,
         string_agg(case when spk is null and not is_meta and not is_sep then line end,
                    chr(10) order by ln) as body
  from grp
  where turn_no > 0
  group by turn_no
)
select
  getvariable('vault_key'), getvariable('sha1'), getvariable('catalog_path'),
  nullif(getvariable('zip_member_path'), ''),
  try_cast(nullif(getvariable('modtime'), '') as TIMESTAMPTZ),
  'elt_ai_chat_memo_txt_v1', getvariable('run_id'),
  case when m.url ilike '%chatgpt.com%' then 'chatgpt'
       when m.url ilike '%claude.ai%'   then 'claude'
       when m.url ilike '%gemini%'      then 'gemini'
       else 'other' end,
  'ai_chat_memo_txt',
  coalesce(nullif(regexp_extract(m.url, '/c/([A-Za-z0-9\-]+)', 1), ''),
           md5(getvariable('vault_key') || '|conv' || t.conv_no::VARCHAR)),
  m.title,
  row_number() over (partition by t.conv_no order by t.first_ln),
  case when t.spk_raw in ('user', 'human', 'you') then 'owner' else 'assistant' end,
  t.spk_raw,
  trim(t.body),
  NULL::TIMESTAMPTZ,
  t.ts_original,
  case when t.ts_original is not null then 'local_no_tz' else 'missing' end
from turns t
left join convmeta m on m.conv_no = t.conv_no
where trim(coalesce(t.body, '')) <> '';
