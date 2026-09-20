-- Byline: Codex | 2026-09-20. Additive overlay; existing corpus tables are retained.
CREATE SCHEMA IF NOT EXISTS catalog_reconcile;
COMMENT ON SCHEMA catalog_reconcile IS 'Case Bible metadata reconciliation contract v1; raw_duck dated facts are authoritative';
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_generations_20260920 (
  generation_id uuid PRIMARY KEY,
  published_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  status text NOT NULL CHECK (status = 'validated_metadata_reconciliation'),
  manifest jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_objects_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id),
  CHECK (payload->>'action' IN ('upload','hide','start')),
  CHECK ((payload->>'size')::bigint >= 0)
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_occurrences_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id),
  CHECK (payload->>'retirement_status' = 'not_cleared'),
  CHECK (payload->>'bas_status' = 'not_assessed')
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_work_items_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id),
  CHECK (payload->>'retirement_status' = 'not_cleared')
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_r2_occurrences_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id),
  CHECK (payload->>'retirement_status' = 'not_cleared')
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_packages_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id)
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_native_exports_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id)
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_source_observations_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id)
);
CREATE TABLE IF NOT EXISTS raw_duck.reconcile_bas_candidates_20260920 (
  generation_id uuid NOT NULL REFERENCES raw_duck.reconcile_generations_20260920,
  id text NOT NULL,
  payload jsonb NOT NULL,
  PRIMARY KEY (generation_id,id),
  CHECK (payload->>'retirement_status' = 'not_cleared'),
  CHECK (payload->>'status' = 'provisional_metadata_only')
);
CREATE INDEX IF NOT EXISTS reconcile_objects_hash_20260920 ON raw_duck.reconcile_objects_20260920
 (generation_id,(payload->>'sha1'),((payload->>'size')::bigint));
CREATE INDEX IF NOT EXISTS reconcile_work_kind_20260920 ON raw_duck.reconcile_work_items_20260920
 (generation_id,(payload->>'kind'));
CREATE INDEX IF NOT EXISTS reconcile_occ_state_20260920 ON raw_duck.reconcile_occurrences_20260920
 (generation_id,(payload->>'state'));
CREATE OR REPLACE VIEW catalog_reconcile.current_generation AS
 SELECT * FROM raw_duck.reconcile_generations_20260920
 WHERE status='validated_metadata_reconciliation' ORDER BY published_at DESC,generation_id DESC LIMIT 1;
