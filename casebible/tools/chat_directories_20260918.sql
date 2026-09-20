-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Chat DIRECTORY map (owner 2026-09-18 20:02 EDT: "scan the directories and make an attempt to identify
-- the chat directories and index those first"). Supersedes the file-by-format candidate ordering of
-- chat_candidates_20260918.sql for indexing order; that table is still used as one of the inputs.
--
-- Catalog only (no re-scan): original paths from raw_duck.intake_catalog_fs_20260917 (rel / parent / name),
-- current B2 vault = raw_duck.vault_objects_20260916_r4 minus raw_duck.vault_onecopy_pilot_delete_20260916.
-- A directory is the catalog `parent` (original folder). A chat directory is one that holds a chat
-- candidate, or whose path names chats/messages/Messenger/inbox/SMS/texts/iMessage/WhatsApp/Voice/Hangouts/
-- Communication/Phone Records/Comms/Phone Data/Court/Takeout/facebook-*/meta-* or the person (Katrina/Kinzel).
--
-- Priority (owner 20:02 + owner priority folders 20:07):
--   1 path contains katrina|kinzel
--   2 owner priority folders: Comms/Communications, Phone Data, Court, Communication Data, SMS
--   3 directories that already produced Katrina events (raw_duck.chat_event_provenance_20260918)
--   4 Phone Records / Messages / iMessage / texts / WhatsApp / chats
--   5 Facebook / Messenger exports
--   6 Google Takeout Voice / Chat / Mail / Hangouts
--   7 AI chats
--   8 the rest
-- Cube ACR folders are audio: only their .json metadata is readable (call log), no transcription.
-- Person names beyond the owner-authorised directory keywords are NOT written here.
--
-- Run: docker exec -i fgz1n7useplhk0t91uk7k1aw psql -U postgres -d casebible -v ON_ERROR_STOP=1 < chat_directories_20260918.sql
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
set work_mem = '512MB';

begin;
drop table if exists raw_duck.chat_dir_files_20260918;
drop table if exists raw_duck.chat_directories_20260918;

create temp table vault_now as
select v.key, v.size, v.sha1
from raw_duck.vault_objects_20260916_r4 v
where not exists (select 1 from raw_duck.vault_onecopy_pilot_delete_20260916 d where d.key = v.key);
create index on vault_now (key);

create temp table kat_keys as
select distinct p.vault_key
from raw_duck.chat_event_provenance_20260918 p
join raw_duck.chat_events_20260918 e using (dedup_key)
where e.katrina_conf = 'strong' and e.katrina_ref_type <> 'group_participant';

create temp table indexed_keys as
select distinct vault_key from raw_duck.chat_event_provenance_20260918;

create temp table cat as
select f.rel, f.parent, f.name, f.source, f.vault_key, v.sha1, v.size,
       lower(substring(f.name from '\.([A-Za-z0-9]+)$')) as ext
from raw_duck.intake_catalog_fs_20260917 f
join vault_now v on v.key = f.vault_key
where f.parent is not null;
create index on cat (parent);

create temp table dir_class as
with d as (
  select parent,
    bool_or(vault_key in (select vault_key from raw_duck.chat_candidates_20260918)) as has_candidate,
    bool_or(vault_key in (select vault_key from kat_keys)) as has_katrina_events
  from cat group by parent
)
select parent, has_candidate, has_katrina_events,
  parent ~* 'katrina|kinzel' as katrina_in_path,
  parent ~* '(^|[^a-z])comms?([^a-z]|$)|communications?|phone data|court|(^|[^a-z])sms([^a-z]|$)' as owner_priority_path,
  parent ~* 'phone records|(^|[^a-z])messages?([^a-z]|$)|imessage|(^|[^a-z])texts?([^a-z]|$)|whatsapp|(^|/)chats?(/|$)' as messages_path,
  parent ~* 'facebook|messenger|(^|/)meta-|(^|/)inbox(/|$)|archived_threads|filtered_threads|(^|[^a-z])fb([^a-z]|$)' as fb_path,
  parent ~* 'takeout' and parent ~* 'voice|(^|[^a-z])chat|mail|hangouts' as takeout_comm_path,
  parent ~* 'chatgpt|claude|gemini|perplexity|ai[ _-]?chats?|(^|/)conversations' as ai_path,
  parent ~* 'takeout|(^|/)facebook-|(^|/)meta-|hangouts|(^|[^a-z])voice([^a-z]|$)' as other_path,
  parent ~* 'cube acr' as audio_dir
from d;

create temp table dirs as
select c.*,
  case when katrina_in_path then 1
       when owner_priority_path then 2
       when has_katrina_events then 3
       when messages_path then 4
       when fb_path then 5
       when takeout_comm_path then 6
       when ai_path then 7
       else 8 end as priority
from dir_class c
where has_candidate or katrina_in_path or owner_priority_path or has_katrina_events or messages_path
   or fb_path or takeout_comm_path or ai_path or other_path;

-- root_dir: the shallowest ancestor whose own name carries the tier keyword, so a tree is indexed together.
create temp table dir_root as
select d.parent, coalesce(r.root, d.parent) as root_dir
from dirs d
left join lateral (
  select array_to_string((string_to_array(d.parent, '/'))[1:min(i)], '/') as root
  from unnest(string_to_array(d.parent, '/')) with ordinality as s(seg, i)
  where case d.priority
          when 1 then seg ~* 'katrina|kinzel'
          when 2 then seg ~* '(^|[^a-z])comms?([^a-z]|$)|communications?|phone data|court|(^|[^a-z])sms([^a-z]|$)'
          when 4 then seg ~* 'phone records|(^|[^a-z])messages?([^a-z]|$)|imessage|(^|[^a-z])texts?([^a-z]|$)|whatsapp|^chats?$'
          when 5 then seg ~* 'facebook|messenger|^meta-|^inbox$|archived_threads|filtered_threads|(^|[^a-z])fb([^a-z]|$)'
          when 6 then seg ~* 'takeout'
          when 7 then seg ~* 'chatgpt|claude|gemini|perplexity|ai[ _-]?chats?|^conversations'
          else seg ~* 'takeout|^facebook-|^meta-|hangouts|voice'
        end
) r on true;

create temp table dir_stats as
select c.parent,
  count(*) as total_files,
  count(*) filter (where c.ext in ('json','html','htm','txt','md','csv','xml','mbox','eml')
                   and (not d.audio_dir or c.ext = 'json')) as readable_files,
  count(*) filter (where c.ext = 'zip') as zip_files,
  sum(c.size) as bytes,
  coalesce(sum(c.size) filter (where c.ext in ('json','html','htm','txt','md','csv','xml','mbox','eml')), 0) as readable_bytes,
  string_agg(distinct c.ext, ',' order by c.ext) filter (where c.ext is not null) as formats,
  count(*) filter (where c.vault_key in (select vault_key from indexed_keys)) as already_indexed_files
from cat c join dirs d using (parent)
group by c.parent;

create table raw_duck.chat_directories_20260918 as
with j as (
  select d.*, r.root_dir, s.total_files, s.readable_files, s.zip_files, s.bytes, s.readable_bytes, s.formats,
         s.already_indexed_files, min(d.priority) over (partition by r.root_dir) as root_priority
  from dirs d join dir_stats s using (parent) join dir_root r using (parent)
)
select
  row_number() over (order by d.root_priority, d.root_dir, d.priority,
                               d.readable_files - d.already_indexed_files desc, d.parent) as dir_rank,
  d.priority, d.root_dir, d.parent as path,
  d.total_files, d.readable_files, d.zip_files, d.bytes, d.readable_bytes, d.formats,
  d.katrina_in_path, d.has_katrina_events, d.has_candidate, d.audio_dir,
  d.already_indexed_files,
  null::int as files_indexed_now, null::int as files_skipped_dup, null::bigint as events_added,
  null::bigint as katrina_events_added, null::bigint as daughter_events_added,
  null::text as status, null::timestamptz as indexed_at, null::text as errors,
  now() as mapped_at
from j d;
alter table raw_duck.chat_directories_20260918 add primary key (dir_rank);
create unique index on raw_duck.chat_directories_20260918 (path);
create index on raw_duck.chat_directories_20260918 (priority);

-- Work list: every catalog file in a chat directory, first occurrence of each vault key (by dir_rank) is the
-- one that gets indexed; later occurrences are recorded as duplicates of an earlier directory.
create table raw_duck.chat_dir_files_20260918 as
select d.dir_rank, c.rel, c.name, c.ext, c.vault_key, c.sha1, c.size,
  (c.ext in ('json','html','htm','txt','md','csv','xml','mbox','eml') and (not d.audio_dir or c.ext = 'json')) as readable,
  row_number() over (partition by c.vault_key order by d.dir_rank, c.rel) = 1 as first_occurrence,
  c.vault_key in (select vault_key from indexed_keys) as indexed_before
from cat c join raw_duck.chat_directories_20260918 d on d.path = c.parent;
create index on raw_duck.chat_dir_files_20260918 (dir_rank);
create index on raw_duck.chat_dir_files_20260918 (vault_key);
commit;

select priority, count(*) as dirs, sum(total_files) as files, sum(readable_files) as readable,
       sum(already_indexed_files) as already_indexed, pg_size_pretty(sum(bytes)) as bytes,
       pg_size_pretty(sum(readable_bytes)) as readable_bytes
from raw_duck.chat_directories_20260918 group by 1 order by 1;
