-- Coco Super Index source table: one row per object in the current vault listing,
-- carrying every recorded occurrence of it (original path and name, source account,
-- modified time, hashes, metadata), so the index can be queried by name and date.
-- Byline: Claude Code · Opus 5 · 2026-09-18 (Build 1; owner 22:47-22:48 EDT: the index
--   must carry dates and names, not just key/size/sha1)
--
-- Inputs (read-only):
--   raw_duck.vault_objects_20260916_r4            current vault listing; has ONLY key, size, sha1
--   raw_duck.vault_onecopy_pilot_delete_20260916  49 keys deleted after r4 was loaded
--   raw_duck.intake_catalog_fs_20260917           every recorded occurrence -> its current vault key
--                                                 (built by intake_catalog_fs_20260917.sql)
-- Output (new dated table, nothing else written): raw_duck.vault_index_source_20260918
--
-- Dates are copied per occurrence exactly as recorded, next to the source they came from.
-- None is merged, picked, normalized or invented here; known-bad values (restore batch
-- stamps, 1980 placeholders) stay visible as they are.
-- Limitation: intake_catalog_fs_20260917 links each occurrence to ONE vault key (same
-- basename first, then shortest key), so extra vault copies of the same content show
-- occurrence_count = 0; the check below counts them.
--
-- Run serially (parallel workers hit "could not resize shared memory segment" before):
--   docker exec -i fgz1n7useplhk0t91uk7k1aw psql -U postgres -d casebible -v ON_ERROR_STOP=1 < vault_index_source_20260918.sql

set max_parallel_workers_per_gather = 0;
set work_mem = '256MB';

create table raw_duck.vault_index_source_20260918 as
select v.key,
       v.size,
       v.sha1,
       regexp_replace(v.key, '^.*/', '') as name,
       count(o.rel) as occurrence_count,
       coalesce(
         jsonb_agg(jsonb_build_object(
             'source', o.source, 'scope', o.scope, 'path', o.path, 'name', o.name,
             'source_id', o.source_id, 'size', o.size, 'modtime', o.modtime,
             'native_hash_kind', o.native_hash_kind, 'native_hash', o.native_hash,
             'md5', o.md5, 'disposition', o.disposition, 'matched_origin', o.matched_origin,
             'recorded_at', o.recorded_at, 'metadata', o.metadata)
           order by o.source, o.scope, o.path)
           filter (where o.rel is not null),
         '[]'::jsonb) as occurrences
from raw_duck.vault_objects_20260916_r4 v
left join raw_duck.intake_catalog_fs_20260917 o on o.vault_key = v.key
where not exists (select 1 from raw_duck.vault_onecopy_pilot_delete_20260916 d where d.key = v.key)
group by v.key, v.size, v.sha1;

alter table raw_duck.vault_index_source_20260918 add primary key (key);

-- Must equal the set verified live on 2026-09-16: 508,152 objects, 2,170,597,644,994 bytes.
select count(*) as objects, sum(size) as bytes from raw_duck.vault_index_source_20260918;
select count(*) filter (where occurrence_count = 0) as objects_without_occurrence,
       sum(occurrence_count) as occurrences_attached
from raw_duck.vault_index_source_20260918;
