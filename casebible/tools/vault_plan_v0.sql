-- Byline: Claude Code · Fable 5.1 · 2026-09-15 04:55 EDT
-- Vault step 1 DRY RUN (owner 04:49/04:50: "consolidate sources in b2 … new dir so nothing is deleted or
-- overwritten … find an entry point or merge plan where a good number of dirs match and merge WITHOUT
-- making the nesting worse" · "dry run"). Read-only against the catalog; builds two analysis tables
-- (raw_duck.vault_occ_v0, raw_duck.vault_content_v0) and prints the plan metrics. NO B2 writes.
--
-- Universe = every live occurrence of every distinct content:
--   * raw_duck.source_occurrences (local/*, onedrive/*, gdrive/*) joined to b2_content on (md5,size)
--   * the three R2-derived buckets on B2 (casebible-raw / -sorted / -quarantine) joined to b2_content on key
-- rel  = path inside its source root (source prefix stripped)   depth = number of path segments (file incl.)
-- Rule under test: a content's step-1 vault path = its SHALLOWEST existing relative path across all sources
-- (ties: sorted > raw > gdrive > onedrive > local > quarantine). Never deeper than any existing placement.
begin;

drop table if exists raw_duck.vault_occ_v0;
create table raw_duck.vault_occ_v0 as
select c.md5, c.size, c.b2_key as canonical_key,
       s.source || case when s.scope <> '' then '/' || s.scope else '' end as src,
       s.path as rel,
       array_length(string_to_array(s.path, '/'), 1) as depth
from raw_duck.source_occurrences s
join raw_duck.b2_content c on c.md5 = s.md5 and c.size = s.size
where s.disposition in ('content_on_b2', 'copied', 'exported')
union all
select c.md5, c.size, c.b2_key,
       'r2/' || split_part(o.key, '/', 6),
       regexp_replace(o.key, '^consignatio/intake/raw-dedupe/v1/source-buckets/[^/]+/', ''),
       array_length(string_to_array(o.key, '/'), 1) - 6
from raw_duck.b2_objects o
join raw_duck.b2_content c on c.b2_key = o.key
where o.key like 'consignatio/intake/raw-dedupe/v1/source-buckets/casebible-%';
-- source priority for ties at equal depth (sorted > raw > gdrive > onedrive > local > quarantine)
alter table raw_duck.vault_occ_v0 add column src_rank int;
update raw_duck.vault_occ_v0 set src_rank = case
  when src like 'r2/casebible-sorted%' then 1 when src like 'r2/casebible-raw%' then 2 when src like 'gdrive/%' then 3
  when src like 'onedrive/%' then 4 when src like 'local/%' then 5 else 6 end;
create index on raw_duck.vault_occ_v0 (md5, size);
create index on raw_duck.vault_occ_v0 (src);

drop table if exists raw_duck.vault_content_v0;
create table raw_duck.vault_content_v0 as
with n as (select md5, size, count(*) occurrences, count(distinct src) sources from raw_duck.vault_occ_v0 group by 1,2),
pick as (
  select distinct on (md5, size) md5, size, canonical_key, src as chosen_src, rel as chosen_rel, depth as chosen_depth
  from raw_duck.vault_occ_v0
  order by md5, size, depth, src_rank, rel)
select p.md5, p.size, p.canonical_key,
       array_length(string_to_array(p.canonical_key, '/'), 1) - 7 as canonical_depth,   -- depth inside its source root
       p.chosen_src, p.chosen_rel, p.chosen_depth, n.occurrences, n.sources
from pick p join n on n.md5 = p.md5 and n.size = p.size;
create unique index on raw_duck.vault_content_v0 (md5, size);
create index on raw_duck.vault_content_v0 (chosen_rel);

\echo === universe
select 'occurrences' k, count(*) from raw_duck.vault_occ_v0
union all select 'distinct contents', count(*) from raw_duck.vault_content_v0
union all select 'contents in >1 source', count(*) from (select md5,size from raw_duck.vault_occ_v0 group by 1,2 having count(distinct src) > 1) t
union all select 'bytes GB', round(sum(size)/1e9) from raw_duck.vault_content_v0;

\echo === occurrences per source root
select src, count(*) occ, count(distinct (md5,size)) contents, round(avg(depth),1) avg_depth, max(depth) max_depth from raw_duck.vault_occ_v0 group by 1 order by 2 desc;

\echo === nesting: canonical key depth today vs shallowest existing placement
select 'contents lifted (shallower than canonical)' k, count(*) from raw_duck.vault_content_v0 where chosen_depth < canonical_depth
union all select 'contents unchanged depth', count(*) from raw_duck.vault_content_v0 where chosen_depth = canonical_depth
union all select 'avg canonical depth x100', round(avg(canonical_depth)*100) from raw_duck.vault_content_v0
union all select 'avg chosen depth x100', round(avg(chosen_depth)*100) from raw_duck.vault_content_v0
union all select 'max canonical depth', max(canonical_depth) from raw_duck.vault_content_v0
union all select 'max chosen depth', max(chosen_depth) from raw_duck.vault_content_v0;

\echo === depth histogram (contents): canonical today vs chosen
select d, sum(case when kind='canonical' then n else 0 end) canonical, sum(case when kind='chosen' then n else 0 end) chosen
from (select canonical_depth d, 'canonical' kind, count(*) n from raw_duck.vault_content_v0 group by 1
      union all select chosen_depth, 'chosen', count(*) from raw_duck.vault_content_v0 group by 1) t
group by d order by d;

\echo === which source root wins the placement
select chosen_src, count(*) contents, round(sum(size)/1e9,1) gb from raw_duck.vault_content_v0 group by 1 order by 2 desc;

\echo === top-level dirs of the resulting single root (first segment of chosen_rel), top 40
select split_part(chosen_rel,'/',1) top, count(*) contents, round(sum(size)/1e9,1) gb, count(distinct chosen_src) srcs from raw_duck.vault_content_v0 group by 1 order by 2 desc limit 40;

\echo === path collisions: different contents that would land on the same vault path
select 'colliding paths' k, count(*) from (select chosen_rel from raw_duck.vault_content_v0 group by 1 having count(*) > 1) t
union all select 'contents involved', count(*) from raw_duck.vault_content_v0 v where exists (select 1 from raw_duck.vault_content_v0 w where w.chosen_rel = v.chosen_rel and (w.md5,w.size) <> (v.md5,v.size));

commit;
