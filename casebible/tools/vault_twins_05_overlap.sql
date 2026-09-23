-- vault_twins_05_overlap.sql
-- Pairwise content overlap between members of each name-normalized candidate
-- group (raw_duck.vault_twins_groups), using the per-directory file listing
-- already expanded in raw_duck.vault_twins_dir_files.
--
-- Identity rule for "the same file" across two directories (per brief):
--   same content hash (sha1, else md5) regardless of relative path, ELSE
--   (no hash on either side) same relative path + size.
-- Classification per pair:
--   IDENTICAL  - no files unique to either side (full match)
--   SUBSET     - one side has zero unique files, the other has some (contained)
--   PARTIAL    - both sides have unique files AND some content is shared
--   DISJOINT   - no shared content at all (same/similar name, different stuff)
-- Nested member paths (one member is an ancestor dir of another in the same
-- group) are dropped from comparison, never compared, per brief 3c.
-- Byline: Claude Code · Sonnet 5 · 2026-09-16; nested test hardened by Claude Code · Fable 5.1 · 2026-09-16

-- 1) Per-(group,member) file list with an identity key.
CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_group_files (
  group_key   text NOT NULL,
  unit_group  boolean NOT NULL,
  member_path text NOT NULL,
  depth       int NOT NULL,
  rel         text NOT NULL,
  size        bigint,
  ik          text NOT NULL
);
TRUNCATE raw_duck.vault_twins_group_files;

INSERT INTO raw_duck.vault_twins_group_files (group_key, unit_group, member_path, depth, rel, size, ik)
SELECT DISTINCT g.group_key, g.unit_group, g.member_path, g.member_depth, f.rel, f.size,
       CASE WHEN f.sha1 IS NOT NULL THEN 'H:' || f.sha1
            WHEN f.md5  IS NOT NULL THEN 'H:' || f.md5
            ELSE 'P:' || f.rel || ':' || f.size::text END AS ik
FROM raw_duck.vault_twins_groups g
JOIN raw_duck.vault_twins_dir_files f
  ON f.depth = g.member_depth AND f.dir_path = g.member_path;

CREATE INDEX IF NOT EXISTS vault_twins_group_files_lookup_idx
  ON raw_duck.vault_twins_group_files (group_key, member_path, ik);

-- 2) Valid (non-nested) member pairs per group.
CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_pairs (
  group_key  text NOT NULL,
  unit_group boolean NOT NULL,
  depth      int NOT NULL,
  path_a     text NOT NULL,
  path_b     text NOT NULL,
  dropped_nested boolean NOT NULL DEFAULT false
);
TRUNCATE raw_duck.vault_twins_pairs;

INSERT INTO raw_duck.vault_twins_pairs (group_key, unit_group, depth, path_a, path_b, dropped_nested)
SELECT a.group_key, a.unit_group, a.member_depth, a.member_path, b.member_path,
       -- starts_with, not LIKE: 962 member paths contain '_' (a LIKE wildcard), which could
       -- over-flag a sibling such as a_b vs a-b/... and drop a valid pair (fixed 2026-09-16, Fable 5.1).
       (starts_with(b.member_path, a.member_path || '/') OR starts_with(a.member_path, b.member_path || '/'))
FROM raw_duck.vault_twins_groups a
JOIN raw_duck.vault_twins_groups b
  ON a.group_key = b.group_key AND a.member_path < b.member_path;

CREATE INDEX IF NOT EXISTS vault_twins_pairs_group_idx ON raw_duck.vault_twins_pairs (group_key);

-- 3) Overlap per valid (non-nested) pair.
CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_overlap (
  group_key      text NOT NULL,
  unit_group     boolean NOT NULL,
  depth          int NOT NULL,
  path_a         text NOT NULL,
  path_b         text NOT NULL,
  a_files        bigint,
  a_bytes        numeric,
  b_files        bigint,
  b_bytes        numeric,
  common_files   bigint,
  common_bytes   numeric,
  only_a_files   bigint,
  only_a_bytes   numeric,
  only_b_files   bigint,
  only_b_bytes   numeric,
  path_conflict_files bigint,
  overlap_pct    numeric,
  class          text
);
TRUNCATE raw_duck.vault_twins_overlap;

