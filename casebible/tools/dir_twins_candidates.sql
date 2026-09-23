-- Byline: Claude Code · Fable 5.1 · 2026-09-14
-- Directory-level consolidation candidates over everything on B2 (raw_duck.b2_objects). Analysis only.
-- Owner 2026-09-14 07:51: "first cleaning task can be consolidating all the same dirs, and the numbered twins,
-- and just collapsing to a single root source — no more raw/sorted/quarantine/gdrive/onedrive".
--
-- raw_duck.dir_manifests : every directory (all depths, all sources) with a recursive member manifest
--   dir_manifest    = sha256 over sorted "relpath<TAB>size<TAB>sha1" (byte-identical trees share it)
--   content_manifest= sha256 over sorted "size<TAB>sha1" (same files, different layout)
-- raw_duck.dir_identical_groups : groups of ≥2 directories with equal dir_manifest (merge to one)
-- raw_duck.dir_twin_groups     : sibling directories whose names differ only by a copy/number suffix
--   (X, X (1), X 2, X (copy 1), X_DUPLICATE, X-1, X_2 …) — merge candidates that need a per-file rule
-- Nothing here moves or decides; unit boundaries (raw_duck.atomic_units) are joined for the report.
begin;
drop table if exists raw_duck.dir_twin_groups;
drop table if exists raw_duck.dir_identical_groups;
drop table if exists raw_duck.dir_manifests;

create temp table k as
select substr(key, length('consignatio/intake/raw-dedupe/v1/source-buckets/') + 1) as rel, size, sha1
from raw_duck.b2_objects;

-- every ancestor directory of every file (depth-limited to 12 for cost)
create temp table anc as
select d.dir, k.rel, k.size, k.sha1
from k, lateral (
  select array_to_string((string_to_array(k.rel, '/'))[1:n], '/') as dir
  from generate_series(1, least(array_length(string_to_array(k.rel, '/'), 1) - 1, 12)) as n
) d;

create table raw_duck.dir_manifests as
select dir,
       case when dir like 'local/%' or dir like 'gdrive/%' then split_part(dir,'/',1)||'/'||split_part(dir,'/',2) else split_part(dir,'/',1) end as source,
       array_length(string_to_array(dir, '/'), 1) as depth,
       regexp_replace(dir, '^.*/', '') as name,
       count(*) as files, sum(size) as bytes,
       encode(sha256(convert_to(string_agg(substr(rel, length(dir) + 2) || E'\t' || size || E'\t' || coalesce(sha1,''), E'\n' order by rel), 'UTF8')), 'hex') as dir_manifest,
       encode(sha256(convert_to(string_agg(size || E'\t' || coalesce(sha1,''), E'\n' order by size, sha1), 'UTF8')), 'hex') as content_manifest
from anc group by dir;
create index on raw_duck.dir_manifests (dir_manifest);
create index on raw_duck.dir_manifests (content_manifest);
create index on raw_duck.dir_manifests (dir);

-- identical trees: keep only the OUTERMOST occurrence per group (a child of an identical tree is identical by construction)
create table raw_duck.dir_identical_groups as
select dir_manifest, count(*) as copies, min(files) as files, min(bytes) as bytes,
       array_agg(dir order by depth, dir) as dirs, array_agg(distinct source) as sources
from raw_duck.dir_manifests m
where files >= 2
  and not exists (select 1 from raw_duck.dir_manifests p
                  where p.dir_manifest <> m.dir_manifest and m.dir like p.dir || '/%'
                    and exists (select 1 from raw_duck.dir_manifests q where q.dir_manifest = p.dir_manifest and q.dir <> p.dir))
group by dir_manifest having count(*) >= 2;

-- numbered / copy twins among siblings (same parent, names equal after stripping a copy suffix)
create table raw_duck.dir_twin_groups as
select parent, base, count(*) as twins, array_agg(name order by name) as names, sum(files) as files, sum(bytes) as bytes,
       count(distinct dir_manifest) as distinct_manifests
