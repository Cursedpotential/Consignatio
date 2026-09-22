-- Coco Super Index object list (DuckDB dialect; the catalog is attached as `catalog`).
-- Byline: Claude Code · Opus 5 · 2026-09-18 (Build 1); resolution added 2026-09-22.
-- Must return key, size, sha1. Every other column it returns rides along into the index as
-- catalog fields (catalog_source.py); widen the index by editing this query, not the code.
-- Table built by Consignatio/casebible/tools/vault_index_source_20260918.sql.
--
-- `resolution`: the catalog has no column of that name. The nearest recorded value is the
-- first occurrence's `disposition` (e.g. "content_on_b2"), which is what says how the
-- object resolves to bytes. It is passed through unchanged, never invented.
SELECT
    key,
    size,
    sha1,
    name,
    occurrence_count,
    occurrences,
    COALESCE(json_extract_string(occurrences, '$[0].disposition'), 'unknown') AS resolution
FROM catalog.raw_duck.vault_index_source_20260918