INSERT INTO raw_duck.vault_twins_overlap
WITH pairs AS (
  SELECT * FROM raw_duck.vault_twins_pairs WHERE NOT dropped_nested
),
fa AS (
  SELECT p.group_key, p.path_a, p.path_b, gf.ik, gf.size, gf.rel
  FROM pairs p
  JOIN raw_duck.vault_twins_group_files gf ON gf.group_key = p.group_key AND gf.member_path = p.path_a
),
fb AS (
  SELECT p.group_key, p.path_a, p.path_b, gf.ik, gf.size, gf.rel
  FROM pairs p
  JOIN raw_duck.vault_twins_group_files gf ON gf.group_key = p.group_key AND gf.member_path = p.path_b
),
matched AS (
  SELECT fa.group_key, fa.path_a, fa.path_b,
         count(*) AS common_files, coalesce(sum(fa.size), 0) AS common_bytes
  FROM fa JOIN fb
    ON fa.group_key = fb.group_key AND fa.path_a = fb.path_a AND fa.path_b = fb.path_b AND fa.ik = fb.ik
  GROUP BY 1, 2, 3
),
only_a AS (
  SELECT fa.group_key, fa.path_a, fa.path_b,
         count(*) AS only_a_files, coalesce(sum(fa.size), 0) AS only_a_bytes
  FROM fa LEFT JOIN fb
    ON fa.group_key = fb.group_key AND fa.path_a = fb.path_a AND fa.path_b = fb.path_b AND fa.ik = fb.ik
  WHERE fb.ik IS NULL
  GROUP BY 1, 2, 3
),
only_b AS (
  SELECT fb.group_key, fb.path_a, fb.path_b,
         count(*) AS only_b_files, coalesce(sum(fb.size), 0) AS only_b_bytes
  FROM fb LEFT JOIN fa
    ON fa.group_key = fb.group_key AND fa.path_a = fb.path_a AND fa.path_b = fb.path_b AND fa.ik = fb.ik
  WHERE fa.ik IS NULL
  GROUP BY 1, 2, 3
),
path_conflict AS (
  -- same relative path present on both sides but different identity key (content differs)
  SELECT fa.group_key, fa.path_a, fa.path_b, count(*) AS path_conflict_files
  FROM fa JOIN fb
    ON fa.group_key = fb.group_key AND fa.path_a = fb.path_a AND fa.path_b = fb.path_b
   AND fa.rel = fb.rel AND fa.ik <> fb.ik
  GROUP BY 1, 2, 3
),
totals AS (
  SELECT p.group_key, p.unit_group, p.depth, p.path_a, p.path_b,
         da.file_count AS a_files, da.total_bytes AS a_bytes,
         db.file_count AS b_files, db.total_bytes AS b_bytes
  FROM pairs p
  JOIN raw_duck.vault_twins_dirs da ON da.depth = p.depth AND da.dir_path = p.path_a
  JOIN raw_duck.vault_twins_dirs db ON db.depth = p.depth AND db.dir_path = p.path_b
)
SELECT t.group_key, t.unit_group, t.depth, t.path_a, t.path_b,
       t.a_files, t.a_bytes, t.b_files, t.b_bytes,
       coalesce(m.common_files, 0), coalesce(m.common_bytes, 0),
       coalesce(oa.only_a_files, 0), coalesce(oa.only_a_bytes, 0),
       coalesce(ob.only_b_files, 0), coalesce(ob.only_b_bytes, 0),
       coalesce(pc.path_conflict_files, 0),
       CASE WHEN least(t.a_bytes, t.b_bytes) > 0
            THEN round(100.0 * coalesce(m.common_bytes, 0) / least(t.a_bytes, t.b_bytes), 1)
            ELSE 0 END AS overlap_pct,
       CASE
         WHEN coalesce(m.common_files, 0) = 0 THEN 'DISJOINT'
         WHEN coalesce(oa.only_a_files, 0) = 0 AND coalesce(ob.only_b_files, 0) = 0 THEN 'IDENTICAL'
         WHEN coalesce(oa.only_a_files, 0) = 0 OR coalesce(ob.only_b_files, 0) = 0 THEN 'SUBSET'
         ELSE 'PARTIAL'
       END AS class
FROM totals t
LEFT JOIN matched m ON m.group_key = t.group_key AND m.path_a = t.path_a AND m.path_b = t.path_b
LEFT JOIN only_a oa ON oa.group_key = t.group_key AND oa.path_a = t.path_a AND oa.path_b = t.path_b
LEFT JOIN only_b ob ON ob.group_key = t.group_key AND ob.path_a = t.path_a AND ob.path_b = t.path_b
LEFT JOIN path_conflict pc ON pc.group_key = t.group_key AND pc.path_a = t.path_a AND pc.path_b = t.path_b;

CREATE INDEX IF NOT EXISTS vault_twins_overlap_class_idx ON raw_duck.vault_twins_overlap (class);
CREATE INDEX IF NOT EXISTS vault_twins_overlap_group_idx ON raw_duck.vault_twins_overlap (group_key);

SELECT unit_group, class, count(*) AS pairs,
       round(sum(common_bytes)/1024.0/1024/1024, 2) AS common_gb,
       round(sum(only_a_bytes + only_b_bytes)/1024.0/1024/1024, 2) AS unique_gb
FROM raw_duck.vault_twins_overlap
GROUP BY unit_group, class ORDER BY unit_group, class;

SELECT count(*) FROM raw_duck.vault_twins_pairs WHERE dropped_nested;