CREATE OR REPLACE VIEW catalog_reconcile.object_versions AS
 SELECT r.generation_id,r.id AS file_id,r.payload->>'bucket' AS bucket,r.payload->>'key' AS object_key,
        r.payload->>'action' AS action,(r.payload->>'size')::bigint AS size,
        r.payload->>'sha1' AS sha1,(r.payload->>'visible')::boolean AS visible,
        to_timestamp((r.payload->>'upload_timestamp_ms')::double precision/1000) AS uploaded_at,
        r.payload->'metadata' AS source_metadata,r.payload->'provider_record' AS provider_record
 FROM raw_duck.reconcile_objects_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.occurrences AS
 SELECT r.generation_id,r.id AS occurrence_id,r.payload->>'source_rel' AS source_rel,
        r.payload->>'source' AS source,r.payload->>'state' AS availability,
        r.payload->>'match_basis' AS match_basis,r.payload->'version_ids' AS version_ids,
        r.payload->'source_record'->>'path' AS source_path,
        r.payload->'source_record'->>'source_id' AS provider_source_id,
        (r.payload->'source_record'->>'size')::bigint AS size,
        r.payload->'source_record'->>'native_hash_kind' AS native_hash_kind,
        r.payload->'source_record'->>'native_hash' AS native_hash,
        r.payload->'source_record'->>'md5' AS recorded_md5,
        r.payload->'source_record'->>'modtime' AS recorded_modtime,
        r.payload->'source_record'->'metadata' AS source_metadata,
        r.payload->'alternative_route_keys' AS alternative_route_keys,
        r.payload->>'route_status' AS route_status,r.payload->'quality_flags' AS quality_flags,
        r.payload->>'bas_status' AS bas_status,r.payload->>'retirement_status' AS retirement_status,
        r.payload->'source_record' AS source_record
 FROM raw_duck.reconcile_occurrences_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.recovery_worklist AS
 SELECT r.generation_id,r.id AS item_id,r.payload->>'kind' AS kind,r.payload->>'source' AS source,
        r.payload->>'priority' AS priority,r.payload->>'reason' AS reason,r.payload->>'next_step' AS next_step,
        r.payload->>'status' AS status,r.payload->>'retirement_status' AS retirement_status,
        r.payload->'evidence' AS evidence
 FROM raw_duck.reconcile_work_items_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.package_records AS
 SELECT r.generation_id,r.id,r.payload->>'dataset' AS dataset,r.payload->'record' AS source_record,
        'current_completeness_unverified'::text AS quality_status
 FROM raw_duck.reconcile_packages_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.r2_occurrences AS
 SELECT r.generation_id,r.id AS occurrence_id,r.payload->'source_record'->>'bucket' AS bucket,
        r.payload->'source_record'->>'path' AS source_path,r.payload->>'state' AS availability,
        r.payload->>'match_basis' AS match_basis,r.payload->'version_ids' AS version_ids,
        r.payload->>'retirement_status' AS retirement_status,r.payload->'source_record' AS source_record
 FROM raw_duck.reconcile_r2_occurrences_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.native_exports AS
 SELECT r.generation_id,r.id,r.payload->>'source' AS source,r.payload->>'source_id' AS provider_source_id,
        r.payload->>'native_path' AS source_path,r.payload->'representations' AS representations,
        r.payload->>'status' AS status,r.payload->>'source_native_retained' AS source_native_retained
 FROM raw_duck.reconcile_native_exports_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.visible_duplicate_identities AS
 SELECT sha1,size,count(*) AS physical_copies,(count(*)-1)*size AS repeated_bytes,
        array_agg(file_id ORDER BY file_id) AS version_ids
 FROM catalog_reconcile.object_versions WHERE visible AND action='upload' AND sha1 IS NOT NULL
 GROUP BY sha1,size HAVING count(*)>1;
CREATE OR REPLACE VIEW catalog_reconcile.source_observations AS
 SELECT r.generation_id,r.id,r.payload->>'source' AS source,r.payload->>'source_id' AS provider_source_id,
        r.payload->>'state' AS status,r.payload->>'observed_at' AS observed_at,r.payload->'metadata' AS metadata,
        r.payload AS observation
 FROM raw_duck.reconcile_source_observations_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.bas_candidates AS
 SELECT r.generation_id,r.id AS family_id,r.payload->>'source' AS source,r.payload->>'source_id' AS provider_source_id,
        r.payload->'bas1_candidate' AS bas1_candidate,r.payload->'bas2_candidate' AS bas2_candidate,
        r.payload->'complementary_representations_to_review' AS complementary_representations_to_review,
        r.payload->>'status' AS status,r.payload->>'retirement_status' AS retirement_status,r.payload AS assessment
 FROM raw_duck.reconcile_bas_candidates_20260920 r JOIN catalog_reconcile.current_generation g USING(generation_id);
CREATE OR REPLACE VIEW catalog_reconcile.availability_summary AS
 SELECT item->>0 AS source,item->>1 AS availability,(item->>2)::bigint AS occurrence_rows
 FROM catalog_reconcile.current_generation g
 CROSS JOIN LATERAL jsonb_array_elements(g.manifest->'occurrence_states') AS entries(item);
COMMENT ON VIEW catalog_reconcile.availability_summary IS 'Exact build-time counts from the validated immutable generation; detailed payloads remain independently queryable.';
COMMENT ON VIEW catalog_reconcile.occurrences IS 'Frozen source occurrences plus metadata-supported version links. No BAS approval, custody acceptance, or deletion authority.';
COMMENT ON VIEW catalog_reconcile.native_exports IS 'Receipt-derived export mappings; source native completeness is not inferred from Office/PDF exports.';
