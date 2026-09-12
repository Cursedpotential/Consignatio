-- canon-registry-0007-DRAFT.sql  (DRAFT — prod DDL, owner approval required before apply)
-- Byline: Claude Code (ORCHESTRATOR) · Fable 5 · 2026-07-02
--
-- WHY: the 2026-06-26 pilot's H2 hash recipe ran from an agent scratchpad and is
-- now LOST (chain-verifiable, never recomputable). This migration makes recipe
-- loss structurally impossible going forward:
--   (1) public.canon_registry — every algorithm/recipe as data, WITH test
--       vectors, so any implementation can be verified or reconstructed;
--   (2) analysis.processing_run.code_ref — every durable-writing run must name
--       the tracked code that produced it (specs/ path + sha256, or repo + git sha);
--       a run without code_ref may no longer claim replayable=true.
--
-- Apply (owner's hand):
--   ssh -i ~/.ssh/ovh ubuntu@100.119.96.29 "docker exec -i agentos-db-ipy7vrw61jjsw0ktou2qr20f-055743909530 psql -U ai -d ai -v ON_ERROR_STOP=1 -f -" < D:/casebible/casebible-coordination/specs/canon-registry-0007-DRAFT.sql
-- Undo: DROP TABLE public.canon_registry; ALTER TABLE analysis.processing_run DROP CONSTRAINT processing_run_replayable_needs_code_ref, DROP COLUMN code_ref;

\set ON_ERROR_STOP on
BEGIN;

-- 1) the canon registry: recipes as data, append-only by convention
CREATE TABLE IF NOT EXISTS public.canon_registry (
    id              uuid PRIMARY KEY DEFAULT uuidv7(),
    canon_name      text NOT NULL,              -- e.g. 'h2-canonical-v2'
    family          text NOT NULL,              -- e.g. 'custody-hash', 'dedup', 'scoring'
    status          text NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'superseded', 'lost')),
    recipe          text NOT NULL,              -- exact, human-readable formula
    reference_impl  text,                       -- tracked path of the implementation
    test_vectors    jsonb NOT NULL DEFAULT '[]'::jsonb,  -- [{inputs..., expected}]
    notes           text,
    established_at  timestamptz NOT NULL DEFAULT now(),
    superseded_by   uuid REFERENCES public.canon_registry(id),
    UNIQUE (canon_name)
);
COMMENT ON TABLE public.canon_registry IS
  'Every algorithm/recipe that produces durable artifacts, as data with test vectors. '
  'NEVER change a recipe in place — add a new canon_name version and mark the old one superseded.';

-- 2) seed: the custody-hash canon family (state as proven/declared 2026-07-02)
INSERT INTO public.canon_registry (canon_name, family, status, recipe, reference_impl, test_vectors, notes) VALUES
('h1-rawbytes-v1', 'custody-hash', 'active',
 'sha256(raw file bytes), streaming',
 'Agno-MCP-Platform/evidence/custody.py::_sha256_file + case-bible plugin tools/cb_custody_chain.py',
 '[{"input_file": "pilot imessage:+18108532989 index.html (325065 bytes)",
    "expected": "8173f2d3977e2dd7920e7fef4284b0ea6a292db00ff921f4dab638e056c69f71"}]'::jsonb,
 'H1 = custody identity: dedupe key, blob path, evidence.evidence_hash row.'),

('h3-chain-v1', 'custody-hash', 'active',
 'entry_hash = sha256(utf8(previous_hash_hex || h2_hash_hex)); genesis previous_hash = the H1 file hash; final entry = chain head, sealed in evidence_hash.meta.chain_head',
 'case-bible plugin tools/cb_custody_chain.py::h3_entry',
 '[{"previous_hash": "8173f2d3977e2dd7920e7fef4284b0ea6a292db00ff921f4dab638e056c69f71",
    "h2_hash": "bcd2b404aa3838e9eb1024a6708e56e6cd8185b271e1e8b29acba42472b167cb",
    "expected": "bc6538b346c192af04f5cdf2f0f42b766f2a95070307fc2aa0f495462ad34016"},
   {"previous_hash": "8173f2d3977e2dd7920e7fef4284b0ea6a292db00ff921f4dab638e056c69f71",
    "h2_hash": "b6b3b4a557d4d02c60168a00d8edc233b68f3a1c14b514b545faddef2904ff46",
    "expected": "676bd4e40eb3556d052ac03782854e5018819aecca855a9664e60eceb9351ca9"}]'::jsonb,
 'PROVEN 2026-07-02 by reverse-engineering vs pilot data: 1918/1918 links recomputed, head matches sealed value.'),

