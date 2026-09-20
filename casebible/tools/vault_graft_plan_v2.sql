-- Byline: Claude Code · Opus 5 · 2026-09-15 05:20 EDT
-- Vault step 1 (source consolidation) — GRAFT PLAN v2 DRY RUN, analysis tables only. NO B2 writes.
-- v1 (vault_graft_plan_v1.sql) grafted every source onto the D:\Backup spine and made 94,974 occurrences DEEPER
-- (e.g. R2 raw root → case/, +1). Owner rule: merge WITHOUT making the nesting worse. v2 rule: for each mount the
-- SHALLOWER side keeps its path.
--   forward mount (source head depth >= spine target depth): the source subtree is re-rooted onto the spine target;
--   reverse mount (source head shallower): the spine subtree under target is re-rooted to the source head, and the
--     source keeps its own paths.
--   Spine paths (D-Backup + forward-grafted occurrences) then get the reverse rewrites, longest target first.
--   Every rewrite shortens or keeps depth, so no occurrence ends deeper than its source-relative path.
-- Collisions (one merged path, different contents): the content with most occurrences keeps the name; the others get
-- "<name> [<md5 first 8>].<ext>" (owner precedent: "<name> [gdrive-<id8>].<ext>").
-- Mount acceptance as v1: >= 100 supporting files; per (source, head) the best-supported target.
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
       coalesce(cardinality(string_to_array(nullif(target, ''), '/')), 0) as td
from m order by src, head, files desc;
create index on mm (src);
create temp table rev as
select distinct on (target) target, head, files from mm where hd < td order by target, files desc;

-- A: source side (longest source mount head)
create temp table a as
select distinct on (o.md5, o.size, o.src, o.rel)
       o.md5, o.size, o.src, o.rel, o.canonical_key, mm.head, mm.target, (mm.hd >= mm.td) as is_fwd
from raw_duck.vault_occ_v0 o
left join mm on o.src <> 'local/D-Backup' and mm.src = o.src and (mm.head = '' or left(o.rel, length(mm.head) + 1) = mm.head || '/')
order by o.md5, o.size, o.src, o.rel, length(mm.head) desc nulls last;

create temp table b as
select a.*,
       case when a.is_fwd then concat_ws('/', nullif(a.target, ''), nullif(substr(a.rel, length(a.head) + case when a.head = '' then 1 else 2 end), ''))
            else a.rel end as p1,
       (a.src = 'local/D-Backup' or coalesce(a.is_fwd, false)) as spine_ns
from a;

-- B: spine side (longest reverse target)
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

drop table if exists raw_duck.vault_place_v2;
create table raw_duck.vault_place_v2 as
select x.*, cardinality(string_to_array(x.vpath, '/')) as new_depth
from (
  select c.md5, c.size, c.src, c.rel, c.canonical_key, c.mount_head, c.is_fwd, c.rev_target, c.vpath0,
         case when pr.rk = 1 then c.vpath0 else regexp_replace(c.vpath0, '(\.[^./]{1,8})?$', ' [' || left(c.md5, 8) || ']\1') end as vpath,
         cardinality(string_to_array(c.rel, '/')) as old_depth
  from c join pr on pr.vpath0 = c.vpath0 and pr.md5 = c.md5 and pr.size = c.size
) x;
create index on raw_duck.vault_place_v2 (vpath);
commit;

\echo === mounts: forward (source onto spine) vs reverse (spine onto shallower source head)
select src, count(*) filter (where hd >= td) fwd, count(*) filter (where hd < td) rev, sum(files) support from mm group by 1 order by 4 desc;
select left(target, 60) spine_target, left(nullif(head, ''), 60) becomes, files from rev order by files desc limit 20;

\echo === placement per source and nesting (deeper MUST be 0)
select src, count(*) occ,
       count(*) filter (where mount_head is not null or rev_target is not null) moved_by_mount,
       count(*) filter (where vpath <> rel) path_changed,
       count(*) filter (where new_depth > old_depth) deeper,
       count(*) filter (where new_depth < old_depth) shallower,
       round(avg(new_depth - old_depth), 2) avg_depth_delta
from raw_duck.vault_place_v2 group by 1 order by 2 desc;

\echo === merged tree size: objects a physical copy would need
select count(*) occurrences, count(distinct vpath) paths,
       (select count(*) from (select distinct vpath, md5, size from raw_duck.vault_place_v2) d) objects,
       (select round(sum(size) / 1e9, 1) from (select distinct vpath, md5, size from raw_duck.vault_place_v2) d) gb_if_copied,
       (select count(*) from (select distinct md5, size from raw_duck.vault_place_v2) d) distinct_contents
from raw_duck.vault_place_v2;

\echo === collisions before / after the md5 suffix
select 'before suffix' k, count(*) paths from (select vpath0 from raw_duck.vault_place_v2 group by 1 having count(distinct (md5, size)) > 1) t
union all
select 'after suffix', count(*) from (select vpath from raw_duck.vault_place_v2 group by 1 having count(distinct (md5, size)) > 1) t;

\echo === top-level folders of the merged root (top 40)
select left(split_part(vpath, '/', 1), 50) top, count(distinct (vpath, md5, size)) objects, count(distinct src) sources, round(sum(size) / 1e9, 1) gb_occ
from raw_duck.vault_place_v2 group by 1 order by 2 desc limit 40;
