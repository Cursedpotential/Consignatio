-- Byline: Claude Code · Opus 5 · 2026-09-18
-- elt_ai_clipped_markdown_v1 -- single-answer AI clippings (Obsidian web clipper, Perplexity)
-- Owner 2026-09-18 21:22 EDT: "many chats are just the first sentence of the first prompt" --
-- the file NAME is unusable, so the discriminator is the front-matter `source:` host
-- (gemini.google.com / chatgpt.com / claude.ai / perplexity.ai / ...) or a provider watermark.
--
-- Emits two turns: the question (owner) and the answer (assistant).
-- Front-matter `created:` is a conversation DATE, not a per-message time:
--   event_ts_utc = that date at 00:00, tz_status = 'date_only'. Never a per-message time.

insert into ai_turns
with f as (select content from read_text(getvariable('src'))),
lines as (
  select generate_subscripts(a, 1) as ln, unnest(a) as line
  from (select str_split(replace(content, chr(13), ''), chr(10)) as a from f)
),
fence as (  -- YAML front matter delimiters, if the file opens with one
  select min(ln) filter (where ln = 1 and trim(line) = '---')                       as open_ln,
         min(ln) filter (where ln > 1 and trim(line) = '---')                        as close_ln
  from lines
),
fm as (
  select
    max(case when regexp_matches(line, '^title[ \t]*:', 'i')
             then trim(both '"''' from trim(regexp_replace(line, '^[^:]*:[ \t]*', '', 'i'))) end) as fm_title,
    max(case when regexp_matches(line, '^(?:source|url|link|permalink)[ \t]*:', 'i')
             then trim(both '<>"''' from trim(regexp_replace(line, '^[^:]*:[ \t]*', '', 'i'))) end) as fm_source,
    max(case when regexp_matches(line, '^(?:created|date|published)[ \t]*:', 'i')
             then trim(both '"''' from trim(regexp_replace(line, '^[^:]*:[ \t]*', '', 'i'))) end) as fm_created,
    max(case when regexp_matches(line, '^author[ \t]*:', 'i')
             then trim(both '"''[] ' from trim(regexp_replace(line, '^[^:]*:[ \t]*', '', 'i'))) end) as fm_author
  from lines, fence
  where fence.close_ln is not null and lines.ln > 1 and lines.ln < fence.close_ln
),
body_lines as (
  select ln, line from lines, fence
  where ln > coalesce(fence.close_ln, 0)
),
h1 as (  -- Perplexity/clipper put the question in the first H1
  select regexp_replace(line, '^#+[ \t]*', '') as q
  from body_lines where regexp_matches(line, '^#[ \t]') order by ln limit 1
),
doc as (
  select
    coalesce(nullif(trim((select q from h1)), ''), fm.fm_title) as question,
    fm.fm_title, fm.fm_source, fm.fm_created, fm.fm_author,
    (select string_agg(line, chr(10) order by ln) from body_lines
      where not regexp_matches(line, '^<img[ \t]')) as answer
  from fm
),
svc as (
  select *,
    case
      when fm_source ilike '%gemini.google.com%' or fm_author ilike '%gemini%' then 'gemini'
      when fm_source ilike '%chatgpt.com%' or fm_source ilike '%chat.openai.com%'
           or fm_author ilike '%chatgpt%' then 'chatgpt'
      when fm_source ilike '%claude.ai%' or fm_author ilike '%claude%' then 'claude'
      when fm_source ilike '%perplexity%' or fm_author ilike '%perplexity%' then 'perplexity'
      when fm_source ilike '%copilot%' then 'copilot'
      when fm_source ilike '%grok%' then 'grok'
      when fm_source ilike '%deepseek%' then 'deepseek'
      when fm_source ilike '%qwen%' then 'qwen'
      when fm_source ilike '%venice%' then 'venice'
      else 'other' end as service,
    try_cast(regexp_extract(coalesce(fm_created, ''), '(\d{4}-\d{2}-\d{2})', 1) as DATE) as created_date
  from doc
),
turns as (
  select 1 as turn_index, 'owner' as speaker, 'question' as role_raw, question as body, * from svc
  where question is not null and length(trim(question)) > 0
  union all
  select 2, 'assistant', coalesce(fm_author, service), answer, * from svc
  where answer is not null and length(trim(answer)) > 0
)
select
  getvariable('vault_key'), getvariable('sha1'), getvariable('catalog_path'),
  nullif(getvariable('zip_member_path'), ''),
  try_cast(nullif(getvariable('modtime'), '') as TIMESTAMPTZ),
  'elt_ai_clipped_markdown_v1', getvariable('run_id'),
  service, 'ai_clipped_markdown',
  coalesce(nullif(fm_source, ''),
           md5(getvariable('vault_key') || '|' || coalesce(getvariable('zip_member_path'), ''))),
  coalesce(fm_title, question),
  turn_index, speaker, role_raw, trim(body),
  case when created_date is not null then created_date::TIMESTAMPTZ end,
  fm_created,
  case when created_date is not null then 'date_only' else 'missing' end
from turns;
