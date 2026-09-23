-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- elt_xml_sanitize_v1 — DuckDB-only sanitizer that makes a SMS Backup & Restore export parseable by
-- webbed read_xml (libxml2 rejects the raw file: "contains invalid XML").
--
-- Why this step exists (evidence, 2026-09-18 20:20 EDT on the decoder baseline file
-- /data/test_data/smsbackuprestore/export-20251206/sms-20251206203434.xml, 1.33 GB, 11,676 records):
--   * read_xml(...) -> Invalid Input Error: contains invalid XML
--   * the file carries a bare '&' that is not part of an entity (1 line), which libxml2 refuses;
--   * MMS payloads are inline base64 in data="..." attributes, up to 95 MB on ONE line, so a DOM parse
--     of the raw file would hold the whole media corpus in memory for no benefit.
-- Everything here runs inside DuckDB (read_csv line stream -> regexp_replace -> COPY). No parser, no Python
-- string handling; the runner only substitutes {{SRC}} / {{DST}}.
--
-- ATTACHMENTS ARE LOCATOR-ONLY tonight (owner-approved for the MVP): the base64 payload of each MMS part is
-- replaced by its byte length and its sha256, so the part stays identifiable and re-extractable from the
-- original B2 object, and no media bytes enter the timeline.
--
-- Transformations, in order, per line:
--   1. data="<base64>"      -> data_len="<chars>" data_sha256="<hex>"   (payload dropped, locator kept)
--   2. XML-illegal C0 control bytes removed (libxml2 rejects them outright)
--   3. every '&' escaped, then real entities repaired (RE2 has no lookahead, so escape-then-repair)
--   4. numeric character references in the surrogate range dropped (not legal XML; emoji written as a
--      surrogate PAIR by some Android builds). Over-covers &#55000;-&#57999; — a few private-use code
--      points are lost with them; that is recorded, not silent.
-- {{DST}} is ONE fixed scratch path that the runner overwrites per file, so temp never accumulates.
copy (
  select
    regexp_replace(
      regexp_replace(
        regexp_replace(
          regexp_replace(
            replace(
              regexp_replace(
                case
                  when line like '% data="%'
                    then regexp_replace(line, ' data="[^"]*"',
                           ' data_len="' || len(regexp_extract(line, ' data="([^"]*)"', 1)) ||
                           '" data_sha256="' || sha256(regexp_extract(line, ' data="([^"]*)"', 1)) || '"', 'g')
                  else line
                end,
                '[\x00-\x08\x0B\x0C\x0E-\x1F]', '', 'g'),
              '&', '&amp;'),
            '&amp;(amp|lt|gt|quot|apos);', '&\1;', 'g'),
          '&amp;#([0-9]+);', '&#\1;', 'g'),
        '&amp;#[xX]([0-9A-Fa-f]+);', '&#x\1;', 'g'),
      '&#5[5-7][0-9][0-9][0-9];', '', 'g') as line
  from read_csv('{{SRC}}', columns = {'line': 'VARCHAR'}, delim = e'\x07', quote = e'\x01', escape = e'\x01',
                header = false, auto_detect = false, max_line_size = 200000000, parallel = false, strict_mode = false)
) to '{{DST}}' (format csv, delimiter e'\x07', quote '', escape '', header false);
-- NOTE (measured 2026-09-18 20:30 EDT): the writer must have quoting OFF (quote ''). With any quote
-- character set, DuckDB quotes a value that contains the text '&#10;' — that stray quote byte lands at the
-- start of the line and makes the output invalid XML (expat: "not well-formed (invalid token)").
