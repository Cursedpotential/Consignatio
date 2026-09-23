-- Byline: Claude Code · Opus 5 · 2026-09-15 08:50 EDT (session propria-79)
-- Finish vault_merge_plan_v6.sql's last two steps. That run built raw_duck.vault_place_v6 / vault_mounts_v6 /
-- vault_copy_manifest_v6 (guards 0, key checks 0) but the "sources_not_on_b2" anti-join failed with
-- "could not resize shared memory segment … No space left on device" (parallel hash join vs the container's small
-- /dev/shm), so the CSV export never ran. Parallel query is off here so no dynamic shared memory is needed.
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
set work_mem = '256MB';

\echo === sources_not_on_b2 (MUST be 0)
select count(*) sources_not_on_b2 from raw_duck.vault_copy_manifest_v6 m
where not exists (select 1 from raw_duck.b2_objects o where o.key = m.canonical_key);

\echo === export
copy (select canonical_key, dest_key, size from raw_duck.vault_copy_manifest_v6 order by dest_key)
  to '/tmp/vault_copy_manifest_v6.csv' with (format csv, header);
