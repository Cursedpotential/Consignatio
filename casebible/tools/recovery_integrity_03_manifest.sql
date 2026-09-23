-- recovery_integrity_03_manifest.sql
-- Keep/extract/link MANIFEST for the PhotoRec recovery dumps (analysis only; nothing is copied,
-- moved or deleted on B2 by this script; materialization is a separate owner GO).
--
-- Inputs: raw_duck.recovery_dump_files_20260916 (40,304 files, built from vault_objects_20260916_r4)
--         raw_duck.recovery_integrity_20260916   (per-file integrity result, scanner v1.1.0/v1.2.0)
--         raw_duck.vault_objects_20260916_r4      (current vault listing, for destination collisions)
-- Rules:  docs/decisions/2026-09-16-recovery-dump-extraction-exception.md, plus
--         owner 2026-09-17 08:06 EDT "yes" to: program files and fonts (types with no content
--         checker) go to their own "Software Fragments/<type>/" folder, kept out of photo/doc folders.
--
-- bucket:
--   TYPE_DIR    status ok, a media/document/archive/text/database type  -> <type dir>/<file>
--   SOFTWARE    any generic "<EXT> Files" type or "No Extension", not failed -> Software Fragments/<type>/<file>
--   UNRESOLVED  status fail or zero_filled                               -> review-and-control/recovery-and-restoration/unresolved-fragments/<type>/<file>
-- action:
--   COPY        first occurrence of its content in the recovery set
--   LINK        same sha1 as an earlier recovery file: no bytes copied, occurrence recorded against the COPY row
-- Filenames are kept (PhotoRec fNNNNNNN.ext); on a destination clash (existing vault key or another
-- manifest row) the recovery folder name is appended before the extension: f123.jpg -> f123__recup_dir.96.jpg
-- Byline: Claude Code · Opus 5 · 2026-09-17

DROP TABLE IF EXISTS raw_duck.recovery_manifest_20260917;
CREATE TABLE raw_duck.recovery_manifest_20260917 (
  src_key       text PRIMARY KEY,
  recup_root    text,
  size          bigint,
  sha1          text,
  dest_type     text,
  detected_type text,
  status        text,
  reason        text,
  bucket        text,
  action        text,
  dest_key      text,
  renamed       boolean DEFAULT false
);

DROP TABLE IF EXISTS m0;
CREATE TEMP TABLE m0 AS
SELECT f.key AS src_key, f.recup_root, f.size, f.sha1, f.dest_type,
       r.detected_type, r.status, r.reason,
       regexp_replace(f.key, '^.*/', '') AS fname,
       regexp_replace(f.recup_root, '^.*/', '') AS recup_name,
       CASE
         WHEN r.status IN ('fail', 'zero_filled') THEN 'UNRESOLVED'
         -- generic types whose content is media, a document or a data archive are not software
         WHEN f.dest_type IN ('CAF Files', 'XZ Files', '7Z Files', 'RAR Files', 'LZ4 Files', 'ZST Files')
           OR r.detected_type IN ('image', 'av', 'pdf', 'sqlite') THEN 'TYPE_DIR'
         WHEN f.dest_type = 'No Extension'
           OR (f.dest_type ~ ' Files$' AND f.dest_type NOT IN ('HTML Files', 'JSON Files')) THEN 'SOFTWARE'
         ELSE 'TYPE_DIR'
       END AS bucket
FROM raw_duck.recovery_dump_files_20260916 f
JOIN raw_duck.recovery_integrity_20260916 r USING (key);

ALTER TABLE m0 ADD COLUMN folder text;
UPDATE m0 SET folder = CASE bucket
  WHEN 'TYPE_DIR'   THEN dest_type
  WHEN 'SOFTWARE'   THEN 'Software Fragments/' || dest_type
  ELSE 'review-and-control/recovery-and-restoration/unresolved-fragments/' || dest_type END;

-- within-recovery duplicates: first key per sha1 is COPY, the rest LINK
ALTER TABLE m0 ADD COLUMN action text;
UPDATE m0 SET action = 'COPY';
UPDATE m0 SET action = 'LINK'
FROM (SELECT src_key, row_number() OVER (PARTITION BY sha1 ORDER BY src_key) rn FROM m0 WHERE sha1 IS NOT NULL) d
WHERE d.src_key = m0.src_key AND d.rn > 1;

