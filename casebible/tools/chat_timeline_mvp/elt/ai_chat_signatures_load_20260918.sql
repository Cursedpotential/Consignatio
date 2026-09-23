-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Load the content-signature results into the catalog and derive the directory inventory
-- the owner asked for: every folder that holds AI chats, files per service, turns extracted.
-- Input: /root/aichat/sig_all.tsv (all loose passes + zip-member pass, one header).

\set ON_ERROR_STOP on

drop table if exists raw_duck.ai_chat_signatures_20260918;
create table raw_duck.ai_chat_signatures_20260918 (
  vault_key            text,
  size                 bigint,
  sha1                 text,
  ext                  text,
  probe_class          text,
  catalog_rel          text,
  catalog_path         text,
  catalog_modtime_hint timestamptz,
  zip_member_path      text,
  member_size          bigint,
  signature            text,
  why                  text,
  status               text
);

\copy raw_duck.ai_chat_signatures_20260918 from '/aichat/sig_all.tsv' with (format csv, delimiter E'\t', header true, null '')

create index on raw_duck.ai_chat_signatures_20260918 (signature);
create index on raw_duck.ai_chat_signatures_20260918 (vault_key);
analyze raw_duck.ai_chat_signatures_20260918;

-- service is derived from the signature, not from any name
drop view if exists raw_duck.ai_chat_hits_20260918;
create view raw_duck.ai_chat_hits_20260918 as
select *,
       case
         when signature = 'chatgpt_conversations_json' then 'chatgpt'
         when signature = 'claude_conversations_json'  then 'claude'
         when signature = 'gemini_activity_json'       then 'gemini'
         when signature = 'gemini_activity_html'       then 'gemini'
         when signature = 'chatgpt_chat_html'          then 'chatgpt'
         else 'undetermined_until_extract'
       end as service_hint,
       -- the FOLDER a chat actually lives in (from the original catalog path when known,
       -- else the vault key), which is what the owner wants the inventory of
       regexp_replace(coalesce(nullif(catalog_path, ''), vault_key), '/[^/]*$', '') as dir_path
from raw_duck.ai_chat_signatures_20260918
where signature is not null;

-- ---------------------------------------------------------------- directory inventory
drop table if exists raw_duck.ai_chat_dir_inventory_20260918;
create table raw_duck.ai_chat_dir_inventory_20260918 as
select dir_path,
       count(*)                                          as hits,
       count(*) filter (where zip_member_path is null)   as loose_files,
       count(*) filter (where zip_member_path is not null) as zip_members,
       count(distinct vault_key)                         as objects,
       count(*) filter (where signature = 'chatgpt_conversations_json') as n_chatgpt_export,
       count(*) filter (where signature = 'claude_conversations_json')  as n_claude_export,
       count(*) filter (where signature = 'gemini_activity_json')       as n_gemini_activity,
       count(*) filter (where signature = 'ai_chat_memo_txt')           as n_chat_memo,
       count(*) filter (where signature = 'ai_markdown_transcript')     as n_md_transcript,
       count(*) filter (where signature = 'ai_clipped_markdown')        as n_clipped,
       count(*) filter (where signature = 'ai_generic_json')            as n_generic_json,
       sum(coalesce(member_size, size))                  as bytes
from raw_duck.ai_chat_hits_20260918
group by dir_path;

create index on raw_duck.ai_chat_dir_inventory_20260918 (hits desc);
analyze raw_duck.ai_chat_dir_inventory_20260918;

select count(*) as directories_holding_ai_chats,
       sum(hits) as signature_hits,
       sum(loose_files) as loose_files,
       sum(zip_members) as zip_members
from raw_duck.ai_chat_dir_inventory_20260918;

select signature, count(*) as hits, count(distinct vault_key) as objects
from raw_duck.ai_chat_hits_20260918 group by 1 order by 2 desc;
