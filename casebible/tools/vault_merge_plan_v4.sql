-- Byline: Claude Code · Opus 5 · 2026-09-15 07:45 EDT (session propria-79)
-- Vault step 1 (collapse sources into one root) — MERGE PLAN v4 DRY RUN, analysis table only. NO B2 writes.
-- Replaces the voided v1–v3 graft plans. Owner rules (verbatim in Consignatio/docs/URGENT-TODO.md):
--   * "onedrive/case bible is the trunk" (07:09) — trunk paths never change.
--   * Takeouts / Facebook-Meta exports / .obsidian are sealed units (raw_duck.vault_occ_v1.unit_root, vault_units_v2):
--     never matched by their member files, never split, never folded ("I would rather you not even try", 07:30).
--   * "Don't destroy my units of organization" (07:26): no folder is renamed into another folder's name. A mount
--     requires at least one common folder name F (same name on both sides); matching only chooses where F goes.
--   * Never deeper (04:55): a mount is used only if the trunk parent of F is not deeper than the source parent of F.
-- Method: non-unit files present in the trunk and another source (same content + same file name) are aligned by their
-- longest common folder suffix (>= 1 folder). The top common folder F gives a mount
--   <source parent>/F  ->  <trunk parent>/F        (>= 20 supporting files; best-supported per source folder)
-- A source occurrence under the deepest matching mount moves to <trunk parent>/F/<rest>; otherwise it keeps its path.
-- Units ride along inside their parent folder (mount points come from non-unit files, so never fall inside a unit).
-- Two different units landing on the same path both stay: the non-trunk one gets " [<source>]" on its root folder.
-- Two different loose files on the same path both stay: the lower-ranked gets " [<md5 8>]" before the extension.
\pset pager off
set work_mem = '1GB';
\timing on
begin;

create temp table occ as
select o.md5, o.size, o.src, o.rel, string_to_array(o.rel, '/') as segs
from raw_duck.vault_occ_v1 o
where o.unit_root is null and o.rel like '%/%'
  and (o.md5, o.size) in (select md5, size from raw_duck.vault_occ_v1 where unit_root is null
                          group by 1, 2 having count(*) between 2 and 12 and count(distinct src) >= 2);

create temp table tails as
select o.md5, o.size, o.src, o.rel, o.segs[cardinality(o.segs)] as base, n,
       array_to_string(o.segs[cardinality(o.segs) - n : cardinality(o.segs) - 1], '/') as tail,
       array_to_string(o.segs[1 : cardinality(o.segs) - 1 - n], '/') as head
from occ o, generate_series(1, least(cardinality(o.segs) - 1, 10)) n;
create index on tails (md5, size, base, n, tail);
analyze tails;

create temp table pair_best as
select distinct on (a.src, a.rel, t.rel)
       a.src, a.head as src_head, t.head as trunk_head, split_part(a.tail, '/', 1) as f, a.n
from tails a
join tails t on t.src = 'onedrive/Case Bible' and t.md5 = a.md5 and t.size = a.size and t.base = a.base and t.n = a.n and t.tail = a.tail
where a.src <> 'onedrive/Case Bible'
order by a.src, a.rel, t.rel, a.n desc;

create temp table mm as
select distinct on (src, src_head, f) src, src_head, f, trunk_head, support,
       coalesce(cardinality(string_to_array(nullif(src_head, ''), '/')), 0) as sd,
       coalesce(cardinality(string_to_array(nullif(trunk_head, ''), '/')), 0) as td,
       concat_ws('/', nullif(src_head, ''), f) as mp
from (select src, src_head, f, trunk_head, count(*) as support from pair_best group by 1, 2, 3, 4 having count(*) >= 20) m
order by src, src_head, f, support desc;
-- all candidate mounts persisted for review; used = false where joining the trunk folder would deepen the source
drop table if exists raw_duck.vault_mounts_v4;
create table raw_duck.vault_mounts_v4 as
select m.*, (m.td <= m.sd) as used,
       (select count(*) from raw_duck.vault_occ_v1 o where o.src = m.src and left(o.rel, length(m.mp) + 1) = m.mp || '/') as source_files
from mm m;
create temp table mm_deeper as select * from mm where td > sd;
delete from mm where td > sd;
create index on mm (src);

create temp table place as
select distinct on (o.src, o.rel)
       o.md5, o.size, o.src, o.rel, o.unit_root, o.unit_class, mm.mp, mm.trunk_head, mm.f,
       case when mm.mp is null then o.rel
            else concat_ws('/', nullif(mm.trunk_head, ''), mm.f, nullif(substr(o.rel, length(mm.mp) + 2), '')) end as vpath0,
       case when o.unit_root is null then null
            when mm.mp is null then o.unit_root
            else concat_ws('/', nullif(mm.trunk_head, ''), mm.f, nullif(substr(o.unit_root, length(mm.mp) + 2), '')) end as vunit0
from raw_duck.vault_occ_v1 o
left join mm on o.src <> 'onedrive/Case Bible' and mm.src = o.src and left(o.rel, length(mm.mp) + 1) = mm.mp || '/'
order by o.src, o.rel, length(mm.mp) desc nulls last;

-- unit root collisions: one landing path, several (source, unit) → trunk keeps the name, others get " [<source>]"
create temp table unit_land as
select distinct src, unit_root, vunit0 from place where unit_root is not null;
create temp table unit_final as
select u.src, u.unit_root, u.vunit0,
       case when c.n > 1 and u.src <> 'onedrive/Case Bible'
            then u.vunit0 || ' [' || replace(u.src, '/', '-') || ']' else u.vunit0 end as vunit
