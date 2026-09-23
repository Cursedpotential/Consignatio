-- Byline: Claude Code · Opus 5 · 2026-09-15 08:40 EDT (session propria-79)
-- Vault step 1 (collapse sources into one root) — MERGE PLAN v6 = the plan that gets COPIED. This SQL writes no B2.
-- v6 = v5 + owner 08:31 "yes" to the one named exception: local/D-Backup `Court/FB DATA` joins the trunk's
-- `moved/Evidence/FB Exports/FB DATA` two levels deeper (37,145 files). Also builds raw_duck.vault_copy_manifest_v6
-- (one object per merged path → consignatio/vault/v1/<path>) and exports it to /tmp/vault_copy_manifest_v6.csv.
-- Earlier header (v5):
-- = v4b (vault_merge_plan_v4.sql) + owner ruling 2026-09-15 ~08:03 EDT (AskUserQuestion answer):
--   "+1 level, not into cleanup" — a source folder may go ONE level deeper to join the trunk's same-named folder;
--   never join into the trunk's cleanup folders (.review_hold, _SWEPT, _DUPLICATES, to_be_deleted) at any depth.
-- Unchanged rules (verbatim in Consignatio/docs/URGENT-TODO.md): trunk = OneDrive Case Bible, its paths never change;
-- Takeout / Facebook-Meta / .obsidian units sealed, never matched by members, never folded; no folder renamed into
-- another name (a mount needs a common folder name F); collisions keep both ([<source>] on unit roots, [<md5 8>] on
-- loose files; the trunk always keeps its name).
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

create temp table mm_all as
select distinct on (src, src_head, f) src, src_head, f, trunk_head, support,
       coalesce(cardinality(string_to_array(nullif(src_head, ''), '/')), 0) as sd,
       coalesce(cardinality(string_to_array(nullif(trunk_head, ''), '/')), 0) as td,
       concat_ws('/', nullif(src_head, ''), f) as mp,
       concat_ws('/', nullif(trunk_head, ''), f) as target
from (select src, src_head, f, trunk_head, count(*) as support from pair_best group by 1, 2, 3, 4 having count(*) >= 20) m
order by src, src_head, f, support desc;

drop table if exists raw_duck.vault_mounts_v6;
create table raw_duck.vault_mounts_v6 as
select m.*,
       case when m.src = 'local/D-Backup' and m.mp = 'Court/FB DATA' and m.target = 'moved/Evidence/FB Exports/FB DATA' then 'used: owner exception +2'
            when m.target ~* '(^|/)(\.review_hold|_swept|_duplicates|_?to_be_deleted)(/|$)' then 'dropped: trunk cleanup folder'
            when m.td > m.sd + 1 then 'dropped: more than 1 level deeper'
            when m.td = m.sd + 1 then 'used: +1 level'
            else 'used' end as decision,
       (select count(*) from raw_duck.vault_occ_v1 o where o.src = m.src and left(o.rel, length(m.mp) + 1) = m.mp || '/') as source_files
from mm_all m;

create temp table mm as select * from raw_duck.vault_mounts_v6 where decision like 'used%';
create index on mm (src);

create temp table place as
select distinct on (o.src, o.rel)
       o.md5, o.size, o.src, o.rel, o.canonical_key, o.unit_root, o.unit_class, mm.mp, mm.trunk_head, mm.f, mm.decision,
       case when mm.mp is null then o.rel
            else concat_ws('/', nullif(mm.trunk_head, ''), mm.f, nullif(substr(o.rel, length(mm.mp) + 2), '')) end as vpath0,
       case when o.unit_root is null then null
            when mm.mp is null then o.unit_root
            else concat_ws('/', nullif(mm.trunk_head, ''), mm.f, nullif(substr(o.unit_root, length(mm.mp) + 2), '')) end as vunit0
