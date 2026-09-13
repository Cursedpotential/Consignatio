-- Case Bible atomic-root and orphan-fragment detection.
-- Byline: Codex · GPT-5 · 2026-09-12.
--
-- Inventory-only operation. This script does not open object bytes, copy or move
-- source objects, choose canonical copies, delete anything, or create a B2 plan.

DO $atomic$
DECLARE
    v_run uuid := uuidv7();
    v_count bigint;
BEGIN
    INSERT INTO inventory.atomic_detection_run(id, rules_version, scope, status, notes)
    VALUES (
        v_run,
        'atomic-boundary-v2',
        'r2+gdrive+onedrive',
        'running',
        'Owner-approved 2026-09-12: individual Facebook/Takeout roots are atomic; collection parents are controlled-consolidation boundaries; internal Facebook fragments remain members when contained and become review flags only when orphaned.'
    );

    CREATE TEMP TABLE _atomic_source_path (
        store text NOT NULL,
        account text,
        container text NOT NULL,
        path text NOT NULL,
        parts text[] NOT NULL
    ) ON COMMIT DROP;

    INSERT INTO _atomic_source_path(store, account, container, path, parts)
    SELECT 'r2', NULL, bucket, normalized, string_to_array(normalized, '/')
    FROM (
        SELECT bucket, replace(path, E'\\', '/') AS normalized
        FROM raw_duck.r2_files
        WHERE path ~* '(facebook|(^|[/\\])fb([ _.-]|[/\\])|meta[- _][0-9]|your_facebook_activity|take[ _.-]*out|google[ _-]*takeout|/messages( \([0-9]+\))?/|facebookuser_|facebook_payments|facebook_accounts_center|apps_and_websites_off_of_facebook|fb_img_)'
    ) s;

    INSERT INTO _atomic_source_path(store, account, container, path, parts)
    SELECT 'gdrive', account, 'drive', normalized, string_to_array(normalized, '/')
    FROM (
        SELECT account, replace(path, E'\\', '/') AS normalized
        FROM gdrive.gd_net_rw
        WHERE path ~* '(facebook|(^|[/\\])fb([ _.-]|[/\\])|meta[- _][0-9]|your_facebook_activity|take[ _.-]*out|google[ _-]*takeout|/messages( \([0-9]+\))?/|facebookuser_|facebook_payments|facebook_accounts_center|apps_and_websites_off_of_facebook|fb_img_)'
    ) s;

    -- catalog.od_manifest contains duplicate scan cohorts; collapse them here.
    INSERT INTO _atomic_source_path(store, account, container, path, parts)
    SELECT 'onedrive', 'od', 'drive', normalized, string_to_array(normalized, '/')
    FROM (
        SELECT DISTINCT replace(path, E'\\', '/') AS normalized
        FROM catalog.od_manifest
        WHERE path ~* '(facebook|(^|[/\\])fb([ _.-]|[/\\])|meta[- _][0-9]|your_facebook_activity|take[ _.-]*out|google[ _-]*takeout|/messages( \([0-9]+\))?/|facebookuser_|facebook_payments|facebook_accounts_center|apps_and_websites_off_of_facebook|fb_img_)'
    ) s;

    CREATE INDEX _atomic_source_path_lookup_idx
        ON _atomic_source_path(store, container, account, path);
    ANALYZE _atomic_source_path;

    CREATE TEMP TABLE _atomic_detected (
        store text NOT NULL,
        account text,
        container text NOT NULL,
        root_path text NOT NULL,
        unit_type text NOT NULL,
        detection_basis text NOT NULL,
        boundary_confidence text NOT NULL,
        handling_mode text NOT NULL,
        review_state text NOT NULL,
        marker_path text NOT NULL
    ) ON COMMIT DROP;

    -- A: individually named Facebook exports, including owner-style names.
    INSERT INTO _atomic_detected
    SELECT s.store, s.account, s.container, array_to_string(s.parts[1:i], '/'),
           'facebook_dyi', 'individual Facebook export directory name',
           'high', 'preserve_whole', 'confirmed', s.path
    FROM _atomic_source_path s
    CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS i
    WHERE i < array_length(s.parts, 1)
      AND s.parts[i] ~* '^facebook[- _].*20[0-9]{2}([ _.-]|$)';

    -- A: canonical internal tree marker; its parent is the package boundary.
    INSERT INTO _atomic_detected
    SELECT s.store, s.account, s.container, array_to_string(s.parts[1:i-1], '/'),
           'facebook_dyi', 'your_facebook_activity tree',
           'high', 'preserve_whole', 'confirmed', s.path
    FROM _atomic_source_path s
    CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS i
    WHERE i > 1 AND lower(s.parts[i]) = 'your_facebook_activity';

    -- B: messy Facebook parents are protected while their contents are cleaned,
    -- reconstructed and deduplicated. They are not migrate-as-is selections.
    INSERT INTO _atomic_detected
    SELECT s.store, s.account, s.container, array_to_string(s.parts[1:i], '/'),
           'facebook_deconstruction',
           'owner-approved Facebook collection/deconstruction directory name',
           'review', 'controlled_consolidation', 'confirmed', s.path
    FROM _atomic_source_path s
    CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS i
    WHERE i < array_length(s.parts, 1)
      AND (
          lower(s.parts[i]) ~ '^(fb[ _-]*(data|exports?)|facebook[ _-]*(data|exports?)|katrina[ _-]*fb[ _-]*data|facebook)$'
          OR lower(s.parts[i]) ~ '^meta[- _]20[0-9]{2}[- _][a-z]{3,9}[- _][0-9]{2}'
      );

    -- Loose messages/message (N) roots are controlled-consolidation parents only
    -- when no approved Facebook boundary already contains them. Individual threads
    -- remain members and are not migration candidates.
    INSERT INTO _atomic_detected
    SELECT s.store, s.account, s.container, array_to_string(s.parts[1:i], '/'),
           'facebook_deconstruction', 'loose Facebook-shaped messages tree',
           'review', 'controlled_consolidation', 'confirmed', s.path
    FROM _atomic_source_path s
    CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS i
    WHERE i < array_length(s.parts, 1)
      AND lower(s.parts[i]) ~ '^messages( \([0-9]+\))?$'
      AND NOT EXISTS (
          SELECT 1
          FROM generate_subscripts(s.parts, 1) AS prior(j)
          WHERE prior.j < i
            AND (
                lower(s.parts[prior.j]) = 'your_facebook_activity'
                OR s.parts[prior.j] ~* '^facebook[- _].*20[0-9]{2}([ _.-]|$)'
                OR lower(s.parts[prior.j]) ~ '^(fb[ _-]*(data|exports?)|facebook[ _-]*(data|exports?)|katrina[ _-]*fb[ _-]*data|facebook)$'
                OR lower(s.parts[prior.j]) ~ '^meta[- _]20[0-9]{2}[- _][a-z]{3,9}[- _][0-9]{2}'
            )
      );

    -- C: individual Takeout packages. Nested and oddly named versions remain
    -- visible; parent linkage below records the nesting without flattening it.
    INSERT INTO _atomic_detected
    SELECT s.store, s.account, s.container, array_to_string(s.parts[1:i], '/'),
           'google_takeout', 'owner-approved individual Takeout directory name',
           'high', 'preserve_whole', 'confirmed', s.path
    FROM _atomic_source_path s
    CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS i
    WHERE i < array_length(s.parts, 1)
      AND s.parts[i] ~* 'take[ _.-]*out'
      AND lower(s.parts[i]) !~ 'timeline[- _]takeout[- _]ingestor'
      AND lower(s.parts[i]) !~ '^(takeout data1?|google[ _-]*takeout( files.*)?|google_takeout)$';

    -- D: Takeout collection parents are controlled-consolidation containers.
    INSERT INTO _atomic_detected
    SELECT s.store, s.account, s.container, array_to_string(s.parts[1:i], '/'),
           'opaque_nested_root',
           'owner-approved Takeout collection wrapper directory name',
           'review', 'controlled_consolidation', 'confirmed', s.path
    FROM _atomic_source_path s
    CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS i
    WHERE i < array_length(s.parts, 1)
      AND lower(s.parts[i]) ~ '^(takeout data1?|google[ _-]*takeout( files.*)?|google_takeout)$';

    -- Structural package types outside the Facebook/Takeout name exception.
    INSERT INTO _atomic_detected
    SELECT 'r2', NULL, bucket, regexp_replace(path, '/[^/]+$', ''),
           'chat_export', 'archive_browser.html marker',
           'high', 'preserve_whole', 'candidate', path
    FROM raw_duck.r2_files
    WHERE lower(name) = 'archive_browser.html';

    INSERT INTO _atomic_detected
    SELECT 'r2', NULL, bucket, regexp_replace(path, '/[^/]+$', ''),
           'code_repository', 'repository manifest outside dependency trees',
           'medium', 'preserve_whole', 'candidate', path
    FROM raw_duck.r2_files
    WHERE lower(name) IN ('pyproject.toml','go.mod','cargo.toml','package.json')
      AND path !~* '/(node_modules|site-packages|vendor|\.venv|venv)/';

    -- Every archive remains an explicit provenance candidate. An archive nested
    -- under a package is linked to that package and is not independently copied.
    INSERT INTO _atomic_detected
    SELECT 'r2', NULL, bucket, path, 'archive_file',
           'archive extension; relationship to extraction unproven',
           'high', 'archive_provenance', 'candidate', path
    FROM raw_duck.r2_files
    WHERE lower(path) ~ '\.(zip|tar|tgz|gz|7z|rar)$';

    INSERT INTO _atomic_detected
    SELECT 'gdrive', account, 'drive', path, 'archive_file',
           'archive extension; relationship to extraction unproven',
           'high', 'archive_provenance', 'candidate', path
    FROM gdrive.gd_net_rw
    WHERE lower(path) ~ '\.(zip|tar|tgz|gz|7z|rar)$';

    INSERT INTO _atomic_detected
    SELECT 'onedrive', 'od', 'drive', path, 'archive_file',
           'archive extension; relationship to extraction unproven',
           'high', 'archive_provenance', 'candidate', path
    FROM (SELECT DISTINCT path FROM catalog.od_manifest) z
    WHERE lower(path) ~ '\.(zip|tar|tgz|gz|7z|rar)$';

    -- Collapse repeated markers into one candidate boundary per run.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_count, marker_paths,
        review_state, handling_mode, attrs)
    SELECT v_run, store, account, container, root_path, unit_type,
           string_agg(DISTINCT detection_basis, '; ' ORDER BY detection_basis),
           CASE WHEN bool_or(boundary_confidence = 'high') THEN 'high' ELSE 'review' END,
           count(DISTINCT marker_path), jsonb_build_array(min(marker_path)),
           CASE WHEN bool_or(review_state = 'confirmed') THEN 'confirmed' ELSE 'candidate' END,
           handling_mode,
           CASE WHEN bool_or(review_state = 'confirmed')
                THEN jsonb_build_object('owner_classification_approved_at', '2026-09-12')
                ELSE '{}'::jsonb END
    FROM _atomic_detected
    WHERE root_path <> ''
    GROUP BY store, account, container, root_path, unit_type, handling_mode;

    -- E: these are ordinary members when an approved Facebook root contains them.
    -- Only genuinely orphaned occurrences become review flags. No individual
    -- message thread is promoted to a migration candidate by this rule.
    WITH folder_fragments AS (
        SELECT s.store, s.account, s.container, s.path,
               array_to_string(s.parts[1:i], '/') AS fragment_path,
               s.parts[i] AS fragment_name,
               'directory'::text AS node_kind
        FROM _atomic_source_path s
        CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS i
        WHERE i < array_length(s.parts, 1)
          AND lower(s.parts[i]) ~ '^(facebookuser_[0-9]+|facebook_payments|facebook_accounts_center|apps_and_websites_off_of_facebook)$'
    ), file_fragments AS (
        SELECT s.store, s.account, s.container, s.path,
               s.path AS fragment_path,
               s.parts[array_length(s.parts, 1)] AS fragment_name,
               'file'::text AS node_kind
        FROM _atomic_source_path s
        WHERE lower(s.parts[array_length(s.parts, 1)]) ~ '^fb_img_'
    ), fragments AS (
        SELECT * FROM folder_fragments
        UNION ALL
        SELECT * FROM file_fragments
    ), orphans AS (
        SELECT f.*
        FROM fragments f
        WHERE NOT EXISTS (
            SELECT 1
            FROM inventory.atomic_unit_candidate c
            WHERE c.run_id = v_run
              AND c.store = f.store
              AND c.container = f.container
              AND coalesce(c.account, '') = coalesce(f.account, '')
              AND c.unit_type IN ('facebook_dyi', 'facebook_deconstruction')
              AND (f.path = c.root_path OR f.path LIKE c.root_path || '/%')
        )
    )
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_count, marker_paths,
        review_state, handling_mode, attrs)
    SELECT v_run, store, account, container, fragment_path,
           'orphaned_export_fragment',
           'Facebook-associated fragment outside an approved Facebook atomic boundary',
           'review', count(DISTINCT path), jsonb_build_array(min(path)),
           'needs_review', 'investigate_orphan',
           jsonb_build_object('node_kind', node_kind, 'fragment_name', min(fragment_name))
    FROM orphans
    GROUP BY store, account, container, fragment_path, node_kind;

    -- Record the nearest enclosing candidate. This preserves nested versions and
    -- prevents nested archives/packages from being treated as independent copies.
    WITH ancestry AS (
        SELECT child.id AS child_id, parent.id AS parent_id,
               row_number() OVER (
                   PARTITION BY child.id
                   ORDER BY ancestor.i DESC
               ) AS preference
        FROM inventory.atomic_unit_candidate child
        CROSS JOIN LATERAL generate_subscripts(
            string_to_array(child.root_path, '/'), 1
        ) AS ancestor(i)
        JOIN inventory.atomic_unit_candidate parent
          ON parent.run_id = child.run_id
         AND parent.store = child.store
         AND parent.container = child.container
         AND coalesce(parent.account, '') = coalesce(child.account, '')
         AND parent.root_path = array_to_string(
             (string_to_array(child.root_path, '/'))[1:ancestor.i], '/')
         AND parent.id <> child.id
        WHERE child.run_id = v_run
          AND ancestor.i < array_length(string_to_array(child.root_path, '/'), 1)
    ), nearest AS (
        SELECT child_id, parent_id
        FROM ancestry
        WHERE preference = 1
    )
    UPDATE inventory.atomic_unit_candidate child
    SET parent_candidate_id = nearest.parent_id
    FROM nearest
    WHERE child.id = nearest.child_id;

    -- Account evidence is attached to the deepest enclosing Takeout candidate.
    -- It remains an observation; no candidate account is finalized here.
    WITH known(account_handle, compact_handle) AS (
        VALUES
            ('matt.salemnet', 'mattsalemnet'),
            ('matt.salem85', 'mattsalem85'),
            ('caminstaller', 'caminstaller'),
            ('salemnma', 'salemnma'),
            ('katrina95xo', 'katrina95xo'),
            ('katrinasalem95', 'katrinasalem95')
    ), identity_source AS (
        SELECT s.*,
               regexp_replace(lower(s.path), '[^a-z0-9]+', '', 'g') AS compact_path
        FROM _atomic_source_path s
        WHERE s.path ~* '(matt[._ -]*salem(net|85)|caminstaller|salemnma|katrina95xo|katrinasalem95)'
    ), candidate_hits AS (
        SELECT s.path, k.account_handle, a.id AS subject_account_id,
               CASE
                   WHEN lower(s.path) ~ '/google account/[^/]*(subscriberinfo|changehistory)'
                   THEN 'strong'
                   ELSE 'hint'
               END AS confidence,
               c.id AS candidate_id,
               row_number() OVER (
                   PARTITION BY s.store, s.account, s.container, s.path, k.account_handle
                   ORDER BY ancestor.i DESC
               ) AS preference
        FROM identity_source s
        JOIN known k
          ON position(k.compact_handle IN s.compact_path) > 0
        JOIN inventory.takeout_subject_account a
          ON a.account_handle = k.account_handle
        CROSS JOIN LATERAL generate_subscripts(s.parts, 1) AS ancestor(i)
        JOIN inventory.atomic_unit_candidate c
          ON c.run_id = v_run
         AND c.store = s.store
         AND c.container = s.container
         AND coalesce(c.account, '') = coalesce(s.account, '')
         AND c.unit_type IN ('google_takeout', 'opaque_nested_root')
         AND c.root_path = array_to_string(s.parts[1:ancestor.i], '/')
    ), hits AS (
        SELECT path, account_handle, subject_account_id, confidence, candidate_id
        FROM candidate_hits
        WHERE preference = 1
    )
    INSERT INTO inventory.atomic_identity_evidence(
        candidate_id, subject_account_id, observed_identifier, evidence_kind,
        source_path, confidence, review_state, attrs)
    SELECT DISTINCT candidate_id, subject_account_id, account_handle,
           'internal_filename', path, confidence, 'unreviewed',
           jsonb_build_object(
               'assignment_effect', 'evidence_only',
               'content_not_read', true)
    FROM hits;

    -- Parse original-looking multipart archive names without assuming that the
    -- observed parts form a complete set or that the subject account is known.
    WITH archive_rows AS (
        SELECT c.*,
               regexp_replace(c.root_path, '^.*/', '') AS filename,
               regexp_match(
                   regexp_replace(c.root_path, '^.*/', ''),
                   '(?i)^takeout-([0-9]{8}T[0-9]{6}Z)-([0-9]+)-([0-9]{3})\.(zip|tgz|tar\.gz)$'
               ) AS parsed
        FROM inventory.atomic_unit_candidate c
        WHERE c.run_id = v_run
          AND c.unit_type = 'archive_file'
          AND lower(c.root_path) ~ '\.(zip|tgz|tar\.gz)$'
          AND (
              c.root_path ~* 'take[ _.-]*out'
              OR EXISTS (
                  SELECT 1
                  FROM inventory.atomic_unit_candidate p
                  WHERE p.run_id = v_run
                    AND p.id = c.parent_candidate_id
                    AND p.unit_type IN ('google_takeout', 'opaque_nested_root')
              )
          )
    )
    INSERT INTO inventory.takeout_archive_part(
        run_id, archive_candidate_id, subject_state, source_series_key,
        export_timestamp_text, export_batch_ordinal, part_number,
        originality_state, archive_filename, parse_basis, attrs)
    SELECT v_run, id, 'unknown',
           CASE WHEN parsed IS NOT NULL THEN
               concat_ws('|', store, coalesce(account, ''), container, parsed[1], parsed[2])
           END,
           CASE WHEN parsed IS NOT NULL THEN parsed[1] END,
           CASE WHEN parsed IS NOT NULL THEN parsed[2]::integer END,
           CASE WHEN parsed IS NOT NULL THEN parsed[3]::integer END,
           CASE
               WHEN parsed IS NOT NULL THEN 'strong_original_name'
               WHEN filename ~* '^takeout' THEN 'possible_original_name'
               ELSE 'takeout_context'
           END,
           filename,
           CASE
               WHEN parsed IS NOT NULL THEN 'standard Takeout timestamp/batch/part filename'
               WHEN filename ~* '^takeout' THEN 'nonstandard Takeout archive filename'
               ELSE 'archive located inside a detected Takeout boundary'
           END,
           jsonb_build_object(
               'subject_account_assignment_required', true,
               'filename_only', true)
    FROM archive_rows;

    WITH coverage AS (
        SELECT source_series_key,
               min(part_number) AS min_part,
               max(part_number) AS max_part,
               count(DISTINCT part_number) AS observed_parts
        FROM inventory.takeout_archive_part
        WHERE run_id = v_run AND source_series_key IS NOT NULL
        GROUP BY source_series_key
    )
    UPDATE inventory.takeout_archive_part p
    SET observed_set_state = CASE
        WHEN c.min_part = 1 AND c.observed_parts = c.max_part
            THEN 'observed_contiguous_from_one'
        WHEN c.min_part = 1
            THEN 'observed_gapped'
        ELSE 'observed_partial'
    END,
        attrs = p.attrs || jsonb_build_object(
            'observed_min_part', c.min_part,
            'observed_max_part', c.max_part,
            'observed_distinct_parts', c.observed_parts)
    FROM coverage c
    WHERE p.run_id = v_run
      AND p.source_series_key = c.source_series_key;

    -- A same-stem directory/archive pairing is only a review hint. Hash/member
    -- evidence is required before confirming that a tree came from an archive.
    INSERT INTO inventory.atomic_candidate_relation(
        from_candidate_id, to_candidate_id, relation_type, confidence,
        evidence_basis, review_state, attrs)
    SELECT extracted.id, archive.id, 'possible_extraction_of', 'hint',
           'same normalized basename within the same source container',
           'unreviewed', jsonb_build_object('content_not_compared', true)
    FROM inventory.atomic_unit_candidate extracted
    JOIN inventory.atomic_unit_candidate archive
      ON archive.run_id = extracted.run_id
     AND archive.store = extracted.store
     AND archive.container = extracted.container
     AND coalesce(archive.account, '') = coalesce(extracted.account, '')
     AND archive.unit_type = 'archive_file'
     AND lower(regexp_replace(archive.root_path, '^.*/', '')) ~ '\.(zip|tgz|tar\.gz)$'
     AND lower(regexp_replace(extracted.root_path, '^.*/', '')) =
         lower(regexp_replace(regexp_replace(archive.root_path, '^.*/', ''), '\.(zip|tgz|tar\.gz)$', '', 'i'))
    WHERE extracted.run_id = v_run
      AND extracted.unit_type = 'google_takeout';

    SELECT count(*) INTO v_count
    FROM inventory.atomic_unit_candidate
    WHERE run_id = v_run;

    UPDATE inventory.atomic_detection_run
    SET status = 'completed', candidate_count = v_count, completed_at = now(),
        notes = notes || ' Candidate roots only; member inventory, completeness, selected conversation threads, canonical-copy selection, and B2 transfer remain unevaluated.'
    WHERE id = v_run;
END
$atomic$;
