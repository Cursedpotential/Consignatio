-- Byline: Claude Code · Opus 5 · 2026-09-15 07:40 EDT (session propria-79)
-- Vault consolidation — UNITS v2 (read-only analysis, NO B2 writes, NO folding).
-- Input: raw_duck.vault_occ_v1 as built by the deleted session propria-6e (casebible/…/vault_units_v1.sql on the VPS run
-- dir): b2_key-first join, OneDrive Case Bible 317,161 occurrences. Its unit_root/unit_class columns are RECOMPUTED here.
-- Why v2: v1's recognizer descends while the next folder says "takeout", so salem85 Takeout/Takeout became unit
-- "Takeout/Takeout" — owner 07:26: "Google Takeout saved directly to Google. And it needed to stop at takeout."
-- Owner rules (verbatim in Consignatio/docs/URGENT-TODO.md): Takeouts are atomic; stop at Takeout, one more folder only
-- for a username, a service folder is too far; ".obsidian" is a boundary (whole folder); Facebook/Meta export roots are
-- units (2026-09-14 07:35); no folding attempts ("I would rather you not even try", 07:30) — every unit stays separate.
-- raw_duck.vault_unit_pairs_v1 (v1) and raw_duck.export_unit_folds_v1 are folding analyses and must not be used.
\pset pager off
set work_mem = '1GB';
\timing on

create or replace function raw_duck.vault_unit_root_v2(p text) returns text[] language plpgsql immutable as $fn$
declare
  s text[] := string_to_array(p, '/');
  n int := cardinality(s) - 1;            -- folders only; the last segment is the file name
  g int; j int;
  tk constant text := '(?i)take[ _-]?out';
  notk constant text := '(?i)(ingest|extract|-master$|-main$|parser|\.py$)';
  containers constant text := '(?i)^(takeout data[0-9]*|google takeout files|google[_ -]takeout)$';
  svc constant text := '(?i)^(google photos|voice|mail|drive|my activity|maps|maps \(your places\)|keep|chrome|youtube.*|google chat|hangouts|contacts|calendar|location history.*|fit|google fit|google pay|google play.*|blogger|profile|access log activity|home app|saved|tasks|news|shopping|discover|google account|google store|groups|android device configuration service|assignments|classroom|google business profile|timeline|google fi|messages|nest|search contributions|street view|alerts|my maps|purchases & reservations|reminders|stadia)$';
  usr constant text := '(?i)(@|salem|katrina|kinzel|potentiallycursed85)';
begin
  if n < 1 then return null; end if;
  for g in 1..n loop
    if s[g] = '.obsidian' then
      return array[array_to_string(s[1:g], '/'), 'obsidian'];
    end if;
    if s[g] ~* '^(facebook-.+-20[0-9]{2}-|meta-20[0-9]{2}-)' then
      return array[array_to_string(s[1:g], '/'), 'facebook'];
    end if;
    if s[g] ~ tk and s[g] !~ notk then
      j := g;
      loop
        exit when j >= n;
        exit when s[j+1] !~ tk or s[j+1] ~ notk;
        exit when s[j+1] ~* '^takeout$' and s[j] !~ containers;   -- Google's own inner wrapper: stop at the outer folder
        j := j + 1;
      end loop;
      if j < n and s[j+1] !~ svc and s[j+1] ~ usr then j := j + 1; end if;
      return array[array_to_string(s[1:j], '/'), 'takeout'];
    end if;
  end loop;
  return null;
end $fn$;

begin;
update raw_duck.vault_occ_v1 set unit_root = null, unit_class = null where unit_root is not null;
update raw_duck.vault_occ_v1 v set unit_root = r[1], unit_class = r[2]
from (select ctid as id, raw_duck.vault_unit_root_v2(rel) as r from raw_duck.vault_occ_v1) x
where v.ctid = x.id and x.r is not null;

drop table if exists raw_duck.vault_units_v2;
create table raw_duck.vault_units_v2 as
select row_number() over (order by src, unit_root) as unit_id, src, unit_root, unit_class,
       count(*) as members, sum(size) as bytes
from raw_duck.vault_occ_v1 where unit_root is not null
group by src, unit_root, unit_class;
create index on raw_duck.vault_units_v2 (src, unit_root);
commit;

\echo === owner's examples: where each unit now stops
select src, left(rel, 80) rel, unit_root, unit_class from raw_duck.vault_occ_v1
where (src = 'gdrive/salem85' and rel like 'Takeout/Takeout/Voice/Spam/+16262493531%')
   or (src = 'local/D-Backup' and rel = 'google/Takeout/Google Photos/Fuck man/IMG_3199.PNG')
   or (src = 'r2/casebible-sorted' and rel = 'Code/to-review/.obsidian/plugins/folder-navigator/manifest.json')
   or (src = 'gdrive/salemnet' and rel like 'Takeout/Takeout 3/Google Photos/%' and rel like '%.jpg' and md5 < '01');

\echo === guards (all MUST be 0)
select 'unit root ends on a service folder' k, count(*) from raw_duck.vault_units_v2
 where unit_class = 'takeout' and regexp_replace(unit_root, '^.*/', '') ~* '^(google photos|voice|mail|drive|my activity|maps|keep|chrome|google chat|contacts|calendar)$'
union all select 'takeout root with an inner Takeout wrapper kept', count(*) from raw_duck.vault_units_v2
 where unit_class = 'takeout' and unit_root ~* '(^|/)takeout/takeout$'
union all select 'obsidian root not ending in .obsidian', count(*) from raw_duck.vault_units_v2
 where unit_class = 'obsidian' and unit_root !~ '(^|/)\.obsidian$';

\echo === units per class and source
select unit_class, src, count(*) units, sum(members) members, round(sum(bytes) / 1e9, 1) gb
from raw_duck.vault_units_v2 group by 1, 2 order by 1, 4 desc;

\echo === takeout units with a username folder
select src, left(unit_root, 90) unit_root, members from raw_duck.vault_units_v2
where unit_class = 'takeout' and regexp_replace(unit_root, '^.*/', '') ~* '(@|salem|katrina|kinzel|potentiallycursed85)'
order by members desc limit 40;

\echo === all takeout units (largest 80)
select src, left(unit_root, 90) unit_root, members, round(bytes / 1e9, 2) gb
from raw_duck.vault_units_v2 where unit_class = 'takeout' order by members desc limit 80;
