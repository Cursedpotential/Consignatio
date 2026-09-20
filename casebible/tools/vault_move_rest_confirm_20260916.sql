-- Byline: Claude Code · Opus 5 · 2026-09-16 17:15 EDT (session propria-79)
-- Step 3 confirm + step 4 list (owner 07:12 "move it. Then clean the intake again"). Catalog only.
-- Input: /tmp/vault_post_move.csv key,size,sha1 (fresh vault listing after the copy).
-- An intake object may be deleted only if its content is proven in the vault now:
--   copy rows: dest_key present with the same size, and the same sha1 when both sides have one
--   already_in_vault rows: same sha1 + size present (or same size at the plain path without sha1)
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
begin;
drop table if exists raw_duck.vault_objects_20260916_post_move;
create table raw_duck.vault_objects_20260916_post_move (key text primary key, size bigint, sha1 text);
\copy raw_duck.vault_objects_20260916_post_move from '/tmp/vault_post_move.csv' with (format csv, header)
create index on raw_duck.vault_objects_20260916_post_move (sha1, size);

drop table if exists raw_duck.intake_moved_delete_20260916;
create table raw_duck.intake_moved_delete_20260916 as
select m.canonical_key as key, m.size, m.sha1, m.action, m.dest_key
from raw_duck.vault_move_rest_20260916 m
where (m.action = 'copy' and exists (
         select 1 from raw_duck.vault_objects_20260916_post_move v
         where v.key = m.dest_key and v.size = m.size and (m.sha1 = '' or coalesce(v.sha1, '') = '' or v.sha1 = m.sha1)))
   or (m.action = 'already_in_vault' and (
         (m.sha1 <> '' and exists (select 1 from raw_duck.vault_objects_20260916_post_move v where v.sha1 = m.sha1 and v.size = m.size))
      or (m.sha1 = '' and exists (select 1 from raw_duck.vault_objects_20260916_post_move v where v.key = m.plain_dest and v.size = m.size))));
commit;

\echo === vault after the move
select count(*) objects, round(sum(size)/1e9, 1) gb from raw_duck.vault_objects_20260916_post_move;

\echo === checks
select 'planned rows' k, count(*) from raw_duck.vault_move_rest_20260916
union all select 'proven in vault (to delete from intake)', count(*) from raw_duck.intake_moved_delete_20260916
union all select 'copy rows NOT proven (MUST be 0)', count(*) from raw_duck.vault_move_rest_20260916 m
  where m.action = 'copy' and not exists (select 1 from raw_duck.intake_moved_delete_20260916 d where d.key = m.canonical_key)
union all select 'objects lost from the post-prune vault (MUST be 0)', count(*) from raw_duck.vault_objects_20260916_post_prune p
  where not exists (select 1 from raw_duck.vault_objects_20260916_post_move v where v.key = p.key);

copy (select key from raw_duck.intake_moved_delete_20260916 order by key) to '/tmp/intake_moved_delete.list' with (format text);
