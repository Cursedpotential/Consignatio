-- Byline: Claude Code · Opus 5 · 2026-09-15 07:30 EDT
-- Vault consolidation — EXPORT UNITS v1 (Takeout boundary), analysis tables only. NO B2 writes.
-- Owner rules 2026-09-15 07:22–07:26 EDT (verbatim in Consignatio/docs/URGENT-TODO.md):
--   "Take outs. Are fucking atomic. Stop when it says take out." · "You can go as far as a username. If there's no
--   username, then stop at takeout. Service name. You've gone too far." · deeper files only as evidence that two exports
--   belong together; "if you can't do that, then just leave it as it is" · salem85 "Google Takeout saved directly to
--   Google. And it needed to stop at takeout." (salem85 Takeout/Takeout → unit = the outer Takeout).
-- Replaces raw_duck.atomic_units for Takeouts (that table cuts at the SERVICE level and saw only the sparse B2 key tree).
--
-- 1. raw_duck.vault_occ_v1 : every live occurrence. Fix over vault_occ_v0: source rows join b2_content by b2_key first,
--    (md5,size) second — v0 used (md5,size) only and dropped the proxy-matched OneDrive Case Bible rows (md5 null).
-- 2. raw_duck.takeout_unit_root(dir) : boundary recognizer
--    - a takeout-named segment starts a unit (code repos like *-master, *Ingestor, *Extractor excluded)
--    - while the next segment is also takeout-named, descend (containers: "Takeout Data", "Google takeout files",
--      salemnet "Takeout" holding "Takeout 3" …) — EXCEPT a child named exactly "Takeout" under a non-container folder,
--      which is Google's own wrapper: stop at the outer folder
--    - then include ONE following segment only if it is a username (@, salem, katrina, kinzel) and not a service name
-- 3. raw_duck.export_units_v1 / export_unit_members_v1 : units with member counts and a content manifest.
-- 4. raw_duck.export_unit_folds_v1 : units with IDENTICAL content sets (proof → fold). Near-matches are only reported.
\pset pager off
set work_mem = '1GB';
\timing on

create or replace function raw_duck.takeout_unit_root(d text) returns text language plpgsql immutable as $fn$
declare
  s text[] := string_to_array(d, '/');
  n int := coalesce(cardinality(s), 0);
  i int; j int;
  tk constant text := '(?i)take[ _-]?out';
  notk constant text := '(?i)(ingest|extract|-master$|-main$|parser|\.py$)';
  containers constant text := '(?i)^(takeout data[0-9]*|google takeout files|google[_ -]takeout)$';
  svc constant text := '(?i)^(google photos|voice|mail|drive|my activity|maps|maps \(your places\)|keep|chrome|youtube.*|google chat|hangouts|contacts|calendar|location history.*|fit|google fit|google pay|google play.*|blogger|profile|access log activity|home app|saved|tasks|news|shopping|discover|google account|google store|groups|android device configuration service|assignments|classroom|google business profile|timeline|google fi|messages|nest|search contributions|street view|alerts|my maps|purchases & reservations|reminders|stadia|archive_browser\.html)$';
  usr constant text := '(?i)(@|salem|katrina|kinzel)';
begin
  for i in 1..n loop
    if s[i] ~ tk and s[i] !~ notk then
      j := i;
      loop
        exit when j >= n;
        exit when s[j+1] !~ tk or s[j+1] ~ notk;
        exit when s[j+1] ~* '^takeout$' and s[j] !~ containers;   -- Google's inner wrapper → stop at the outer folder
        j := j + 1;
      end loop;
      if j < n and s[j+1] !~ svc and s[j+1] ~ usr then j := j + 1; end if;
      return array_to_string(s[1:j], '/');
    end if;
  end loop;
  return null;
end $fn$;

begin;
drop table if exists raw_duck.vault_occ_v1;
create table raw_duck.vault_occ_v1 as
select coalesce(k.md5, m.md5) as md5, coalesce(k.size, m.size) as size, coalesce(k.b2_key, m.b2_key) as canonical_key,
       s.source || case when s.scope <> '' then '/' || s.scope else '' end as src, s.path as rel
from raw_duck.source_occurrences s
left join raw_duck.b2_content k on k.b2_key = s.b2_key
left join raw_duck.b2_content m on k.b2_key is null and m.md5 = s.md5 and m.size = s.size
where s.disposition in ('content_on_b2', 'copied', 'exported') and coalesce(k.b2_key, m.b2_key) is not null
union all
select c.md5, c.size, c.b2_key, 'r2/' || split_part(o.key, '/', 6),
       regexp_replace(o.key, '^consignatio/intake/raw-dedupe/v1/source-buckets/[^/]+/', '')
from raw_duck.b2_objects o
join raw_duck.b2_content c on c.b2_key = o.key
where o.key like 'consignatio/intake/raw-dedupe/v1/source-buckets/casebible-%';
create index on raw_duck.vault_occ_v1 (src);
create index on raw_duck.vault_occ_v1 (md5, size);

