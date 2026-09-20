-- Byline: Claude Code · Opus 5 · 2026-09-15
-- Read-only survey for the source-root consolidation (owner 2026-09-15 04:55: "consolidate sources in b2,
-- then twins, then same meaning … new dir so nothing is deleted or overwritten … find an entry point where a
-- good number of dirs match and merge WITHOUT making the nesting worse").
-- Run: ssh ovh-files 'docker exec -i fgz1n7useplhk0t91uk7k1aw psql -U postgres -d casebible' < source_root_survey.sql
\pset pager off
select count(*) objs, round(sum(size)/1e9,1) gb, min(listed_at) min_listed, max(listed_at) max_listed from raw_duck.b2_objects;

select split_part(key,'/',1)||'/'||split_part(key,'/',2)||'/'||split_part(key,'/',3)||'/'||split_part(key,'/',4) pfx,
       count(*) objs, round(sum(size)/1e9,1) gb
from raw_duck.b2_objects group by 1 order by 2 desc limit 10;

-- top levels under source-buckets/ (level 2 in full, level 3 only where >= 2,000 files)
create temp table k as select substr(key, length('consignatio/intake/raw-dedupe/v1/source-buckets/')+1) rel, size
  from raw_duck.b2_objects where key like 'consignatio/intake/raw-dedupe/v1/source-buckets/%';
select left(split_part(rel,'/',1),24) s1, left(split_part(rel,'/',2),40) s2, count(*) files, round(sum(size)/1e9,1) gb,
       count(distinct split_part(rel,'/',3)) children
from k group by 1,2 order by 1, files desc;
select left(split_part(rel,'/',1),24) s1, left(split_part(rel,'/',2),30) s2, left(split_part(rel,'/',3),40) s3, count(*) files, round(sum(size)/1e9,1) gb
from k group by 1,2,3 having count(*) >= 2000 order by 1,2, files desc;

-- occurrence catalog shape
select column_name, data_type from information_schema.columns
where table_schema='raw_duck' and table_name='source_occurrences' order by ordinal_position;
select source, scope, disposition, count(*) from raw_duck.source_occurrences group by 1,2,3 order by 1,2,4 desc;
