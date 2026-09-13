-- Case Bible atomic-unit discovery and deduplication boundaries.
-- Additive/append-only: no source rows or files are changed or removed.

CREATE SCHEMA IF NOT EXISTS inventory;

CREATE TABLE IF NOT EXISTS inventory.atomic_detection_run (
    id                  uuid PRIMARY KEY DEFAULT uuidv7(),
    rules_version       text NOT NULL,
    scope               text NOT NULL,
    status              text NOT NULL CHECK (status IN ('running','completed','failed')),
    candidate_count     bigint,
    started_at          timestamptz NOT NULL DEFAULT now(),
    completed_at        timestamptz,
    notes               text
);

CREATE TABLE IF NOT EXISTS inventory.atomic_unit_candidate (
    id                  uuid PRIMARY KEY DEFAULT uuidv7(),
    run_id              uuid NOT NULL REFERENCES inventory.atomic_detection_run(id),
    store               text NOT NULL CHECK (store IN ('r2','onedrive','gdrive','local')),
    account             text,
    container           text NOT NULL,
    root_path           text NOT NULL,
    unit_type           text NOT NULL CHECK (unit_type IN (
                            'google_takeout','facebook_dyi','facebook_deconstruction',
                            'chat_export','code_repository','ios_backup',
                            'archive_file','opaque_nested_root',
                            'orphaned_export_fragment','other_package')),
    detection_basis     text NOT NULL,
    boundary_confidence text NOT NULL CHECK (boundary_confidence IN ('high','medium','review')),
    marker_count        bigint NOT NULL DEFAULT 1,
    marker_paths        jsonb NOT NULL DEFAULT '[]',
    parent_candidate_id uuid REFERENCES inventory.atomic_unit_candidate(id),
    review_state        text NOT NULL DEFAULT 'candidate'
                         CHECK (review_state IN ('candidate','confirmed','rejected','needs_review')),
    handling_mode       text NOT NULL DEFAULT 'normal_dedup'
                         CHECK (handling_mode IN (
                             'normal_dedup','preserve_whole',
                             'archive_provenance','defer_dissection',
                             'controlled_consolidation','investigate_orphan')),
    attrs               jsonb NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, store, container, root_path, unit_type)
);

CREATE INDEX IF NOT EXISTS atomic_candidate_run_idx
    ON inventory.atomic_unit_candidate(run_id, unit_type);
CREATE INDEX IF NOT EXISTS atomic_candidate_root_idx
    ON inventory.atomic_unit_candidate(store, container, root_path);
CREATE INDEX IF NOT EXISTS atomic_candidate_run_root_idx
    ON inventory.atomic_unit_candidate(
        run_id, store, container, coalesce(account, ''), root_path);

CREATE TABLE IF NOT EXISTS inventory.atomic_path_index (
    store               text NOT NULL CHECK (store IN ('r2','onedrive','gdrive','local')),
    account_key         text NOT NULL DEFAULT '',
    container           text NOT NULL,
    path                text NOT NULL,
    source_variant_key  text NOT NULL,
    name                text NOT NULL,
    byte_size           bigint,
    md5                 text,
    sha1                text,
    sha256              text,
    quickxor            text,
    mtime_text          text,
    source_row_count    bigint NOT NULL DEFAULT 1,
    source_refs         jsonb NOT NULL DEFAULT '[]',
    path_parts          text[] GENERATED ALWAYS AS (
                            string_to_array(replace(path, E'\\', '/'), '/')) STORED,
    indexed_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (store, account_key, container, path, source_variant_key)
);

CREATE INDEX IF NOT EXISTS atomic_path_index_path_idx
    ON inventory.atomic_path_index(store, account_key, container, path);
CREATE INDEX IF NOT EXISTS atomic_path_index_name_idx
    ON inventory.atomic_path_index(lower(name));

COMMENT ON TABLE inventory.atomic_path_index IS
  'Normalized provider locations relevant to atomic detection. Distinct metadata/hash variants at the same path remain separate; duplicate OneDrive scan rows are counted, not discarded.';

CREATE TABLE IF NOT EXISTS inventory.atomic_copy (
    id                    uuid PRIMARY KEY DEFAULT uuidv7(),
    candidate_id          uuid NOT NULL REFERENCES inventory.atomic_unit_candidate(id),
    member_count          bigint,
    total_bytes           bigint,
    hashed_member_count   bigint,
    marker_valid          boolean,
    manifest_sha256       bytea,
    completeness_state    text NOT NULL DEFAULT 'unmeasured'
                           CHECK (completeness_state IN (
                               'unmeasured','complete','partial','complementary',
                               'divergent','corrupt','unreadable')),
    selection_state       text NOT NULL DEFAULT 'unresolved'
                           CHECK (selection_state IN (
                               'unresolved','proposed_base','approved_base',
                               'supplemental','rejected')),
    quality_score         numeric,
    selection_reason      text,
    created_at            timestamptz NOT NULL DEFAULT now(),
    UNIQUE (candidate_id)
);

