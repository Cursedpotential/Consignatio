"""SQLite ledger schema.

The ledger separates immutable observations from derived identity, provisional
assertions, and resumable transfer state.  Schema changes must be additive and
versioned; inventory rows are never discarded because a later snapshot repeats
the same object.
"""

SCHEMA_VERSION = 6

SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_batch (
    inventory_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL UNIQUE,
    captured_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0)
);

CREATE TABLE IF NOT EXISTS content_identity (
    content_id TEXT PRIMARY KEY,
    identity_kind TEXT NOT NULL CHECK (
        identity_kind IN ('sha256_verified', 'md5_size_candidate', 'pending_fingerprint')
    ),
    sha256 TEXT,
    md5 TEXT,
    byte_size INTEGER CHECK (byte_size IS NULL OR byte_size >= 0),
    identity_status TEXT NOT NULL CHECK (
        identity_status IN (
            'sha256_verified', 'md5_size_candidate', 'missing_hash',
            'invalid_hash', 'hash_error', 'hash_unsupported',
            'md5_size_conflict', 'sha256_assertion_conflict',
            'sha256_size_conflict'
        )
    ),
    fingerprint_required INTEGER NOT NULL CHECK (fingerprint_required IN (0, 1)),
    created_at TEXT NOT NULL,
    UNIQUE(identity_kind, sha256, md5, byte_size, content_id)
);

CREATE TABLE IF NOT EXISTS occurrence (
    occurrence_id TEXT PRIMARY KEY,
    inventory_id TEXT NOT NULL REFERENCES inventory_batch(inventory_id),
    row_number INTEGER NOT NULL CHECK (row_number > 0),
    bucket TEXT NOT NULL,
    object_path TEXT NOT NULL,
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    md5_raw TEXT,
    md5_normalized TEXT,
    md5_valid INTEGER NOT NULL CHECK (md5_valid IN (0, 1)),
    md5_state TEXT NOT NULL CHECK (
        md5_state IN ('valid', 'empty', 'error', 'unsupported', 'invalid')
    ),
    modtime_raw TEXT,
    mimetype_raw TEXT,
    content_id TEXT REFERENCES content_identity(content_id),
    UNIQUE(inventory_id, row_number)
);

CREATE INDEX IF NOT EXISTS occurrence_content_idx ON occurrence(content_id);
CREATE INDEX IF NOT EXISTS occurrence_location_idx ON occurrence(bucket, object_path);
CREATE INDEX IF NOT EXISTS occurrence_md5_idx ON occurrence(md5_normalized, byte_size);