from unit_land u
join (select vunit0, count(*) n from unit_land group by 1) c using (vunit0);

drop table if exists raw_duck.vault_place_v4;
create table raw_duck.vault_place_v4 as
select p.md5, p.size, p.src, p.rel, p.unit_root, p.unit_class, p.mp, p.trunk_head, uf.vunit,
       case when uf.vunit is not null then uf.vunit || substr(p.vpath0, length(p.vunit0) + 1) else p.vpath0 end as vpath1,
       cardinality(string_to_array(p.rel, '/')) as old_depth
from place p
left join unit_final uf on uf.src = p.src and uf.unit_root = p.unit_root;

-- loose-file collisions (units cannot collide after the root suffix)
create temp table fr as
select vpath1, md5, size, row_number() over (partition by vpath1 order by trunk desc, n desc, md5, size) rk   -- the trunk's file always keeps its name
from (select vpath1, md5, size, count(*) n, bool_or(src = 'onedrive/Case Bible') trunk
      from raw_duck.vault_place_v4 where unit_root is null group by 1, 2, 3) t;
alter table raw_duck.vault_place_v4 add column vpath text, add column new_depth int;
update raw_duck.vault_place_v4 v set vpath = case when v.unit_root is null and fr.rk > 1
         then regexp_replace(v.vpath1, '(\.[^./]{1,8})?$', ' [' || left(v.md5, 8) || ']\1') else v.vpath1 end
from fr where fr.vpath1 = v.vpath1 and fr.md5 = v.md5 and fr.size = v.size and v.unit_root is null;
update raw_duck.vault_place_v4 set vpath = vpath1 where vpath is null;
update raw_duck.vault_place_v4 set new_depth = cardinality(string_to_array(vpath, '/'));
create index on raw_duck.vault_place_v4 (vpath);
commit;

\echo === mounts used per source, and mounts dropped because they would deepen
select src, count(*) mounts, sum(support) support from mm group by 1 order by 3 desc;
select src, count(*) dropped_deeper, sum(support) support from mm_deeper group by 1 order by 3 desc;

\echo === mounts NOT used because the source folder would go one or more levels deeper to join the trunk folder
select left(src, 22) src, left(mp, 60) source_folder, left(concat_ws('/', nullif(trunk_head, ''), f), 60) would_join, td - sd extra_levels, support, source_files
from raw_duck.vault_mounts_v4 where not used order by source_files desc limit 30;
select sum(source_files) files_kept_out_of_trunk, count(*) mounts from raw_duck.vault_mounts_v4 where not used;

\echo === largest mounts (source folder -> trunk location; F keeps its name)
select left(src, 22) src, left(mp, 60) source_folder, left(concat_ws('/', nullif(trunk_head, ''), f), 60) trunk_folder, support
from mm order by support desc limit 30;

\echo === guards (all MUST be 0)
select 'trunk rows moved' k, count(*) from raw_duck.vault_place_v4 where src = 'onedrive/Case Bible' and vpath <> rel
union all select 'rows deeper than before', count(*) from raw_duck.vault_place_v4 where new_depth > old_depth
union all select 'units split across landing roots', count(*) from (select src, unit_root from raw_duck.vault_place_v4 where unit_root is not null group by 1, 2 having count(distinct vunit) > 1) t
union all select 'paths with different contents', count(*) from (select vpath from raw_duck.vault_place_v4 group by 1 having count(distinct (md5, size)) > 1) t
union all select 'mount folder renamed', count(*) from raw_duck.vault_place_v4 where mp is not null and split_part(substr(vpath, length(concat_ws('/', nullif(trunk_head, ''), '')) + 1), '/', 1) <> regexp_replace(mp, '^.*/', '') and trunk_head <> '';

\echo === placement per source
select src, count(*) occ, count(*) filter (where vpath <> rel) moved, count(*) filter (where new_depth < old_depth) shallower,
       round(avg(new_depth - old_depth), 2) avg_depth_change
from raw_duck.vault_place_v4 group by 1 order by 2 desc;

\echo === units that landed on an occupied path and got a source tag
select count(*) tagged_units from unit_final where vunit <> vunit0;
select left(src, 22) src, left(unit_root, 60) unit_root, left(vunit, 90) lands_as from unit_final where vunit <> vunit0 order by vunit limit 20;

\echo === merged tree size
select count(*) occurrences, count(distinct vpath) paths,
       (select count(*) from (select distinct vpath, md5, size from raw_duck.vault_place_v4) d) objects,
       (select round(sum(size) / 1e9, 1) from (select distinct vpath, md5, size from raw_duck.vault_place_v4) d) gb_if_copied
from raw_duck.vault_place_v4;

\echo === top-level folders (top 40)
select left(split_part(vpath, '/', 1), 50) top, count(distinct (vpath, md5, size)) objects, count(distinct src) sources
from raw_duck.vault_place_v4 group by 1 order by 2 desc limit 40;

\echo === examples the owner flagged earlier
select src, left(rel, 90) rel, left(vpath, 90) vpath from raw_duck.vault_place_v4
where (src = 'local/F-case' and rel like 'Evidence/Cube ACR/2025-08-03/2025-08-03 18-19-49%')
   or (src = 'local/D-Backup' and rel = 'google/Takeout/Google Photos/Fuck man/IMG_3199.PNG')
   or (src = 'gdrive/salem85' and rel like 'Takeout/Takeout/Voice/Spam/+16262493531%')
   or (src = 'r2/casebible-sorted' and rel = 'Code/to-review/.obsidian/plugins/folder-navigator/manifest.json')
   or (src = 'r2/casebible-quarantine' and rel = 'onedrive/Pictures/Camera Roll/2018/07/IMG_2406.HEIC');