CREATE TABLE IF NOT EXISTS inventory.atomic_member (
    id                  uuid PRIMARY KEY DEFAULT uuidv7(),
    copy_id             uuid NOT NULL REFERENCES inventory.atomic_copy(id),
    relative_path       text NOT NULL,
    full_path           text NOT NULL,
    byte_size           bigint,
    md5                 text,
    sha1                text,
    sha256              text,
    quickxor            text,
    mtime               timestamptz,
    is_marker           boolean NOT NULL DEFAULT false,
    member_state        text NOT NULL DEFAULT 'present'
                         CHECK (member_state IN ('present','missing','conflicting','unhashed')),
    source_ref          text NOT NULL,
    attrs               jsonb NOT NULL DEFAULT '{}',
    UNIQUE (copy_id, relative_path, full_path)
);

CREATE INDEX IF NOT EXISTS atomic_member_copy_idx
    ON inventory.atomic_member(copy_id, relative_path);
CREATE INDEX IF NOT EXISTS atomic_member_md5_idx
    ON inventory.atomic_member(md5) WHERE md5 IS NOT NULL;
CREATE INDEX IF NOT EXISTS atomic_member_sha256_idx
    ON inventory.atomic_member(sha256) WHERE sha256 IS NOT NULL;

CREATE TABLE IF NOT EXISTS inventory.takeout_subject_account (
    id                  uuid PRIMARY KEY DEFAULT uuidv7(),
    account_handle      text NOT NULL UNIQUE,
    account_domain      text,
    evidence_priority   text NOT NULL DEFAULT 'normal'
                         CHECK (evidence_priority IN ('normal','high','critical')),
    account_state       text NOT NULL DEFAULT 'discovered'
                         CHECK (account_state IN (
                             'owner_supplied','discovered','confirmed','unknown')),
    supplied_at         timestamptz,
    notes               text,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory.atomic_identity_evidence (
    id                  uuid PRIMARY KEY DEFAULT uuidv7(),
    candidate_id        uuid NOT NULL REFERENCES inventory.atomic_unit_candidate(id),
    subject_account_id  uuid REFERENCES inventory.takeout_subject_account(id),
    observed_identifier text NOT NULL,
    evidence_kind       text NOT NULL CHECK (evidence_kind IN (
                            'owner_account_list','folder_hint','internal_filename',
                            'internal_content','archive_filename','manifest_overlap')),
    source_path         text NOT NULL,
    evidence_hash       text,
    confidence          text NOT NULL CHECK (confidence IN ('hint','medium','strong')),
    review_state        text NOT NULL DEFAULT 'unreviewed'
                         CHECK (review_state IN (
                             'unreviewed','corroborated','confirmed','rejected')),
    attrs               jsonb NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (candidate_id, evidence_kind, source_path, observed_identifier)
);

CREATE INDEX IF NOT EXISTS atomic_identity_candidate_idx
    ON inventory.atomic_identity_evidence(candidate_id);
CREATE INDEX IF NOT EXISTS atomic_identity_identifier_idx
    ON inventory.atomic_identity_evidence(lower(observed_identifier));

CREATE TABLE IF NOT EXISTS inventory.takeout_archive_part (
    id                    uuid PRIMARY KEY DEFAULT uuidv7(),
    run_id                uuid NOT NULL REFERENCES inventory.atomic_detection_run(id),
    archive_candidate_id  uuid NOT NULL UNIQUE REFERENCES inventory.atomic_unit_candidate(id),
    subject_account_id    uuid REFERENCES inventory.takeout_subject_account(id),
    subject_state         text NOT NULL DEFAULT 'unknown'
                           CHECK (subject_state IN ('unknown','hinted','corroborated','confirmed')),
    source_series_key     text,
    export_timestamp_text text,
    export_batch_ordinal  integer,
    part_number           integer,
    observed_set_state    text NOT NULL DEFAULT 'not_evaluated'
                           CHECK (observed_set_state IN (
                               'not_evaluated','observed_contiguous_from_one',
                               'observed_gapped','observed_partial')),
    originality_state     text NOT NULL CHECK (originality_state IN (
                               'strong_original_name','possible_original_name',
                               'takeout_context')),
    archive_filename      text NOT NULL,
    parse_basis           text NOT NULL,
    attrs                 jsonb NOT NULL DEFAULT '{}',
    created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS takeout_archive_series_idx
    ON inventory.takeout_archive_part(run_id, source_series_key, part_number);

CREATE TABLE IF NOT EXISTS inventory.atomic_candidate_relation (
    from_candidate_id   uuid NOT NULL REFERENCES inventory.atomic_unit_candidate(id),
    to_candidate_id     uuid NOT NULL REFERENCES inventory.atomic_unit_candidate(id),
    relation_type       text NOT NULL CHECK (relation_type IN (
                            'possible_extraction_of','confirmed_extraction_of',
                            'same_export_event','supplements','contains')),
    confidence          text NOT NULL CHECK (confidence IN ('hint','medium','strong')),
    evidence_basis      text NOT NULL,
    review_state        text NOT NULL DEFAULT 'unreviewed'
                         CHECK (review_state IN ('unreviewed','confirmed','rejected')),
    attrs               jsonb NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (from_candidate_id, to_candidate_id, relation_type)
);

CREATE TABLE IF NOT EXISTS inventory.atomic_group (
    id                    uuid PRIMARY KEY DEFAULT uuidv7(),
    run_id                uuid NOT NULL REFERENCES inventory.atomic_detection_run(id),
    unit_type             text NOT NULL,
    grouping_basis        text NOT NULL CHECK (grouping_basis IN (
                              'exact_manifest','member_overlap','manual','unresolved')),
    selected_copy_id      uuid REFERENCES inventory.atomic_copy(id),
    review_state          text NOT NULL DEFAULT 'unresolved'
                           CHECK (review_state IN ('unresolved','proposed','approved','disputed')),
    reconstruction_state  text NOT NULL DEFAULT 'not_evaluated'
                           CHECK (reconstruction_state IN (
                               'not_evaluated','complete_base','needs_supplement',
                               'composite_proposed','composite_approved','blocked')),
    b2_state              text NOT NULL DEFAULT 'not_planned'
                           CHECK (b2_state IN ('not_planned','candidate','approved','copied','verified','blocked')),
    reasoning             text,
    created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory.atomic_group_copy (
    group_id            uuid NOT NULL REFERENCES inventory.atomic_group(id),
    copy_id             uuid NOT NULL REFERENCES inventory.atomic_copy(id),
    role                text NOT NULL DEFAULT 'candidate'
                         CHECK (role IN ('candidate','selected_base','supplemental','rejected')),
    PRIMARY KEY (group_id, copy_id)
);

COMMENT ON TABLE inventory.atomic_unit_candidate IS
  'Structurally detected package roots. A candidate boundary is never a disposition decision.';
COMMENT ON TABLE inventory.atomic_member IS
  'Members remain attached to their package so ordinary file dedup cannot shred atomic exports or repositories.';
COMMENT ON TABLE inventory.atomic_group IS
  'Logical package copies. One complete base may be supplemented by missing members from another copy; every source remains recorded.';
COMMENT ON TABLE inventory.atomic_identity_evidence IS
  'Account identity observations remain separate from package rows. Folder names are hints; internal content or corroborated evidence is required for confirmation.';
COMMENT ON TABLE inventory.takeout_archive_part IS
  'Original-looking Google Takeout archives represented per export event and part. Unknown accounts and missing part numbers remain explicit.';
COMMENT ON TABLE inventory.atomic_candidate_relation IS
  'Proposed archive/extraction and reconstruction relationships. Filename similarity alone never confirms a relationship.';

INSERT INTO inventory.takeout_subject_account(
    account_handle, account_state, evidence_priority, supplied_at, notes)
VALUES
    ('matt.salemnet', 'owner_supplied', 'critical', '2026-09-12', 'Owner corrected the exact handle and identified it as the largest and one of the two most important Takeout accounts.'),
    ('matt.salem85', 'owner_supplied', 'normal', '2026-09-12', 'Owner supplied as a Takeout account handle.'),
    ('caminstaller', 'owner_supplied', 'normal', '2026-09-12', 'Owner supplied as a Takeout account handle.'),
    ('salemnma', 'owner_supplied', 'normal', '2026-09-12', 'Owner supplied as a Takeout account handle.'),
    ('katrina95xo', 'owner_supplied', 'normal', '2026-09-12', 'Owner supplied as a Takeout account handle.'),
    ('katrinasalem95', 'owner_supplied', 'normal', '2026-09-12', 'Owner supplied as a Takeout account handle.')
ON CONFLICT (account_handle) DO NOTHING;

-- Upgrade an already-created v1 table without removing any rows.
ALTER TABLE inventory.atomic_unit_candidate
    ADD COLUMN IF NOT EXISTS handling_mode text NOT NULL DEFAULT 'normal_dedup';

DO $upgrade$
BEGIN
    ALTER TABLE inventory.atomic_unit_candidate
        DROP CONSTRAINT IF EXISTS atomic_unit_candidate_unit_type_check;
    ALTER TABLE inventory.atomic_unit_candidate
        ADD CONSTRAINT atomic_unit_candidate_unit_type_check CHECK (unit_type IN (
            'google_takeout','facebook_dyi','facebook_deconstruction',
            'chat_export','code_repository','ios_backup','archive_file',
            'opaque_nested_root','orphaned_export_fragment','other_package'));

    ALTER TABLE inventory.atomic_unit_candidate
        DROP CONSTRAINT IF EXISTS atomic_unit_candidate_handling_mode_check;
    ALTER TABLE inventory.atomic_unit_candidate
        ADD CONSTRAINT atomic_unit_candidate_handling_mode_check CHECK (handling_mode IN (
            'normal_dedup','preserve_whole','archive_provenance','defer_dissection',
            'controlled_consolidation','investigate_orphan'));
END
$upgrade$;
