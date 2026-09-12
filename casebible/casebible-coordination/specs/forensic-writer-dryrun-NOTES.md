# Forensic ingest WRITER fix + rolled-back dry-run — NOTES

> _Byline: Claude Code · Opus 4.8 · 2026-07-01 · 🟥 PIPELINE lane_
> Serves TASKS 2026-07-01 (PIPELINE): "update the ingest WRITER to satisfy
> evidence_hash_subject_ck ... then a rolled-back dry-run to prove insertability."
> Ref: LOG 2026-07-01 05:50 · docs/planning/forensic-db-reconciliation/STATUS.md.

## The problem (why the old writer would now fail)
Migration `0005_forensic_reconciliation.sql` added, `NOT VALID`, to
`evidence.evidence_hash`:

```sql
ALTER TABLE evidence.evidence_hash
  ADD COLUMN level text NOT NULL DEFAULT 'H1' CHECK (level IN ('H1','H2','H3')),
  ADD COLUMN source_id uuid REFERENCES evidence.source(id),
  ADD COLUMN file_node_id uuid REFERENCES evidence.file_node(id), ... ;
ALTER TABLE evidence.evidence_hash
  ADD CONSTRAINT evidence_hash_subject_ck CHECK (
    level = 'H3' OR source_id IS NOT NULL OR file_node_id IS NOT NULL) NOT VALID;
```

`NOT VALID` = existing rows are grandfathered, but **every NEW insert is checked**.
The as-built writer (`evidence/custody.py::ingest_artifact`) inserted the H1 hash
as `(source_ref, algo, digest, blob_key, meta)` only — so `level` defaulted to
`'H1'` and `source_id` was NULL → `evidence_hash_subject_ck` **fails**, and no new
custody hash can be written. That is the "old provisional bare-hash path needs this
update" flagged in LOG 05:50.

## The fix (code, this pass — reversible/local, PIPELINE lane)
`evidence/custody.py` now writes in the correct order inside the one custody txn:

1. **`evidence.source` FIRST** — the file-level custodial source row. Required
   NOT-NULL-no-default cols: `sha256, byte_size, source_type, acquisition_source`
   (`custodian` defaults `'Matt Salem'`). Deduped on `UNIQUE(sha256)` via
   `ON CONFLICT (sha256) DO UPDATE ... RETURNING id`, so re-ingest reuses the
   same source (custody idempotency preserved).
2. **`evidence.evidence_hash` (H1)** — now carries `level='H1'`,
   `source_id=<the source>`, `canon_version='h1-rawbytes-v1'`,
   `computed_by='evidence.custody.ingest_artifact'`. digest/blob_key/meta
   unchanged → satisfies `evidence_hash_subject_ck`.
3. `analysis.normalized_record` is written downstream by `evidence/store.py`
   (`artifact_id` = the H1 hash id) — unchanged and already correct.

New helpers: `_source_fields()` derives + validates the source columns from the
existing `source_meta` dict; `source_type` / `acquisition_method` are coerced
against their CHECK sets (fallback `'other'` / `NULL`) so a stray tag never
aborts the source insert. No signature change to `ingest_artifact` — callers
(workflows/CLI) are unaffected; richer provenance flows through if `source_meta`
carries `source_type / acquisition_source / r2_bucket / r2_key / md5 / mime_type`.

## The dry-run (`forensic-writer-dryrun.sql`)
One `BEGIN … ROLLBACK` transaction that inserts the FULL path with throwaway
deterministic digests and asserts it landed, then rolls back (writes nothing
durable). It exercises all three hash levels to prove the subject CHECK end-to-end:

| step | table | level | source_id | proves |
|---|---|---|---|---|
| 1 | evidence.source | — | (new) | file-level source exists first |
| 2 | evidence.evidence_hash | H1 | set | H1 satisfies subject_ck via source_id |
| 3 | evidence.evidence_hash | H2 | set | per-message hash also carries source_id |
| 4 | evidence.evidence_hash | H3 | NULL | chain head legitimately omits source_id (level='H3') |
| 5 | analysis.normalized_record | — | — | record inserts with artifact_id = H1 id |

On success it RAISEs `DRY-RUN OK … ROLLED BACK`; any constraint violation aborts
the txn and surfaces the error (fail-loud). No real PII — participant/conversation
values are `+1XXXXXXXXXX` placeholders.

## Verification status (verify-before-claiming)
- ✅ `evidence/custody.py` parses (`ast.parse` OK).
- ✅ SQL **statically verified** against the applied DDL (live-introspection
  `PG_live_schema.sql` + `0005`): 3 distinct 32-byte digests (no unique-index
  collision); all 4 required `source` cols supplied; `source_type='chat_export'`
  & `acquisition_method='manual_export'` in their CHECK sets; H1/H2 carry
  `source_id`, H3 uses `level='H3'`; `record_type='message'` &
  `disclosure_tier='contemporaneous'` in their CHECK sets.
- ⛔ **NOT executed against live PG.** Running it needs the Tailscale→ovh3-data
  connection + `$AGNO_PG_URL` (a prod-infra connection) → GATED. It is a
  read-only-net (rolled-back) proof but still a live-DB touch, so it is queued
  for the owner/live-session rather than run unattended. Command in the file
  header.

## Next (after the dry-run passes live)
- Behavioral **detection runner** over the 1943 `analysis.normalized_record`
  rows → `analysis.pattern_finding`, using the seeded ontology
  (detection_pattern=512 / behavior_category=153 / pattern_lexicon=51). Every
  finding written `bias_caution=true, requires_human_review=true,
  review_status='unreviewed', safe_for_legal_use=false` (the legal-gate CHECK).
  Build = next pass (reversible/local; the live write is gated).
