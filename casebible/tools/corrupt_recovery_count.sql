-- Byline: Claude Code · Fable 5.1 · 2026-09-14
-- Final corrupt-vs-recovered count (owner 2026-09-14 10:21: "a final corrupt and missing vs corrupt and recovered count").
-- corrupt  = every all-zero-payload occurrence found on 2026-09-13/14: the R2+B2+Drive hold manifest plus the
--            local (F:, D:) zero-filled rows from the dedupe plans. Empty (0-byte) files are not corruption.
-- recovered= a GOOD copy of the same file exists somewhere: identity is basename + size (all a placeholder keeps).
--   good-copy universes: (1) B2 live tree (raw_duck.b2_objects outside _quarantine/ — every zero-filled object was
--   moved out of it and the hold list blocked the rest); (2) catalog occurrences with a real content disposition
--   (raw_duck.source_occurrences: D:/F:/OneDrive/Drive rows in content_on_b2 | copied | pending_carrier | exported).
-- missing  = no such copy anywhere → listed for the owner. Analysis only; writes nothing durable except the report tables.
begin;
drop table if exists raw_duck.corrupt_recovery;
create temp table cr_in (store text, container text, path text, size bigint, hash_kind text, hash text, reason text);
\copy cr_in from '/tmp/zero_filled_hold_manifest.csv' with (format csv, header true)
\copy cr_in from '/tmp/local_zero_rows.csv' with (format csv, header true)

create temp table good_b2 as
  select regexp_replace(key, '^.*/', '') as name, size from raw_duck.b2_objects
  where key not like 'consignatio/intake/_quarantine/%' and size > 0;
create index on good_b2 (name, size);
create temp table good_occ as
  select distinct regexp_replace(path, '^.*/', '') as name, size from raw_duck.source_occurrences
  where disposition in ('content_on_b2', 'copied', 'pending_carrier', 'exported') and size > 0;
create index on good_occ (name, size);

create table raw_duck.corrupt_recovery as
select c.store, c.container, c.path, c.size, c.hash,
       regexp_replace(c.path, '^.*/', '') as name,
       exists (select 1 from good_b2 g where g.name = regexp_replace(c.path, '^.*/', '') and g.size = c.size) as good_on_b2,
       exists (select 1 from good_occ g where g.name = regexp_replace(c.path, '^.*/', '') and g.size = c.size) as good_in_catalog
from cr_in c;
commit;

select store, count(*) as corrupt,
       count(*) filter (where good_on_b2 or good_in_catalog) as recovered,
       count(*) filter (where not good_on_b2 and not good_in_catalog) as missing,
       round(sum(size) filter (where not good_on_b2 and not good_in_catalog) / 1e6, 1) as missing_mb
from raw_duck.corrupt_recovery group by store order by corrupt desc;
select 'TOTAL corrupt=' || count(*) || ' recovered=' || count(*) filter (where good_on_b2 or good_in_catalog)
    || ' missing=' || count(*) filter (where not good_on_b2 and not good_in_catalog)
    || ' distinct_missing_files(name+size)=' || count(distinct (name, size)) filter (where not good_on_b2 and not good_in_catalog)
from raw_duck.corrupt_recovery;
\copy (select store, container, path, size from raw_duck.corrupt_recovery where not good_on_b2 and not good_in_catalog order by size desc, path) to '/tmp/corrupt_missing.csv' with (format csv, header true)
select name, size, count(*) as occurrences, min(store || ':' || coalesce(nullif(container, '') || '/', '') || path) as example
from raw_duck.corrupt_recovery where not good_on_b2 and not good_in_catalog group by name, size order by size desc limit 25;
