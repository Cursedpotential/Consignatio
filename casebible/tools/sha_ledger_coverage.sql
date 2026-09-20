-- Byline: Claude Code · Opus 5 · 2026-09-13
-- Read-only coverage measurement: how much of the R2 catalog (raw_duck) has a SHA-256 ledger record.
-- Loads the flattened ledger into a TEMP table and ends with ROLLBACK; no durable change.
-- Input: /tmp/sha_ledger_flat.tsv inside the database container (digest, bucket, key, etag, size).
begin;
-- Some ledger records have no sourceSize, so size loads as text and converts empty to NULL.
create temp table sha_ledger_raw(digest text, bucket text, key text, etag text, size text);
\copy sha_ledger_raw from '/tmp/sha_ledger_flat.tsv' with (format text)
create temp table sha_ledger as
  select digest, bucket, key, etag, nullif(size, '')::bigint as size from sha_ledger_raw;
select 'sha ledger rows / distinct digests', count(*), count(distinct digest) from sha_ledger;
select 'ledger records with no size / no etag / no digest', count(*) filter (where size is null),
  count(*) filter (where etag = ''), count(*) filter (where digest = '') from sha_ledger;
select 'catalog occurrences', count(*) from raw_duck.r2_files;
select 'occurrences with an exact (bucket, path) ledger record', count(*)
  from raw_duck.r2_files r where exists (select 1 from sha_ledger s where s.bucket = r.bucket and s.key = r.path);
select 'distinct catalog contents (md5, size)', count(*)
  from (select distinct md5, size from raw_duck.r2_files where md5 is not null) c;
select 'distinct contents with a sha256 (etag = md5, same size)', count(*)
  from (select distinct r.md5, r.size from raw_duck.r2_files r join sha_ledger s on s.etag = r.md5 and s.size = r.size) c;
select 'distinct contents md5-only (no sha256)', count(*)
  from (select distinct md5, size from raw_duck.r2_files where md5 is not null) c
  where not exists (select 1 from sha_ledger s where s.etag = c.md5 and s.size = c.size);
select 'eligible survivors (unflagged, hashed)', count(*)
  from raw_duck.final_survivors where integrity_status is null and md5 is not null;
select 'eligible survivors with a sha256', count(*)
  from raw_duck.final_survivors f where f.integrity_status is null and f.md5 is not null
  and exists (select 1 from sha_ledger s where s.etag = f.md5 and s.size = f.size);
select 'ledger records whose etag is not an md5 (multipart style)', count(*) from sha_ledger where etag !~ '^[0-9a-f]{32}$';
rollback;