ALTER TABLE m0 ADD COLUMN dest_key text;
ALTER TABLE m0 ADD COLUMN renamed boolean DEFAULT false;
UPDATE m0 SET dest_key = 'consignatio/vault/v1/' || folder || '/' || fname WHERE action = 'COPY';
CREATE INDEX ON m0 (dest_key); ANALYZE m0;

-- clash with an existing vault object, or with another COPY row: append the recovery folder name
UPDATE m0 SET renamed = true,
  dest_key = 'consignatio/vault/v1/' || folder || '/' ||
             CASE WHEN fname ~ '\.[^.]+$'
                  THEN regexp_replace(fname, '(\.[^.]+)$', '__' || recup_name || '\1')
                  ELSE fname || '__' || recup_name END
WHERE action = 'COPY' AND (
  EXISTS (SELECT 1 FROM raw_duck.vault_objects_20260916_r4 v WHERE v.key = m0.dest_key)
  OR dest_key IN (SELECT dest_key FROM m0 WHERE action = 'COPY' GROUP BY dest_key HAVING count(*) > 1));

-- still clashing (same recup_dir.N name under two parents, e.g. fb/recup_dir.862 and
-- social backup/fb/recup_dir.862): add the first 8 hex of md5(recup_root) as well
UPDATE m0 SET
  dest_key = 'consignatio/vault/v1/' || folder || '/' ||
             CASE WHEN fname ~ '\.[^.]+$'
                  THEN regexp_replace(fname, '(\.[^.]+)$', '__' || recup_name || '_' || left(md5(recup_root), 8) || '\1')
                  ELSE fname || '__' || recup_name || '_' || left(md5(recup_root), 8) END
WHERE action = 'COPY' AND dest_key IN (SELECT dest_key FROM m0 WHERE action = 'COPY' GROUP BY dest_key HAVING count(*) > 1);

-- LINK rows point at their COPY row's destination
UPDATE m0 SET dest_key = c.dest_key
FROM (SELECT DISTINCT ON (sha1) sha1, dest_key FROM m0 WHERE action = 'COPY' AND sha1 IS NOT NULL ORDER BY sha1, src_key) c
WHERE m0.action = 'LINK' AND m0.sha1 = c.sha1;

INSERT INTO raw_duck.recovery_manifest_20260917
SELECT src_key, recup_root, size, sha1, dest_type, detected_type, status, reason, bucket, action, dest_key, renamed FROM m0;

CREATE INDEX ON raw_duck.recovery_manifest_20260917 (bucket, dest_type);
CREATE INDEX ON raw_duck.recovery_manifest_20260917 (dest_key);

-- checks
SELECT 'rows' AS k, count(*)::text AS v FROM raw_duck.recovery_manifest_20260917
UNION ALL SELECT 'scope', count(*)::text FROM raw_duck.recovery_dump_files_20260916
UNION ALL SELECT 'copy_dest_clashes_remaining', count(*)::text FROM (SELECT dest_key FROM raw_duck.recovery_manifest_20260917 WHERE action='COPY' GROUP BY dest_key HAVING count(*)>1) x
UNION ALL SELECT 'copy_dest_exists_in_vault', count(*)::text FROM raw_duck.recovery_manifest_20260917 m WHERE action='COPY' AND EXISTS (SELECT 1 FROM raw_duck.vault_objects_20260916_r4 v WHERE v.key=m.dest_key)
UNION ALL SELECT 'renamed', count(*)::text FROM raw_duck.recovery_manifest_20260917 WHERE renamed
UNION ALL SELECT 'link_rows', count(*)::text FROM raw_duck.recovery_manifest_20260917 WHERE action='LINK';

SELECT bucket, action, count(*) AS files, round(sum(size)/1024.0^3, 2) AS gb
FROM raw_duck.recovery_manifest_20260917 GROUP BY 1, 2 ORDER BY 1, 2;

SELECT bucket, regexp_replace(dest_key, '^consignatio/vault/v1/(.*)/[^/]*$', '\1') AS folder,
       count(*) AS files, round(sum(size)/1024.0^3, 2) AS gb
FROM raw_duck.recovery_manifest_20260917 WHERE action = 'COPY'
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 30;
