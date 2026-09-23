-- Byline: Claude Code · Opus 5 · 2026-09-15 05:15 EDT
-- Vault step 1 (source consolidation) — GRAFT PLAN DRY RUN, analysis tables only. NO B2 writes.
-- Input: raw_duck.vault_occ_v0 (every occurrence) + raw_duck.source_mount_candidates (source_mount_candidates.sql).
-- Finding 05:10 EDT: every other source root has direct mounts onto local/D-Backup (the largest tree, 833k
-- occurrences, containing case/ = F:\case = the R2 raw vault root, google/, Photos/, Court/, fb/ …), so the spine is
-- D:\Backup and every other source grafts onto it:
--   an occurrence goes under the DEEPEST (longest) mount head of its source that contains it, re-rooted at that mount's
--   D-Backup target; no mount → its source-relative path unchanged (reported as fallback). D-Backup paths are unchanged.
-- Mount acceptance: >= 100 supporting files; per (source, head) the best-supported target wins.
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
select distinct on (src, head) src, head, target, files from m order by src, head, files desc;
create index on mm (src);

drop table if exists raw_duck.vault_place_v1;
create table raw_duck.vault_place_v1 as
select distinct on (o.md5, o.size, o.src, o.rel)
       o.md5, o.size, o.src, o.rel, o.canonical_key, mm.head as mount_head, mm.target as mount_target,
       case when mm.src is null then o.rel
            else concat_ws('/', nullif(mm.target, ''), nullif(substr(o.rel, length(mm.head) + case when mm.head = '' then 1 else 2 end), ''))
       end as vpath
from raw_duck.vault_occ_v0 o
left join mm on mm.src = o.src and (mm.head = '' or left(o.rel, length(mm.head) + 1) = mm.head || '/')
order by o.md5, o.size, o.src, o.rel, length(mm.head) desc nulls last;
alter table raw_duck.vault_place_v1 add column old_depth int, add column new_depth int;
update raw_duck.vault_place_v1 set old_depth = cardinality(string_to_array(rel, '/')), new_depth = cardinality(string_to_array(vpath, '/'));
create index on raw_duck.vault_place_v1 (vpath);
commit;

\echo === mounts accepted per source (onto D-Backup)
select src, count(*) mounts, sum(files) support from mm group by 1 order by 3 desc;

\echo === placement per source: via mount vs fallback, nesting change
select src, count(*) occ,
       count(*) filter (where mount_head is not null) via_mount,
       count(*) filter (where mount_head is null) fallback,
       count(*) filter (where new_depth > old_depth) deeper,
       count(*) filter (where new_depth < old_depth) shallower,
       round(avg(new_depth - old_depth), 2) avg_depth_delta
from raw_duck.vault_place_v1 group by 1 order by 2 desc;

\echo === merged tree size: objects a physical copy would need
select count(*) occurrences,
       count(distinct vpath) paths,
       count(distinct (vpath, md5, size)) path_content_objects,
       round(sum(size) filter (where rn = 1) / 1e9, 1) gb_if_copied,
       count(distinct (md5, size)) distinct_contents
from (select *, row_number() over (partition by vpath, md5, size order by src) rn from raw_duck.vault_place_v1) t;

\echo === collisions: one merged path, different contents
select count(*) colliding_paths, sum(n) contents_involved
from (select vpath, count(distinct (md5, size)) n from raw_duck.vault_place_v1 group by 1 having count(distinct (md5, size)) > 1) t;

\echo === top-level folders of the merged root (top 40)
select left(split_part(vpath, '/', 1), 50) top, count(distinct (vpath, md5, size)) objects, count(distinct src) sources,
       round(sum(size) / 1e9, 1) gb_occ
from raw_duck.vault_place_v1 group by 1 order by 2 desc limit 40;

\echo === largest fallback top-level dirs (not grafted), top 25
select src, left(split_part(rel, '/', 1) || '/' || split_part(rel, '/', 2), 70) dir, count(*) occ
from raw_duck.vault_place_v1 where mount_head is null and src <> 'local/D-Backup'
group by 1, 2 order by 3 desc limit 25;