from (
  select regexp_replace(dir, '/[^/]*$', '') as parent, dir, name, files, bytes, dir_manifest,
         case when name ~ '^[0-9]{4}(-[0-9]{2}){1,2}$' then lower(name)   -- date-named folders (Cube ACR 2025-06 …) are never twins
              else lower(regexp_replace(name,
                '(\s*\((copy\s*)?[0-9]+\)|\s*-\s*copy(\s*\([0-9]+\))?|[ _-](copy|dup(licate)?|DUPLICATE)[ _-]?[0-9]*|[ _-][0-9]{1,2})$', '')) end as base
  from raw_duck.dir_manifests where depth >= 2
) s
group by parent, base having count(*) >= 2;

-- same-named directories under DIFFERENT roots (across sources or within one) with partially overlapping content:
-- the "consolidate all the same dirs" candidates. Overlap = shared sha1 set between the two trees.
drop table if exists raw_duck.dir_samename_overlap;
create temp table ds as select distinct dir, sha1 from anc where sha1 is not null;
create index on ds (dir, sha1);
create temp table named as
  select m.dir, m.source, m.name, m.files, m.bytes, m.dir_manifest
  from raw_duck.dir_manifests m
  where m.files >= 20 and m.name !~ '^[0-9]{4}(-[0-9]{2}){1,2}$' and lower(m.name) not in ('takeout','google photos','messages','inbox','photos','videos','documents','desktop','downloads','html','json','img','images','css','js','lib','src','dist','build','test','tests','docs','data','output','logs','archive','backup','new folder','untitled');
create temp table pairs as
  select a.dir as dir_a, b.dir as dir_b, a.name, a.source as src_a, b.source as src_b, a.files as files_a, b.files as files_b
  from named a join named b on lower(a.name) = lower(b.name) and a.dir < b.dir and a.dir_manifest <> b.dir_manifest
    and not (b.dir like a.dir || '/%') and not (a.dir like b.dir || '/%')
  order by least(a.files, b.files) desc limit 20000;   -- bounded: the largest same-name pairs first
create table raw_duck.dir_samename_overlap as
select p.*, s.shared_sha1,
       round(s.shared_sha1::numeric / greatest(least(p.files_a, p.files_b), 1), 2) as overlap_of_smaller
from pairs p
join lateral (select count(*) as shared_sha1 from ds a join ds b on b.sha1 = a.sha1 where a.dir = p.dir_a and b.dir = p.dir_b) s on true
where s.shared_sha1 > 0;

commit;

select 'dirs=' || (select count(*) from raw_duck.dir_manifests)
    || ' identical_groups=' || (select count(*) from raw_duck.dir_identical_groups)
    || ' identical_extra_copies=' || (select coalesce(sum(copies - 1), 0) from raw_duck.dir_identical_groups)
    || ' identical_extra_files=' || (select coalesce(sum((copies - 1) * files), 0) from raw_duck.dir_identical_groups)
    || ' identical_extra_GB=' || (select round(coalesce(sum((copies - 1) * bytes), 0) / 1e9, 1) from raw_duck.dir_identical_groups)
    || ' twin_groups=' || (select count(*) from raw_duck.dir_twin_groups)
    || ' twin_groups_all_identical=' || (select count(*) from raw_duck.dir_twin_groups where distinct_manifests = 1)
    || ' twin_dirs=' || (select coalesce(sum(twins), 0) from raw_duck.dir_twin_groups);
select copies, files, round(bytes/1e9, 2) as gb, sources, dirs[1:3] as first_dirs
from raw_duck.dir_identical_groups order by (copies - 1) * bytes desc limit 15;
select parent, base, twins, distinct_manifests, files, round(bytes/1e9,2) as gb, names[1:4]
from raw_duck.dir_twin_groups order by files desc limit 15;
select 'samename_pairs=' || count(*) || ' pairs_overlap_ge_0.9=' || count(*) filter (where overlap_of_smaller >= 0.9)
    || ' pairs_overlap_0.5_0.9=' || count(*) filter (where overlap_of_smaller >= 0.5 and overlap_of_smaller < 0.9)
    || ' cross_source_pairs=' || count(*) filter (where src_a <> src_b) from raw_duck.dir_samename_overlap;
select name, src_a, src_b, files_a, files_b, shared_sha1, overlap_of_smaller, left(dir_a, 70) as dir_a, left(dir_b, 70) as dir_b
from raw_duck.dir_samename_overlap order by shared_sha1 desc limit 20;
