-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- elt_smsbackuprestore_v1 — SMS Backup & Restore export (sms / mms / call) -> event contract, DuckDB only.
-- Engine: webbed read_xml over the sanitized copy produced by elt_xml_sanitize_v1.sql ({{SRC}}).
--
-- Blocks are separated by "-- @block <name>"; the runner executes only the blocks whose record element the
-- file actually contains (read_xml errors when a record element is absent).
--
-- Field semantics mirror the 2026-08 decoder contract so the dedup key of an event is unchanged when the
-- same message is re-extracted here (dedup = counterparty phone + instant + kind + normalized body):
--   * sms/mms body: attribute body, or for MMS the text of every text/plain part joined with newline, trimmed;
--   * call body: the decoder's synthesized descriptor, including its forensic flags;
--   * event_kind: 'call' for <call>, otherwise 'message';
--   * counterparty_phone: last 10 digits of address/number.
-- Direction/sender are taken from msg_box for MMS (the decoder left MMS direction 'unknown'); that is an
-- improvement and does not move the dedup key.
-- ATTACHMENTS ARE LOCATOR-ONLY: the sanitizer replaced each part's base64 data with data_len + data_sha256.

-- @block sms
select
  row_number() over () - 1 as record_index,
  case when try_cast(date as bigint) > 0 then to_timestamp(try_cast(date as bigint) / 1000.0) end as event_ts_utc,
  null::timestamp as sort_ts,
  'date=' || coalesce(date, '') || '; readable_date=' || coalesce(readable_date, '') as ts_original,
  'date(epoch_ms,UTC)' as ts_field,
  case when try_cast(date as bigint) > 0 then 'utc_known' else 'missing' end as tz_status,
  'message' as event_kind,
  coalesce(nullif(regexp_replace(coalesce(address, ''), '[^0-9]', '', 'g'), ''), other) as conversation_id,
  other as conversation_title,
  ['owner', other] as participants,
  case when coalesce(type, '0') in ('2', '4', '5', '6') then 'owner' else other end as sender,
  case when coalesce(type, '0') in ('2', '4', '5', '6') then [other] else ['owner'] end as recipients,
  case coalesce(type, '0') when '1' then 'received' when '2' then 'sent' when '3' then 'draft'
       when '4' then 'outbox' when '5' then 'failed' when '6' then 'queued' else 'unknown' end as direction,
  right(regexp_replace(coalesce(address, ''), '[^0-9]', '', 'g'), 10) as counterparty_phone,
  contact_name,
  trim(coalesce(nullif(body, 'null'), '')) as body,
  null::varchar as attachments,
  null::varchar as member_path
from (
  select *, case when coalesce(trim(contact_name), '') not in ('', 'unknown', '(Unknown)', '(unknown)', 'null')
                 then trim(contact_name) else coalesce(nullif(trim(address), ''), 'unknown') end as other
  from read_xml('{{SRC}}', record_element := 'sms', maximum_file_size := 4000000000,
                columns := {'address': 'VARCHAR', 'date': 'VARCHAR', 'type': 'VARCHAR', 'body': 'VARCHAR',
                            'contact_name': 'VARCHAR', 'readable_date': 'VARCHAR', 'date_sent': 'VARCHAR'})
);

-- @block mms
select
  row_number() over () - 1 as record_index,
  case when try_cast(date as bigint) > 0 then to_timestamp(try_cast(date as bigint) / 1000.0) end as event_ts_utc,
  null::timestamp as sort_ts,
  'date=' || coalesce(date, '') || '; readable_date=' || coalesce(readable_date, '') as ts_original,
  'date(epoch_ms,UTC)' as ts_field,
  case when try_cast(date as bigint) > 0 then 'utc_known' else 'missing' end as tz_status,
  'message' as event_kind,
  coalesce(nullif(regexp_replace(coalesce(address, ''), '[^0-9]', '', 'g'), ''), other) as conversation_id,
  other as conversation_title,
  list_distinct(list_concat(['owner', other],
      coalesce(list_transform(list_filter(addrs.addr, a -> a.address is not null), a -> a.address), []))) as participants,
  case when msg_box = '2' then 'owner' else other end as sender,
  case when msg_box = '2'
       then coalesce(list_transform(list_filter(addrs.addr, a -> a."type" = '151'), a -> a.address), [other])
       else ['owner'] end as recipients,
  case msg_box when '1' then 'received' when '2' then 'sent' when '3' then 'draft' when '4' then 'outbox'
       else 'unknown' end as direction,
  right(regexp_replace(coalesce(address, ''), '[^0-9]', '', 'g'), 10) as counterparty_phone,
  contact_name,
  trim(coalesce(array_to_string(
      list_filter(list_transform(parts.part, p -> case when lower(coalesce(p.ct, '')) in ('text/plain', '')
                                                       and coalesce(p."text", '') not in ('', 'null')
                                                  then p."text" end),
                  x -> x is not null),
      chr(10)), '')) as body,
  case when len(list_filter(parts.part, p -> lower(coalesce(p.ct, '')) not in ('text/plain', 'application/smil', ''))) > 0
       then to_json(list_transform(
              list_filter(parts.part, p -> lower(coalesce(p.ct, '')) not in ('text/plain', 'application/smil', '')),
              p -> {'ct': lower(p.ct), 'name': coalesce(p.cl, p."name", ''),
                    'b64_len': try_cast(p.data_len as bigint), 'b64_sha256': p.data_sha256}))::varchar end as attachments,
  null::varchar as member_path
