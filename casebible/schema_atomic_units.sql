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
                            'archive_file','opaque_nested_root','other_package')),
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
                             'archive_provenance','defer_dissection')),
    attrs               jsonb NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (run_id, store, container, root_path, unit_type)
);

CREATE INDEX IF NOT EXISTS atomic_candidate_run_idx
    ON inventory.atomic_unit_candidate(run_id, unit_type);
CREATE INDEX IF NOT EXISTS atomic_candidate_root_idx
    ON inventory.atomic_unit_candidate(store, container, root_path);

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
            'opaque_nested_root','other_package'));

    ALTER TABLE inventory.atomic_unit_candidate
        DROP CONSTRAINT IF EXISTS atomic_unit_candidate_handling_mode_check;
    ALTER TABLE inventory.atomic_unit_candidate
        ADD CONSTRAINT atomic_unit_candidate_handling_mode_check CHECK (handling_mode IN (
            'normal_dedup','preserve_whole','archive_provenance','defer_dissection'));
END
$upgrade$;
