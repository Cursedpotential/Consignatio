-- vault_twins_07_group_summary.sql
-- Per-GROUP (not per-pair) reconciliation numbers: the pairwise overlap table
-- inflates totals via combinatorics on large groups (e.g. 101-member Takeout
-- subfolders -> 5,050 pairs), so this computes the union-dedup view instead:
-- for each group, total bytes across all members vs. distinct-content bytes,
-- the difference being what an actual merge-to-one-copy would collapse.
-- Byline: Claude Code · Sonnet 5 · 2026-09-16

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_group_summary (
  group_key      text PRIMARY KEY,
  unit_group     boolean,
  n_members      int,
  total_files    bigint,
  total_bytes    numeric,
  distinct_files bigint,
  distinct_bytes numeric,
  dup_files      bigint,
  dup_bytes      numeric,
  trunk_member   text,
  trunk_bytes    numeric
);
TRUNCATE raw_duck.vault_twins_group_summary;

INSERT INTO raw_duck.vault_twins_group_summary
WITH per_ik AS (
  SELECT group_key, unit_group, ik, size, count(*) AS occurrences
  FROM raw_duck.vault_twins_group_files
  GROUP BY group_key, unit_group, ik, size
),
group_totals AS (
  SELECT group_key, unit_group,
         sum(occurrences) AS total_files,
         sum(occurrences::numeric * size) AS total_bytes,
         count(*) AS distinct_files,
         sum(size) AS distinct_bytes
  FROM per_ik GROUP BY group_key, unit_group
),
member_bytes AS (
  SELECT group_key, member_path, sum(size) AS bytes
  FROM raw_duck.vault_twins_group_files
  GROUP BY group_key, member_path
),
trunk AS (
  SELECT group_key, member_path, bytes,
         row_number() OVER (PARTITION BY group_key ORDER BY bytes DESC, member_path) AS rn
  FROM member_bytes
),
member_counts AS (
  SELECT group_key, count(*) AS n_members FROM member_bytes GROUP BY group_key
)
SELECT gt.group_key, gt.unit_group, mc.n_members, gt.total_files, gt.total_bytes,
       gt.distinct_files, gt.distinct_bytes,
       (gt.total_files - gt.distinct_files) AS dup_files,
       (gt.total_bytes - gt.distinct_bytes) AS dup_bytes,
       tr.member_path AS trunk_member, tr.bytes AS trunk_bytes
FROM group_totals gt
JOIN member_counts mc ON mc.group_key = gt.group_key
JOIN trunk tr ON tr.group_key = gt.group_key AND tr.rn = 1;

CREATE INDEX IF NOT EXISTS vault_twins_group_summary_dup_idx ON raw_duck.vault_twins_group_summary (dup_bytes DESC);

SELECT unit_group,
       count(*) AS groups,
       round(sum(dup_bytes)/1024.0/1024/1024, 2) AS dup_gb,
       round(sum(total_bytes)/1024.0/1024/1024, 2) AS total_gb
FROM raw_duck.vault_twins_group_summary GROUP BY unit_group;

-- top 15 non-unit groups by collapsible (duplicate) bytes
SELECT group_key, n_members, total_files, round(total_bytes/1024.0/1024/1024,2) AS total_gb,
       round(dup_bytes/1024.0/1024/1024,2) AS dup_gb, trunk_member,
       round(trunk_bytes/1024.0/1024/1024,2) AS trunk_gb
FROM raw_duck.vault_twins_group_summary
WHERE NOT unit_group
ORDER BY dup_bytes DESC LIMIT 15;
