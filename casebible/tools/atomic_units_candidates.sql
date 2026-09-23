-- Byline: Claude Code · Fable 5.1 · 2026-09-14
-- Atomic-unit CANDIDATE inventory over what is on B2 (raw_duck.b2_objects). Analysis only: writes two derived
-- catalog tables, moves nothing, decides nothing. Rebuilt on every run.
--
-- Granularity (owner 2026-09-14 07:35): an export root (a Takeout tree, a Facebook/Meta download, a Snapchat
-- export, a Cube ACR folder, a ChatGPT export, a git repo, an Obsidian vault) is the PARENT unit; the unit that
-- gets placed and gets a sidecar is the SERVICE inside it (Takeout/Voice, facebook/messages, Snap/chat_media …).
-- Detection is by path signature only — a candidate, not a proven complete export (Intake/docs/ATOMIC-UNITS.md).
-- Member manifest = sha256 over sorted "relpath<TAB>size<TAB>sha1" lines → byte-identical units share it;
-- content_manifest = same over sorted "size<TAB>sha1" (structure ignored) → content-equal units with different layout.
begin;
drop table if exists raw_duck.atomic_unit_members;
drop table if exists raw_duck.atomic_units;

create temp table k as
select key,
       substr(key, length('consignatio/intake/raw-dedupe/v1/source-buckets/') + 1) as rel,
       size, sha1
from raw_duck.b2_objects;

-- export root per key, first matching signature wins (deepest-specific first)
create temp table roots as
select key, rel, size, sha1,
  case
    when rel ~ '(^|/)takeout-[0-9]{8}T[0-9]{6}Z[^/]*\.(zip|tgz)$' then 'takeout_zip'
    when rel ~ '(^|/)Takeout/'                                    then 'takeout'
    when rel ~* '(^|/)(facebook-[a-z0-9._-]+-[0-9]{4}-[0-9]{2}-[0-9]{2}[^/]*|meta-[0-9]{4}-[A-Za-z]{3}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2})/' then 'facebook'
    when rel ~* '(^|/)(Snap_Export_[0-9-]+|mydata~[0-9]+)/'        then 'snapchat'
    when rel ~* '(^|/)(Cube ACR|All Recordings)/'                 then 'cube_acr'
    when rel ~ '/\.git/'                                          then 'git_repo'
    when rel ~ '/\.obsidian/'                                     then 'obsidian_vault'
  end as unit_type,
  case
    when rel ~ '(^|/)takeout-[0-9]{8}T[0-9]{6}Z[^/]*\.(zip|tgz)$' then rel
    -- greedy ".*" = the DEEPEST export folder is the root (exports were copied inside other exports; "Takeout 5/Takeout/Voice")
    when rel ~ '(^|/)Takeout/'  then regexp_replace(rel, '^(.*(^|/)Takeout( [0-9]+|-[0-9]+)?)/.*$', '\1')
    when rel ~* '(^|/)(facebook-[a-z0-9._-]+-[0-9]{4}-[0-9]{2}-[0-9]{2}[^/]*|meta-[0-9]{4}-[A-Za-z]{3}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2})/'
         then regexp_replace(rel, '^(.*(^|/)(facebook-[a-z0-9._-]+-[0-9]{4}-[0-9]{2}-[0-9]{2}[^/]*|meta-[0-9]{4}-[A-Za-z]{3}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}))/.*$', '\1', 'i')
    when rel ~* '(^|/)(Snap_Export_[0-9-]+|mydata~[0-9]+)/' then regexp_replace(rel, '^(.*(^|/)(Snap_Export_[0-9-]+|mydata~[0-9]+))/.*$', '\1', 'i')
    when rel ~* '(^|/)(Cube ACR|All Recordings)/'           then regexp_replace(rel, '^(.*?(^|/)(Cube ACR|All Recordings))/.*$', '\1', 'i')
    when rel ~ '/\.git/'                                    then regexp_replace(rel, '^(.*?)/\.git/.*$', '\1')
    when rel ~ '/\.obsidian/'                               then regexp_replace(rel, '^(.*?)/\.obsidian/.*$', '\1')
  end as export_root
from k;