create temp table dirs as
select distinct src, regexp_replace(rel, '/[^/]*$', '') as dir from raw_duck.vault_occ_v1 where rel like '%/%';
create temp table dir_unit as
select src, dir, raw_duck.takeout_unit_root(dir) as unit_root from dirs where dir ~* 'take[ _-]?out';

drop table if exists raw_duck.export_unit_members_v1;
create table raw_duck.export_unit_members_v1 as
select o.src, u.unit_root, o.rel, o.md5, o.size
from raw_duck.vault_occ_v1 o
join dir_unit u on u.src = o.src and u.dir = regexp_replace(o.rel, '/[^/]*$', '')
where u.unit_root is not null;
create index on raw_duck.export_unit_members_v1 (src, unit_root);

drop table if exists raw_duck.export_units_v1;
create table raw_duck.export_units_v1 as
select src, unit_root, sum(n) as members, count(*) as contents, sum(size) as bytes,
       encode(sha256(convert_to(string_agg(md5 || ':' || size, ',' order by md5, size), 'UTF8')), 'hex') as content_manifest
from (select src, unit_root, md5, size, count(*) n from raw_duck.export_unit_members_v1 group by 1, 2, 3, 4) d
group by 1, 2;

drop table if exists raw_duck.export_unit_folds_v1;
create table raw_duck.export_unit_folds_v1 as
select content_manifest, count(*) as units, min(contents) as contents, min(bytes) as bytes,
       array_agg(src || ':' || unit_root order by length(unit_root), src) as members
from raw_duck.export_units_v1 group by 1 having count(*) > 1;
commit;

\echo === universe v1 vs v0 per source (v0 dropped proxy-matched rows)
select coalesce(a.src, b.src) src, a.n v1, b.n v0
from (select src, count(*) n from raw_duck.vault_occ_v1 group by 1) a
full join (select src, count(*) n from raw_duck.vault_occ_v0 group by 1) b using (src) order by 2 desc nulls last;

\echo === the owner's two failing examples: where the unit now stops
select src, rel, raw_duck.takeout_unit_root(regexp_replace(rel, '/[^/]*$', '')) unit_root
from raw_duck.vault_occ_v1
where (src = 'local/D-Backup' and rel = 'google/Takeout/Google Photos/Fuck man/IMG_3199.PNG')
   or (src = 'gdrive/salem85' and rel = 'Takeout/Takeout/Voice/Spam/+16262493531 - Voicemail - 2024-02-08T16_41_25Z.mp3')
   or (rel like 'Google takeout files/Takeout 13/Voice/Spam/+16262493531%');

\echo === units per source
select src, count(*) units, sum(members) member_occ, round(sum(bytes) / 1e9, 1) gb from raw_duck.export_units_v1 group by 1 order by 3 desc;

\echo === all units (largest 60)
select left(src, 22) src, left(unit_root, 80) unit_root, members, contents, round(bytes / 1e9, 2) gb
from raw_duck.export_units_v1 order by members desc limit 60;

\echo === units that include a username segment
select left(src, 22) src, left(unit_root, 90) unit_root, members from raw_duck.export_units_v1
where split_part(unit_root, '/', cardinality(string_to_array(unit_root, '/'))) ~* '(@|salem|katrina|kinzel)' order by members desc limit 30;

\echo === PROOF folds: identical content sets (these become one unit)
select units, contents, round(bytes / 1e9, 2) gb, left(array_to_string(members, '  |  '), 240) members
from raw_duck.export_unit_folds_v1 order by contents desc limit 40;

\echo === near-matches for the owner (not folded): smaller unit >= 95% contained in a larger one
create temp table uc as select distinct src, unit_root, md5, size from raw_duck.export_unit_members_v1;
create index on uc (md5, size);
select left(a.src || ':' || a.unit_root, 90) smaller, left(b.src || ':' || b.unit_root, 90) larger, x.shared, ua.contents smaller_contents, ub.contents larger_contents
from (select a.src asrc, a.unit_root aroot, b.src bsrc, b.unit_root broot, count(*) shared
      from uc a join uc b on b.md5 = a.md5 and b.size = a.size and (b.src, b.unit_root) <> (a.src, a.unit_root)
      group by 1, 2, 3, 4) x
join raw_duck.export_units_v1 ua on ua.src = x.asrc and ua.unit_root = x.aroot
join raw_duck.export_units_v1 ub on ub.src = x.bsrc and ub.unit_root = x.broot
cross join lateral (select x.asrc src, x.aroot unit_root) a
cross join lateral (select x.bsrc src, x.broot unit_root) b
where ua.contents <= ub.contents and ua.content_manifest <> ub.content_manifest and x.shared >= 0.95 * ua.contents and ua.contents >= 10
order by x.shared desc limit 40;
