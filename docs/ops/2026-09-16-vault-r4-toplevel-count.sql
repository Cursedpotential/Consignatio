-- Byline: Claude Code · Sonnet 5 · 2026-09-16
-- Count distinct top-level directory names implied by raw_duck.vault_objects_20260916_r4
-- keys (minus the 49 pilot-delete keys), to cross-check against the parent's cited "269
-- top-level names" for /media/openlist/b2/salem-data/consignatio/vault/v1.
SELECT count(DISTINCT split_part(replace(v.key, 'consignatio/vault/v1/', ''), '/', 1)) AS distinct_top_level
FROM raw_duck.vault_objects_20260916_r4 v
WHERE NOT EXISTS (SELECT 1 FROM raw_duck.vault_onecopy_pilot_delete_20260916 d WHERE d.key = v.key);
