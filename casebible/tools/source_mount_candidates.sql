-- Byline: Claude Code · Opus 5 · 2026-09-15 05:02 EDT
-- Vault step 1 (source consolidation) — ENTRY-POINT DETECTION, read-only analysis. NO B2 writes.
-- Owner 2026-09-15 04:55: "find an entry point or merge plan where a good number of dirs match and merge
-- WITHOUT making the nesting worse". Supersedes the per-file "shallowest path" rule in vault_plan_v0.sql
-- (that rule scatters a folder's files across different dirs); vault_occ_v0 is reused as the input universe.
--
-- Method: the same content (md5,size) with the same file name in two different source roots is aligned by its
-- longest common trailing directory suffix. What is left above that suffix on each side is a MOUNT:
--   src_a:head_a  ≡  src_b:head_b   (e.g. r2/casebible-quarantine:onedrive/Pictures/Camera Roll ≡ gdrive/salemnet:Google Photos)
-- Mounts supported by many files are the merge entry points. The shallower head becomes the merged location,
-- so the merge never nests deeper than the shallower side already is.
-- Output: raw_duck.source_mount_candidates (mounts with >= 25 supporting files) + report.
\pset pager off
set work_mem = '1GB';
\timing on
begin;

create temp table occ as
select v.md5, v.size, v.src, v.rel, string_to_array(v.rel, '/') as segs
from raw_duck.vault_occ_v0 v
join raw_duck.vault_content_v0 c on c.md5 = v.md5 and c.size = v.size
where v.depth >= 2 and c.sources >= 2 and c.occurrences <= 12;   -- bounded: skip ultra-common contents (icons, junk)

create temp table tails as
select o.md5, o.size, o.src, o.rel, o.segs[cardinality(o.segs)] as base, n,
       array_to_string(o.segs[cardinality(o.segs) - n : cardinality(o.segs) - 1], '/') as tail,
       array_to_string(o.segs[1 : cardinality(o.segs) - 1 - n], '/') as head
from occ o, generate_series(0, least(cardinality(o.segs) - 1, 10)) n;
create index on tails (md5, size, base, n, tail);
analyze tails;

-- best (deepest common suffix) alignment per occurrence pair across different source roots
create temp table pair_best as
select distinct on (a.src, a.rel, b.src, b.rel)
       a.src as src_a, a.head as head_a, b.src as src_b, b.head as head_b, a.n as tail_len, a.size
from tails a
join tails b on b.md5 = a.md5 and b.size = a.size and b.base = a.base and b.n = a.n and b.tail = a.tail and b.src > a.src
order by a.src, a.rel, b.src, b.rel, a.n desc;

drop table if exists raw_duck.source_mount_candidates;
create table raw_duck.source_mount_candidates as
select src_a, head_a, src_b, head_b, count(*) as files, sum(size) as bytes, round(avg(tail_len), 1) as avg_tail
from pair_best group by 1, 2, 3, 4 having count(*) >= 25;
create index on raw_duck.source_mount_candidates (src_a, head_a);
commit;

\echo === source-root pairs: how many aligned files link them
select src_a, src_b, count(*) mounts, sum(files) files, round(sum(bytes)/1e9,1) gb
from raw_duck.source_mount_candidates group by 1,2 order by 4 desc;

\echo === top 80 mounts (entry points), with each head's total file count for coverage
select left(src_a,22) src_a, left(nullif(head_a,''),55) head_a, left(src_b,22) src_b, left(nullif(head_b,''),55) head_b,
       files, round(bytes/1e9,1) gb, avg_tail,
       (select count(*) from raw_duck.vault_occ_v0 v where v.src = m.src_a and (m.head_a = '' or left(v.rel, length(m.head_a) + 1) = m.head_a || '/')) tot_a,
       (select count(*) from raw_duck.vault_occ_v0 v where v.src = m.src_b and (m.head_b = '' or left(v.rel, length(m.head_b) + 1) = m.head_b || '/')) tot_b
from (select * from raw_duck.source_mount_candidates order by files desc limit 80) m
order by files desc;
