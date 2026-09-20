-- Byline: Claude Code · Opus 5 · 2026-09-16 07:05 EDT (session propria-79)
-- Inputs for vault_dedupe_intake_prune.py. Writes analysis tables + two CSVs; no B2 writes.
-- Owner 2026-09-16 07:01: "You need to dedupe this. And if it's into the vault [it] needs to be removed from intake."
-- raw_duck.vault_keep_v6: ONE vault object per distinct source object (canonical_key), chosen:
--   1. a path placed from the OneDrive Case Bible trunk, 2. a path without a " [<source>]" tag,
--   3. the shallowest path, 4. alphabetical.
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
set work_mem = '512MB';

begin;
drop table if exists raw_duck.vault_keep_v6;
create table raw_duck.vault_keep_v6 as
select distinct on (m.canonical_key) m.canonical_key, m.dest_key, m.size
from raw_duck.vault_copy_manifest_v6 m
left join lateral (
  select bool_or(p.src = 'onedrive/Case Bible') as trunk
  from raw_duck.vault_place_v6 p where p.vpath = substr(m.dest_key, 22)
) t on true
order by m.canonical_key,
         coalesce(t.trunk, false) desc,
         (m.dest_key ~ ' \[[^]]+\]') asc,
         cardinality(string_to_array(m.dest_key, '/')) asc,
         m.dest_key;
create unique index on raw_duck.vault_keep_v6 (canonical_key);
commit;

select count(*) kept_objects, round(sum(size) / 1e9, 1) kept_gb from raw_duck.vault_keep_v6;

copy (select canonical_key, dest_key, size from raw_duck.vault_keep_v6 order by canonical_key)
  to '/tmp/vault_keep_v6.csv' with (format csv, header);
copy (select key, size, coalesce(sha1, '') as sha1 from raw_duck.b2_objects order by key)
  to '/tmp/intake_catalog_sha1.csv' with (format csv, header);
