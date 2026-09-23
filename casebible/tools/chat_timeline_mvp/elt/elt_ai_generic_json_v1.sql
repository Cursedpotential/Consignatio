-- Byline: Claude Code · Opus 5 · 2026-09-18
-- elt_ai_generic_json_v1 -- single-chat JSON exports carrying a role/content turn array
-- (Gemini web export, Claude single-chat export, AI Studio, LibreChat, generic tools).
-- Signature: JSON with "role"/"sender" + "content"/"text"/"parts" turn objects.
-- Timestamps are taken only when a turn actually carries one; otherwise NULL + 'missing'.

insert into ai_turns
with doc as (
  select json(content) as j from read_text(getvariable('src'))
),
arr as (
  select coalesce(
           json_extract(j, '$.messages'),
           json_extract(j, '$.chat_messages'),
           json_extract(j, '$.conversation'),
           json_extract(j, '$.chunkedPrompt.chunks'),
           json_extract(j, '$.turns'),
           json_extract(j, '$.history'),
           json_extract(j, '$.mapping'),
           case when json_type(j) = 'ARRAY' then j end) as a,
         coalesce(json_extract_string(j, '$.title'),
                  json_extract_string(j, '$.name'),
                  json_extract_string(j, '$.conversation_title')) as title,
         coalesce(json_extract_string(j, '$.uuid'),
                  json_extract_string(j, '$.id'),
                  json_extract_string(j, '$.conversation_id')) as cid
  from doc
),
msg as (
  select cid, title, generate_subscripts(l, 1) as turn_index, unnest(l) as m
  from (select cid, title, coalesce(try_cast(from_json(a, '["JSON"]') as JSON[]), []) as l from arr)
),
fields as (
  select cid, title, turn_index,
         coalesce(json_extract_string(m, '$.role'),   json_extract_string(m, '$.sender'),
                  json_extract_string(m, '$.author'), json_extract_string(m, '$.from'),
                  json_extract_string(m, '$.speaker'),
                  json_extract_string(m, '$.author.role')) as role_raw,
         coalesce(json_extract_string(m, '$.create_time'), json_extract_string(m, '$.created_at'),
                  json_extract_string(m, '$.timestamp'),   json_extract_string(m, '$.time'),
                  json_extract_string(m, '$.date'))        as ts_original,
         coalesce(
           case when json_type(json_extract(m, '$.content')) = 'VARCHAR'
                then json_extract_string(m, '$.content') end,
           nullif(trim(coalesce(json_extract_string(m, '$.text'), '')), ''),
           nullif(array_to_string(
             list_filter(
               list_transform(
                 coalesce(try_cast(from_json(coalesce(json_extract(m, '$.content'),
                                                      json_extract(m, '$.parts')), '["JSON"]') as JSON[]), []),
                 x -> coalesce(json_extract_string(x, '$.text'),
                               case when json_type(x) = 'VARCHAR' then json_extract_string(x, '$') end)),
               y -> y is not null and length(trim(y)) > 0),
             chr(10)), ''),
           nullif(trim(coalesce(json_extract_string(m, '$.message'), '')), '')
         ) as body
  from msg
)
select
  getvariable('vault_key'), getvariable('sha1'), getvariable('catalog_path'),
  nullif(getvariable('zip_member_path'), ''),
  try_cast(nullif(getvariable('modtime'), '') as TIMESTAMPTZ),
  'elt_ai_generic_json_v1', getvariable('run_id'),
  'other', 'ai_generic_json',
  coalesce(cid, md5(getvariable('vault_key') || coalesce(getvariable('zip_member_path'), ''))),
  title, turn_index,
  case
    when lower(coalesce(role_raw, '')) in ('user', 'human', 'me', 'you', 'prompt') then 'owner'
    when lower(coalesce(role_raw, '')) in ('assistant', 'model', 'ai', 'bot', 'gemini', 'claude', 'chatgpt', 'gpt')
      then 'assistant'
    when lower(coalesce(role_raw, '')) = 'system' then 'system'
    else 'other' end,
  role_raw, body,
  coalesce(try_cast(ts_original as TIMESTAMPTZ),
           case when try_cast(ts_original as DOUBLE) between 1000000000 and 4000000000
                then to_timestamp(try_cast(ts_original as DOUBLE)) end),
  ts_original,
  case when coalesce(try_cast(ts_original as TIMESTAMPTZ),
                     case when try_cast(ts_original as DOUBLE) between 1000000000 and 4000000000
                          then to_timestamp(try_cast(ts_original as DOUBLE)) end) is not null then 'utc_known'
       when ts_original is null then 'missing' else 'unparsed' end
from fields
where body is not null and length(trim(body)) > 0
  and role_raw is not null;
