-- Byline: Claude Code · Opus 5 · 2026-09-17
-- Intake engine v1: catalog:// as an ordinary filesystem tree (owner 08:38-08:43 EDT, parent answer 08:58 EDT).
--
-- Tree   : catalog://<source>/<scope>/<recorded path>   (scope segment omitted when empty)
--          built from raw_duck.source_occurrences exactly as recorded; nothing is re-scanned.
-- Resolve: occurrence.b2_key (stale intake/raw-dedupe key) -> raw_duck.b2_objects.sha1 (+size)
--          -> raw_duck.vault_objects_20260916_r4 (current B2 truth, record 2026-09-16 22:00 UTC)
--          minus raw_duck.vault_onecopy_pilot_delete_20260916.
--          When several vault keys share the content, prefer the one with the same basename, then the shortest key.
-- Rows that do not resolve are KEPT (resolution <> 'resolved') so the UI lists them with a flag, never hides them.
-- Same (source, scope, path) recorded under several source_id values: the 2nd+ get " (occurrence N)" appended.
--
-- Run (read-only on every source table; writes only these two new dated tables):
--   docker exec -i fgz1n7useplhk0t91uk7k1aw psql -U postgres -d casebible -v ON_ERROR_STOP=1 < intake_catalog_fs_20260917.sql
-- Default ACL on raw_duck grants SELECT on postgres-created tables to metabase_ro (the engine's read role).
\pset pager off
\timing on
-- The container's /dev/shm is 64 MB: parallel hash joins exhaust it (first run 09:14 EDT failed with
-- "could not resize shared memory segment"), so run serially with a moderate work_mem.
set max_parallel_workers_per_gather = 0;
set work_mem = '256MB';

begin;

create table raw_duck.intake_catalog_fs_20260917 as
with occ as (
  select s.*,
         row_number() over (partition by s.source, s.scope, s.path order by s.source_id) as dup_rank
  from raw_duck.source_occurrences s
),
resolved as (
  select distinct on (o.source, o.scope, o.path, o.source_id)
         o.source, o.scope, o.path, o.source_id, o.size, o.modtime, o.native_hash_kind, o.native_hash,
         o.md5, o.disposition, o.b2_key as b2_key_recorded, o.matched_origin, o.metadata, o.recorded_at,
         o.dup_rank, bo.sha1, v.key as vault_key
  from occ o
  left join raw_duck.b2_objects bo on bo.key = o.b2_key
  left join raw_duck.vault_objects_20260916_r4 v
         on v.sha1 = bo.sha1 and v.size = bo.size
        and not exists (select 1 from raw_duck.vault_onecopy_pilot_delete_20260916 d where d.key = v.key)
  order by o.source, o.scope, o.path, o.source_id,
           (v.key is null),
           (regexp_replace(coalesce(v.key, ''), '^.*/', '') = regexp_replace(o.path, '^.*/', '')) desc,
           length(v.key), v.key
)
select
  rel,
  case when strpos(rel, '/') = 0 then '' else regexp_replace(rel, '/[^/]*$', '') end as parent,
  regexp_replace(rel, '^.*/', '') as name,
  source, scope, path, source_id, size, modtime, native_hash_kind, native_hash, md5, disposition,
  b2_key_recorded, matched_origin, metadata, recorded_at, sha1, vault_key,
  case when vault_key is not null then 'resolved'
       when b2_key_recorded is null then 'no_b2_key'
       when sha1 is null then 'b2_key_not_in_b2_objects'
       else 'no_current_vault_object' end as resolution
from (
  select r.*,
         r.source
         || case when coalesce(r.scope, '') = '' then '' else '/' || r.scope end
         || '/' || trim(both '/' from r.path)
         || case when r.dup_rank > 1 then ' (occurrence ' || r.dup_rank || ')' else '' end as rel
  from resolved r
) x;

alter table raw_duck.intake_catalog_fs_20260917 add primary key (rel);
create index intake_catalog_fs_20260917_parent on raw_duck.intake_catalog_fs_20260917 (parent, name);
create index intake_catalog_fs_20260917_vault_key on raw_duck.intake_catalog_fs_20260917 (vault_key);

-- Every ancestor directory of every file, with direct and nested counts.
create table raw_duck.intake_catalog_dirs_20260917 as
with parts as (
  select f.size, string_to_array(f.rel, '/') as segs
  from raw_duck.intake_catalog_fs_20260917 f
),
prefixes as (
  select array_to_string(segs[1:n], '/') as rel, size
  from parts, generate_series(1, array_length(segs, 1) - 1) as n
)
select rel,
       case when strpos(rel, '/') = 0 then '' else regexp_replace(rel, '/[^/]*$', '') end as parent,
       regexp_replace(rel, '^.*/', '') as name,
       count(*) as nested_files,
       coalesce(sum(size), 0) as nested_bytes
from prefixes
group by rel;

alter table raw_duck.intake_catalog_dirs_20260917 add primary key (rel);
create index intake_catalog_dirs_20260917_parent on raw_duck.intake_catalog_dirs_20260917 (parent, name);

commit;

analyze raw_duck.intake_catalog_fs_20260917;
analyze raw_duck.intake_catalog_dirs_20260917;

-- Report: totals, unresolved remainder by reason, and a sample of 10 unresolved rows.
select count(*) as files,
       count(*) filter (where resolution = 'resolved') as resolved,
       count(*) filter (where resolution <> 'resolved') as unresolved
from raw_duck.intake_catalog_fs_20260917;
select resolution, count(*) from raw_duck.intake_catalog_fs_20260917 group by 1 order by 2 desc;
select count(*) as dirs from raw_duck.intake_catalog_dirs_20260917;
select rel, resolution, b2_key_recorded from raw_duck.intake_catalog_fs_20260917
 where resolution <> 'resolved' order by md5(rel) limit 10;
