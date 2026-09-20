-- vault_twins_08a_unit_roots.sql
-- Vault-side atomic-unit roots for the twin safety check.
-- Why: vault_units_v2.unit_root is SOURCE-relative (e.g. 'Court/Takeout' from
-- local/D-Backup); the step-1 merge renamed colliding roots with '[source-tag]'
-- suffixes ('Takeout [local-D-Backup]'), so 229 of 575 inventory roots did not
-- exist as vault dirs and every unit under a tagged root was invisible to 08.
-- Three sources, unioned:
--   vunit      raw_duck.vault_place_v6.vunit  - the unit root in vault-path terms
--   units_v2   raw_duck.vault_units_v2.unit_root where it exists verbatim in the vault
--   name-rule  owner 2026-09-16 15:25 EDT: "do not rip apart Facebook or Google
--              Takeout containers ... those stay put; if it's just a bunch of photo
--              directories at the top, mix those" - any vault directory whose own
--              name is Takeout- or Facebook-export shaped is a unit root, whatever
--              the detectors said. 15:28: Snapchat exports are units too.
--              Service folders inside any export are never processed.
-- Byline: Claude Code · Fable 5.1 · 2026-09-16

CREATE TABLE IF NOT EXISTS raw_duck.vault_unit_roots (
  unit_root  text NOT NULL,
  unit_class text,
  source     text NOT NULL,
  PRIMARY KEY (unit_root, source)
);
TRUNCATE raw_duck.vault_unit_roots;

INSERT INTO raw_duck.vault_unit_roots (unit_root, unit_class, source)
SELECT DISTINCT vunit, max(unit_class), 'vunit'
FROM raw_duck.vault_place_v6
WHERE vunit IS NOT NULL AND vunit <> ''
GROUP BY vunit;

INSERT INTO raw_duck.vault_unit_roots (unit_root, unit_class, source)
SELECT DISTINCT u.unit_root, max(u.unit_class), 'units_v2'
FROM raw_duck.vault_units_v2 u
JOIN raw_duck.vault_twins_dirs d ON d.dir_path = u.unit_root
GROUP BY u.unit_root
ON CONFLICT DO NOTHING;

-- name rule: the directory's own basename looks like a Takeout or Facebook export container
INSERT INTO raw_duck.vault_unit_roots (unit_root, unit_class, source)
SELECT d.dir_path,
       CASE WHEN regexp_replace(d.dir_path, '^.*/', '') ~* '(facebook|^fb data|^fb$|^meta-[0-9]{4}-)' THEN 'facebook'
            WHEN regexp_replace(d.dir_path, '^.*/', '') ~* '(^snap|^mydata~)' THEN 'snapchat' ELSE 'takeout' END,
       'name-rule'
FROM raw_duck.vault_twins_dirs d
WHERE regexp_replace(d.dir_path, '^.*/', '') ~* (
     '^(takeout|google takeout|google takeout files|takeout data)( ?[0-9]+| ?\([^)]*\)| ?\[[^]]*\]|[0-9]*)*$'
  || '|^takeout-[0-9]{8}T[0-9]{6}Z'
  || '|^facebook-'
  || '|^meta-[0-9]{4}-'
  || '|^fb data$|^fb$|^facebook data$|^fb exports$|^facebook$'
  || '|^your_facebook_activity$'
  -- owner 2026-09-16 15:28 EDT: "DO NOT STRIP SNAP CHATS ... THATS A UNIT"
  || '|^snap_export|^snap export|^snap data$|^snap$|^snapchat|^mydata~[0-9]+'
)
ON CONFLICT DO NOTHING;

SELECT source, unit_class, count(*) FROM raw_duck.vault_unit_roots GROUP BY 1,2 ORDER BY 1,2;
SELECT count(DISTINCT unit_root) AS distinct_roots FROM raw_duck.vault_unit_roots;
-- roots that are themselves nested inside another root (fine, both stay whole; listed for the record)
SELECT count(*) AS nested_roots FROM raw_duck.vault_unit_roots a
WHERE EXISTS (SELECT 1 FROM raw_duck.vault_unit_roots b WHERE starts_with(a.unit_root, b.unit_root || '/'));
