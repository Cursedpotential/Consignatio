-- Byline: Claude Code · Opus 5 · 2026-09-18
-- elt_ai_gemini_activity_v1 -- Google Takeout "My Activity / Gemini Apps" JSON
-- Signature: array of {header, title, titleUrl, time, products[]} with a Gemini/Bard header.
-- The owner's PROMPT is the `title` after the "Prompted " prefix; Google's reply is in
-- `subtitles[].name` when the export carries it. `time` is ISO-8601 UTC -> utc_known.

insert into ai_turns
with raw as (
  select generate_subscripts(a, 1) as rec_no, unnest(a) as r
  from (select coalesce(try_cast(from_json(json(content), '["JSON"]') as JSON[]), []) as a
        from read_text(getvariable('src')))
),
rec as (
  select rec_no,
         json_extract_string(r, '$.header') as header,
         json_extract_string(r, '$.title')  as title,
         json_extract_string(r, '$.time')   as ts_original,
         nullif(array_to_string(
           list_filter(
             list_transform(coalesce(try_cast(from_json(json_extract(r, '$.subtitles'), '["JSON"]') as JSON[]), []),
                            x -> json_extract_string(x, '$.name')),
             y -> y is not null and length(trim(y)) > 0),
           chr(10)), '') as reply
  from raw
  where json_extract_string(r, '$.header') is not null
),
owner_turn as (
  select rec_no, ts_original, 'owner' as speaker, 'prompt' as role_raw,
         regexp_replace(title, '^(?:Prompted|Asked|Searched for|Used)\s+', '') as body
  from rec
  where title is not null and length(trim(title)) > 0
),
reply_turn as (
  select rec_no, ts_original, 'assistant' as speaker, 'gemini' as role_raw, reply as body
  from rec
  where reply is not null
),
all_turns as (select * from owner_turn union all select * from reply_turn)
select
  getvariable('vault_key'), getvariable('sha1'), getvariable('catalog_path'),
  nullif(getvariable('zip_member_path'), ''),
  try_cast(nullif(getvariable('modtime'), '') as TIMESTAMPTZ),
  'elt_ai_gemini_activity_v1', getvariable('run_id'),
  'gemini', 'gemini_activity_json',
  md5(getvariable('vault_key') || '|' || coalesce(getvariable('zip_member_path'), '')),
  'Gemini Apps activity',
  row_number() over (order by ts_original nulls last, rec_no, speaker desc),
  speaker, role_raw, body,
  try_cast(ts_original as TIMESTAMPTZ), ts_original,
  case when try_cast(ts_original as TIMESTAMPTZ) is not null then 'utc_known'
       when ts_original is null then 'missing' else 'unparsed' end
from all_turns
where body is not null and length(trim(body)) > 0;
