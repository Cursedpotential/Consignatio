-- Byline: Claude Code · Opus 5 · 2026-09-18
-- elt_ai_chatgpt_v1 -- ChatGPT data export `conversations.json`
-- Signature: top-level array of objects carrying `mapping` (node id -> {message:{author:{role},content}}).
-- Pure DuckDB (owner 2026-09-18 20:12 EDT: ALL extraction via the DuckDB ELT process).
--
-- Bound by the driver: src, vault_key, sha1, catalog_path, zip_member_path, modtime, run_id.
-- Timestamps: message.create_time is epoch SECONDS in UTC -> utc_known. Missing -> NULL + 'missing'.

insert into ai_turns
with raw as (
  select
    coalesce(conversation_id, id, md5(coalesce(title,'') || coalesce(create_time::VARCHAR,''))) as conversation_id,
    title,
    mapping
  from read_json(getvariable('src'),
                 format = 'array',
                 maximum_object_size = 1073741824,
                 columns = {title:'VARCHAR', create_time:'DOUBLE', conversation_id:'VARCHAR',
                            id:'VARCHAR', mapping:'JSON'})
  where mapping is not null
),
nodes as (
  select conversation_id, title, unnest(map_entries(mapping::MAP(VARCHAR, JSON))) as e
  from raw
),
msg as (
  select conversation_id, title, e.key as node_id, json_extract(e.value, '$.message') as m
  from nodes
),
turn as (
  select
    conversation_id,
    title,
    node_id,
    json_extract_string(m, '$.author.role')          as role_raw,
    try_cast(json_extract(m, '$.create_time') as DOUBLE) as ct,
    json_extract_string(m, '$.content.content_type') as content_type,
    json_extract(m, '$.content.parts')               as parts,
    json_extract_string(m, '$.content.text')         as ctext,
    try_cast(json_extract_string(m, '$.metadata.is_visually_hidden_from_conversation') as BOOLEAN) as hidden
  from msg
  where m is not null and json_type(m) = 'OBJECT'
),
bodied as (
  select
    conversation_id, title, node_id, role_raw, ct, content_type,
    coalesce(
      nullif(array_to_string(
        list_filter(
          list_transform(
            coalesce(try_cast(from_json(parts, '["JSON"]') as JSON[]), []),
            x -> case when json_type(x) = 'VARCHAR' then json_extract_string(x, '$')
                      else json_extract_string(x, '$.text') end),
          y -> y is not null and length(trim(y)) > 0),
        chr(10)), ''),
      ctext) as body,
    hidden
  from turn
),
ordered as (
  select *,
         row_number() over (partition by conversation_id
                            order by ct nulls last, node_id) as turn_index
  from bodied
  where body is not null and length(trim(body)) > 0
    and coalesce(hidden, false) = false
    and coalesce(role_raw, '') not in ('system')
)
select
  getvariable('vault_key')                              as vault_key,
  getvariable('sha1')                                   as sha1,
  getvariable('catalog_path')                           as catalog_path,
  nullif(getvariable('zip_member_path'), '')            as zip_member_path,
  try_cast(nullif(getvariable('modtime'), '') as TIMESTAMPTZ) as catalog_modtime_hint,
  'elt_ai_chatgpt_v1'                                   as extractor,
  getvariable('run_id')                                 as ingest_run_id,
  'chatgpt'                                             as service,
  'chatgpt_conversations_json'                          as source_format,
  conversation_id,
  title                                                 as conversation_title,
  turn_index,
  case lower(coalesce(role_raw, ''))
    when 'user' then 'owner' when 'human' then 'owner'
    when 'assistant' then 'assistant' when 'model' then 'assistant'
    when 'tool' then 'tool' else 'other' end            as speaker,
  role_raw,
  body,
  case when ct is not null and ct > 0 then to_timestamp(ct) end as event_ts_utc,
  case when ct is not null and ct > 0 then ct::VARCHAR end     as ts_original,
  case when ct is not null and ct > 0 then 'utc_known' else 'missing' end as tz_status
from ordered;
