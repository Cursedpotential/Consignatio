-- Byline: Claude Code · Opus 5 · 2026-09-18
-- elt_ai_markdown_transcript_v1 -- markdown / txt AI chat transcripts
--
-- Two marker shapes, both anchored at start of line, matching what the owner's exporters write:
--   inline   "You said:", "**User:**", "> Assistant:", "User: [2025-11-12 19:31:34] ..."
--   heading  "### 🤖 Assistant (9:31:04 AM)", "## User", "You (11/12/2025, 7:31:34 PM)"
-- A parenthesised/bracketed timestamp between the speaker and the colon is captured into
-- ts_original VERBATIM. Those exporters write LOCAL wall-clock with no zone, so event_ts_utc
-- stays NULL and tz_status is 'local_no_tz' -- a timestamp is never invented or re-zoned here.
-- Transcripts with no per-turn timestamp at all get tz_status 'missing'.

insert into ai_turns
with f as (select content from read_text(getvariable('src'))),
lines as (
  select generate_subscripts(a, 1) as ln, unnest(a) as line
  from (select str_split(replace(content, chr(13), ''), chr(10)) as a from f)
),
marked as (
  select ln, line,
    case
      when regexp_matches(line, '^[ \t]{0,3}(?:#{1,6}[ \t]*)?(?:>[ \t]*)?(?:[-*][ \t]*)?(?:\*\*|__)?[ \t]*(?:[^\x00-\x7F][ \t]*)*(?:you said|user|human|prompt|matt|question|me|you)(?:[ \t]*\([^)]{0,48}\))?(?:[ \t]*\[[^\]]{0,48}\])?(?:[ \t]*(?:\*\*|__)?[ \t]*:|[ \t]*(?:\*\*|__)?[ \t]*$)', 'i')
        then 'owner'
      when regexp_matches(line, '^[ \t]{0,3}(?:#{1,6}[ \t]*)?(?:>[ \t]*)?(?:[-*][ \t]*)?(?:\*\*|__)?[ \t]*(?:[^\x00-\x7F][ \t]*)*(?:chatgpt said|gemini said|claude said|assistant|chatgpt|claude|gemini|bard|copilot|perplexity|deepseek|grok|qwen|model|answer|response|ai)(?:[ \t]*\([^)]{0,48}\))?(?:[ \t]*\[[^\]]{0,48}\])?(?:[ \t]*(?:\*\*|__)?[ \t]*:|[ \t]*(?:\*\*|__)?[ \t]*$)', 'i')
        then 'assistant'
    end as spk,
    nullif(coalesce(
      regexp_extract(line, '^[^\n]{0,40}?\(([0-9][^)]{0,46})\)', 1),
      regexp_extract(line, '^[^\n]{0,40}?\[([0-9][^\]]{0,46})\]', 1)), '') as ts_raw
  from lines
),
grp as (
  select ln, line, spk, ts_raw,
         sum(case when spk is not null then 1 else 0 end)
           over (order by ln rows between unbounded preceding and current row) as turn_no
  from marked
),
turns as (
  select turn_no,
         max(spk)    as speaker,
         min(ln)     as first_ln,
         max(case when spk is not null then ts_raw end) as ts_original,
         string_agg(
           case when spk is not null
                then regexp_replace(line, '^[ \t]{0,3}(?:#{1,6}[ \t]*)?(?:>[ \t]*)?(?:[-*][ \t]*)?(?:\*\*|__)?[ \t]*(?:[^\x00-\x7F][ \t]*)*(?:you said|chatgpt said|gemini said|claude said|user|human|prompt|matt|question|assistant|chatgpt|claude|gemini|bard|copilot|perplexity|deepseek|grok|qwen|model|answer|response|me|you|ai)(?:[ \t]*\([^)]{0,48}\))?(?:[ \t]*\[[^\]]{0,48}\])?[ \t]*(?:\*\*|__)?[ \t]*:?[ \t]*', '', 'i')
                else line end,
           chr(10) order by ln) as body
  from grp
  where turn_no > 0
  group by turn_no
),
titled as (
  select (select regexp_replace(line, '^[#>* \t]*', '')
          from lines where trim(line) <> '' order by ln limit 1) as title
)
select
  getvariable('vault_key'), getvariable('sha1'), getvariable('catalog_path'),
  nullif(getvariable('zip_member_path'), ''),
  try_cast(nullif(getvariable('modtime'), '') as TIMESTAMPTZ),
  'elt_ai_markdown_transcript_v1', getvariable('run_id'),
  'other', 'ai_markdown_transcript',
  md5(getvariable('vault_key') || '|' || coalesce(getvariable('zip_member_path'), '')),
  (select title from titled),
  row_number() over (order by first_ln),
  speaker, speaker, trim(body),
  NULL::TIMESTAMPTZ,
  ts_original,
  case when ts_original is not null then 'local_no_tz' else 'missing' end
from turns
where trim(coalesce(body, '')) <> '';
