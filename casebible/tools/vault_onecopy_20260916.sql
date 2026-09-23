-- Byline: Claude Code · Opus 5 · 2026-09-16 18:05 EDT (session propria-79)
-- Step 5 (owner 07:13 "verify that there's one copy in the vault"). Catalog only, no B2 writes.
-- Input: raw_duck.vault_objects_20260916_r4 (fresh vault listing after the last move round, B2-stored sha1).
-- Same content = same sha1 + size (objects without a stored sha1: same file name + size).
-- Where a content has more than one copy, the keep order is the owner's: not inside a cleanup-class folder
-- (.review_hold/_SWEPT/_DUPLICATES/_TO_BE_DELETED*/_dedup*/_REVIEW_HOLD/_Quarantine*/NOT FUCKING TRSASH/Triage/_recovered),
-- not the 2026-09-12 pilot tree (casebible-sorted/ at the vault root, _system/canary/), no " [<source>]" tag,
-- shallowest, alphabetical. Output: raw_duck.vault_onecopy_extra_20260916 (the extra copies) + list.
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
begin;
drop table if exists raw_duck.vault_onecopy_extra_20260916;
create table raw_duck.vault_onecopy_extra_20260916 as
with v as (
  select key, size, coalesce(sha1, '') sha1, substr(key, 22) rel,
         case when coalesce(sha1, '') <> '' then 'sha1:' || sha1 || ':' || size
              else 'name:' || regexp_replace(key, '^.*/', '') || ':' || size end as content_id
  from raw_duck.vault_objects_20260916_r4 where size > 0
), ranked as (
  select v.*, row_number() over (partition by content_id order by
           (rel ~* '(^|/)(\.review_hold|_swept|_duplicates|_?to_be_deleted[^/]*|_dedup[^/]*|_review_hold|_quarantine[^/]*|not fucking trsash)(/|$)'
            or rel ~* '(^|/)triage/_recovered(/|$)') asc,
           (rel like 'casebible-sorted/%' or rel like '_system/canary/%') asc,
           (rel ~ ' \[[^]]+\]') asc,
           cardinality(string_to_array(rel, '/')) asc,
           rel) as rk,
         count(*) over (partition by content_id) as copies
  from v
)
select key, size, sha1, content_id, copies,
       (select r2.key from ranked r2 where r2.content_id = ranked.content_id and r2.rk = 1) as kept_key
from ranked where rk > 1;
commit;

\echo === vault now
select count(*) objects, round(sum(size)/1e9, 1) gb, count(*) filter (where coalesce(sha1,'') = '') without_sha1
from raw_duck.vault_objects_20260916_r4;

\echo === one-copy check
select count(*) extra_copies, round(coalesce(sum(size), 0)/1e9, 3) extra_gb, count(distinct content_id) contents_with_extras
from raw_duck.vault_onecopy_extra_20260916;

\echo === extra copies by where they sit
select case when substr(key, 22) like 'casebible-sorted/%' or substr(key, 22) like '_system/canary/%' then '2026-09-12 pilot tree'
            else split_part(substr(key, 22), '/', 1) end place, count(*), round(sum(size)/1e6, 1) mb
from raw_duck.vault_onecopy_extra_20260916 group by 1 order by 2 desc limit 15;

\echo === examples (extra -> kept)
select left(substr(key, 22), 90) extra, left(substr(kept_key, 22), 90) kept, size
from raw_duck.vault_onecopy_extra_20260916 order by size desc limit 12;

copy (select key from raw_duck.vault_onecopy_extra_20260916 order by key) to '/tmp/vault_onecopy_extra.list' with (format text);
copy (select key, size, sha1 from raw_duck.vault_onecopy_extra_20260916 order by key) to '/tmp/vault_onecopy_extra_catalog.csv' with (format csv, header);
