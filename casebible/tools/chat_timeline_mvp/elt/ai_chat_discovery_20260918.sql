-- Byline: Claude Code · Opus 5 · 2026-09-18
-- AI-chat candidate enumeration from the catalog (PG casebible, schema raw_duck).
-- Catalog is the source of truth (Consignatio/docs/decisions/2026-09-16-catalog-source-of-truth.md):
-- this file NEVER re-scans B2; it only asks the catalog which objects exist and how big they are.
--
-- Current vault truth = vault_objects_20260916_r4 MINUS vault_onecopy_pilot_delete_20260916.
-- Original paths + modtime come from intake_catalog_fs_20260917.
-- modtime is carried as catalog_modtime_hint and is NEVER an event timestamp.
--
-- Extension is used ONLY to decide which objects are worth spending a range read on.
-- The format decision itself is made from the BYTES, in ai_chat_signature_probe.py
-- (owner 2026-09-18 20:13 EDT: "The folder names don't mean shit man").

\set ON_ERROR_STOP on

drop table if exists raw_duck.ai_chat_probe_20260918;

create table raw_duck.ai_chat_probe_20260918 as
with live as (
  select v.key, v.size, v.sha1
  from raw_duck.vault_objects_20260916_r4 v
  left join raw_duck.vault_onecopy_pilot_delete_20260916 d on d.key = v.key
  where d.key is null
),
klass as (
  select key, size, sha1,
         lower(coalesce(substring(key from '\.([A-Za-z0-9]{1,8})$'), '')) as ext
  from live
),
picked as (
  select key, size, sha1, ext,
         case
           when ext in ('json','ndjson','jsonl')                  then 'json'
           when ext in ('md','markdown','mdx','txt','text','log')  then 'text'
           when ext in ('html','htm','mhtml','xhtml')              then 'html'
           when ext = 'zip'                                        then 'zip'
         end as probe_class
  from klass
  where ext in ('json','ndjson','jsonl','md','markdown','mdx','txt','text','log',
                'html','htm','mhtml','xhtml','zip')
    and size > 200
),
occ as (
  select vault_key,
         count(*) as n_catalog_occurrences,
         min(rel)      as catalog_rel,
         min(path)     as catalog_path,
         max(modtime)  as catalog_modtime_hint
  from raw_duck.intake_catalog_fs_20260917
  where vault_key is not null
  group by vault_key
)
select p.key as vault_key, p.size, p.sha1, p.ext, p.probe_class,
       o.catalog_rel, o.catalog_path, o.catalog_modtime_hint,
       coalesce(o.n_catalog_occurrences, 0) as n_catalog_occurrences,
       now() as discovered_at
from picked p
left join occ o on o.vault_key = p.key
where not (p.probe_class = 'zip' and p.size < 4096);

create index on raw_duck.ai_chat_probe_20260918 (probe_class);
create index on raw_duck.ai_chat_probe_20260918 (vault_key);
analyze raw_duck.ai_chat_probe_20260918;

select probe_class, count(*) as n_objects, sum(size) as bytes,
       pg_size_pretty(sum(size)) as pretty
from raw_duck.ai_chat_probe_20260918
group by 1 order by 1;
