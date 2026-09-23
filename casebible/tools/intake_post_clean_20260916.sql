-- Byline: Claude Code · Opus 5 · 2026-09-16 11:00 EDT (session propria-79)
-- Step 1 check (owner 07:11 "First, clean the intake"): load the fresh post-clean intake listing into the catalog and
-- prove the cleanup against the checked delete list. Catalog rule (owner 08:32): listings land as raw_duck tables.
-- Inputs staged into the PG container /tmp by the caller:
--   intake_post_clean.csv   key,size,sha1   fresh listing after all 949 phases
--   intake_before.csv       key,size        listing 11:11 UTC before any delete
--   intake_delete.csv       key             checked delete list (526,393)
--   versions_differ.csv     key,size,sha1   kept: stored content differs from the proven copy
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
begin;
drop table if exists raw_duck.intake_objects_20260916_post_clean;
create table raw_duck.intake_objects_20260916_post_clean (key text primary key, size bigint, sha1 text);
\copy raw_duck.intake_objects_20260916_post_clean from '/tmp/intake_post_clean.csv' with (format csv, header)
drop table if exists raw_duck.intake_objects_20260916_before;
create table raw_duck.intake_objects_20260916_before (key text primary key, size bigint);
\copy raw_duck.intake_objects_20260916_before from '/tmp/intake_before.csv' with (format csv, header)
drop table if exists raw_duck.intake_delete_20260916;
create table raw_duck.intake_delete_20260916 (key text primary key);
\copy raw_duck.intake_delete_20260916 from '/tmp/intake_delete.csv' with (format csv, header)
drop table if exists raw_duck.intake_versions_differ_20260916;
create table raw_duck.intake_versions_differ_20260916 (key text, size bigint, sha1 text);
\copy raw_duck.intake_versions_differ_20260916 from '/tmp/versions_differ.csv' with (format csv, header)
commit;

\echo === intake before / now
select (select count(*) from raw_duck.intake_objects_20260916_before) before_objects,
       (select round(sum(size)/1e9,1) from raw_duck.intake_objects_20260916_before) before_gb,
       (select count(*) from raw_duck.intake_objects_20260916_post_clean) now_objects,
       (select round(sum(size)/1e9,2) from raw_duck.intake_objects_20260916_post_clean) now_gb;

\echo === checks (first two MUST be 0)
select 'gone but NOT on the delete list' k, count(*) from raw_duck.intake_objects_20260916_before b
  where not exists (select 1 from raw_duck.intake_objects_20260916_post_clean n where n.key = b.key)
    and not exists (select 1 from raw_duck.intake_delete_20260916 d where d.key = b.key)
union all
select 'on the delete list and still present, not a recorded differing version', count(*) from raw_duck.intake_delete_20260916 d
  join raw_duck.intake_objects_20260916_post_clean n using (key)
  where not exists (select 1 from raw_duck.intake_versions_differ_20260916 v where v.key = d.key)
union all
select 'kept: differing stored versions', count(distinct key) from raw_duck.intake_versions_differ_20260916
union all
select 'left in intake, not on the delete list (to move into the vault)', count(*) from raw_duck.intake_objects_20260916_post_clean n
  where not exists (select 1 from raw_duck.intake_delete_20260916 d where d.key = n.key);

\echo === what is left in intake, by top folder
select split_part(substr(key, 49), '/', 1) || '/' || split_part(substr(key, 49), '/', 2) folder, count(*) objects, round(sum(size)/1e9,2) gb
from raw_duck.intake_objects_20260916_post_clean group by 1 order by 2 desc limit 15;
