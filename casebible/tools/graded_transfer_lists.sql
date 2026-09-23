-- Byline: Claude Code · Fable 5 · 2026-09-13
-- Build per-bucket transfer lists from raw_duck.graded_selection: one payload per content,
-- excluding contents already present on B2 (matched by md5+size via the fresh B2 listing).
-- Winner rows are preferred; for keep-both ties the lexically first path carries the payload
-- (all tied rows remain in the catalog). Zero-filled contents are excluded by construction.
-- Read-only against durable tables; outputs land in /tmp inside the DB container.
-- Input: /tmp/b2_listing.tsv (key<TAB>size) = fresh lsf of the B2 source-buckets prefix.
begin;

create temp table b2(key text, size bigint);
\copy b2 from '/tmp/b2_listing.tsv' with (format text)
select 'b2 objects loaded', count(*) from b2;

-- contents already on B2 (matched through the catalog by bucket/path -> md5)
create temp table b2_contents as
  select distinct r.md5, r.size
  from b2 join raw_duck.r2_files r on (r.bucket || '/' || r.path) = b2.key and r.size = b2.size
  where coalesce(r.md5, '') <> '';
select 'contents already on B2', count(*) from b2_contents;

-- one carrier row per content still missing
create temp table carriers as
  select distinct on (md5, size) bucket, path, size, md5
  from raw_duck.graded_selection g
  where not exists (select 1 from b2_contents b where b.md5 = g.md5 and b.size = g.size)
  order by md5, size, (disposition <> 'winner'), path;

select 'contents to copy', count(*), round(sum(size) / 1e9, 1) as gb from carriers;
select 'by source bucket', bucket, count(*), round(sum(size) / 1e9, 1) as gb from carriers group by bucket order by bucket;

\copy (select path from carriers where bucket = 'casebible-quarantine' order by path) to '/tmp/graded-casebible-quarantine.list'
\copy (select path from carriers where bucket = 'casebible-raw' order by path) to '/tmp/graded-casebible-raw.list'
\copy (select path from carriers where bucket = 'casebible-sorted' order by path) to '/tmp/graded-casebible-sorted.list'
\copy (select bucket, path, size, md5 from carriers order by bucket, path) to '/tmp/graded-carriers-all.tsv'

rollback;
