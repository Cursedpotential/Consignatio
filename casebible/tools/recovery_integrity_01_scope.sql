-- recovery_integrity_01_scope.sql
-- Byline: Claude Code (Sonnet 5, general-purpose agent) · Fable 5.1 · 2026-09-16
--
-- Builds raw_duck.recovery_dump_files_20260916 from the newest vault listing
-- (raw_duck.vault_objects_20260916_r4 as of this writing -- re-check for a
-- newer vault_objects_2026% table before re-running: this script hardcodes
-- the r4 source and must be edited, not silently pointed elsewhere, if a
-- newer listing exists).
--
-- Scope: every row whose key contains a path segment matching ^recup_dir\.[0-9]+$
-- (PhotoRec recovery-dump output), per the owner decision recorded in
-- docs/decisions/2026-09-16-recovery-dump-extraction-exception.md.
--
-- recup_root = the key truncated to (and including) the DEEPEST recup_dir.N
--   segment found in the key (greedy regex picks the right-most occurrence).
-- depth = number of '/'-separated path segments in recup_root (1-indexed,
--   counting from the bucket-key root, i.e. including the "consignatio",
--   "vault", "v1" prefix segments).
-- ext = lower-cased file extension of the final path segment (empty/NULL if
--   the filename has no dot-extension).
-- dest_type = the owner's Windows-style type-directory name, per the mapping
--   below; unmapped extensions fall back to "<EXT> Files" (upper-cased ext);
--   no-extension files fall back to "No Extension".
--
-- This script is READ-ONLY against B2. It only creates/replaces a derived
-- Postgres catalog table from the existing vault_objects listing.

DROP TABLE IF EXISTS raw_duck.recovery_dump_files_20260916;

CREATE TABLE raw_duck.recovery_dump_files_20260916 AS
WITH src AS (
    SELECT
        key,
        size,
        sha1
    FROM raw_duck.vault_objects_20260916_r4
    WHERE key ~ '(^|/)recup_dir\.[0-9]+(/|$)'
),
parsed AS (
    SELECT
        key,
        size,
        sha1,
        -- greedy .* picks the right-most (deepest) recup_dir.N segment
        (regexp_match(key, '^(.*recup_dir\.[0-9]+)(/.*)?$'))[1] AS recup_root,
        regexp_replace(key, '^.*/', '') AS basename
    FROM src
)
SELECT
    key,
    size,
    sha1,
    recup_root,
    array_length(regexp_split_to_array(recup_root, '/'), 1) AS depth,
    lower(substring(basename FROM '\.([^./]+)$')) AS ext,
    CASE lower(substring(basename FROM '\.([^./]+)$'))
        WHEN 'jpg'      THEN 'JPEG Images'
        WHEN 'jpeg'     THEN 'JPEG Images'
        WHEN 'png'      THEN 'PNG Images'
        WHEN 'gif'      THEN 'GIF Images'
        WHEN 'webp'     THEN 'WebP Images'
        WHEN 'svg'      THEN 'SVG graphics'
        WHEN 'heic'     THEN 'High Efficiency Image (heic)'
        WHEN 'tif'      THEN 'Tagged Image Format (tiff)'
        WHEN 'tiff'     THEN 'Tagged Image Format (tiff)'
        WHEN 'bmp'      THEN 'Bitmap Images (bmp)'
        WHEN 'pdf'      THEN 'PDF Documents'
        WHEN 'docx'     THEN 'Word Documents (docx)'
        WHEN 'doc'      THEN 'Word Documents (doc)'
        WHEN 'xlsx'     THEN 'Excel Documents (xlsx)'
        WHEN 'xls'      THEN 'Excel Documents (xls)'
        WHEN 'pptx'     THEN 'PowerPoint Presentations (pptx)'
        WHEN 'txt'      THEN 'Text Documents (txt)'
        WHEN 'html'     THEN 'HTML Files'
        WHEN 'htm'      THEN 'HTML Files'
        WHEN 'xml'      THEN 'XML Documents'
        WHEN 'json'     THEN 'JSON Files'
        WHEN 'csv'      THEN 'CSV'
        WHEN 'md'       THEN 'Markdown Documents (md)'
        WHEN 'mp4'      THEN 'Movie Files (mp4)'
        WHEN 'mov'      THEN 'Movie Files (mov)'
        WHEN 'mkv'      THEN 'Matroska Video Files (MKV)'
        WHEN '3gp'      THEN '3GP Video Files'
        WHEN 'mp3'      THEN 'MP3 Audio'
        WHEN 'ogg'      THEN 'Ogg files'
        WHEN 'oga'      THEN 'Ogg files'
        WHEN 'wav'      THEN 'WAV Audio'
        WHEN 'm4a'      THEN 'M4A Audio'
        WHEN 'amr'      THEN 'AMR Audio'
        WHEN 'zip'      THEN 'ZIP archives'
        WHEN 'gz'       THEN 'GZIP Archives (gz)'
        WHEN 'bz2'      THEN 'BZIP2 Archives (bz2)'
        WHEN 'tar'      THEN 'TAR Archives'
        WHEN '7z'       THEN '7-Zip Archives'
        WHEN 'rar'      THEN 'RAR Archives'
        WHEN 'sqlite'   THEN 'SQLite databases'
        WHEN 'sqlite3'  THEN 'SQLite databases'
        WHEN 'db'       THEN 'SQLite databases'
        WHEN NULL       THEN 'No Extension'
        ELSE COALESCE(upper(substring(basename FROM '\.([^./]+)$')) || ' Files', 'No Extension')
    END AS dest_type
FROM parsed;

ALTER TABLE raw_duck.recovery_dump_files_20260916 ADD PRIMARY KEY (key);
CREATE INDEX ON raw_duck.recovery_dump_files_20260916 (sha1);
CREATE INDEX ON raw_duck.recovery_dump_files_20260916 (dest_type);
CREATE INDEX ON raw_duck.recovery_dump_files_20260916 (recup_root);

-- ---------------------------------------------------------------------
-- Report queries (run these separately to produce the deliverable numbers)
-- ---------------------------------------------------------------------

-- 1. Totals
-- SELECT count(*) AS files, sum(size) AS bytes,
--        count(DISTINCT recup_root) AS distinct_recup_roots
-- FROM raw_duck.recovery_dump_files_20260916;

-- 2. Count by depth of root
-- SELECT depth, count(DISTINCT recup_root) AS roots, count(*) AS files, sum(size) AS bytes
-- FROM raw_duck.recovery_dump_files_20260916
-- GROUP BY depth ORDER BY depth;

-- 3. Top 25 extensions by count, with MB
-- SELECT coalesce(ext, '(none)') AS ext, count(*) AS files,
--        round(sum(size)/1024.0/1024.0, 2) AS mb
-- FROM raw_duck.recovery_dump_files_20260916
-- GROUP BY ext ORDER BY files DESC LIMIT 25;

-- 4. Exact-hash duplicates of non-recup vault objects
-- SELECT count(*) AS recup_files_with_hash_elsewhere
-- FROM raw_duck.recovery_dump_files_20260916 r
-- WHERE r.sha1 IS NOT NULL AND EXISTS (
--     SELECT 1 FROM raw_duck.vault_objects_20260916_r4 v
--     WHERE v.sha1 = r.sha1
--       AND v.key !~ '(^|/)recup_dir\.[0-9]+(/|$)'
-- );
