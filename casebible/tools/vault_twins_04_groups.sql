-- vault_twins_04_groups.sql
-- Load the parent session's name-normalization candidate groups
-- (docs/receipts/2026-09-16-vault-twins-candidates.json, flattened by
-- vault_twins_groups_load.py) into raw_duck.vault_twins_groups.
-- Byline: Claude Code · Sonnet 5 · 2026-09-16

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_groups (
  group_key         text NOT NULL,
  unit_group        boolean NOT NULL,
  member_path       text NOT NULL,
  member_depth      int NOT NULL,
  member_files      bigint,
  member_gb         numeric,
  member_units_json jsonb
);
TRUNCATE raw_duck.vault_twins_groups;
-- loaded externally via:
--   python3 casebible/tools/vault_twins_groups_load.py docs/receipts/2026-09-16-vault-twins-candidates.json \
--     | ssh ovh-files "docker exec -i <pg-container> psql -U postgres -d casebible \
--         -c \"\copy raw_duck.vault_twins_groups(group_key,unit_group,member_path,member_depth,member_files,member_gb,member_units_json) FROM STDIN WITH (FORMAT text, DELIMITER E'\t')\""

CREATE INDEX IF NOT EXISTS vault_twins_groups_key_idx ON raw_duck.vault_twins_groups (group_key);
CREATE INDEX IF NOT EXISTS vault_twins_groups_path_idx ON raw_duck.vault_twins_groups (member_path);

SELECT count(distinct group_key) AS groups,
       count(distinct group_key) FILTER (WHERE unit_group) AS unit_groups,
       count(*) AS members
FROM raw_duck.vault_twins_groups;
