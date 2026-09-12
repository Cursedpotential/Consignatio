-- Append a high-confidence atomic-root detection run.
-- This creates candidates only. It does not populate members, select winners,
-- alter files, or plan B2 transfers.

DO $atomic$
DECLARE
    v_run uuid := uuidv7();
    v_count bigint;
BEGIN
    INSERT INTO inventory.atomic_detection_run(id, rules_version, scope, status, notes)
    VALUES (v_run, 'atomic-boundary-v1', 'r2+gdrive+onedrive', 'running',
            'High-confidence structural markers; folder names alone do not establish disposition.');

    -- R2 Facebook DYI: the structural marker is your_facebook_activity.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_count, marker_paths, handling_mode)
    SELECT v_run, 'r2', NULL, bucket,
           regexp_replace(path, '(?i)/your_facebook_activity/.*$', ''),
           'facebook_dyi', 'your_facebook_activity tree', 'high', count(*),
           coalesce(
             jsonb_agg(path ORDER BY path) FILTER (WHERE lower(name) IN ('start_here.html','index.html')),
             '[]'::jsonb), 'preserve_whole'
    FROM raw_duck.r2_files
    WHERE path ~* '(^|/)your_facebook_activity/'
    GROUP BY bucket, regexp_replace(path, '(?i)/your_facebook_activity/.*$', '');

    -- R2 Google Takeout: retain the named Takeout root as the package boundary.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_count, handling_mode)
    SELECT v_run, 'r2', NULL, bucket, root_path, 'google_takeout',
           'Takeout tree plus export structure', 'high', count(*), 'preserve_whole'
    FROM (
        SELECT bucket, path,
               substring(path from '(?i)^(.*(?:^|/)takeout(?: [^/]*)?)(?:/|$)') AS root_path
        FROM raw_duck.r2_files
        WHERE path ~* '(^|/)takeout([^/]*)/'
    ) s
    WHERE root_path IS NOT NULL
    GROUP BY bucket, root_path;

    -- R2 chat/browser export packages.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_paths, handling_mode)
    SELECT v_run, 'r2', NULL, bucket,
           regexp_replace(path, '/[^/]+$', ''), 'chat_export',
           'archive_browser.html marker', 'high', jsonb_build_array(path), 'preserve_whole'
    FROM raw_duck.r2_files
    WHERE lower(name) = 'archive_browser.html';

    -- Standalone repository candidates. Dependency/vendor manifests are excluded;
    -- outer export/package boundaries take precedence during membership assignment.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_paths, handling_mode)
    SELECT v_run, 'r2', NULL, bucket,
           regexp_replace(path, '/[^/]+$', ''), 'code_repository',
           'repository manifest outside dependency trees', 'medium', jsonb_build_array(path), 'preserve_whole'
    FROM raw_duck.r2_files
    WHERE lower(name) IN ('pyproject.toml','go.mod','cargo.toml','package.json')
      AND path !~* '/(node_modules|site-packages|vendor|\.venv|venv)/';

    -- Every archive is atomic provenance. Nested archives may later be linked to
    -- an outer package; they are never independently copied when already covered.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_paths, handling_mode)
    SELECT v_run, 'r2', NULL, bucket, path, 'archive_file',
           'archive extension; relationship to extraction unproven', 'high',
           jsonb_build_array(path), 'archive_provenance'
    FROM raw_duck.r2_files
    WHERE lower(ext) IN ('zip','tar','tgz','gz','7z','rar');

    -- Facebook message trees that lack the normal your_facebook_activity wrapper
    -- are preserved at their weird export/deconstruction root for later work.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_count, handling_mode)
    SELECT v_run, 'r2', NULL, bucket,
           regexp_replace(path, '(?i)/messages/.*$', ''),
           'facebook_deconstruction',
           'Facebook message tree without standard DYI wrapper', 'review',
           count(*), 'defer_dissection'
    FROM raw_duck.r2_files
    WHERE path ~* '/messages/(inbox|archived_threads|filtered_threads)/'
      AND path !~* '(^|/)your_facebook_activity/'
    GROUP BY bucket, regexp_replace(path, '(?i)/messages/.*$', '');

    -- Google Drive high-confidence markers.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_count, handling_mode)
    SELECT v_run, 'gdrive', account, 'drive', root_path, unit_type,
           basis, confidence, count(*), 'preserve_whole'
    FROM (
        SELECT account, path,
               CASE
                 WHEN path ~* '(^|/)your_facebook_activity/' THEN
                   regexp_replace(path, '(?i)/your_facebook_activity/.*$', '')
                 WHEN path ~* '(^|/)takeout([^/]*)/' THEN
                   substring(path from '(?i)^(.*(?:^|/)takeout(?: [^/]*)?)(?:/|$)')
               END AS root_path,
               CASE WHEN path ~* '(^|/)your_facebook_activity/' THEN 'facebook_dyi'
                    ELSE 'google_takeout' END AS unit_type,
               CASE WHEN path ~* '(^|/)your_facebook_activity/' THEN 'your_facebook_activity tree'
                    ELSE 'Takeout tree plus export structure' END AS basis,
               'high' AS confidence
        FROM gdrive.gd_net_rw
        WHERE path ~* '(^|/)(your_facebook_activity|takeout([^/]*))/'
    ) s
    WHERE root_path IS NOT NULL
    GROUP BY account, root_path, unit_type, basis, confidence;

    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_paths, handling_mode)
    SELECT v_run, 'gdrive', account, 'drive', regexp_replace(path, '/[^/]+$', ''),
           'chat_export', 'archive_browser.html marker', 'high', jsonb_build_array(path), 'preserve_whole'
    FROM gdrive.gd_net_rw
    WHERE lower(name) = 'archive_browser.html';

    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_paths, handling_mode)
    SELECT v_run, 'gdrive', account, 'drive', path, 'archive_file',
           'archive extension; relationship to extraction unproven', 'high',
           jsonb_build_array(path), 'archive_provenance'
    FROM gdrive.gd_net_rw
    WHERE lower(split_part(name, '.', -1)) IN ('zip','tar','tgz','gz','7z','rar');

    -- OneDrive: only structural Facebook/Takeout markers, deduplicated across the
    -- duplicated manifest scans. No tree name is treated as disposition authority.
    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_count, handling_mode)
    SELECT v_run, 'onedrive', 'od', 'drive', root_path, unit_type,
           basis, 'high', count(*), 'preserve_whole'
    FROM (
        SELECT DISTINCT path,
               CASE
                 WHEN path ~* '(^|/)your_facebook_activity/' THEN
                   regexp_replace(path, '(?i)/your_facebook_activity/.*$', '')
                 ELSE substring(path from '(?i)^(.*(?:^|/)takeout(?: [^/]*)?)(?:/|$)')
               END AS root_path,
               CASE WHEN path ~* '(^|/)your_facebook_activity/' THEN 'facebook_dyi'
                    ELSE 'google_takeout' END AS unit_type,
               CASE WHEN path ~* '(^|/)your_facebook_activity/' THEN 'your_facebook_activity tree'
                    ELSE 'Takeout tree plus export structure' END AS basis
        FROM catalog.od_manifest
        WHERE path ~* '(^|/)(your_facebook_activity|takeout([^/]*))/'
    ) s
    WHERE root_path IS NOT NULL
    GROUP BY root_path, unit_type, basis;

    INSERT INTO inventory.atomic_unit_candidate(
        run_id, store, account, container, root_path, unit_type,
        detection_basis, boundary_confidence, marker_paths, handling_mode)
    SELECT v_run, 'onedrive', 'od', 'drive', path, 'archive_file',
           'archive extension; relationship to extraction unproven', 'high',
           jsonb_build_array(path), 'archive_provenance'
    FROM (
        SELECT DISTINCT path
        FROM catalog.od_manifest
        WHERE lower(split_part(path, '.', -1)) IN ('zip','tar','tgz','gz','7z','rar')
    ) z;

    SELECT count(*) INTO v_count
    FROM inventory.atomic_unit_candidate WHERE run_id = v_run;

    UPDATE inventory.atomic_detection_run
    SET status='completed', candidate_count=v_count, completed_at=now(),
        notes=notes || ' Candidate roots only; membership/completeness/selection not yet evaluated.'
    WHERE id=v_run;
END
$atomic$;
