-- Byline: Claude Code · Opus 5 · 2026-09-18
-- elt_ai_claude_v1 -- Claude data export `conversations.json`
-- Signature: top-level array of objects carrying `chat_messages[]` with `sender`.
-- created_at is an ISO-8601 UTC string -> utc_known; missing -> NULL + 'missing'.

insert into ai_turns
with raw as (
  select coalesce(uuid, md5(coalesce(name,'') || coalesce(created_at,''))) as conversation_id,
         coalesce(name, summary) as title,
         chat_messages
  from read_json(getvariable('src'),
                 format = 'array',
                 maximum_object_size = 1073741824,
                 columns = {uuid:'VARCHAR', name:'VARCHAR', summary:'VARCHAR',
                            created_at:'VARCHAR', chat_messages:'JSON'})
  where chat_messages is not null
),
msg as (
  select conversation_id, title,
         generate_subscripts(a, 1) as turn_index,
         unnest(a) as m
  from (select conversation_id, title,
               coalesce(try_cast(from_json(chat_messages, '["JSON"]') as JSON[]), []) as a
        from raw)
),
bodied as (
  select conversation_id, title, turn_index,
         json_extract_string(m, '$.sender')     as role_raw,
         json_extract_string(m, '$.created_at') as ts_original,
         coalesce(
           nullif(trim(coalesce(json_extract_string(m, '$.text'), '')), ''),
           nullif(array_to_string(
             list_filter(
               list_transform(
                 coalesce(try_cast(from_json(json_extract(m, '$.content'), '["JSON"]') as JSON[]), []),
                 x -> coalesce(json_extract_string(x, '$.text'),
                               case when json_type(x) = 'VARCHAR' then json_extract_string(x, '$') end)),
               y -> y is not null and length(trim(y)) > 0),
             chr(10)), '')
         ) as body
  from msg
)
select
  getvariable('vault_key'), getvariable('sha1'), getvariable('catalog_path'),
  nullif(getvariable('zip_member_path'), ''),
  try_cast(nullif(getvariable('modtime'), '') as TIMESTAMPTZ),
  'elt_ai_claude_v1', getvariable('run_id'),
  'claude', 'claude_conversations_json',
  conversation_id, title, turn_index,
  case lower(coalesce(role_raw, ''))
    when 'human' then 'owner' when 'user' then 'owner'
    when 'assistant' then 'assistant' else 'other' end,
  role_raw,
  body,
  try_cast(ts_original as TIMESTAMPTZ),
  ts_original,
  case when try_cast(ts_original as TIMESTAMPTZ) is not null then 'utc_known'
       when ts_original is null then 'missing' else 'unparsed' end
from bodied
where body is not null and length(trim(body)) > 0;
