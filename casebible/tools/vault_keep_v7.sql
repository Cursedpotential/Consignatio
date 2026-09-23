-- Byline: Claude Code · Opus 5 · 2026-09-16 08:45 EDT (session propria-79)
-- Vault dedupe keep table v7 = v6 keep order with the owner's 07:41/07:49 rule applied first: anything inside a
-- quarantine / hold / delete-class folder in the vault is misclassified, so a copy there is never the kept copy when a
-- copy exists outside such folders. Owner 08:40 AskUserQuestion: "Yes, dedupe the vault next".
-- Keep order per source object: 1. not in a cleanup-class folder, 2. placed from the OneDrive Case Bible trunk,
-- 3. no " [<source>]" tag, 4. shallowest, 5. alphabetical.
-- Writes catalog tables only (catalog rule, owner 08:32): raw_duck.vault_keep_v7, raw_duck.vault_delete_v7. No B2 writes.
\pset pager off
\timing on
set max_parallel_workers_per_gather = 0;
set work_mem = '512MB';

begin;
drop table if exists raw_duck.vault_keep_v7;
create table raw_duck.vault_keep_v7 as
select distinct on (m.canonical_key) m.canonical_key, m.dest_key, m.size
from raw_duck.vault_copy_manifest_v6 m
left join lateral (
  select bool_or(p.src = 'onedrive/Case Bible') as trunk
  from raw_duck.vault_place_v6 p where p.vpath = substr(m.dest_key, 22)
) t on true
order by m.canonical_key,
         (m.dest_key ~* '(^|/)(\.review_hold|_swept|_duplicates|_?to_be_deleted[^/]*|_dedup[^/]*|_review_hold|_quarantine[^/]*|not fucking trsash)(/|$)'
          or m.dest_key ~* '(^|/)triage/_recovered(/|$)') asc,
         coalesce(t.trunk, false) desc,
         (m.dest_key ~ ' \[[^]]+\]') asc,
         cardinality(string_to_array(m.dest_key, '/')) asc,
         m.dest_key;
create unique index on raw_duck.vault_keep_v7 (canonical_key);
create index on raw_duck.vault_keep_v7 (dest_key);

drop table if exists raw_duck.vault_delete_v7;
create table raw_duck.vault_delete_v7 as
select m.canonical_key, m.dest_key, m.size
from raw_duck.vault_copy_manifest_v6 m
where not exists (select 1 from raw_duck.vault_keep_v7 k where k.dest_key = m.dest_key);
create index on raw_duck.vault_delete_v7 (dest_key);
commit;

\echo === keep v7 vs v6
select count(*) kept, round(sum(size) / 1e9, 1) kept_gb from raw_duck.vault_keep_v7;
select count(*) delete_objects, round(sum(size) / 1e9, 1) delete_gb from raw_duck.vault_delete_v7;
select count(*) kept_copy_changed from raw_duck.vault_keep_v7 k join raw_duck.vault_keep_v6 o using (canonical_key) where k.dest_key <> o.dest_key;
select count(*) kept_inside_cleanup_folders_v7 from raw_duck.vault_keep_v7
where dest_key ~* '(^|/)(\.review_hold|_swept|_duplicates|_?to_be_deleted[^/]*|_dedup[^/]*|_review_hold|_quarantine[^/]*|not fucking trsash)(/|$)' or dest_key ~* '(^|/)triage/_recovered(/|$)';

\echo === guards (MUST be 0)
select 'source objects without a kept copy' k, count(*) from (select distinct canonical_key from raw_duck.vault_copy_manifest_v6) s
  where not exists (select 1 from raw_duck.vault_keep_v7 k where k.canonical_key = s.canonical_key)
union all select 'kept key also on delete list', count(*) from raw_duck.vault_keep_v7 k join raw_duck.vault_delete_v7 d using (dest_key)
union all select 'manifest rows neither kept nor deleted', (select count(*) from raw_duck.vault_copy_manifest_v6) - (select count(*) from raw_duck.vault_keep_v7) - (select count(*) from raw_duck.vault_delete_v7);

-- the delete list itself is written by vault_dedupe_intake_prune.py from this keep table (CSV-safe, re-checks every
-- kept object against a listing); raw_duck.vault_delete_v7 is its catalog twin
copy (select canonical_key, dest_key, size from raw_duck.vault_keep_v7 order by canonical_key) to '/tmp/vault_keep_v7.csv' with (format csv, header);