-- service = first path segment under the export root (Takeout/Voice, facebook/messages …); zips/repos/vaults are one unit
create temp table svc as
select *,
  case when unit_type in ('takeout_zip') then '(bundle)'
       when unit_type in ('git_repo','obsidian_vault','cube_acr') then '(whole)'
       -- new-format Facebook exports nest the services one level down: your_facebook_activity/messages
       when unit_type = 'facebook' and split_part(substr(rel, length(export_root) + 2), '/', 1) in ('your_facebook_activity','your_activity_across_facebook')
            and nullif(split_part(substr(rel, length(export_root) + 2), '/', 2), '') is not null
         then split_part(substr(rel, length(export_root) + 2), '/', 1) || '/' || split_part(substr(rel, length(export_root) + 2), '/', 2)
       else coalesce(nullif(split_part(substr(rel, length(export_root) + 2), '/', 1), ''), '(root files)') end as service,
  case when rel like 'local/%' or rel like 'gdrive/%' then split_part(rel, '/', 1) || '/' || split_part(rel, '/', 2) else split_part(rel, '/', 1) end as source
from roots where unit_type is not null;

-- the placed unit = export_root + service; files directly in the service root count as members of that service
create table raw_duck.atomic_units as
select row_number() over (order by unit_type, export_root, service) as unit_id,
       unit_type, source, export_root, service,
       case when service in ('(bundle)','(whole)','(root files)') then export_root else export_root || '/' || service end as unit_root,
       count(*) as member_count, sum(size) as total_bytes,
       encode(sha256(convert_to(string_agg(substr(rel, length(export_root) + 2) || E'\t' || size || E'\t' || coalesce(sha1, ''), E'\n' order by rel), 'UTF8')), 'hex') as member_manifest,
       encode(sha256(convert_to(string_agg(size || E'\t' || coalesce(sha1, ''), E'\n' order by size, sha1), 'UTF8')), 'hex') as content_manifest,
       count(*) filter (where sha1 is null) as members_without_sha1
from svc group by unit_type, source, export_root, service;
create index on raw_duck.atomic_units (member_manifest);
create index on raw_duck.atomic_units (content_manifest);

create table raw_duck.atomic_unit_members as
select u.unit_id, s.key from svc s join raw_duck.atomic_units u
  on u.unit_type = s.unit_type and u.source = s.source and u.export_root = s.export_root and u.service = s.service;
create index on raw_duck.atomic_unit_members (unit_id);

-- parent export unit and nesting (a repo inside a Takeout, a Takeout inside a Facebook folder …) by root prefix
alter table raw_duck.atomic_units add column parent_unit_id bigint;
update raw_duck.atomic_units u set parent_unit_id = p.unit_id
from (select unit_id, unit_root, source from raw_duck.atomic_units) p
where p.source = u.source and p.unit_id <> u.unit_id and u.unit_root like p.unit_root || '/%'
  and p.unit_root = (select max(q.unit_root) from raw_duck.atomic_units q where q.source = u.source and q.unit_id <> u.unit_id and u.unit_root like q.unit_root || '/%');

commit;

-- report
select unit_type, count(*) as units, count(distinct member_manifest) as distinct_by_manifest, count(distinct content_manifest) as distinct_by_content,
       sum(member_count) as files, round(sum(total_bytes)/1e9, 1) as gb
from raw_duck.atomic_units group by 1 order by files desc;
select unit_type, service, count(*) as units, sum(member_count) as files, round(sum(total_bytes)/1e9,1) as gb
from raw_duck.atomic_units where unit_type in ('takeout','facebook','snapchat') group by 1,2 order by 1, files desc limit 40;
select 'files_in_units=' || (select count(*) from raw_duck.atomic_unit_members) || ' of ' || (select count(*) from raw_duck.b2_objects)
    || ' | units_with_byte_identical_twin=' || (select count(*) from raw_duck.atomic_units a where exists (select 1 from raw_duck.atomic_units b where b.member_manifest = a.member_manifest and b.unit_id <> a.unit_id))
    || ' | nested_units=' || (select count(*) from raw_duck.atomic_units where parent_unit_id is not null);
