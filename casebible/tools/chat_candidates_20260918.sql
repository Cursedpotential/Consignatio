-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Chat discovery from the catalog (owner 2026-09-18 12:32 EDT: timeline + history context, chats first).
-- Source of truth: raw_duck.vault_objects_20260916_r4 minus raw_duck.vault_onecopy_pilot_delete_20260916
-- (current B2 vault). Nothing is re-scanned. Original catalog paths come from
-- raw_duck.intake_catalog_fs_20260917 (one representative rel + occurrence count per vault key).
-- Scope: B2 only (owner 12:37 "everything should be in B2 now").
--
-- format_guess is a path/name heuristic, not a content check; the extractor re-checks content.
-- Person-name matching is NOT done here (it lives in an untracked server-side terms file).
--
-- Run:
--   docker exec -i fgz1n7useplhk0t91uk7k1aw psql -U postgres -d casebible -v ON_ERROR_STOP=1 < chat_candidates_20260918.sql
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
set work_mem = '256MB';

begin;
drop table if exists raw_duck.chat_candidates_20260918;
create table raw_duck.chat_candidates_20260918 as
with v as (
  select v.key, v.size, v.sha1
  from raw_duck.vault_objects_20260916_r4 v
  where not exists (select 1 from raw_duck.vault_onecopy_pilot_delete_20260916 d where d.key = v.key)
),
g as (
  select key, size, sha1,
    case
      when key ~* '/(messages|your_messages)/(inbox|archived_threads|filtered_threads|message_requests|e2ee_cutover)/[^/]+/message_[0-9]+\.json$'
           and key ~* 'instagram' then 'instagram_json'
      when key ~* '/(messages|your_messages)/(inbox|archived_threads|filtered_threads|message_requests|e2ee_cutover)/[^/]+/message_[0-9]+\.json$' then 'fb_messenger_json'
      when key ~* '/(messages|your_messages)/(inbox|archived_threads|filtered_threads|message_requests|e2ee_cutover)/[^/]+/(files/)?message_[0-9_]+\.html$' then 'fb_messenger_html'
      when key ~* '/sms-[^/]*\.xml$' then 'sms_backup_xml'
      when key ~* '/calls(-[^/]*)?\.xml$' then 'calls_backup_xml'
      when key ~* '/(_chat\.txt|WhatsApp Chat[^/]*\.txt)$' then 'whatsapp_txt'
      when key ~* 'whatsapp[^/]*\.zip$' then 'whatsapp_zip'
      when key ~* '/Google Chat/(Groups|DMs?)/[^/]+/messages\.json$' then 'google_chat_json'
      when key ~* '/Hangouts/Hangouts\.json$' then 'hangouts_json'
      when key ~* '/Voice/Calls/[^/]*\.html$' then 'google_voice_html'
      when key ~* '\.mbox$' then 'mbox'
      when key ~* '\.eml$' then 'eml'
      when key ~* '/conversations\.json$' then 'ai_conversations_json'
      when key ~* '/(My ?Activity)/Gemini Apps/[^/]*\.(html|json)$' then 'gemini_activity'
      when key ~* 'imessage[^/]*/.*\.html$' or key ~* '/\+?[0-9]{10,12}/[^/]*\.html$' then 'imessage_html'
      when key ~* '/\+[0-9]{10,12}\.txt$' then 'imessage_txt'
      when key ~* '/\+[0-9]{10,12}\.zip$' then 'imessage_zip'
      when key ~* '/Cube ACR/.*\.json$' then 'cube_acr_json'
      when key ~* '/(takeout-[^/]*|facebook-[^/]*|meta-[^/]*|instagram-[^/]*)\.zip$' then 'export_zip'
      when key ~* '/(chats?|ai_chats?|ai-chats?|chatgpt|claude|gemini|perplexity)/[^/]*\.(md|json|jsonl)$' then 'ai_chat_file'
      when key ~* '(sms|messages?|conversation|chat)[^/]*\.csv$' then 'message_csv'
      when key ~* '/result\.json$' and key ~* 'telegram' then 'telegram_json'
      when key ~* 'signal[^/]*\.(json|txt)$' then 'signal_export'
      else null
    end as format_guess
  from v
)
select g.format_guess, g.key as vault_key, g.size, g.sha1,
       c.rel as catalog_rel_example, coalesce(c.n_occurrences, 0) as n_catalog_occurrences,
       now() as discovered_at
from g
left join lateral (
  select min(f.rel) as rel, count(*) as n_occurrences
  from raw_duck.intake_catalog_fs_20260917 f where f.vault_key = g.key
) c on true
where g.format_guess is not null;

create index on raw_duck.chat_candidates_20260918 (format_guess);
create index on raw_duck.chat_candidates_20260918 (sha1);
commit;

select format_guess, count(*) as files, pg_size_pretty(sum(size)) as bytes, count(distinct sha1) as distinct_sha1
from raw_duck.chat_candidates_20260918 group by 1 order by 2 desc;