from raw_duck.vault_occ_v1 o
left join mm on o.src <> 'onedrive/Case Bible' and mm.src = o.src and left(o.rel, length(mm.mp) + 1) = mm.mp || '/'
order by o.src, o.rel, length(mm.mp) desc nulls last;

create temp table unit_land as
select distinct src, unit_root, vunit0 from place where unit_root is not null;
create temp table unit_final as
select u.src, u.unit_root, u.vunit0,
       case when c.n > 1 and u.src <> 'onedrive/Case Bible'
            then u.vunit0 || ' [' || replace(u.src, '/', '-') || ']' else u.vunit0 end as vunit
from unit_land u
join (select vunit0, count(*) n from unit_land group by 1) c using (vunit0);

drop table if exists raw_duck.vault_place_v6;
create table raw_duck.vault_place_v6 as
select p.md5, p.size, p.src, p.rel, p.canonical_key, p.unit_root, p.unit_class, p.mp, p.trunk_head, p.decision, uf.vunit,
       case when uf.vunit is not null then uf.vunit || substr(p.vpath0, length(p.vunit0) + 1) else p.vpath0 end as vpath1,
       cardinality(string_to_array(p.rel, '/')) as old_depth
from place p
left join unit_final uf on uf.src = p.src and uf.unit_root = p.unit_root;

create temp table fr as
select vpath1, md5, size, row_number() over (partition by vpath1 order by trunk desc, n desc, md5, size) rk   -- the trunk's file always keeps its name
from (select vpath1, md5, size, count(*) n, bool_or(src = 'onedrive/Case Bible') trunk
      from raw_duck.vault_place_v6 where unit_root is null group by 1, 2, 3) t;
alter table raw_duck.vault_place_v6 add column vpath text, add column new_depth int;
update raw_duck.vault_place_v6 v set vpath = case when v.unit_root is null and fr.rk > 1
         then regexp_replace(v.vpath1, '(\.[^./]{1,8})?$', ' [' || left(v.md5, 8) || ']\1') else v.vpath1 end
from fr where fr.vpath1 = v.vpath1 and fr.md5 = v.md5 and fr.size = v.size and v.unit_root is null;
update raw_duck.vault_place_v6 set vpath = vpath1 where vpath is null;
update raw_duck.vault_place_v6 set new_depth = cardinality(string_to_array(vpath, '/'));
create index on raw_duck.vault_place_v6 (vpath);
commit;

\echo === mount decisions per source
select src, decision, count(*) mounts, sum(support) support, sum(source_files) source_files
from raw_duck.vault_mounts_v6 group by 1, 2 order by 1, 2;
select decision, count(*) mounts, sum(source_files) source_files from raw_duck.vault_mounts_v6 group by 1 order by 1;

\echo === largest mounts used (source folder -> trunk folder)
select left(src, 22) src, left(mp, 55) source_folder, left(target, 55) trunk_folder, decision, support, source_files
from raw_duck.vault_mounts_v6 where decision like 'used%' order by source_files desc limit 30;

\echo === largest mounts dropped
select left(src, 22) src, left(mp, 55) source_folder, left(target, 55) would_join, decision, source_files
from raw_duck.vault_mounts_v6 where decision like 'dropped%' order by source_files desc limit 15;

\echo === guards (all MUST be 0)
select 'trunk rows moved' k, count(*) from raw_duck.vault_place_v6 where src = 'onedrive/Case Bible' and vpath <> rel
union all select 'rows more than 1 level deeper', count(*) from raw_duck.vault_place_v6 where new_depth > old_depth + 1 and coalesce(decision, '') <> 'used: owner exception +2'
union all select 'rows +1 deeper without a +1 mount', count(*) from raw_duck.vault_place_v6 where new_depth = old_depth + 1 and coalesce(decision, '') <> 'used: +1 level'
union all select 'rows moved into a trunk cleanup folder', count(*) from raw_duck.vault_place_v6 where mp is not null and vpath ~* '(^|/)(\.review_hold|_swept|_duplicates|_?to_be_deleted)(/|$)' and rel !~* '(^|/)(\.review_hold|_swept|_duplicates|_?to_be_deleted)(/|$)'
union all select 'units split across landing roots', count(*) from (select src, unit_root from raw_duck.vault_place_v6 where unit_root is not null group by 1, 2 having count(distinct vunit) > 1) t
union all select 'paths with different contents', count(*) from (select vpath from raw_duck.vault_place_v6 group by 1 having count(distinct (md5, size)) > 1) t;

