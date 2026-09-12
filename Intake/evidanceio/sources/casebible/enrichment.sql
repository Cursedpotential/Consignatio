select
  file_id,
  regexp_extract(coalesce(r2_relpath, source_path), '[^/]+$') as file,
  doc_type,
  proposed_domain as domain,
  relevance,
  disposition,
  confidence,
  needs_review,
  is_conversation,
  platform_source,
  date_start,
  date_end,
  bytes,
  ext,
  model,
  summary
from enrichment