CREATE TABLE IF NOT EXISTS strong_fingerprint_assertion (
    fingerprint_assertion_id TEXT PRIMARY KEY,
    occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    inventory_id TEXT NOT NULL REFERENCES inventory_batch(inventory_id),
    bucket TEXT NOT NULL,
    object_path TEXT NOT NULL,
    source_version TEXT,
    source_etag TEXT,
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    observed_md5 TEXT,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    verification_method TEXT NOT NULL CHECK (
        verification_method IN ('source_sha256_ledger', 'streamed_byte_hash', 'destination_readback')
    ),
    verifier TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    assertion_version TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS fingerprint_occurrence_idx
ON strong_fingerprint_assertion(occurrence_id, sha256);

CREATE TABLE IF NOT EXISTS fingerprint_import_partition (
    partition_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    bound_count INTEGER NOT NULL CHECK (bound_count >= 0),
    held_count INTEGER NOT NULL CHECK (held_count >= 0)
);

CREATE TABLE IF NOT EXISTS fingerprint_import_assertion (
    import_assertion_id TEXT PRIMARY KEY,
    partition_id TEXT NOT NULL REFERENCES fingerprint_import_partition(partition_id),
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    raw_sha256 TEXT NOT NULL CHECK (length(raw_sha256) = 64),
    raw_record TEXT NOT NULL,
    schema_name TEXT,
    algorithm TEXT,
    digest_raw TEXT,
    source_bucket TEXT,
    source_key TEXT,
    source_size INTEGER,
    md5_raw TEXT,
    source_version TEXT,
    source_etag TEXT,
    computed_at TEXT,
    computation TEXT,
    disposition TEXT NOT NULL CHECK (
        disposition IN (
            'bound', 'held_blank_record', 'held_malformed_utf8',
            'held_malformed_json', 'held_non_object', 'held_schema_mismatch',
            'held_algorithm_mismatch', 'held_invalid_digest',
            'held_invalid_locator', 'held_invalid_md5',
            'held_source_field_conflict', 'held_unmatched_occurrence',
            'held_ambiguous_occurrence', 'held_deferred_missing_computed_at',
            'held_digest_conflict'
        )
    ),
    detail_json TEXT NOT NULL,
    asserted_at TEXT NOT NULL,
    UNIQUE(partition_id, line_number)
);

CREATE INDEX IF NOT EXISTS fingerprint_import_disposition_idx
ON fingerprint_import_assertion(partition_id, disposition);

CREATE TABLE IF NOT EXISTS fingerprint_import_binding (
    import_assertion_id TEXT NOT NULL
        REFERENCES fingerprint_import_assertion(import_assertion_id),
    fingerprint_assertion_id TEXT NOT NULL
        REFERENCES strong_fingerprint_assertion(fingerprint_assertion_id),
    occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    PRIMARY KEY (import_assertion_id, fingerprint_assertion_id, occurrence_id)
);

CREATE TABLE IF NOT EXISTS sha256_bridge_finalization (
    finalization_id TEXT PRIMARY KEY,
    expected_partition_count INTEGER NOT NULL CHECK (expected_partition_count > 0),
    expected_record_count INTEGER NOT NULL CHECK (expected_record_count > 0),
    observed_partition_count INTEGER NOT NULL,
    observed_record_count INTEGER NOT NULL,
    partition_set_sha256 TEXT NOT NULL CHECK (length(partition_set_sha256) = 64),
    assertion_set_sha256 TEXT NOT NULL CHECK (length(assertion_set_sha256) = 64),
    bridge_group_count INTEGER NOT NULL CHECK (bridge_group_count >= 0),
    finalized_at TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state = 'frozen'),
    UNIQUE(expected_partition_count, expected_record_count,
           partition_set_sha256, assertion_set_sha256)
);

CREATE TABLE IF NOT EXISTS sha256_md5_size_bridge (
    md5 TEXT NOT NULL CHECK (length(md5) = 32),
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    direct_assertion_count INTEGER NOT NULL CHECK (direct_assertion_count > 0),
    finalization_id TEXT NOT NULL
        REFERENCES sha256_bridge_finalization(finalization_id),
    created_at TEXT NOT NULL,
    PRIMARY KEY (md5, byte_size)
);

CREATE INDEX IF NOT EXISTS sha256_bridge_digest_idx
ON sha256_md5_size_bridge(sha256, byte_size);

CREATE TABLE IF NOT EXISTS candidate_representative (
    content_id TEXT PRIMARY KEY REFERENCES content_identity(content_id),
    representative_occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    selection_rule TEXT NOT NULL,
    selection_is_quality_judgment INTEGER NOT NULL DEFAULT 0
        CHECK (selection_is_quality_judgment = 0),
    selected_at TEXT NOT NULL
);

