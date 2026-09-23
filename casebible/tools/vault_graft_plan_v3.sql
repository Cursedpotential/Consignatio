-- Byline: Claude Code · Opus 5 · 2026-09-15 05:30 EDT
-- Vault step 1 (source consolidation) — GRAFT PLAN v3 DRY RUN, analysis tables only. NO B2 writes.
-- = v2 (vault_graft_plan_v2.sql) + owner ruling 2026-09-15 05:27 EDT "Meaningful name wins": when one side of a mount
-- is a recovery-generated name (8-hex carved folder, $R… recycle-bin name, recup_dir.N) and the other side is not,
-- the meaningful side keeps its path even if it is deeper. Otherwise the shallower side keeps its path (v2 rule).
-- v2 put 6,516 occurrences under such names (D-Backup 3,004 · F:\Disk Drill 2,210 · R2 raw 1,187 · salemnet 115).
\pset pager off
set work_mem = '1GB';
\timing on
begin;

create temp table m as
select case when src_a = 'local/D-Backup' then src_b else src_a end as src,
       case when src_a = 'local/D-Backup' then head_b else head_a end as head,
       case when src_a = 'local/D-Backup' then head_a else head_b end as target,
       files
from raw_duck.source_mount_candidates
where 'local/D-Backup' in (src_a, src_b) and files >= 100;
create temp table mm as
select distinct on (src, head) src, head, target, files,
       coalesce(cardinality(string_to_array(nullif(head, ''), '/')), 0) as hd,
       coalesce(cardinality(string_to_array(nullif(target, ''), '/')), 0) as td,
       head   ~ '(^|/)([0-9A-Fa-f]{8}|\$R[0-9A-Z]{6}|recup_dir\.[0-9]+)(/|$)' as head_junk,
       target ~ '(^|/)([0-9A-Fa-f]{8}|\$R[0-9A-Z]{6}|recup_dir\.[0-9]+)(/|$)' as target_junk
from m order by src, head, files desc;
alter table mm add column is_fwd boolean;
update mm set is_fwd = case when target_junk and not head_junk then false   -- keep the source's meaningful name
                            when head_junk and not target_junk then true    -- keep the spine's meaningful name
                            else hd >= td end;
create index on mm (src);
create temp table rev as
select distinct on (target) target, head, files from mm where not is_fwd order by target, files desc;

create temp table a as
select distinct on (o.md5, o.size, o.src, o.rel)
       o.md5, o.size, o.src, o.rel, o.canonical_key, mm.head, mm.target, mm.is_fwd
from raw_duck.vault_occ_v0 o
left join mm on o.src <> 'local/D-Backup' and mm.src = o.src and (mm.head = '' or left(o.rel, length(mm.head) + 1) = mm.head || '/')
order by o.md5, o.size, o.src, o.rel, length(mm.head) desc nulls last;

create temp table b as
select a.*,
       case when a.is_fwd then concat_ws('/', nullif(a.target, ''), nullif(substr(a.rel, length(a.head) + case when a.head = '' then 1 else 2 end), ''))
            else a.rel end as p1,
       (a.src = 'local/D-Backup' or coalesce(a.is_fwd, false)) as spine_ns
from a;

create temp table c as
select distinct on (b.md5, b.size, b.src, b.rel)
       b.md5, b.size, b.src, b.rel, b.canonical_key, b.head as mount_head, b.is_fwd, rev.target as rev_target,
       case when rev.target is null then b.p1
            else concat_ws('/', nullif(rev.head, ''), substr(b.p1, length(rev.target) + 2)) end as vpath0
from b
left join rev on b.spine_ns and left(b.p1, length(rev.target) + 1) = rev.target || '/'
order by b.md5, b.size, b.src, b.rel, length(rev.target) desc nulls last;

create temp table pr as
select vpath0, md5, size, row_number() over (partition by vpath0 order by occ desc, md5, size) as rk
from (select vpath0, md5, size, count(*) occ from c group by 1, 2, 3) t;

drop table if exists raw_duck.vault_place_v3;
create table raw_duck.vault_place_v3 as
select x.*, cardinality(string_to_array(x.vpath, '/')) as new_depth
from (
  select c.md5, c.size, c.src, c.rel, c.canonical_key, c.mount_head, c.is_fwd, c.rev_target, c.vpath0,
         case when pr.rk = 1 then c.vpath0 else regexp_replace(c.vpath0, '(\.[^./]{1,8})?$', ' [' || left(c.md5, 8) || ']\1') end as vpath,
         cardinality(string_to_array(c.rel, '/')) as old_depth
  from c join pr on pr.vpath0 = c.vpath0 and pr.md5 = c.md5 and pr.size = c.size
) x;
create index on raw_duck.vault_place_v3 (vpath);
commit;

\echo === mounts flipped by the meaningful-name rule
select count(*) filter (where target_junk and not head_junk) keep_source_name, count(*) filter (where head_junk and not target_junk) keep_spine_name from mm;

\echo === placement per source and nesting (deeper allowed only through the meaningful-name rule)
select src, count(*) occ, count(*) filter (where vpath <> rel) path_changed,
       count(*) filter (where new_depth > old_depth) deeper, count(*) filter (where new_depth < old_depth) shallower,
       round(avg(new_depth - old_depth), 2) avg_depth_delta
from raw_duck.vault_place_v3 group by 1 order by 2 desc;

\echo === files newly placed under a recovery-generated name (target 0)
select src, count(*) from raw_duck.vault_place_v3
where vpath <> rel and vpath ~ '(^|/)([0-9A-Fa-f]{8}|\$R[0-9A-Z]{6}|recup_dir\.[0-9]+)(/|$)' and rel !~ '(^|/)([0-9A-Fa-f]{8}|\$R[0-9A-Z]{6}|recup_dir\.[0-9]+)(/|$)'
group by 1 order by 2 desc;

\echo === merged tree size and collisions
select count(*) occurrences, count(distinct vpath) paths,
       (select count(*) from (select distinct vpath, md5, size from raw_duck.vault_place_v3) d) objects,
       (select round(sum(size) / 1e9, 1) from (select distinct vpath, md5, size from raw_duck.vault_place_v3) d) gb_if_copied
from raw_duck.vault_place_v3;
select 'collisions after suffix' k, count(*) from (select vpath from raw_duck.vault_place_v3 group by 1 having count(distinct (md5, size)) > 1) t;

\echo === top-level folders (top 40)
select left(split_part(vpath, '/', 1), 50) top, count(distinct (vpath, md5, size)) objects, count(distinct src) sources, round(sum(size) / 1e9, 1) gb_occ
from raw_duck.vault_place_v3 group by 1 order by 2 desc limit 40;
