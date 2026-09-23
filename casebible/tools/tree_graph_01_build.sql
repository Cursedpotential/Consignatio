-- tree_graph_01_build.sql
-- Directory GRAPH of the current vault (vault_objects_20260916_r4) for the tree-by-tree restructure into the
-- Case Bible skeleton (D:/casebible/vault-sorted, domains Vault / CaseManagement / KnowledgeBase / Entities /
-- Code / Triage / Recovered / Archive). Analysis only: writes catalog tables, touches nothing on B2.
--
-- Owner 2026-09-17 08:53-09:00 EDT: _backup_import, moved, recovered, Backup … must collapse into the Case Bible
-- structure; Case Bible trees and backups are nested inside other structures; "there is no flat way to do this …
-- one directory at a time, one tree at a time"; "the last move was garbage, think it through better";
-- invoked /think:graph-thinking.
--
-- Nodes  raw_duck.tg_dirs          every directory: depth, files, bytes, distinct contents, flags
--        raw_duck.tg_nodes         candidate trees: Case Bible-shaped, backup/moved/recovered/import-shaped,
--                                  skeleton-domain-named below the root (all at any depth, >= 20 files)
-- Edges  raw_duck.tg_edge_contains node A is an ancestor of node B (nesting)
--        raw_duck.tg_edge_overlap  node A and node B (neither inside the other) share content: shared distinct
--                                  sha1, and what share of each side that is
--        raw_duck.tg_edge_home     for each node, where ELSE in the vault its content already lives, by top folder
-- Byline: Claude Code · Opus 5 · 2026-09-17

DROP TABLE IF EXISTS raw_duck.tg_files;
CREATE TABLE raw_duck.tg_files AS
SELECT substr(key, 22) AS path, size, sha1
FROM raw_duck.vault_objects_20260916_r4;
CREATE INDEX ON raw_duck.tg_files (sha1);

DROP TABLE IF EXISTS raw_duck.tg_dirs;
CREATE TABLE raw_duck.tg_dirs AS
SELECT d.dir, d.depth, count(*) AS files, sum(f.size) AS bytes, count(DISTINCT f.sha1) AS contents
FROM raw_duck.tg_files f
CROSS JOIN LATERAL (
  SELECT array_to_string((string_to_array(f.path, '/'))[1:n], '/') AS dir, n AS depth
  FROM generate_series(1, least(12, array_length(string_to_array(f.path, '/'), 1) - 1)) n
) d
GROUP BY d.dir, d.depth;
CREATE UNIQUE INDEX ON raw_duck.tg_dirs (dir);

DROP TABLE IF EXISTS raw_duck.tg_nodes;
CREATE TABLE raw_duck.tg_nodes AS
SELECT dir, depth, files, bytes, contents,
       CASE
         WHEN regexp_replace(dir, '^.*/', '') ~* '^(case ?bible|casebible)' THEN 'case_bible'
         WHEN regexp_replace(dir, '^.*/', '') ~* '(backup|^_?backup_import$|^moved$|^recovered$|^recovery|photo_recovery|^restored$|^old$|^_?dedup|^_?swept$|to_be_deleted|review_hold|^existing$)' THEN 'process'
         WHEN depth >= 2 AND regexp_replace(dir, '^.*/', '') ~ '^(Vault|Evidence|EvidenceVault|CaseManagement|Case Management|KnowledgeBase|Entities|Triage|Recovered|Context|_system)$' THEN 'domain_nested'
       END AS kind
FROM raw_duck.tg_dirs
WHERE files >= 20;
DELETE FROM raw_duck.tg_nodes WHERE kind IS NULL;
-- process containers named at the root that the owner called out, whatever their name pattern
INSERT INTO raw_duck.tg_nodes
SELECT dir, depth, files, bytes, contents, 'process'
FROM raw_duck.tg_dirs
WHERE depth = 1 AND dir IN ('_backup_import', 'moved', 'recovered', 'Backup', 'Recovered Files', 'Existing', 'onedrive', 'Archive', 'Triage')
  AND dir NOT IN (SELECT dir FROM raw_duck.tg_nodes);
CREATE UNIQUE INDEX ON raw_duck.tg_nodes (dir);

DROP TABLE IF EXISTS raw_duck.tg_edge_contains;
CREATE TABLE raw_duck.tg_edge_contains AS
SELECT a.dir AS parent, b.dir AS child
FROM raw_duck.tg_nodes a
JOIN raw_duck.tg_nodes b ON starts_with(b.dir, a.dir || '/');

-- node -> distinct content membership
DROP TABLE IF EXISTS raw_duck.tg_node_content;
CREATE TABLE raw_duck.tg_node_content AS
SELECT DISTINCT n.dir, f.sha1
FROM raw_duck.tg_nodes n
JOIN raw_duck.tg_files f ON starts_with(f.path, n.dir || '/')
WHERE f.sha1 IS NOT NULL;
CREATE INDEX ON raw_duck.tg_node_content (sha1);
CREATE INDEX ON raw_duck.tg_node_content (dir);
ANALYZE raw_duck.tg_node_content;

DROP TABLE IF EXISTS raw_duck.tg_edge_overlap;
CREATE TABLE raw_duck.tg_edge_overlap AS
SELECT a.dir AS a, b.dir AS b, count(*) AS shared,
       round(100.0 * count(*) / na.contents, 1) AS pct_of_a,
       round(100.0 * count(*) / nb.contents, 1) AS pct_of_b
FROM raw_duck.tg_node_content a
JOIN raw_duck.tg_node_content b ON a.sha1 = b.sha1 AND a.dir < b.dir
JOIN raw_duck.tg_nodes na ON na.dir = a.dir
JOIN raw_duck.tg_nodes nb ON nb.dir = b.dir
WHERE NOT starts_with(b.dir, a.dir || '/') AND NOT starts_with(a.dir, b.dir || '/')
GROUP BY a.dir, b.dir, na.contents, nb.contents
HAVING count(*) >= 10;

-- where else each node's content lives, by top-level folder outside the node
DROP TABLE IF EXISTS raw_duck.tg_edge_home;
CREATE TABLE raw_duck.tg_edge_home AS
SELECT nc.dir, split_part(f.path, '/', 1) AS other_top, count(DISTINCT nc.sha1) AS shared
FROM raw_duck.tg_node_content nc
JOIN raw_duck.tg_files f ON f.sha1 = nc.sha1 AND NOT starts_with(f.path, nc.dir || '/')
GROUP BY 1, 2
HAVING count(DISTINCT nc.sha1) >= 10;

SELECT kind, count(*) AS nodes, sum(files) FILTER (WHERE depth = 1) AS root_files FROM raw_duck.tg_nodes GROUP BY 1;
SELECT count(*) AS contains_edges FROM raw_duck.tg_edge_contains;
SELECT count(*) AS overlap_edges FROM raw_duck.tg_edge_overlap;
