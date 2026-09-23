-- Byline: Claude Code · Opus 5 · 2026-09-16 17:05 EDT (session propria-79)
-- Step 3 plan (owner 07:12 "what's not in the vault … still in intake — move it"). Catalog only, no B2 writes.
-- Inputs: raw_duck.intake_objects_20260916_post_clean (fresh intake, sha1), raw_duck.vault_objects_20260916_post_prune
-- (fresh vault, sha1). For every object still in intake:
--   already_in_vault : same sha1 + size anywhere in the vault; or (no sha1) same size at the planned path
--   copy             : otherwise → consignatio/vault/v1/<path inside its source root> (casebible-* strips 1 segment,
--                      gdrive/local/onedrive strip 2); name taken in the vault or by another move → " [<source>]"
--                      before the extension (e.g. " [gdrive-salemnet]"), then " [<source>-2]" …; nothing is overwritten.
-- The 6 recorded differing versions (raw_duck.intake_versions_differ_20260916) go through the same sha1 test.
-- Output: raw_duck.vault_move_rest_20260916 (canonical_key, dest_key, size, sha1, action), CSV of copy rows.
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
begin;
drop table if exists raw_duck.vault_move_rest_20260916;
create table raw_duck.vault_move_rest_20260916 as
with i as (
  select key, size, coalesce(sha1, '') sha1,
         substr(key, length('consignatio/intake/raw-dedupe/v1/source-buckets/') + 1) rel
  from raw_duck.intake_objects_20260916_post_clean
), p as (
  select i.*,
         case when rel like 'casebible-%' then split_part(rel, '/', 1)
              else split_part(rel, '/', 1) || '-' || split_part(rel, '/', 2) end as tag,
         case when rel like 'casebible-%' then substr(rel, length(split_part(rel, '/', 1)) + 2)
              else substr(rel, length(split_part(rel, '/', 1)) + length(split_part(rel, '/', 2)) + 3) end as inner_path
  from i
)
select p.key as canonical_key, p.size, p.sha1, p.tag, p.inner_path,
       'consignatio/vault/v1/' || p.inner_path as plain_dest,
       case when p.sha1 <> '' and exists (select 1 from raw_duck.vault_objects_20260916_post_prune v
                                          where v.sha1 = p.sha1 and v.size = p.size) then 'already_in_vault'
            when p.sha1 = '' and exists (select 1 from raw_duck.vault_objects_20260916_post_prune v
                                         where v.key = 'consignatio/vault/v1/' || p.inner_path and v.size = p.size) then 'already_in_vault'
            else 'copy' end as action,
       null::text as dest_key
from p;

-- destination names for copy rows: plain if free, else tagged, else tagged-N
create temp table taken as select key from raw_duck.vault_objects_20260916_post_prune;
create unique index on taken (key);
do $$
declare r record; cand text; n int; stem text; ext text;
begin
  for r in select canonical_key, plain_dest, tag from raw_duck.vault_move_rest_20260916 where action = 'copy' order by canonical_key loop
    cand := r.plain_dest;
    if exists (select 1 from taken where key = cand) then
      stem := regexp_replace(r.plain_dest, '(\.[^./]{1,8})$', '');
      ext := coalesce(substring(r.plain_dest from '(\.[^./]{1,8})$'), '');
      cand := stem || ' [' || r.tag || ']' || ext;
      n := 2;
      while exists (select 1 from taken where key = cand) loop
        cand := stem || ' [' || r.tag || '-' || n || ']' || ext;
        n := n + 1;
      end loop;
    end if;
    insert into taken values (cand);
    update raw_duck.vault_move_rest_20260916 set dest_key = cand where canonical_key = r.canonical_key;
  end loop;
end $$;
commit;

\echo === step 3 plan
select action, count(*) objects, round(sum(size)/1e9, 3) gb, count(*) filter (where dest_key <> plain_dest) renamed
from raw_duck.vault_move_rest_20260916 group by 1 order by 1;
select 'differing versions: ' || coalesce(m.action, 'NOT IN PLAN') k, count(*)
from raw_duck.intake_versions_differ_20260916 d left join raw_duck.vault_move_rest_20260916 m on m.canonical_key = d.key
group by 1;

\echo === guards (MUST be 0)
select 'copy rows without a destination' k, count(*) from raw_duck.vault_move_rest_20260916 where action = 'copy' and dest_key is null
union all select 'destination already in the vault', count(*) from raw_duck.vault_move_rest_20260916 m
  join raw_duck.vault_objects_20260916_post_prune v on v.key = m.dest_key where m.action = 'copy'
union all select 'duplicate destinations', count(*) - count(distinct dest_key) from raw_duck.vault_move_rest_20260916 where action = 'copy'
union all select 'intake objects not in the plan', (select count(*) from raw_duck.intake_objects_20260916_post_clean) - (select count(*) from raw_duck.vault_move_rest_20260916);

\echo === where copies land (top folders)
select split_part(substr(dest_key, 22), '/', 1) top, count(*) objects, round(sum(size)/1e9, 3) gb
from raw_duck.vault_move_rest_20260916 where action = 'copy' group by 1 order by 2 desc limit 15;

copy (select canonical_key, dest_key, size from raw_duck.vault_move_rest_20260916 where action = 'copy' order by dest_key)
  to '/tmp/move_rest_manifest.csv' with (format csv, header);
