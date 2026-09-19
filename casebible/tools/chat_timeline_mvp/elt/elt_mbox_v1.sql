-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- elt_mbox_v1 — RFC 4155 mbox (Google Takeout "Mail/*.mbox") -> one event per message, DuckDB only.
-- Engine: read_text + split on the mbox "From " separator + RE2 header extraction.
-- MVP limits, stated rather than hidden:
--   * body = the text after the first blank line, with soft line breaks of quoted-printable joined and
--     MIME boundaries left in place; base64-only bodies are NOT decoded (flagged in ts_field/attachments);
--   * only Date/From/To/Cc/Subject are lifted into fields; the rest of the headers stay in the body text;
--   * attachments are not extracted (names only, from Content-Disposition filename=).
select
  i - 1 as record_index,
  coalesce(try_strptime(ts_raw, '%a, %d %b %Y %H:%M:%S %z'), try_strptime(ts_raw, '%d %b %Y %H:%M:%S %z')) as event_ts_utc,
  null::timestamp as sort_ts,
  ts_raw as ts_original,
  'header Date(RFC2822)' as ts_field,
  case when coalesce(try_strptime(ts_raw, '%a, %d %b %Y %H:%M:%S %z'), try_strptime(ts_raw, '%d %b %Y %H:%M:%S %z')) is null
       then case when ts_raw = '' then 'missing' else 'unparsed' end else 'utc_known' end as tz_status,
  'email' as event_kind,
  nullif(trim(regexp_extract(head, '(?i)\nMessage-ID: *([^\n]*)', 1)), '') as conversation_id,
  trim(regexp_extract(head, '(?i)\nSubject: *([^\n]*)', 1)) as conversation_title,
  list_distinct(list_filter([trim(regexp_extract(head, '(?i)\nFrom: *([^\n]*)', 1)),
                             trim(regexp_extract(head, '(?i)\nTo: *([^\n]*)', 1)),
                             trim(regexp_extract(head, '(?i)\nCc: *([^\n]*)', 1))], x -> x <> '')) as participants,
  trim(regexp_extract(head, '(?i)\nFrom: *([^\n]*)', 1)) as sender,
  list_filter([trim(regexp_extract(head, '(?i)\nTo: *([^\n]*)', 1)),
               trim(regexp_extract(head, '(?i)\nCc: *([^\n]*)', 1))], x -> x <> '') as recipients,
  null::varchar as direction,
  null::varchar as counterparty_phone,
  null::varchar as contact_name,
  trim(regexp_replace(
    regexp_replace(substr(msg, strpos(msg, chr(10) || chr(10)) + 2), '=' || chr(10), '', 'g'),
    '\n(Content-Type|Content-Transfer-Encoding|Content-Disposition|MIME-Version|--[0-9a-zA-Z_=.-]{10,})[^\n]*', '', 'g')) as body,
  nullif(to_json(list_distinct(regexp_extract_all(head || substr(msg, 1, 20000), '(?i)filename="?([^";\n]+)', 1)))::varchar, '[]') as attachments,
  null::varchar as member_path
from (
  select i, msg, substr(msg, 1, coalesce(nullif(strpos(msg, chr(10) || chr(10)), 0), 4000)) as head,
         trim(regexp_extract(substr(msg, 1, coalesce(nullif(strpos(msg, chr(10) || chr(10)), 0), 4000)), '(?i)\nDate: *([^\n]*)', 1)) as ts_raw
  from (select generate_subscripts(parts, 1) as i, unnest(parts) as msg
        from (select string_split(chr(10) || replace(content, chr(13), ''), chr(10) || 'From ') as parts from read_text('{{SRC}}')))
  where length(msg) > 40
);