-- Provenance-bearing metadata recovered from PostgreSQL catalogs, provider
-- inventories, sidecars, or extraction tools. Inventory path/modtime/MIME
-- observations remain in ``occurrence`` and are merged with these assertions
-- during resolution rather than copied into this table.
CREATE TABLE IF NOT EXISTS metadata_assertion (
    metadata_assertion_id TEXT PRIMARY KEY,
    occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    field_name TEXT NOT NULL,
    value_json TEXT NOT NULL,
    assertion_class TEXT NOT NULL CHECK (
        assertion_class IN (
            'embedded', 'external_sidecar', 'provider', 'catalog', 'human'
        )
    ),
    source_system TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_path TEXT,
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    trust_score INTEGER NOT NULL CHECK (trust_score >= 0 AND trust_score <= 100),
    observed_at TEXT,
    asserted_at TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    detail_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS metadata_assertion_occurrence_idx
ON metadata_assertion(occurrence_id, field_name);

CREATE INDEX IF NOT EXISTS metadata_assertion_source_idx
ON metadata_assertion(source_system, source_table, source_key);

CREATE TABLE IF NOT EXISTS metadata_import_partition (
    partition_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    assertion_count INTEGER NOT NULL CHECK (assertion_count >= 0)
);

-- Every inbound metadata row is retained before binding.  Historical path,
-- size, recovery labels, provider match percentages, MD5, and QuickXor are
-- locator/candidate assertions only; none of them creates content identity.
-- A row reaches ``metadata_assertion`` only after its candidate occurrences
-- resolve to one already SHA-256-verified content group.
CREATE TABLE IF NOT EXISTS metadata_import_record (
    import_record_id TEXT PRIMARY KEY,
    partition_id TEXT NOT NULL REFERENCES metadata_import_partition(partition_id),
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    raw_sha256 TEXT NOT NULL CHECK (length(raw_sha256) = 64),
    raw_record TEXT NOT NULL,
    source_system TEXT,
    source_table TEXT,
    source_key TEXT,
    source_account TEXT,
    source_tree TEXT,
    snapshot_id TEXT,
    source_version TEXT,
    explicit_occurrence_id TEXT,
    source_bucket TEXT,
    source_path TEXT,
    source_filename TEXT,
    byte_size INTEGER,
    sha256_hint TEXT,
    md5_hint TEXT,
    quickxor_hint TEXT,
    match_percent REAL,
    identity_authority TEXT,
    disposition TEXT NOT NULL CHECK (
        disposition IN (
            'staged', 'bound_explicit_occurrence', 'bound_verified_sha256',
            'bound_unique_verified_content', 'held_blank_record',
            'held_malformed_json', 'held_non_object', 'held_invalid_record',
            'held_invalid_identity_hint', 'held_unmatched_occurrence',
            'held_unverified_candidates', 'held_ambiguous_occurrence',
            'held_quickxor_drift'
        )
    ),
    selected_occurrence_id TEXT REFERENCES occurrence(occurrence_id),
    detail_json TEXT NOT NULL,
    asserted_at TEXT NOT NULL,
    UNIQUE(partition_id, line_number)
);

CREATE INDEX IF NOT EXISTS metadata_import_record_disposition_idx
ON metadata_import_record(partition_id, disposition);

CREATE INDEX IF NOT EXISTS metadata_import_record_locator_idx
ON metadata_import_record(source_bucket, source_path, byte_size);

CREATE TABLE IF NOT EXISTS metadata_import_candidate (
    import_record_id TEXT NOT NULL REFERENCES metadata_import_record(import_record_id),
    occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    content_id TEXT REFERENCES content_identity(content_id),
    identity_status TEXT,
    match_basis TEXT NOT NULL,
    selected INTEGER NOT NULL DEFAULT 0 CHECK (selected IN (0, 1)),
    PRIMARY KEY(import_record_id, occurrence_id)
);

CREATE INDEX IF NOT EXISTS metadata_import_candidate_content_idx
ON metadata_import_candidate(content_id, import_record_id);

-- Resolution rows are immutable snapshots. A stable hash of the complete
-- resolution makes regeneration idempotent; the current view selects the most
-- recently asserted snapshot without rewriting prior decisions.
CREATE TABLE IF NOT EXISTS content_metadata_resolution (
    resolution_id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES content_identity(content_id),
    primary_occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    canonical_filename TEXT NOT NULL,
    canonical_filename_assertion_id TEXT,
    oldest_trustworthy_timestamp TEXT,
    oldest_timestamp_assertion_id TEXT,
    resolution_state TEXT NOT NULL CHECK (
        resolution_state IN ('resolved', 'review_required', 'blocked_embedded_conflict')
    ),
    rule_version TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    input_set_sha256 TEXT NOT NULL CHECK (length(input_set_sha256) = 64),
    resolved_at TEXT NOT NULL,
    UNIQUE(content_id, input_set_sha256, rule_version)
);

CREATE INDEX IF NOT EXISTS content_metadata_resolution_content_idx
ON content_metadata_resolution(content_id, resolved_at, resolution_id);

CREATE TABLE IF NOT EXISTS metadata_field_resolution (
    field_resolution_id TEXT PRIMARY KEY,
    resolution_id TEXT NOT NULL
        REFERENCES content_metadata_resolution(resolution_id),
    field_name TEXT NOT NULL,
    selected_assertion_id TEXT,
    selected_value_json TEXT,
    resolution_state TEXT NOT NULL CHECK (
        resolution_state IN ('resolved', 'review_required', 'blocked_embedded_conflict')
    ),
    alternatives_json TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    UNIQUE(resolution_id, field_name)
);

CREATE VIEW IF NOT EXISTS current_content_metadata_resolution AS
SELECT r.*
FROM content_metadata_resolution r
WHERE r.rowid = (
    SELECT MAX(newer.rowid)
    FROM content_metadata_resolution newer
    WHERE newer.content_id = r.content_id
);

CREATE TABLE IF NOT EXISTS assertion (
    assertion_id TEXT PRIMARY KEY,
    occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    assertion_kind TEXT NOT NULL CHECK (
        assertion_kind IN ('high_level_category', 'atomic_unit_hint')
    ),
    label TEXT NOT NULL,
    grouping_key TEXT,
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    rule_set TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    provisional INTEGER NOT NULL DEFAULT 1 CHECK (provisional = 1),
    evidence_json TEXT NOT NULL,
    asserted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS assertion_occurrence_idx ON assertion(occurrence_id);
CREATE INDEX IF NOT EXISTS assertion_rule_idx ON assertion(rule_set, rule_version);

CREATE TABLE IF NOT EXISTS transfer_generation (
    generation_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    destination_remote TEXT NOT NULL,
    destination_prefix TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    inventory_set_sha256 TEXT NOT NULL,
    fingerprint_set_sha256 TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('open', 'frozen', 'retired'))
);

CREATE TABLE IF NOT EXISTS transfer_item (
    transfer_item_id TEXT PRIMARY KEY,
    generation_id TEXT NOT NULL REFERENCES transfer_generation(generation_id),
    content_id TEXT NOT NULL REFERENCES content_identity(content_id),
    representative_occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    source_relpath TEXT NOT NULL,
    destination_relpath TEXT NOT NULL,
    selection_rule TEXT NOT NULL,
    selection_is_quality_judgment INTEGER NOT NULL DEFAULT 0
        CHECK (selection_is_quality_judgment = 0),
    dedupe_authority TEXT NOT NULL CHECK (
        dedupe_authority IN (
            'sha256_verified', 'sha256_via_conflict_free_md5_size_bridge',
            'md5_candidate_no_suppression',
            'none_pending_fingerprint', 'none_conflict'
        )
    ),
    initial_status TEXT NOT NULL,
    UNIQUE(generation_id, content_id, representative_occurrence_id)
);

CREATE TABLE IF NOT EXISTS transfer_item_occurrence (
    transfer_item_id TEXT NOT NULL REFERENCES transfer_item(transfer_item_id),
    occurrence_id TEXT NOT NULL REFERENCES occurrence(occurrence_id),
    PRIMARY KEY (transfer_item_id, occurrence_id)
);

CREATE TABLE IF NOT EXISTS transfer_status_event (
    event_id TEXT PRIMARY KEY,
    transfer_item_id TEXT NOT NULL REFERENCES transfer_item(transfer_item_id),
    sequence_number INTEGER NOT NULL CHECK (sequence_number > 0),
    status TEXT NOT NULL CHECK (
        status IN (
            'planned', 'queued', 'copying', 'copied', 'verified',
            'skipped_existing_verified', 'retryable_error', 'permanent_error',
            'held_missing_hash', 'held_invalid_hash',
            'held_hash_error', 'held_hash_unsupported',
            'held_md5_size_conflict', 'held_sha256_assertion_conflict',
            'held_sha256_size_conflict', 'held_source_location_drift',
            'held_unsafe_path'
        )
    ),
    recorded_at TEXT NOT NULL,
    detail TEXT,
    UNIQUE(transfer_item_id, sequence_number)
);

CREATE VIEW IF NOT EXISTS transfer_item_current_status AS
SELECT e.transfer_item_id, e.status, e.recorded_at, e.detail, e.sequence_number
FROM transfer_status_event e
JOIN (
    SELECT transfer_item_id, MAX(sequence_number) AS sequence_number
    FROM transfer_status_event
    GROUP BY transfer_item_id
) latest
ON latest.transfer_item_id = e.transfer_item_id
AND latest.sequence_number = e.sequence_number;
"""
