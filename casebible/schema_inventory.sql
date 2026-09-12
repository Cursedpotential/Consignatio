-- ============================================================================
-- Case Bible INVENTORY schema
-- Target: casebible @ ovh-files.tilapia-skilift.ts.net:5434  (PG18)
-- ============================================================================
-- SCOPE: inventory ONLY. What exists, where it lives, what's been hashed,
-- what's been sorted, and every move it has made. The PLATFORM handles
-- evidence, parsing, ingestion, custody chain, working dirs. Not here.
--
-- Column names/types deliberately mirror evidence.source / evidence_hash /
-- custody_event so handoff to the platform is a straight INSERT..SELECT.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS inventory;
COMMENT ON SCHEMA inventory IS
  'Case Bible corpus inventory. Content identity, locations, hash state, '
  'sort state, movement provenance. Feeds the platform; is not the platform.';

-- ---------------------------------------------------------------------------
-- item - one row per unique CONTENT (not per path)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory.item (
    id                uuid PRIMARY KEY DEFAULT uuidv7(),

    -- identity (mirrors evidence.source)
    sha256            bytea,
    md5_prefilter     bytea,
    sha1              bytea,
    quickxor          text,                    -- OneDrive-only; joins nothing else
    byte_size         bigint NOT NULL,
    mime_type         text,
    original_filename text,
    ext               text,

    -- WHAT'S BEEN HASHED
    hash_state        text NOT NULL DEFAULT 'none'
        CHECK (hash_state IN ('none','md5_only','quickxor_only','sha256_only','full')),
    hashed_at         timestamptz,
    hashed_by         text,
    hash_canon_version text NOT NULL DEFAULT 'h1-rawbytes-v1',

    -- WHAT'S BEEN SORTED
    sort_state        text NOT NULL DEFAULT 'unsorted'
        CHECK (sort_state IN ('unsorted','proposed','sorted','quarantined','held','rejected')),
    sorted_domain     text,
    sorted_at         timestamptz,
    sort_reason       text,

    -- dedup / canonical selection (mirrors evidence.source.supersedes_source_id)
    duplicate_group   text,
    canonical_status  text NOT NULL DEFAULT 'unresolved'
        CHECK (canonical_status IN ('canonical','alternate_retained','duplicate_candidate',
                                    'near_duplicate_candidate','superseded_but_preserved','unresolved')),
    supersedes_item_id uuid REFERENCES inventory.item(id),
    quality_score     numeric,

    -- WHEN DID IT COME INTO EXISTENCE (earliest observed across all locations)
    earliest_btime    timestamptz,
    earliest_mtime    timestamptz,

    -- handoff
    exported_to_platform_at timestamptz,
    platform_source_id      uuid,

    attrs             jsonb NOT NULL DEFAULT '{}',
    first_seen        timestamptz NOT NULL DEFAULT now(),
    last_seen         timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT item_sha_len  CHECK (sha256 IS NULL OR octet_length(sha256) = 32),
    CONSTRAINT item_md5_len  CHECK (md5_prefilter IS NULL OR octet_length(md5_prefilter) = 16),
    CONSTRAINT item_sha1_len CHECK (sha1 IS NULL OR octet_length(sha1) = 20),
    CONSTRAINT item_has_some_id CHECK (
        sha256 IS NOT NULL OR md5_prefilter IS NOT NULL OR quickxor IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS item_sha256_uniq ON inventory.item (sha256) WHERE sha256 IS NOT NULL;
CREATE INDEX IF NOT EXISTS item_md5_idx        ON inventory.item (md5_prefilter);
CREATE INDEX IF NOT EXISTS item_quickxor_idx   ON inventory.item (quickxor);
CREATE INDEX IF NOT EXISTS item_hash_state_idx ON inventory.item (hash_state);
CREATE INDEX IF NOT EXISTS item_sort_state_idx ON inventory.item (sort_state);
CREATE INDEX IF NOT EXISTS item_dupgroup_idx   ON inventory.item (duplicate_group);
CREATE INDEX IF NOT EXISTS item_size_idx       ON inventory.item (byte_size);


-- ---------------------------------------------------------------------------
-- location - WHERE DOES IT LIVE. N rows per item, one per place it exists.
-- Same content in R2 + OneDrive + F:\case + GDrive = 4 rows.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory.location (
    id            uuid PRIMARY KEY DEFAULT uuidv7(),
    item_id       uuid NOT NULL REFERENCES inventory.item(id) ON DELETE CASCADE,

    -- WHERE
    store         text NOT NULL
        CHECK (store IN ('r2','b2','onedrive','gdrive','local','unknown')),
    account       text,               -- matt.salemnet@gmail.com, od, od1
    container     text,               -- bucket / drive letter / share
    path          text NOT NULL,      -- full key or path, structure preserved
    filename      text,
    external_id   text,               -- Drive file ID, OneDrive item id

    -- state AT THIS LOCATION
    byte_size     bigint,
    mtime         timestamptz,
    btime         timestamptz,
    present       boolean NOT NULL DEFAULT true,   -- false = observed gone
    is_canonical  boolean NOT NULL DEFAULT false,  -- the copy of record

    -- how we know
    observed_at   timestamptz NOT NULL DEFAULT now(),
    observed_by   text,               -- scan/tool that saw it
    scan_ref      text,               -- manifest/scan file it came from

    attrs         jsonb NOT NULL DEFAULT '{}',
    CONSTRAINT location_uniq UNIQUE (store, container, path, observed_at)
);

CREATE INDEX IF NOT EXISTS loc_item_idx      ON inventory.location (item_id);
CREATE INDEX IF NOT EXISTS loc_store_idx     ON inventory.location (store, container);
CREATE INDEX IF NOT EXISTS loc_path_idx      ON inventory.location (path);
CREATE INDEX IF NOT EXISTS loc_present_idx   ON inventory.location (present) WHERE present;
CREATE INDEX IF NOT EXISTS loc_canonical_idx ON inventory.location (item_id) WHERE is_canonical;

COMMENT ON TABLE inventory.location IS
  'Every observed location of an item. present=false records a place it USED '
  'to be. This is what evidence.source cannot express (one path per row).';

-- ---------------------------------------------------------------------------
-- movement - PROVENANCE. Every move/copy/quarantine. Who touched it, when.
-- Mirrors evidence.custody_event shape for handoff.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory.movement (
    id             uuid PRIMARY KEY DEFAULT uuidv7(),
    item_id        uuid REFERENCES inventory.item(id) ON DELETE CASCADE,

    action         text NOT NULL
        CHECK (action IN ('copy','move','quarantine','restore','rename',
                          'delete_proposed','hash','scan','sort','promote','supersede')),

    -- FROM -> TO
    from_store     text,
    from_path      text,
    to_store       text,
    to_path        text,

    -- WHO TOUCHED IT
    actor          text NOT NULL,      -- agent name, tool, or human
    actor_kind     text NOT NULL DEFAULT 'agent'
        CHECK (actor_kind IN ('human','agent','tool','unknown')),
    approved_by    text,
    batch          text,               -- e.g. group1-pilot

    -- DID IT VERIFY
    verified       boolean,
    verify_method  text,               -- md5 / sha256 / count / none
    verify_detail  text,

    reason         text,
    occurred_at    timestamptz NOT NULL DEFAULT now(),
    recorded_at    timestamptz NOT NULL DEFAULT now(),
    ledger_ref     text,               -- source ledger file this came from
    attrs          jsonb NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS mv_item_idx    ON inventory.movement (item_id, occurred_at);
CREATE INDEX IF NOT EXISTS mv_action_idx  ON inventory.movement (action);
CREATE INDEX IF NOT EXISTS mv_actor_idx   ON inventory.movement (actor);
CREATE INDEX IF NOT EXISTS mv_batch_idx   ON inventory.movement (batch);
CREATE INDEX IF NOT EXISTS mv_frompath_idx ON inventory.movement (from_path);
CREATE INDEX IF NOT EXISTS mv_topath_idx   ON inventory.movement (to_path);

COMMENT ON TABLE inventory.movement IS
  'Append-only provenance. Every observed move/copy/quarantine, from where, '
  'to where, by whom, verified or not. Never UPDATE - append a correction.';
