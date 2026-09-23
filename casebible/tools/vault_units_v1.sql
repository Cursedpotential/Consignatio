-- Byline: Claude Code · Opus 5 · 2026-09-15 07:35 EDT
-- Vault consolidation — UNITS FIRST (read-only analysis tables, NO B2 writes). Replaces the v0–v3 plans, voided by the owner.
-- Owner rules 2026-09-15 07:22–07:26 EDT (verbatim in Consignatio/docs/URGENT-TODO.md):
--   * Takeouts are atomic: the unit root stops at the Takeout-named folder, plus the next folder only if it is a
--     username. A service folder (Google Photos, Voice …) is too far.
--   * ".obsidian" is a boundary: the whole .obsidian folder is one piece.
--   * Member files may be read only to PROVE two units are the same account/export. Not proven → separate units.
--   * Existing folders are units of organization: never renamed into another folder (applies to the later merge step).
-- Facebook / Meta export roots (facebook-<name>-<date>-…, meta-<date>-…) are units too (owner 2026-09-14 07:35).
--
-- 1. raw_duck.vault_occ_v1 : every occurrence, now joined by b2_key first (vault_occ_v0 joined only by md5 and lost
--    291,010 proxy-matched OneDrive Case Bible rows), md5 fallback; unit_root/unit_class per occurrence.
-- 2. raw_duck.vault_units_v1 : one row per unit occurrence (source + unit root).
-- 3. raw_duck.vault_unit_pairs_v1 : unit pairs sharing members (same path inside the unit + same content), overlap
--    of the smaller unit. >= 0.90 = proven same unit; below = not proven, kept separate.
\pset pager off
set work_mem = '1GB';
\timing on

create or replace function raw_duck.vault_unit_root(p text) returns text[] language plpgsql immutable as $$
declare s text[] := string_to_array(p, '/'); n int := cardinality(s) - 1; g int; j int;
begin
  for g in 1..n loop
    if s[g] = '.obsidian' then
      return array[array_to_string(s[1:g], '/'), 'obsidian'];
    end if;
    if s[g] ~* '^(facebook-.+-20[0-9]{2}-|meta-20[0-9]{2}-)' then
      return array[array_to_string(s[1:g], '/'), 'facebook'];
    end if;
    if s[g] ~* 'takeout' then
      j := g;
      while j < n and s[j + 1] ~* 'takeout' loop j := j + 1; end loop;
      if j < n and s[j + 1] ~* '(@|^(matt[._-]?salem[^/]*|msalem|salem85|potentiallycursed85)$)' then j := j + 1; end if;
      return array[array_to_string(s[1:j], '/'), 'takeout'];
    end if;
  end loop;
  return null;
end $$;

begin;
drop table if exists raw_duck.vault_unit_pairs_v1;
drop table if exists raw_duck.vault_units_v1;
drop table if exists raw_duck.vault_occ_v1;

create temp table bk as select distinct on (b2_key) b2_key, md5, size from raw_duck.b2_content order by b2_key;
create index on bk (b2_key);
create temp table bm as select distinct on (md5, size) md5, size, b2_key from raw_duck.b2_content order by md5, size, b2_key;
create index on bm (md5, size);

create table raw_duck.vault_occ_v1 as
with so as (
  select s.source || case when s.scope <> '' then '/' || s.scope else '' end as src, s.path as rel, s.b2_key, s.md5, s.size
  from raw_duck.source_occurrences s
  where s.disposition in ('content_on_b2', 'copied', 'exported'))
select coalesce(k.md5, m.md5) as md5, coalesce(k.size, m.size) as size, coalesce(k.b2_key, m.b2_key) as canonical_key,
       so.src, so.rel, case when k.b2_key is not null then 'b2_key' else 'md5' end as joined_by
from so
left join bk k on k.b2_key = so.b2_key
left join bm m on k.b2_key is null and m.md5 = so.md5 and m.size = so.size
where k.b2_key is not null or m.b2_key is not null
union all
select c.md5, c.size, c.b2_key, 'r2/' || split_part(o.key, '/', 6),
       regexp_replace(o.key, '^consignatio/intake/raw-dedupe/v1/source-buckets/[^/]+/', ''), 'b2_key'
