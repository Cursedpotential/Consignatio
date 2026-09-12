# Data contract

> Byline: OpenAI Codex · 2026-09-06

## Authority and provenance

The datasets are derived review projections. They do not replace source bytes, PostgreSQL custody,
human annotations, or approval workflows. The document dataset explicitly separates:

- Source facts: relative path, filename, extension, size, SHA-256, filesystem timestamps.
- Extraction facts: method, text/page counts, status, notes.
- Machine proposals: title, document type/date, summaries, entities/topics, confidence.
- Model provenance: summary model, embedding model/dimensions, schema version, index time.

`document_id` is UUIDv5 over stable `source_id + relative_path`. `version_id` is UUIDv5 over the
document ID, source SHA-256, source modification nanoseconds, model IDs, and schema version.
`artifact_id` hashes the validated enrichment, chunk text, and embedding bytes.

## Documents

One row per immutable document artifact. Important columns include `document_date` and
`date_basis` (model proposal), `source_created_at` and `source_modified_at` (filesystem facts),
`short_summary`, `detailed_summary`, entity/topic lists, summary coverage, review state, and model
provenance.

## Chunks

One row per text chunk. The row repeats enough document metadata to return a useful hit without a
second lookup and includes exact character bounds, text SHA-256, token estimate, and a fixed-size
2,048-value embedding. DuckDB reads the Parquet field as `FLOAT[]` and casts it to the fixed-size
`FLOAT[2048]` array required by its native cosine-similarity function.

## Active snapshots

The newest active snapshot maps each currently present source-relative path to one document,
version, and artifact ID. Search always joins through this snapshot, so old immutable versions do
not appear in current results.

## Atomic unit candidates

`units.parquet` mirrors the concepts in the repository's additive PostgreSQL atomic-unit schema:
candidate root, type, detection basis, confidence, parent, handling mode, markers, member counts,
and review state. `members.parquet` assigns a file to the deepest detected boundary.
`edges.parquet` preserves nested containment and carries the no-double-copy flag.

The rules are deliberately asymmetric: structural markers may propose a boundary, but only human
review can confirm a boundary, compare package completeness, select the best copy, or authorize a
future B2 copy plan.

## File fingerprints and duplicate candidates

`fingerprints/<run>/files.parquet` is a read-only derivative of a specific path inventory. Exact
hashes are streamed from the source and accepted only if size and modified time remain stable before
and after the read. Symlink targets are never followed.

| Field | Meaning and authority |
|---|---|
| `md5` | Legacy/R2 exact-dedup compatibility; not security or custody proof |
| `sha256` | H1 `rawbytes-v1` custody-compatible digest and exact group key |
| `blake3` | Independent fast cryptographic exact digest |
| `sample_blake2b_256` | First/middle/last prefilter only; never sufficient to declare equality |
| `normalized_text_sha256` | Exact semantic-text serialization equivalence after NFKC/case/space normalization |
| `text_simhash64` | Locality-sensitive candidate fingerprint; distance is review evidence, not identity |

`hash_status` distinguishes hashed, unchanged/reused, skipped unique-size, skipped symlink,
unreadable, changed-since-inventory, and changed-during-hash cases. `copy_quality` marks zero-byte
files as `bad_zero_byte`; non-empty files are only `good_unverified` because parsing and format
integrity remain separate checks.

The run emits byte-exact groups and members, normalized-text groups, near-text pairs, whole-package
manifests, and exact package groups. Every disposition remains `review_required`; there is no
canonical or loser selection. A package manifest is complete only when every file below its atomic
root has an accepted SHA-256. Manifest identity is SHA-256 over ordered relative member path, byte
size, and member SHA-256, so different recovery roots can still compare equal while nested structure
remains part of the identity.
