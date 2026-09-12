-- forensic-writer-dryrun.sql
-- Byline: Claude Code · Opus 4.8 · 2026-07-01 · PIPELINE lane
--
-- PURPOSE: prove that the CORRECTED ingest write order
--   evidence.source  ->  evidence.evidence_hash (H1/H2 with source_id)  ->  analysis.normalized_record
-- inserts cleanly against the LIVE post-0005/0006 schema and, in particular,
-- SATISFIES the new  evidence_hash_subject_ck  CHECK
--   ( level='H3' OR source_id IS NOT NULL OR file_node_id IS NOT NULL )
-- that migration 0005 added NOT VALID (enforced on all NEW inserts).
--
-- SAFETY: the whole thing runs inside ONE transaction that ends in ROLLBACK,
-- so it writes NOTHING durable. It also RAISEs a NOTICE-only summary. If any
-- INSERT violates a constraint the transaction aborts and you see the error —
-- that is the test failing loudly (verify-before-claiming).
--
-- RUN (owner / live-connection, over Tailscale to ovh3-data):
--   psql "$AGNO_PG_URL" -v ON_ERROR_STOP=1 -f forensic-writer-dryrun.sql
-- Expect: a block of NOTICE lines ending in "DRY-RUN OK ... ROLLED BACK",
-- then "ROLLBACK". Live row counts are UNCHANGED afterwards.

\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE
  v_src   uuid;
  v_h1    uuid;
  v_h2    uuid;
  v_h3    uuid;
  v_art   uuid;
  -- deterministic throwaway digests (never collide with real evidence)
  v_sha_f bytea := decode(repeat('a1',32), 'hex');  -- file-level (H1)
  v_sha_m bytea := decode(repeat('b2',32), 'hex');  -- per-message (H2)
  v_sha_c bytea := decode(repeat('c3',32), 'hex');  -- chain head (H3)
  n_src   int;
  n_h     int;
  n_rec   int;
BEGIN
  -- 1) FILE-LEVEL SOURCE (must exist before any H1/H2 hash) -----------------
  INSERT INTO evidence.source
    (sha256, byte_size, source_type, source_platform,
     original_filename, acquisition_source, acquisition_method)
  VALUES
    (v_sha_f, 8523776, 'chat_export', 'imessage',
     'dryrun_thread.html', 'manual_export', 'manual_export')
  RETURNING id INTO v_src;

  -- 2) H1 file-level custody hash — carries level + source_id --------------
  INSERT INTO evidence.evidence_hash
    (source_ref, algo, digest, level, source_id, canon_version, computed_by, meta)
  VALUES
    ('dryrun_thread.html', 'sha256', v_sha_f, 'H1', v_src,
     'h1-rawbytes-v1', 'dryrun', '{}'::jsonb)
  RETURNING id INTO v_h1;

  -- 3) H2 per-message hash — also carries source_id (subject CHECK) --------
  INSERT INTO evidence.evidence_hash
    (source_ref, algo, digest, level, source_id, record_locator,
     canon_version, computed_by, meta)
  VALUES
    ('dryrun_thread.html#msg=1', 'sha256', v_sha_m, 'H2', v_src,
     '{"conversation_id":"+1XXXXXXXXXX","seq":1}'::jsonb,
     'h2-permsg-v1', 'dryrun', '{}'::jsonb)
  RETURNING id INTO v_h2;

  -- 4) H3 chain head — the ONLY level allowed to omit source_id -----------
  INSERT INTO evidence.evidence_hash
    (source_ref, algo, digest, level, member_hash_ids,
     canon_version, computed_by, meta)
  VALUES
    ('dryrun_thread.html#chain', 'sha256', v_sha_c, 'H3',
     ARRAY[v_h1, v_h2]::uuid[], 'h3-chain-v1', 'dryrun', '{}'::jsonb)
  RETURNING id INTO v_h3;

  -- 5) NORMALIZED_RECORD — artifact_id references the H1 hash id ----------
  INSERT INTO analysis.normalized_record
    (artifact_id, record_type, source, conversation_id, role,
     participants, content, occurred_at, disclosure_tier)
  VALUES
    (v_h1, 'message', 'imessage', '+1XXXXXXXXXX', 'Me',
     '["Me","+1XXXXXXXXXX"]'::jsonb, 'dry-run message body',
     now(), 'contemporaneous')
  RETURNING id INTO v_art;

  -- 6) PROOF: everything landed and the CHECK held -----------------------
  SELECT count(*) INTO n_src FROM evidence.source        WHERE id = v_src;
  SELECT count(*) INTO n_h   FROM evidence.evidence_hash WHERE id IN (v_h1, v_h2, v_h3);
  SELECT count(*) INTO n_rec FROM analysis.normalized_record WHERE id = v_art;

  IF n_src <> 1 OR n_h <> 3 OR n_rec <> 1 THEN
    RAISE EXCEPTION 'DRY-RUN FAILED: source=% hashes=% record=% (want 1/3/1)',
      n_src, n_h, n_rec;
  END IF;

  RAISE NOTICE 'DRY-RUN OK: source=% h1=% h2=% h3=% record=% -- all inserts satisfied evidence_hash_subject_ck; ROLLED BACK (no durable write).',
    v_src, v_h1, v_h2, v_h3, v_art;
END $$;

ROLLBACK;