from (
  select *, case when coalesce(trim(contact_name), '') not in ('', 'unknown', '(Unknown)', '(unknown)', 'null')
                 then trim(contact_name) else coalesce(nullif(trim(address), ''), 'unknown') end as other
  from read_xml('{{SRC}}', record_element := 'mms', maximum_file_size := 4000000000,
                columns := {'address': 'VARCHAR', 'date': 'VARCHAR', 'msg_box': 'VARCHAR', 'contact_name': 'VARCHAR',
                            'readable_date': 'VARCHAR', 'date_sent': 'VARCHAR', 'm_type': 'VARCHAR',
                            'parts': 'STRUCT(part STRUCT(seq VARCHAR, ct VARCHAR, "name" VARCHAR, cl VARCHAR, "text" VARCHAR, data_len VARCHAR, data_sha256 VARCHAR)[])',
                            'addrs': 'STRUCT(addr STRUCT(address VARCHAR, "type" VARCHAR)[])'})
);

-- @block call
select
  row_number() over () - 1 as record_index,
  case when try_cast(date as bigint) > 0 then to_timestamp(try_cast(date as bigint) / 1000.0) end as event_ts_utc,
  null::timestamp as sort_ts,
  'date=' || coalesce(date, '') || '; readable_date=' || coalesce(readable_date, '') as ts_original,
  'date(epoch_ms,UTC)' as ts_field,
  case when try_cast(date as bigint) > 0 then 'utc_known' else 'missing' end as tz_status,
  'call' as event_kind,
  coalesce(nullif(regexp_replace(coalesce(number, ''), '[^0-9]', '', 'g'), ''), other) as conversation_id,
  other as conversation_title,
  ['owner', other] as participants,
  case when coalesce(type, '0') = '2' then 'owner' else other end as sender,
  case when coalesce(type, '0') = '2' then [other] else ['owner'] end as recipients,
  label as direction,
  right(regexp_replace(coalesce(number, ''), '[^0-9]', '', 'g'), 10) as counterparty_phone,
  contact_name,
  upper(label[1]) || label[2:] || ' call with ' || other || ' (duration: ' || coalesce(duration, '0') || 's)'
    || case when len(flags) > 0 then ' [FORENSIC FLAG: ' || array_to_string(flags, ', ') || ']' else '' end as body,
  null::varchar as attachments,
  null::varchar as member_path
from (
  select *,
    case coalesce(type, '0') when '1' then 'incoming' when '2' then 'outgoing' when '3' then 'missed'
         when '4' then 'voicemail' when '5' then 'rejected' when '6' then 'refused_list' else 'unknown' end as label,
    case when coalesce(trim(contact_name), '') not in ('', 'unknown', '(Unknown)', '(unknown)', 'null')
         then trim(contact_name) else coalesce(nullif(trim(number), ''), 'unknown') end as other,
    list_filter([case when coalesce(type, '0') = '5' then 'call actively rejected' end,
                 case when coalesce(type, '0') = '6' then 'number on refuse/block list' end,
                 case when coalesce(type, '0') = '2' and coalesce(duration, '0') = '0'
                      then 'outgoing call with 0 duration - did not connect' end], x -> x is not null) as flags
  from read_xml('{{SRC}}', record_element := 'call', maximum_file_size := 4000000000,
                columns := {'number': 'VARCHAR', 'date': 'VARCHAR', 'type': 'VARCHAR', 'duration': 'VARCHAR',
                            'contact_name': 'VARCHAR', 'readable_date': 'VARCHAR'})
);
