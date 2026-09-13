-- Normalize provider paths needed by atomic-unit detection.
-- Byline: Codex · GPT-5 · 2026-09-12.
--
-- Idempotent derived index. Source catalogs and cloud objects are read only.
-- source_variant_key identifies a metadata/hash variant; it is not a content hash.

INSERT INTO inventory.atomic_path_index(
    store, account_key, container, path, source_variant_key, name,
    byte_size, md5, mtime_text, source_row_count, source_refs)
SELECT 'r2', '', bucket, normalized_path,
       pg_catalog.md5(concat_ws(E'\x1f',
           coalesce(size::text, ''), coalesce(r2.md5, ''),
           coalesce(modtime::text, ''))),
       name, size, r2.md5, modtime::text, count(*),
       jsonb_build_array(min(_src_file))
FROM (
    SELECT bucket, replace(path, E'\\', '/') AS normalized_path,
           name, size, md5, modtime, _src_file
    FROM raw_duck.r2_files
    WHERE lower(path) ~ '\.(zip|tar|tgz|gz|7z|rar)$'
       OR path ~* '(facebook|(^|[/\\])fb([ _.-]|[/\\])|meta[- _][0-9]|your_facebook_activity|take[ _.-]*out|google[ _-]*takeout|/messages( \([0-9]+\))?/|facebookuser_|facebook_payments|facebook_accounts_center|apps_and_websites_off_of_facebook|fb_img_)'
) r2
GROUP BY bucket, normalized_path, name, size, r2.md5, modtime
ON CONFLICT (store, account_key, container, path, source_variant_key)
DO UPDATE SET
    source_row_count = EXCLUDED.source_row_count,
    source_refs = EXCLUDED.source_refs,
    indexed_at = now();

INSERT INTO inventory.atomic_path_index(
    store, account_key, container, path, source_variant_key, name,
    byte_size, md5, sha1, sha256, mtime_text, source_row_count, source_refs)
SELECT 'gdrive', account, 'drive', normalized_path,
       pg_catalog.md5(concat_ws(E'\x1f',
           coalesce(size::text, ''), coalesce(gd.md5, ''),
           coalesce(sha1, ''), coalesce(sha256, ''),
           coalesce(mod_time::text, ''))),
       name, size, gd.md5, sha1, sha256, mod_time::text, count(*),
       jsonb_build_array(min(_src_file))
FROM (
    SELECT account, replace(path, E'\\', '/') AS normalized_path,
           name, size, md5, sha1, sha256, mod_time, _src_file
    FROM gdrive.gd_net_rw
    WHERE lower(path) ~ '\.(zip|tar|tgz|gz|7z|rar)$'
       OR path ~* '(facebook|(^|[/\\])fb([ _.-]|[/\\])|meta[- _][0-9]|your_facebook_activity|take[ _.-]*out|google[ _-]*takeout|/messages( \([0-9]+\))?/|facebookuser_|facebook_payments|facebook_accounts_center|apps_and_websites_off_of_facebook|fb_img_)'
) gd
GROUP BY account, normalized_path, name, size, gd.md5, sha1, sha256, mod_time
ON CONFLICT (store, account_key, container, path, source_variant_key)
DO UPDATE SET
    source_row_count = EXCLUDED.source_row_count,
    source_refs = EXCLUDED.source_refs,
    indexed_at = now();

INSERT INTO inventory.atomic_path_index(
    store, account_key, container, path, source_variant_key, name,
    byte_size, quickxor, mtime_text, source_row_count, source_refs)
SELECT 'onedrive', 'od', 'drive', normalized_path,
       pg_catalog.md5(concat_ws(E'\x1f',
           coalesce(size::text, ''), coalesce(quickxor, ''),
           coalesce(modtime, ''))),
       regexp_replace(normalized_path, '^.*/', ''),
       size, quickxor, modtime, count(*),
       jsonb_agg(DISTINCT jsonb_build_object(
           'tree', tree, 'scan_file', scan_file, 'scanned_at', scanned_at))
FROM (
    SELECT tree, replace(path, E'\\', '/') AS normalized_path,
           size, quickxor, modtime, scan_file, scanned_at
    FROM catalog.od_manifest
    WHERE lower(path) ~ '\.(zip|tar|tgz|gz|7z|rar)$'
       OR path ~* '(facebook|(^|[/\\])fb([ _.-]|[/\\])|meta[- _][0-9]|your_facebook_activity|take[ _.-]*out|google[ _-]*takeout|/messages( \([0-9]+\))?/|facebookuser_|facebook_payments|facebook_accounts_center|apps_and_websites_off_of_facebook|fb_img_)'
) od
GROUP BY normalized_path, size, quickxor, modtime
ON CONFLICT (store, account_key, container, path, source_variant_key)
DO UPDATE SET
    source_row_count = EXCLUDED.source_row_count,
    source_refs = EXCLUDED.source_refs,
    indexed_at = now();

ANALYZE inventory.atomic_path_index;
