-- Byline: Claude Code · Fable 5.1 · 2026-09-14
-- Content-on-B2 catalog: which (md5,size) already has a payload on B2, and under which key.
-- Backbone for every source join (OneDrive, Drive, D:\Backup): a source file whose (md5,size) is in
-- raw_duck.b2_content is catalog-only (occurrence row, no second payload); anything else is copied.
--
-- Inputs (staged by b2_content_catalog.sh; \copy cannot interpolate psql variables, so the paths are literal):
--   /tmp/graded_carriers.tsv = bucket\tpath\tsize\tmd5 (graded-carriers-all.tsv, the distinct contents the
--   graded tranches copy); /tmp/b2_listing.tsv = key\tsize from a fresh `rclone lsf -R --format ps` of
--   b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/; psql -v listed_at = ISO timestamp.
-- Derived tables: dropped and rebuilt on every run (nothing here is hand-curated).
\set B2_PREFIX 'consignatio/intake/raw-dedupe/v1/source-buckets/'

begin;

drop table if exists raw_duck.graded_carriers;
create table raw_duck.graded_carriers (
  bucket text not null, path text not null, size bigint not null, md5 text not null,
  b2_key text generated always as (:'B2_PREFIX' || bucket || '/' || path) stored
);
\copy raw_duck.graded_carriers (bucket, path, size, md5) from '/tmp/graded_carriers.tsv' with (format csv, delimiter E'\t', quote E'\x01', escape E'\x01')
create index on raw_duck.graded_carriers (md5, size);

drop table if exists raw_duck.b2_objects;
-- sha1 comes free with the B2 listing (lsf --format psh --hash SHA-1); large multipart objects may carry none
create table raw_duck.b2_objects (key text primary key, size bigint not null, sha1 text, listed_at timestamptz not null);
create temp table b2_in (rel text, size bigint, sha1 text);
\copy b2_in from '/tmp/b2_listing.tsv' with (format csv, delimiter E'\t', quote E'\x01', escape E'\x01')
insert into raw_duck.b2_objects select :'B2_PREFIX' || rel, size, nullif(sha1, ''), :'listed_at'::timestamptz from b2_in;

-- (md5,size) -> one b2 key. Carriers whose object is present on B2 win; otherwise any r2_files row whose
-- mirrored key is present (pre-existing objects from the server-to-server move). Held rows have null md5
-- so they never appear. Junk-filtered r2 rows were never copied, so they are absent from b2_objects.
drop table if exists raw_duck.b2_content;
create table raw_duck.b2_content as
select distinct on (md5, size) md5, size, b2_key, origin
from (
  select c.md5, c.size, c.b2_key, 'carrier' as origin
  from raw_duck.graded_carriers c join raw_duck.b2_objects o on o.key = c.b2_key and o.size = c.size
  union all
  select r.md5, r.size, o.key, 'preexisting'
  from raw_duck.r2_files r join raw_duck.b2_objects o
    on o.key = :'B2_PREFIX' || r.bucket || '/' || r.path and o.size = r.size
  where r.md5 is not null and r.md5 <> ''
  union all
  -- payloads uploaded straight from a source (F:, D:, OneDrive, Drive): ANY occurrence whose b2_key is present on
  -- B2 with a known md5 — not only disposition 'copied', because an early re-join relabelled some copied rows
  -- content_on_b2 (their own key) and their payloads dropped out of this table (found 2026-09-14 14:45 EDT via an
  -- 840 MB OneDrive upload that then looked "not on B2" to the D:\Backup plan)
  select s.md5, s.size, s.b2_key, 'source_copy'
  from raw_duck.source_occurrences s join raw_duck.b2_objects o on o.key = s.b2_key and o.size = s.size
  where s.md5 is not null and s.b2_key like 'consignatio/intake/raw-dedupe/v1/source-buckets/%'
) u
order by md5, size, origin;   -- 'carrier' < 'preexisting' < 'source_copy'
create unique index on raw_duck.b2_content (md5, size);

select 'graded_carriers' as t, count(*) from raw_duck.graded_carriers
union all select 'b2_objects', count(*) from raw_duck.b2_objects
union all select 'b2_content', count(*) from raw_duck.b2_content
union all select 'carriers_not_yet_on_b2', count(*) from raw_duck.graded_carriers c
          where not exists (select 1 from raw_duck.b2_objects o where o.key = c.b2_key);

commit;
