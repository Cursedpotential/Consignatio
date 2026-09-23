-- vault_twins_09_merge_plan.sql
-- Merge PROPOSAL for name-twin groups that touch no atomic unit
-- (raw_duck.vault_twins_unit_safety.safety_class = 'NO_UNIT_OVERLAP').
-- Analysis only: writes raw_duck.vault_twins_merge_plan (per member) and
-- raw_duck.vault_twins_merge_plan_groups (per group). Nothing is copied,
-- moved or deleted; materialization is a separate owner GO.
--
-- Shape of a merge: the group's trunk (largest member by bytes, from
-- vault_twins_group_summary) is kept in place; every other member is FOLDED:
--   dup_in_trunk_*  = member files whose content key already exists in the trunk
--                     (collapse: record the occurrence, no bytes to move)
--   carry_*         = member files not present in the trunk
--                     (would be copied into the trunk path, then the member retired)
-- Scope (owner rules 2026-09-16 15:25-15:33): only groups whose EVERY member is a top-level
-- container; Takeout / Facebook / Snapchat containers and any directory attached to a doc that
-- references it are units and never enter; service folders inside exports are never processed.
-- batch 1 = group 'photos' (Photos + images + Google Photos + Pictures + Images), folded as
--           Photos/<relative path> so camera-model / date / origin containers inside members survive.
-- batch 2 = every other top-level-only safe group, listed as candidates.
-- Byline: Claude Code · Fable 5.1 · 2026-09-16

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_merge_plan (
  group_key          text NOT NULL,
  member_path        text NOT NULL,
  role               text NOT NULL,          -- TRUNK | FOLD
  member_files       bigint,
  member_bytes       numeric,
  dup_in_trunk_files bigint,
  dup_in_trunk_bytes numeric,
  carry_files        bigint,
  carry_bytes        numeric,
  batch              int,
  PRIMARY KEY (group_key, member_path)
);
TRUNCATE raw_duck.vault_twins_merge_plan;

-- Temp tables instead of CTEs: with CTEs the planner estimated ~1k trunk keys
-- (there are >100k in 'photos' alone) and merge-joined on group_key only,
-- filtering ik row by row -> billions of comparisons, cancelled after 8 min.
DROP TABLE IF EXISTS mp_safe;
CREATE TEMP TABLE mp_safe AS
SELECT gs.group_key, gs.trunk_member,
       -- batch 1 = the photo home only (owner 15:33: "top level images and photos and pics and
       -- pictures are fair game to merge"); every other top-level-only safe group is batch 2, a candidate
       CASE WHEN gs.group_key = 'photos' THEN 1 ELSE 2 END AS batch
FROM raw_duck.vault_twins_group_summary gs
JOIN raw_duck.vault_twins_unit_safety s USING (group_key)
WHERE s.safety_class = 'NO_UNIT_OVERLAP'
  -- owner 2026-09-16 15:30: "dedicated top level only; once it dips into a subfolder you went too far"
  AND NOT EXISTS (SELECT 1 FROM raw_duck.vault_twins_groups m WHERE m.group_key = gs.group_key AND m.member_depth <> 1)
  -- owner 15:33: "any photos dir attached to a doc that references them is a unit" - a member with a
  -- sibling <name>.html/.htm/.md/.pdf at the vault root, or named *_files, keeps its export
  AND NOT EXISTS (
    SELECT 1 FROM raw_duck.vault_twins_groups m
    WHERE m.group_key = gs.group_key AND (
      m.member_path ILIKE '%\_files' OR m.member_path ILIKE '%\_fichiers'
      OR EXISTS (SELECT 1 FROM raw_duck.vault_objects o
                 WHERE position('/' in o.key) = 0
                   AND lower(o.key) IN (lower(m.member_path)||'.html', lower(m.member_path)||'.htm',
                                        lower(m.member_path)||'.md',   lower(m.member_path)||'.pdf'))));
CREATE INDEX ON mp_safe (group_key);
ANALYZE mp_safe;

DROP TABLE IF EXISTS mp_trunk_keys;
CREATE TEMP TABLE mp_trunk_keys AS
SELECT DISTINCT gf.group_key, gf.ik
FROM raw_duck.vault_twins_group_files gf
JOIN mp_safe s ON s.group_key = gf.group_key AND s.trunk_member = gf.member_path;
CREATE INDEX ON mp_trunk_keys (group_key, ik);
ANALYZE mp_trunk_keys;

INSERT INTO raw_duck.vault_twins_merge_plan
SELECT gf.group_key, gf.member_path,
       CASE WHEN gf.member_path = s.trunk_member THEN 'TRUNK' ELSE 'FOLD' END AS role,
       count(*) AS member_files,
       sum(gf.size) AS member_bytes,
       count(*) FILTER (WHERE tk.ik IS NOT NULL AND gf.member_path <> s.trunk_member) AS dup_in_trunk_files,
       coalesce(sum(gf.size) FILTER (WHERE tk.ik IS NOT NULL AND gf.member_path <> s.trunk_member), 0) AS dup_in_trunk_bytes,
       count(*) FILTER (WHERE tk.ik IS NULL) AS carry_files,
       coalesce(sum(gf.size) FILTER (WHERE tk.ik IS NULL), 0) AS carry_bytes,
       s.batch
FROM raw_duck.vault_twins_group_files gf
JOIN mp_safe s ON s.group_key = gf.group_key
LEFT JOIN mp_trunk_keys tk ON tk.group_key = gf.group_key AND tk.ik = gf.ik
GROUP BY gf.group_key, gf.member_path, s.trunk_member, s.batch;

CREATE INDEX IF NOT EXISTS vault_twins_merge_plan_batch_idx ON raw_duck.vault_twins_merge_plan (batch, group_key);

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_merge_plan_groups (
  group_key     text PRIMARY KEY,
  batch         int,
  trunk_member  text,
  n_fold        int,
  fold_members  text,
  trunk_files   bigint,
  trunk_bytes   numeric,
  dup_files     bigint,
  dup_bytes     numeric,
  carry_files   bigint,
  carry_bytes   numeric
);
TRUNCATE raw_duck.vault_twins_merge_plan_groups;

INSERT INTO raw_duck.vault_twins_merge_plan_groups
SELECT group_key, max(batch),
       max(member_path) FILTER (WHERE role = 'TRUNK'),
       count(*) FILTER (WHERE role = 'FOLD'),
       string_agg(member_path, ' | ' ORDER BY member_bytes DESC) FILTER (WHERE role = 'FOLD'),
       max(member_files) FILTER (WHERE role = 'TRUNK'),
       max(member_bytes) FILTER (WHERE role = 'TRUNK'),
       sum(dup_in_trunk_files) FILTER (WHERE role = 'FOLD'),
       sum(dup_in_trunk_bytes) FILTER (WHERE role = 'FOLD'),
       sum(carry_files) FILTER (WHERE role = 'FOLD'),
       sum(carry_bytes) FILTER (WHERE role = 'FOLD')
FROM raw_duck.vault_twins_merge_plan
GROUP BY group_key;

-- rollup
SELECT batch, count(*) AS groups, sum(n_fold) AS members_folded,
       sum(dup_files) AS dup_files, round(sum(dup_bytes)/1024.0/1024/1024, 2) AS dup_gb,
       sum(carry_files) AS carry_files, round(sum(carry_bytes)/1024.0/1024/1024, 2) AS carry_gb
FROM raw_duck.vault_twins_merge_plan_groups GROUP BY batch ORDER BY batch;
