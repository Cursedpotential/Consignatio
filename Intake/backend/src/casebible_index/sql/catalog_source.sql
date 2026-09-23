-- Coco Super Index object list (DuckDB dialect; the catalog is attached as `catalog`).
-- Byline: Claude Code · Opus 5 · 2026-09-18 (Build 1)
-- Must return key, size, sha1. Every other column rides along into the index as catalog
-- fields (catalog_source.py); widen the index by editing this query, not the code.
-- Table built by Consignatio/casebible/tools/vault_index_source_20260918.sql.
SELECT key, size, sha1, name, occurrence_count, occurrences
FROM catalog.raw_duck.vault_index_source_20260918
