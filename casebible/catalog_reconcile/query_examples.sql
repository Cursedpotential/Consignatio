-- Byline: Codex | 2026-09-20. Read-only queries for the live PostgreSQL overlay.

-- Where the known occurrences are available, with current versus historical links.
SELECT * FROM catalog_reconcile.availability_summary ORDER BY source,availability;

-- Prioritized tasks; evidence includes exact source IDs and retained version IDs.
SELECT kind,source,priority,count(*) AS items
FROM catalog_reconcile.recovery_worklist GROUP BY 1,2,3 ORDER BY 1,2,3;

-- Inspect a bounded group before any source metadata probe.
SELECT item_id,kind,source,reason,next_step,evidence
FROM catalog_reconcile.recovery_worklist
WHERE kind='relink_historical_version' ORDER BY item_id LIMIT 20;

-- Repeated physical bytes are candidates for review, not a deletion instruction.
SELECT sha1,size,physical_copies,repeated_bytes,version_ids
FROM catalog_reconcile.visible_duplicate_identities ORDER BY repeated_bytes DESC LIMIT 20;

-- Native sources whose live metadata was checked, with provisional BAS status.
SELECT source,provider_source_id,status,bas1_candidate,bas2_candidate,
       complementary_representations_to_review
FROM catalog_reconcile.bas_candidates ORDER BY source,provider_source_id;

-- Source records and original metadata remain available after byte matching.
SELECT occurrence_id,source,source_path,provider_source_id,availability,version_ids,
       source_metadata,quality_flags,bas_status
FROM catalog_reconcile.occurrences WHERE availability='historical_exact'
ORDER BY occurrence_id LIMIT 20;

-- Unresolved R2 links and retirement holds remain visible.
SELECT bucket,availability,retirement_status,count(*)
FROM catalog_reconcile.r2_occurrences GROUP BY 1,2,3 ORDER BY 1,2;

-- Zero clearances are expected in this generation.
SELECT count(*) AS unexpected_clearances FROM catalog_reconcile.r2_occurrences
WHERE retirement_status <> 'not_cleared';
