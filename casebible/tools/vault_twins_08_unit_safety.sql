-- vault_twins_08_unit_safety.sql
-- Unit-safety check: does any member of a candidate group coincide with, sit
-- inside, or contain a recognized atomic unit (raw_duck.vault_unit_roots, built by
-- vault_twins_08a_unit_roots.sql = vault-side vunit ∪ units_v2 ∪ owner name rule)?
-- A merge proposal must never be made for a group where this is true - either
-- the members ARE separate units (should be linked, not merged) or a member
-- is a subfolder that recurs identically-named across many different units
-- (not a real duplicate - an occurrence inside a different unit each time).
-- Byline: Claude Code · Sonnet 5 · 2026-09-16; containment test switched from LIKE to starts_with
-- (962 member paths contain '_', a LIKE wildcard) by Claude Code · Fable 5.1 · 2026-09-16

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_unit_safety (
  group_key         text PRIMARY KEY,
  normalizer_unit_flag boolean,
  n_members         int,
  any_is_unit       boolean,
  any_contains_unit boolean,
  any_inside_unit   boolean,
  safety_class      text
);
TRUNCATE raw_duck.vault_twins_unit_safety;

INSERT INTO raw_duck.vault_twins_unit_safety
WITH member_flags AS (
  SELECT g.group_key, g.unit_group, g.member_path,
    bool_or(u.unit_root = g.member_path) AS is_unit,
    bool_or(starts_with(u.unit_root, g.member_path || '/')) AS contains_unit,
    bool_or(starts_with(g.member_path, u.unit_root || '/')) AS inside_unit
  FROM raw_duck.vault_twins_groups g
  LEFT JOIN (SELECT DISTINCT unit_root FROM raw_duck.vault_unit_roots) u   -- was vault_units_v2 (source-relative roots); see 08a
    ON u.unit_root = g.member_path
    OR starts_with(u.unit_root, g.member_path || '/')
    OR starts_with(g.member_path, u.unit_root || '/')
  GROUP BY g.group_key, g.unit_group, g.member_path
),
group_flags AS (
  SELECT group_key, bool_or(unit_group) AS normalizer_unit_flag, count(*) AS n_members,
         bool_or(coalesce(is_unit,false)) AS any_is_unit,
         bool_or(coalesce(contains_unit,false)) AS any_contains_unit,
         bool_or(coalesce(inside_unit,false)) AS any_inside_unit,
         bool_and(coalesce(is_unit,false)) AS all_is_unit
  FROM member_flags GROUP BY group_key
)
SELECT group_key, normalizer_unit_flag, n_members, any_is_unit, any_contains_unit, any_inside_unit,
  CASE
    WHEN all_is_unit THEN 'ALL_MEMBERS_ARE_UNITS'
    WHEN any_is_unit OR any_inside_unit OR any_contains_unit THEN 'UNIT_OVERLAP_UNSAFE'
    ELSE 'NO_UNIT_OVERLAP'
  END AS safety_class
FROM group_flags;

CREATE INDEX IF NOT EXISTS vault_twins_unit_safety_class_idx ON raw_duck.vault_twins_unit_safety (safety_class);

-- how many non-unit-flagged groups are actually unit-unsafe (the normalizer's gap)
SELECT normalizer_unit_flag, safety_class, count(*) AS groups
FROM raw_duck.vault_twins_unit_safety GROUP BY 1,2 ORDER BY 1,2;

-- how much collapsible GB (from vault_twins_group_summary) sits in groups that are actually safe to merge
SELECT s.safety_class, count(*) AS groups,
       round(sum(gs.dup_bytes)/1024.0/1024/1024,2) AS dup_gb,
       round(sum(gs.total_bytes)/1024.0/1024/1024,2) AS total_gb
FROM raw_duck.vault_twins_unit_safety s
JOIN raw_duck.vault_twins_group_summary gs ON gs.group_key = s.group_key
WHERE NOT gs.unit_group
GROUP BY s.safety_class ORDER BY dup_gb DESC;
