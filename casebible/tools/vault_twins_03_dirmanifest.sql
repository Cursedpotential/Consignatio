-- vault_twins_03_dirmanifest.sql
-- Directory manifest for vault/v1, depth 1-4: file count, total bytes, and
-- content signatures (path+size, and content-hash where known), per directory.
-- Also persists the per-file/per-ancestor-directory expansion
-- (raw_duck.vault_twins_dir_files) so step 3 (pairwise overlap) can reuse it
-- without re-deriving directory ancestors from vault_objects.
-- Byline: Claude Code · Sonnet 5 · 2026-09-16

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_dir_files (
  dir_path text NOT NULL,
  depth    int  NOT NULL,
  rel      text NOT NULL,
  key      text NOT NULL,
  size     bigint,
  sha1     text,
  md5      text
);
TRUNCATE raw_duck.vault_twins_dir_files;

INSERT INTO raw_duck.vault_twins_dir_files (dir_path, depth, rel, key, size, sha1, md5)
SELECT array_to_string(s.segs[1:depth.d], '/') AS dir_path,
       depth.d AS depth,
       array_to_string(s.segs[depth.d + 1:s.n], '/') AS rel,
       vo.key, vo.size, vo.sha1, vo.md5
FROM raw_duck.vault_objects vo
CROSS JOIN LATERAL (SELECT string_to_array(vo.key, '/') AS segs) s0
CROSS JOIN LATERAL (SELECT s0.segs AS segs, array_length(s0.segs, 1) AS n) s
CROSS JOIN LATERAL generate_series(1, LEAST(s.n - 1, 4)) AS depth(d)
WHERE s.n > 1;

CREATE INDEX IF NOT EXISTS vault_twins_dir_files_dir_idx ON raw_duck.vault_twins_dir_files (depth, dir_path);
CREATE INDEX IF NOT EXISTS vault_twins_dir_files_relsize_idx ON raw_duck.vault_twins_dir_files (rel, size);

CREATE TABLE IF NOT EXISTS raw_duck.vault_twins_dirs (
  dir_path          text NOT NULL,
  depth             int  NOT NULL,
  file_count        bigint,
  total_bytes       numeric,
  hashed_file_count bigint,
  path_size_sig     text,
  content_sig       text,
  PRIMARY KEY (depth, dir_path)
);
TRUNCATE raw_duck.vault_twins_dirs;

INSERT INTO raw_duck.vault_twins_dirs (dir_path, depth, file_count, total_bytes, hashed_file_count, path_size_sig, content_sig)
SELECT dir_path, depth,
       count(*) AS file_count,
       sum(size) AS total_bytes,
       count(*) FILTER (WHERE sha1 IS NOT NULL OR md5 IS NOT NULL) AS hashed_file_count,
       md5(string_agg(rel || ':' || size::text, chr(10) ORDER BY rel)) AS path_size_sig,
       md5(string_agg(rel || ':' || coalesce(sha1, 'md5:' || md5, 'NOHASH'), chr(10) ORDER BY rel)) AS content_sig
FROM raw_duck.vault_twins_dir_files
GROUP BY dir_path, depth;

CREATE INDEX IF NOT EXISTS vault_twins_dirs_depth_idx ON raw_duck.vault_twins_dirs (depth);

SELECT depth, count(*) AS dirs, sum(file_count) AS files, round(sum(total_bytes)/1024.0/1024/1024, 1) AS gb
FROM raw_duck.vault_twins_dirs GROUP BY depth ORDER BY depth;
