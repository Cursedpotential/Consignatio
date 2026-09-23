INSERT INTO raw_duck.vault_objects (key, size, b2_id, depth)
SELECT key, size, b2_id, array_length(string_to_array(key, '/'), 1) - 1 AS depth
FROM (
  SELECT key, size, b2_id,
         row_number() OVER (PARTITION BY key ORDER BY size DESC) rn
  FROM raw_duck.vault_objects_stage
) t
WHERE rn = 1
ON CONFLICT (key) DO UPDATE SET size = EXCLUDED.size, b2_id = EXCLUDED.b2_id, depth = EXCLUDED.depth;

WITH vp AS (
  SELECT DISTINCT ON (vpath) vpath, md5, canonical_key, size
  FROM raw_duck.vault_place_v6
  ORDER BY vpath, (decision IS NOT NULL AND decision <> '') DESC, decision
)
UPDATE raw_duck.vault_objects vo
SET md5 = vp.md5, hash_source = 'vault_place_v6'
FROM vp
WHERE vo.key = vp.vpath AND vp.md5 IS NOT NULL AND vo.md5 IS NULL;

WITH vp AS (
  SELECT DISTINCT ON (vpath) vpath, canonical_key
  FROM raw_duck.vault_place_v6
  WHERE canonical_key IS NOT NULL
  ORDER BY vpath, (decision IS NOT NULL AND decision <> '') DESC, decision
)
UPDATE raw_duck.vault_objects vo
SET sha1 = bo.sha1
FROM vp
JOIN raw_duck.b2_objects bo ON bo.key = vp.canonical_key
WHERE vo.key = vp.vpath AND bo.sha1 IS NOT NULL AND vo.sha1 IS NULL;

CREATE INDEX IF NOT EXISTS vault_objects_md5_idx ON raw_duck.vault_objects (md5);
CREATE INDEX IF NOT EXISTS vault_objects_sha1_idx ON raw_duck.vault_objects (sha1);
CREATE INDEX IF NOT EXISTS vault_objects_depth_idx ON raw_duck.vault_objects (depth);

SELECT
  count(*) AS total_rows,
  count(md5) AS rows_with_md5,
  count(sha1) AS rows_with_sha1,
  count(*) FILTER (WHERE md5 IS NOT NULL OR sha1 IS NOT NULL) AS rows_with_any_hash
FROM raw_duck.vault_objects;
