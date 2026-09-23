-- vault_twins_06_rehome.sql
-- Owner order 2026-09-16 07:49: every vault/v1 path under a quarantine/hold/
-- delete-class folder needs a re-home classification against the rest of the
-- vault (content match, path/name match, or orphan). Read-only analysis:
-- writes only to raw_duck.vault_twins_quarantine_roots / vault_twins_rehome.
-- Byline: Claude Code · Sonnet 5 · 2026-09-16

-- 0) one-time helper columns on vault_objects (basename, quarantine flag)
ALTER TABLE raw_duck.vault_objects ADD COLUMN IF NOT EXISTS basename text;
UPDATE raw_duck.vault_objects SET basename = regexp_replace(key, '^.*/', '') WHERE basename IS NULL;
CREATE INDEX IF NOT EXISTS vault_objects_basename_idx ON raw_duck.vault_objects (basename);

-- 1) Quarantine/hold/delete-class roots (depth-1, plus the one known depth-2
-- exception Triage/_recovered). Wildcard names resolved against the actual
-- depth-1 directory list so we don't guess exact spellings/casing.
CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_quarantine_roots (dir_path text PRIMARY KEY);
TRUNCATE raw_duck.vault_twins_quarantine_roots;

INSERT INTO raw_duck.vault_twins_quarantine_roots (dir_path)
SELECT dir_path FROM raw_duck.vault_twins_dirs
WHERE depth = 1 AND (
  dir_path ILIKE '.review_hold'
  OR dir_path ILIKE '_REVIEW_HOLD'
  OR dir_path ILIKE '_SWEPT'
  OR dir_path ILIKE '_TO_BE_DELETED%'
  OR dir_path ILIKE '_DUPLICATES'
  OR dir_path ILIKE '_dedup%'
  OR dir_path ILIKE '_Quarantine%'
  OR dir_path ILIKE '.trash'
  OR dir_path ILIKE 'Recently Deleted'
  OR dir_path ILIKE 'flagged-junk'
  OR dir_path ILIKE '_sync-conflicts'
  OR dir_path ILIKE 'NOT FUCKING TRSASH'
)
ON CONFLICT DO NOTHING;

INSERT INTO raw_duck.vault_twins_quarantine_roots (dir_path)
SELECT 'Triage/_recovered' WHERE EXISTS (
  SELECT 1 FROM raw_duck.vault_twins_dirs WHERE depth = 2 AND dir_path = 'Triage/_recovered'
)
ON CONFLICT DO NOTHING;

-- sanity check against the owner's 52 GB / 42k files estimate (roots are not nested in each other, safe to sum)
SELECT count(*) AS root_count,
       sum(d.file_count) AS files,
       round(sum(d.total_bytes) / 1024.0 / 1024 / 1024, 1) AS gb
FROM raw_duck.vault_twins_quarantine_roots r
JOIN raw_duck.vault_twins_dirs d
  ON d.dir_path = r.dir_path
 AND d.depth = (length(r.dir_path) - length(replace(r.dir_path, '/', '')) + 1);

-- 2) mark quarantine membership on vault_objects
ALTER TABLE raw_duck.vault_objects ADD COLUMN IF NOT EXISTS in_quarantine boolean;
UPDATE raw_duck.vault_objects SET in_quarantine = false WHERE in_quarantine IS NULL;
UPDATE raw_duck.vault_objects vo
SET in_quarantine = true
FROM raw_duck.vault_twins_quarantine_roots r
WHERE vo.key LIKE r.dir_path || '/%' AND vo.in_quarantine = false;
CREATE INDEX IF NOT EXISTS vault_objects_quarantine_idx ON raw_duck.vault_objects (in_quarantine);

SELECT count(*) AS quarantine_files, round(sum(size)/1024.0/1024/1024,1) AS quarantine_gb
FROM raw_duck.vault_objects WHERE in_quarantine;

-- 3) re-home classification
CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_rehome (
  key          text PRIMARY KEY,
  root         text,
  size         bigint,
  class        text,
  example_home text
);
TRUNCATE raw_duck.vault_twins_rehome;

INSERT INTO raw_duck.vault_twins_rehome (key, root, size, class, example_home)
WITH qfiles AS (
  SELECT vo.key, vo.size, vo.sha1, vo.md5, vo.basename,
         (SELECT r.dir_path FROM raw_duck.vault_twins_quarantine_roots r
          WHERE vo.key LIKE r.dir_path || '/%' ORDER BY length(r.dir_path) DESC LIMIT 1) AS root
  FROM raw_duck.vault_objects vo
  WHERE vo.in_quarantine
),
hash_home AS (
  SELECT q.key, min(o.key) AS home_key
  FROM qfiles q
  JOIN raw_duck.vault_objects o
    ON o.in_quarantine = false
   AND ((q.sha1 IS NOT NULL AND o.sha1 = q.sha1) OR (q.md5 IS NOT NULL AND o.md5 = q.md5))
  GROUP BY q.key
),
name_home AS (
  SELECT q.key, min(o.key) AS home_key
  FROM qfiles q
  JOIN raw_duck.vault_objects o
    ON o.in_quarantine = false AND o.basename = q.basename
  WHERE q.key NOT IN (SELECT key FROM hash_home)
  GROUP BY q.key
)
SELECT q.key, q.root, q.size,
       CASE WHEN hh.home_key IS NOT NULL THEN 'HAS-HOME-IN-VAULT'
            WHEN nh.home_key IS NOT NULL THEN 'PATH-TWIN-ONLY'
            ELSE 'ORPHAN' END AS class,
       coalesce(hh.home_key, nh.home_key) AS example_home
FROM qfiles q
LEFT JOIN hash_home hh ON hh.key = q.key
LEFT JOIN name_home nh ON nh.key = q.key;

CREATE INDEX IF NOT EXISTS vault_twins_rehome_class_idx ON raw_duck.vault_twins_rehome (class);
CREATE INDEX IF NOT EXISTS vault_twins_rehome_root_idx ON raw_duck.vault_twins_rehome (root);

SELECT root, class, count(*) AS files, round(sum(size)/1024.0/1024/1024,2) AS gb
FROM raw_duck.vault_twins_rehome
GROUP BY root, class ORDER BY root, class;

SELECT class, count(*) AS files, round(sum(size)/1024.0/1024/1024,2) AS gb
FROM raw_duck.vault_twins_rehome
GROUP BY class ORDER BY class;