\echo === placement per source
select src, count(*) occ, count(*) filter (where vpath <> rel) moved, count(*) filter (where new_depth > old_depth) one_deeper,
       count(*) filter (where new_depth < old_depth) shallower, round(avg(new_depth - old_depth), 2) avg_depth_change
from raw_duck.vault_place_v6 group by 1 order by 2 desc;

\echo === units that landed on an occupied path and got a source tag
select count(*) tagged_units from unit_final where vunit <> vunit0;

\echo === merged tree size
select count(*) occurrences, count(distinct vpath) paths,
       (select count(*) from (select distinct vpath, md5, size from raw_duck.vault_place_v6) d) objects,
       (select round(sum(size) / 1e9, 1) from (select distinct vpath, md5, size from raw_duck.vault_place_v6) d) gb_if_copied
from raw_duck.vault_place_v6;

\echo === top-level folders (top 40)
select left(split_part(vpath, '/', 1), 50) top, count(distinct (vpath, md5, size)) objects, count(distinct src) sources
from raw_duck.vault_place_v6 group by 1 order by 2 desc limit 40;

\echo === examples flagged earlier
select src, left(rel, 90) rel, left(vpath, 90) vpath from raw_duck.vault_place_v6
where (src = 'local/F-case' and rel like 'Evidence/Cube ACR/2025-08-03/2025-08-03 18-19-49%')
   or (src = 'local/D-Backup' and rel = 'google/Takeout/Google Photos/Fuck man/IMG_3199.PNG')
   or (src = 'gdrive/salem85' and rel like 'Takeout/Takeout/Voice/Spam/+16262493531%mp3')
   or (src = 'r2/casebible-sorted' and rel = 'Code/to-review/.obsidian/plugins/folder-navigator/manifest.json')
   or (src = 'r2/casebible-quarantine' and rel = 'onedrive/Pictures/Camera Roll/2018/07/IMG_2406.HEIC');

\echo === owner exception rows
select count(*) exception_rows, max(new_depth - old_depth) max_extra_levels from raw_duck.vault_place_v6 where decision = 'used: owner exception +2';

\echo === copy manifest: one object per merged path
begin;
drop table if exists raw_duck.vault_copy_manifest_v6;
create table raw_duck.vault_copy_manifest_v6 as
select min(canonical_key) as canonical_key, 'consignatio/vault/v1/' || vpath as dest_key, min(size) as size
from raw_duck.vault_place_v6 group by vpath;
create unique index on raw_duck.vault_copy_manifest_v6 (dest_key);
commit;

\echo === manifest checks (key_too_long, bad_key, no_source, sources_not_on_b2 MUST be 0)
select count(*) objects, round(sum(size) / 1e9, 1) gb, count(*) filter (where size > 5e9) over_5gb,
       count(*) filter (where octet_length(dest_key) > 1024) key_too_long,
       count(*) filter (where dest_key ~ '//' or dest_key ~ '/$') bad_key,
       count(*) filter (where canonical_key is null) no_source
from raw_duck.vault_copy_manifest_v6;
select count(*) sources_not_on_b2 from raw_duck.vault_copy_manifest_v6 m
where not exists (select 1 from raw_duck.b2_objects o where o.key = m.canonical_key);

copy (select canonical_key, dest_key, size from raw_duck.vault_copy_manifest_v6 order by dest_key)
  to '/tmp/vault_copy_manifest_v6.csv' with (format csv, header);
