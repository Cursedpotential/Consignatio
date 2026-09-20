-- Byline: Claude Code · Fable 5.1 · 2026-09-15 00:40 EDT
-- fn::handoff_write fix — owner 2026-09-15 00:25: "If it's a known bug in an app that we wrote, why not fix it?"
--
-- BUG (live since 2026-09-09): the function superseded ONE arbitrary active handoff with ANY overlapping
-- domain (LIMIT 1). It clobbered other lanes (2026-09-09/10: 4 real handoffs flipped; 2026-09-14: the
-- B2-consolidation handoff document:al3a33z0sm0w635lkaxg was superseded by an Intake handoff that merely
-- shared the 'consignatio' domain) while leaving a second overlapping handoff active.
--
-- FIX: 4th optional arg $supersedes. Explicit list wins; otherwise every ACTIVE handoff whose domain SET
-- equals $domains exactly (order/duplicates ignored). 3-arg callers keep working (trailing optional arg).
-- Recorded choice: exact-set default, not "all overlapping" (that would clobber more, not less); a lane that
-- changes its domain list passes $supersedes.
--
-- WHY THIS FILE EXISTS: this session's live DEFINE (docs MCP) and its edit of
-- Probata/probata/scripts/docstore/schema/090_docs_api.surql were both denied by the auto-mode classifier.
-- The canonical home is that .surql file (lines 359-400); apply this patch there and to the live store:
--   live:   feed this file to the docs SurrealDB (ns probata, db docs) — e.g. the docs MCP `query` tool, or
--           surreal sql --endpoint <docs url> --ns probata --db docs < docs/ops/docstore-handoff-write-fix-2026-09-15.surql
--   source: replace the fn::handoff_write block in 090_docs_api.surql with the DEFINE below, then
--           python scripts/docstore/apply_schema.py <url> probata docs
-- Proven on a throwaway SurrealDB v3.2.4 (same image as production) on ovh-files — see URGENT-TODO 2026-09-15.

DEFINE FUNCTION OVERWRITE fn::handoff_write(
  $title: string,
  $body: string,
  $domains: array<string>,
  $supersedes: none | array<record<document>>
) {
  LET $explicit = $supersedes ?? [];
  LET $wanted = array::sort::asc(array::distinct($domains));
  LET $same_set = (
    SELECT VALUE id FROM document
    WHERE doc_type = "handoff" AND status = "active"
      AND array::sort::asc(array::distinct(domains)) = $wanted
  );
  LET $prev = IF array::len($explicit) > 0 { $explicit } ELSE { $same_set };

  LET $slug = string::lowercase(string::replace($title, " ", "-"));
  LET $path = "handoff://" + $slug + "/" + <string>rand::uuid();

  LET $new = CREATE ONLY document SET
    source_path  = $path,
    title        = $title,
    doc_type     = "handoff",
    domains      = $domains,
    status       = "active",
    body         = $body,
    content_hash = crypto::sha256($body),
    authored_at  = time::now();
  LET $new_id = $new.id;

  FOR $p IN $prev {
    IF $p != $new_id AND (SELECT VALUE doc_type FROM ONLY $p) = "handoff" {
      RELATE $new_id->supersedes->$p SET at = time::now();
      UPDATE $p SET status = "superseded";
    };
  };

  RETURN {
    id: $new_id,
    superseded: $prev,
    match: IF array::len($explicit) > 0 { "explicit" } ELSE { "same_domain_set" }
  };
} COMMENT "New active handoff doc. Supersedes $supersedes when given (explicit list); otherwise every active handoff whose domain SET equals $domains exactly. Until 2026-09-15 it superseded ONE arbitrary handoff with ANY overlapping domain (LIMIT 1), which clobbered other lanes." PERMISSIONS FULL;
