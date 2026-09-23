-- Byline: Claude Code · Fable 5 · 2026-09-13
-- Best-copy grading per owner rules (2026-09-13 11:46 + 12:40 EDT):
--   per exact content (md5, size): the occurrence with the OLDEST REAL date wins;
--   sentinel dates (1970-01-01, 1979-12-31, 1980-01-01, anything pre-1990) and
--   batch-stamp cluster dates (same exact timestamp on >100 files = copy event) are NOT real;
--   next tiebreak: most complete metadata; filename quality is the LEAST important;
--   if still tied, KEEP BOTH; zero-filled/zero-byte occurrences are never candidates.
-- DRY RUN by default: ends with ROLLBACK. Run with final line changed to COMMIT
-- (grading_selection.COMMIT.sql) only after the owner has seen the counts.
-- Additive only: creates raw_duck.graded_selection; existing tables untouched.
begin;

-- 1. Batch-stamp clusters: exact timestamps shared by >100 files are copy events, not origin dates.
create temp table batch_stamps as
  select modtime, count(*) as n
  from raw_duck.r2_files
  where modtime is not null and integrity_status is null
  group by modtime
  having count(*) > 100;

select 'batch-stamp cluster timestamps (untrusted)', count(*), sum(n) as files_affected from batch_stamps;

-- 2. Score every eligible occurrence.
create temp table scored as
  select r.bucket, r.path, r.name, r.size, r.md5, r.modtime, r.mimetype,
         -- date trust
         (r.modtime is not null
          and r.modtime >= timestamp '1990-01-01'
          and r.modtime::date not in (date '1970-01-01', date '1979-12-31', date '1980-01-01')
          and not exists (select 1 from batch_stamps b where b.modtime = r.modtime)
         ) as date_trusted,
         -- metadata completeness score (0-3): trusted date, mimetype present, path depth beyond a dump folder
         (case when r.modtime is not null then 1 else 0 end
          + case when coalesce(r.mimetype, '') <> '' then 1 else 0 end
          + case when r.path like '%/%' then 1 else 0 end) as completeness
  from raw_duck.r2_files r
  where r.integrity_status is null and coalesce(r.md5, '') <> '' and r.size > 0;

select 'eligible occurrences scored', count(*),
       'with trusted date', count(*) filter (where date_trusted) from scored;

-- 3. Rank within each content: trusted-oldest date first, completeness second, path stability last.
create temp table ranked as
  select s.*,
         rank() over (partition by md5, size
                      order by (not date_trusted),                       -- trusted dates first
                               case when date_trusted then modtime end,  -- oldest trusted date
                               completeness desc,
                               path) as pick_rank,
         -- a REAL tie: same trust, same date, same completeness as the rank-1 row but a different path
         count(*) over (partition by md5, size, (not date_trusted),
                        case when date_trusted then modtime end, completeness) as peers_at_level
  from scored s;

create temp table selection as
  select bucket, path, name, size, md5, modtime, mimetype, date_trusted, completeness,
         case when pick_rank = 1 and peers_at_level = 1 then 'winner'
              when pick_rank = 1 and peers_at_level > 1 then 'keep_both'
              else 'recorded_loser' end as disposition
  from ranked
  where pick_rank = 1
     or (peers_at_level > 1
         and (md5, size, coalesce(modtime, timestamp '0001-01-01'), completeness) in
             (select md5, size, coalesce(modtime, timestamp '0001-01-01'), completeness
              from ranked where pick_rank = 1));

-- 4. Counts for the owner.
select 'distinct contents graded', count(distinct (md5, size)) from selection;
select 'clear winners', count(*) from selection where disposition = 'winner';
select 'keep-both contents', count(distinct (md5, size)) from selection where disposition = 'keep_both';
select 'keep-both copies carried', count(*) from selection where disposition = 'keep_both';
select 'winners with trusted date', count(*) filter (where date_trusted),
       'winners with NO trusted date on any copy', count(*) filter (where not date_trusted)
  from selection where disposition in ('winner');
select 'selection rows total', count(*) from selection where disposition in ('winner', 'keep_both');
select 'selection bytes GB', round(sum(size) / 1e9, 1) from selection where disposition in ('winner', 'keep_both');

-- 5. Durable output (only reached on COMMIT variant).
create table if not exists raw_duck.graded_selection (
  bucket text, path text, name text, size bigint, md5 text,
  modtime timestamp, mimetype text, date_trusted boolean, completeness int,
  disposition text, rule_version text default 'owner-2026-09-13', graded_at timestamptz default now());
delete from raw_duck.graded_selection where rule_version = 'owner-2026-09-13';
insert into raw_duck.graded_selection
  (bucket, path, name, size, md5, modtime, mimetype, date_trusted, completeness, disposition)
  select bucket, path, name, size, md5, modtime, mimetype, date_trusted, completeness, disposition
  from selection where disposition in ('winner', 'keep_both');
select 'graded_selection rows written', count(*) from raw_duck.graded_selection;

COMMIT;
