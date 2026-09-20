-- vault_twins_analysis.sql
-- Purpose: purely analytical (read-only on B2/Spacedrive) directory-twin reconciliation
-- analysis for the fresh vault/v1 listing (2026-09-16). Writes ONLY to PG schema
-- raw_duck, new tables prefixed vault_objects / vault_twins_*.
-- Byline: Claude Code · Sonnet 5 · 2026-09-16
--
-- This file is organized in numbered sections, executed as separate psql
-- invocations from the desktop over SSH (see docs/receipts/2026-09-16-vault-twins-analysis.md
-- for the exact commands run). Sections are idempotent (CREATE TABLE IF NOT EXISTS /
-- TRUNCATE) so they can be re-run safely.

-- ============================================================
-- SECTION 1: vault_objects catalog (the fresh vault/v1 listing, hashed where joinable)
-- ============================================================

CREATE TABLE IF NOT EXISTS raw_duck.vault_objects_stage (
  key   text,
  size  bigint,
  b2_id text
);
TRUNCATE raw_duck.vault_objects_stage;
-- loaded externally via: jq -r '.[] | [.Path,.Size,.ID] | @tsv' <listing.json> \
--   | docker exec -i <pg-container> psql -U postgres -d casebible \
--     -c "\copy raw_duck.vault_objects_stage(key,size,b2_id) FROM STDIN WITH (FORMAT text, DELIMITER E'\t')"

CREATE TABLE IF NOT EXISTS raw_duck.vault_objects (
  key         text PRIMARY KEY,
  size        bigint NOT NULL,
  b2_id       text,
  md5         text,
  sha1        text,
  hash_source text,
  depth       int
);

INSERT INTO raw_duck.vault_objects (key, size, b2_id, depth)
SELECT key, size, b2_id, array_length(string_to_array(key, '/'), 1) - 1 AS depth
FROM (
  SELECT key, size, b2_id,
         row_number() OVER (PARTITION BY key ORDER BY size DESC) rn
  FROM raw_duck.vault_objects_stage
) t
WHERE rn = 1
ON CONFLICT (key) DO UPDATE SET size = EXCLUDED.size, b2_id = EXCLUDED.b2_id, depth = EXCLUDED.depth;

-- Hash join #1: vault_place_v6.vpath == vault_objects.key (same relative-path scheme),
-- vault_place_v6 already carries md5 and the source canonical_key.
WITH vp AS (
  SELECT DISTINCT ON (vpath) vpath, md5, canonical_key, size
  FROM raw_duck.vault_place_v6
  ORDER BY vpath, (decision IS NOT NULL AND decision <> '') DESC, decision
)
UPDATE raw_duck.vault_objects vo
SET md5 = vp.md5, hash_source = 'vault_place_v6'
FROM vp
WHERE vo.key = vp.vpath AND vp.md5 IS NOT NULL AND vo.md5 IS NULL;

-- Hash join #2: sha1 via the same vpath->canonical_key lookup into b2_objects (intake layer sha1 ledger)
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

-- Report line for section 1
SELECT
  count(*) AS total_rows,
  count(md5) AS rows_with_md5,
  count(sha1) AS rows_with_sha1,
  count(*) FILTER (WHERE md5 IS NOT NULL OR sha1 IS NOT NULL) AS rows_with_any_hash
FROM raw_duck.vault_objects;
