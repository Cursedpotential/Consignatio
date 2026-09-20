-- Byline: Claude Code · Opus 5 · 2026-09-16 16:55 EDT (session propria-79)
-- Step 2 check of the owner's 07:12 order ("Then clean the vault"): load the fresh post-dedupe vault listing into the
-- catalog and prove it against the keep table. Catalog rule (owner 08:32). Name agreed with intake-16:
-- raw_duck.vault_objects_20260916_post_prune.
-- Input staged by vault_post_prune_load.sh: /tmp/vault_post_prune.csv  key,size,sha1
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
begin;
drop table if exists raw_duck.vault_objects_20260916_post_prune;
create table raw_duck.vault_objects_20260916_post_prune (key text primary key, size bigint, sha1 text);
\copy raw_duck.vault_objects_20260916_post_prune from '/tmp/vault_post_prune.csv' with (format csv, header)
create index on raw_duck.vault_objects_20260916_post_prune (sha1, size);
commit;

\echo === vault now
select count(*) objects, round(sum(size)/1e9,1) gb, count(*) filter (where sha1 is null or sha1 = '') without_sha1
from raw_duck.vault_objects_20260916_post_prune;

\echo === checks (first three MUST be 0)
select 'kept copy missing from the vault' k, count(*) from raw_duck.vault_keep_v7 k
  where not exists (select 1 from raw_duck.vault_objects_20260916_post_prune v where v.key = k.dest_key)
union all
select 'kept copy present with a different size', count(*) from raw_duck.vault_keep_v7 k
  join raw_duck.vault_objects_20260916_post_prune v on v.key = k.dest_key where v.size <> k.size
union all
select 'deleted copy still present', count(*) from raw_duck.vault_delete_v7 d
  join raw_duck.vault_objects_20260916_post_prune v on v.key = d.dest_key
union all
select 'objects not in the keep table (51 pilot objects expected)', count(*) from raw_duck.vault_objects_20260916_post_prune v
  where not exists (select 1 from raw_duck.vault_keep_v7 k where k.dest_key = v.key);

\echo === one copy per content (B2-stored sha1 + size; objects without sha1 by file name + size)
select 'extra copies, same sha1+size' k, coalesce(sum(n - 1), 0) extra, round(coalesce(sum((n - 1) * size), 0)/1e9, 2) gb
from (select sha1, size, count(*) n from raw_duck.vault_objects_20260916_post_prune
      where sha1 <> '' and size > 0 group by 1, 2 having count(*) > 1) t
union all
select 'extra copies, no sha1, same name+size', coalesce(sum(n - 1), 0), round(coalesce(sum((n - 1) * size), 0)/1e9, 2)
from (select regexp_replace(key, '^.*/', '') nm, size, count(*) n from raw_duck.vault_objects_20260916_post_prune
      where (sha1 is null or sha1 = '') and size > 0 group by 1, 2 having count(*) > 1) t;

\echo === largest remaining same-content groups (first 10)
select size, n, left(array_to_string(keys[1:2], '  |  '), 220) examples
from (select sha1, size, count(*) n, array_agg(substr(key, 22) order by key) keys
      from raw_duck.vault_objects_20260916_post_prune where sha1 <> '' and size > 0
      group by 1, 2 having count(*) > 1) t
order by (n - 1) * size desc limit 10;
