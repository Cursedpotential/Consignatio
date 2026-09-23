-- Byline: Claude Code · Opus 5 · 2026-09-13
-- Zero-filled / zero-byte catalog quarantine for raw_duck. Owner decision 2026-09-13:
-- flag and exclude, keep rows, null the hash; zero-byte rows carry no hash.
-- Run with the final line set to ROLLBACK for a dry run, COMMIT to apply.
begin;
create temp table hold_r2(bucket text, path text, size bigint, md5 text);
\copy hold_r2 from '/tmp/r2_zero_hold_rows.csv' with (format csv)
select 'hold rows loaded', count(*) from hold_r2;

select 'BEFORE r2_files md5 not null', count(*) filter (where coalesce(md5,'') <> ''), 'survivors md5 not null', (select count(*) from raw_duck.final_survivors where coalesce(md5,'') <> '') from raw_duck.r2_files;

create table if not exists raw_duck.integrity_hold (
  id bigserial primary key, catalog text not null, bucket text, path text, size bigint,
  hash_kind text, original_hash text, status text not null, reason text not null,
  detector text not null, detected_at timestamptz not null default now());
alter table raw_duck.r2_files add column if not exists integrity_status text, add column if not exists integrity_reason text;
alter table raw_duck.final_survivors add column if not exists integrity_status text, add column if not exists integrity_reason text;

create temp table zero_pairs as select distinct md5, size from hold_r2;

insert into raw_duck.integrity_hold (catalog, bucket, path, size, hash_kind, original_hash, status, reason, detector)
select 'raw_duck.r2_files', r.bucket, r.path, r.size, 'md5', r.md5, 'quarantined', 'all_zero_payload', 'zero-hash-by-size 2026-09-13'
from raw_duck.r2_files r join hold_r2 h on h.bucket = r.bucket and h.path = r.path and h.size = r.size and h.md5 = r.md5
union all
select 'raw_duck.r2_files', r.bucket, r.path, r.size, 'md5', r.md5, 'quarantined', 'zero_bytes_no_content', 'zero-hash-by-size 2026-09-13'
from raw_duck.r2_files r where r.size = 0
union all
select 'raw_duck.final_survivors', f.bucket, f.path, f.size, 'md5', f.md5, 'excluded_from_migration', 'all_zero_payload', 'zero-hash-by-size 2026-09-13'
from raw_duck.final_survivors f join zero_pairs z on z.md5 = f.md5 and z.size = f.size
union all
select 'raw_duck.final_survivors', f.bucket, f.path, f.size, 'md5', f.md5, 'excluded_from_migration', 'zero_bytes_no_content', 'zero-hash-by-size 2026-09-13'
from raw_duck.final_survivors f where f.size = 0;
select 'audit rows', catalog, reason, count(*) from raw_duck.integrity_hold group by 2, 3 order by 2, 3;

update raw_duck.r2_files r set md5 = null, integrity_status = 'quarantined', integrity_reason = 'all_zero_payload'
from hold_r2 h where h.bucket = r.bucket and h.path = r.path and h.size = r.size and h.md5 = r.md5;
update raw_duck.r2_files set md5 = null, integrity_status = 'quarantined', integrity_reason = 'zero_bytes_no_content' where size = 0;
update raw_duck.final_survivors f set md5 = null, integrity_status = 'excluded_from_migration', integrity_reason = 'all_zero_payload'
from zero_pairs z where z.md5 = f.md5 and z.size = f.size;
update raw_duck.final_survivors set md5 = null, integrity_status = 'excluded_from_migration', integrity_reason = 'zero_bytes_no_content' where size = 0;

select 'AFTER flagged r2_files', count(*), 'flagged still hashed (must be 0)', count(*) filter (where md5 is not null) from raw_duck.r2_files where integrity_status is not null;
select 'AFTER flagged survivors', count(*), 'still hashed (must be 0)', count(*) filter (where md5 is not null) from raw_duck.final_survivors where integrity_status is not null;
select 'AFTER r2_files md5 not null', count(*) filter (where coalesce(md5,'') <> ''), 'survivors md5 not null', (select count(*) from raw_duck.final_survivors where coalesce(md5,'') <> '') from raw_duck.r2_files;
select 'good rows touched (must be 0)', count(*) from raw_duck.r2_files r where r.integrity_status is not null and r.size > 0
  and not exists (select 1 from hold_r2 h where h.bucket = r.bucket and h.path = r.path);
select 'zero payload still matchable by md5 (must be 0)', count(*) from raw_duck.r2_files r join zero_pairs z on z.md5 = r.md5 and z.size = r.size;
COMMIT;
