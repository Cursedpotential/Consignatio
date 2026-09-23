-- vault_twins_10_batch1_manifest.sql
-- Per-file copy manifest for merge batch 1 (owner decision 2026-09-16 14:38 EDT,
-- "Batch 1 only"): group 'photos' + every NO_UNIT_OVERLAP group whose pairs are
-- all IDENTICAL (raw_duck.vault_twins_merge_plan.batch = 1).
-- Analysis only: writes raw_duck.vault_twins_copy_manifest_b1. No object is
-- copied, moved or deleted; the driver that consumes this table needs its own GO.
--
-- One row per file in a FOLD member. action:
--   RECORD   content key already exists anywhere in the trunk -> catalog occurrence
--            row only, no bytes move (dst_key = the trunk file holding that content)
--   COPY     content not in trunk and trunk has nothing at the same relative path
--            -> server-side copy to dst_key = trunk/<rel>
--   CONFLICT content not in trunk but trunk already has a DIFFERENT file at the
--            same relative path -> needs a rename rule before it can be copied
-- Byline: Claude Code · Fable 5.1 · 2026-09-16

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_copy_manifest_b1 (
  group_key    text NOT NULL,
  member_path  text NOT NULL,
  src_key      text NOT NULL,
  rel          text NOT NULL,
  size         bigint,
  ik           text,
  trunk_member text NOT NULL,
  action       text NOT NULL,
  dst_key      text,
  PRIMARY KEY (group_key, src_key)
);
TRUNCATE raw_duck.vault_twins_copy_manifest_b1;

DROP TABLE IF EXISTS b1_groups;
CREATE TEMP TABLE b1_groups AS
SELECT group_key, trunk_member FROM raw_duck.vault_twins_merge_plan_groups WHERE batch = 1;
CREATE INDEX ON b1_groups (group_key);
ANALYZE b1_groups;

-- trunk files: by content key (first key wins) and by relative path
DROP TABLE IF EXISTS b1_trunk_by_ik;
CREATE TEMP TABLE b1_trunk_by_ik AS
SELECT gf.group_key, gf.ik, min(gf.member_path || '/' || gf.rel) AS trunk_key
FROM raw_duck.vault_twins_group_files gf
JOIN b1_groups g ON g.group_key = gf.group_key AND g.trunk_member = gf.member_path
GROUP BY gf.group_key, gf.ik;
CREATE INDEX ON b1_trunk_by_ik (group_key, ik);
ANALYZE b1_trunk_by_ik;

DROP TABLE IF EXISTS b1_trunk_by_rel;
CREATE TEMP TABLE b1_trunk_by_rel AS
SELECT gf.group_key, gf.rel, min(gf.ik) AS ik
FROM raw_duck.vault_twins_group_files gf
JOIN b1_groups g ON g.group_key = gf.group_key AND g.trunk_member = gf.member_path
GROUP BY gf.group_key, gf.rel;
CREATE INDEX ON b1_trunk_by_rel (group_key, rel);
ANALYZE b1_trunk_by_rel;

INSERT INTO raw_duck.vault_twins_copy_manifest_b1
SELECT gf.group_key, gf.member_path,
       gf.member_path || '/' || gf.rel AS src_key,
       gf.rel, gf.size, gf.ik, g.trunk_member,
       CASE WHEN tk.ik IS NOT NULL THEN 'RECORD'
            WHEN tr.rel IS NOT NULL THEN 'CONFLICT'
            ELSE 'COPY' END AS action,
       CASE WHEN tk.ik IS NOT NULL THEN tk.trunk_key
            WHEN tr.rel IS NOT NULL THEN NULL
            ELSE g.trunk_member || '/' || gf.rel END AS dst_key
FROM raw_duck.vault_twins_group_files gf
JOIN b1_groups g ON g.group_key = gf.group_key AND g.trunk_member <> gf.member_path
LEFT JOIN b1_trunk_by_ik  tk ON tk.group_key = gf.group_key AND tk.ik = gf.ik
LEFT JOIN b1_trunk_by_rel tr ON tr.group_key = gf.group_key AND tr.rel = gf.rel
ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS vault_twins_copy_manifest_b1_action_idx ON raw_duck.vault_twins_copy_manifest_b1 (action);

-- rollup
SELECT action, count(*) AS files, round(sum(size)/1024.0/1024/1024, 2) AS gb
FROM raw_duck.vault_twins_copy_manifest_b1 GROUP BY action ORDER BY action;

-- per group, top 20 by carry bytes
SELECT group_key, trunk_member,
       count(*) FILTER (WHERE action = 'RECORD')   AS record_files,
       count(*) FILTER (WHERE action = 'COPY')     AS copy_files,
       round(sum(size) FILTER (WHERE action = 'COPY')/1024.0/1024/1024, 2) AS copy_gb,
       count(*) FILTER (WHERE action = 'CONFLICT') AS conflict_files
FROM raw_duck.vault_twins_copy_manifest_b1
GROUP BY group_key, trunk_member ORDER BY copy_gb DESC NULLS LAST LIMIT 20;

-- destination collisions inside the manifest itself (two fold members carrying
-- different content to the same trunk path) - must be 0 or resolved by rule
SELECT count(*) AS dst_collisions FROM (
  SELECT dst_key FROM raw_duck.vault_twins_copy_manifest_b1
  WHERE action = 'COPY' GROUP BY dst_key HAVING count(DISTINCT ik) > 1
) x;