from raw_duck.b2_objects o join bk c on c.b2_key = o.key
where o.key like 'consignatio/intake/raw-dedupe/v1/source-buckets/casebible-%';

alter table raw_duck.vault_occ_v1 add column unit_root text, add column unit_class text;
update raw_duck.vault_occ_v1 v set unit_root = r[1], unit_class = r[2]
from (select ctid as id, raw_duck.vault_unit_root(rel) as r from raw_duck.vault_occ_v1) x
where v.ctid = x.id and x.r is not null;
create index on raw_duck.vault_occ_v1 (src, unit_root);

create table raw_duck.vault_units_v1 as
select row_number() over (order by src, unit_root) as unit_id, src, unit_root, unit_class,
       count(*) as members, sum(size) as bytes
from raw_duck.vault_occ_v1 where unit_root is not null
group by src, unit_root, unit_class;
create index on raw_duck.vault_units_v1 (src, unit_root);

-- members keyed by (path inside the unit, content); keys present in > 40 units are skipped as non-identifying
create temp table mem as
select u.unit_id, u.unit_class, md5(substr(o.rel, length(o.unit_root) + 2) || E'\t' || o.md5 || E'\t' || o.size) as k
from raw_duck.vault_occ_v1 o join raw_duck.vault_units_v1 u on u.src = o.src and u.unit_root = o.unit_root
group by 1, 2, 3;
create index on mem (k);
create temp table common_keys as select k from mem group by k having count(*) between 2 and 40;

create table raw_duck.vault_unit_pairs_v1 as
select a.unit_id as unit_a, b.unit_id as unit_b, count(*) as shared
from mem a join common_keys ck on ck.k = a.k
join mem b on b.k = a.k and b.unit_id > a.unit_id and b.unit_class = a.unit_class
group by 1, 2;
alter table raw_duck.vault_unit_pairs_v1 add column overlap_of_smaller numeric;
update raw_duck.vault_unit_pairs_v1 p set overlap_of_smaller = round(p.shared::numeric / least(ua.members, ub.members), 3)
from raw_duck.vault_units_v1 ua, raw_duck.vault_units_v1 ub where ua.unit_id = p.unit_a and ub.unit_id = p.unit_b;
commit;

\echo === universe: occurrences per source (b2_key join vs md5 fallback)
select src, count(*) occ, count(*) filter (where joined_by = 'md5') via_md5, count(*) filter (where unit_root is not null) in_units
from raw_duck.vault_occ_v1 group by 1 order by 2 desc;

\echo === units per class and source
select unit_class, src, count(*) units, sum(members) members, round(sum(bytes) / 1e9, 1) gb
from raw_duck.vault_units_v1 group by 1, 2 order by 1, 4 desc;

\echo === unit pairs: proven (>= 0.90 of the smaller) vs not proven
select u.unit_class,
       count(*) filter (where p.overlap_of_smaller >= 0.9) proven_pairs,
       count(*) filter (where p.overlap_of_smaller >= 0.5 and p.overlap_of_smaller < 0.9) partial_pairs_kept_separate,
       count(*) filter (where p.overlap_of_smaller < 0.5) weak_pairs_kept_separate
from raw_duck.vault_unit_pairs_v1 p join raw_duck.vault_units_v1 u on u.unit_id = p.unit_a group by 1;

\echo === takeout units (all), with best proven partner
select u.unit_id, u.src, left(u.unit_root, 70) unit_root, u.members, round(u.bytes / 1e9, 1) gb,
       (select string_agg(p2.other::text || '@' || p2.ov, ', ') from (
          select case when p.unit_a = u.unit_id then p.unit_b else p.unit_a end other, p.overlap_of_smaller ov
          from raw_duck.vault_unit_pairs_v1 p where (p.unit_a = u.unit_id or p.unit_b = u.unit_id) and p.overlap_of_smaller >= 0.9
          order by p.overlap_of_smaller desc limit 4) p2) proven_same_as
from raw_duck.vault_units_v1 u where u.unit_class = 'takeout'
order by u.members desc limit 120;