('h2-filebound-v1', 'custody-hash', 'lost',
 'UNKNOWN — "sha256 of the canonical message including the file hash" (pilot doc); exact serialization irrecoverable (~1.5M candidates exhausted 2026-07-02)',
 NULL,
 '[{"file_hash": "8173f2d3977e2dd7920e7fef4284b0ea6a292db00ff921f4dab638e056c69f71",
    "sequence_number": 0, "role": "them", "content": "Oh haaaay.",
    "occurred_at_original": "2019-02-21 05:03 PM", "occurred_at_utc": "2019-02-21 22:03:00+00:00",
    "expected": "bcd2b404aa3838e9eb1024a6708e56e6cd8185b271e1e8b29acba42472b167cb"},
   {"file_hash": "8173f2d3977e2dd7920e7fef4284b0ea6a292db00ff921f4dab638e056c69f71",
    "sequence_number": 4, "role": "them", "content": "756 yes",
    "occurred_at_original": "2019-02-21 05:26 PM", "occurred_at_utc": "2019-02-21 22:26:00+00:00",
    "expected": "c4e570c4d23442a2edff311a590015b70d73b97db975cfd48d9ab174792a0874"}]'::jsonb,
 'Ran from an agent scratchpad (bestoffort-v2-2026-06-26), code died with the session. Pilot H2s stay tamper-evident via h3-chain-v1 + sealed head but cannot be recomputed. Test vectors kept for any future reconstruction attempt. THE loss that motivated this table.'),

('h2-canonical-v2', 'custody-hash', 'active',
 'sha256(utf8(file_hash_hex || ''|'' || sequence_number || ''|'' || role || ''|'' || occurred_at_utc_iso || ''|'' || content)); occurred_at_utc_iso format YYYY-MM-DD HH:MM:SS+00:00',
 'case-bible plugin tools/cb_custody_chain.py::h2_canonical_v2',
 '[{"file_hash": "8173f2d3977e2dd7920e7fef4284b0ea6a292db00ff921f4dab638e056c69f71",
    "sequence_number": 0, "role": "them", "occurred_at": "2019-01-01 00:00:00+00:00", "content": "hello",
    "expected": "b6b3b4a557d4d02c60168a00d8edc233b68f3a1c14b514b545faddef2904ff46"}]'::jsonb,
 'CURRENT canon for ALL new ingests. Fully recomputable from record content + H1.')
ON CONFLICT (canon_name) DO NOTHING;

-- 3) processing_run.code_ref: runs must name their code
ALTER TABLE analysis.processing_run ADD COLUMN IF NOT EXISTS code_ref text;
COMMENT ON COLUMN analysis.processing_run.code_ref IS
  'Tracked location of the code that performed this run: "specs/<file> sha256:<hex>" or "repo:<path>@<git sha>". Required to claim replayable=true.';

-- NOT VALID: pilot-era rows (replayable=true, code_ref NULL) stay; new rows must comply.
ALTER TABLE analysis.processing_run
  ADD CONSTRAINT processing_run_replayable_needs_code_ref
  CHECK (NOT replayable OR code_ref IS NOT NULL) NOT VALID;

-- 4) acceptance
\echo '--- canon registry seeded ---'
SELECT canon_name, family, status, jsonb_array_length(test_vectors) AS vectors FROM public.canon_registry ORDER BY canon_name;

COMMIT;
\echo '--- COMMITTED ---'
