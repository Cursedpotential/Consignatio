# Case Bible CocoIndex

> Byline: OpenAI Codex · 2026-09-06

This standalone app incrementally indexes text-bearing Case Bible documents, asks NVIDIA-hosted
NIM models for structured summaries and embeddings, writes portable Parquet datasets, and searches
those datasets with DuckDB. Source files are read-only. Every summary and classification is labeled
as an unreviewed machine proposal, never as evidence truth or approval authority.

The initial scope is text: plain text, Markdown, JSON/JSONL, CSV/TSV, YAML, HTML, XML, email, RTF,
DOCX, and PDFs that already contain a usable text layer. Images, audio/video, and scanned/image-only
PDFs are deliberately deferred. A path/stat inventory can still recognize those files as members of
an export package without opening their contents.

## What it produces

All outputs are immutable, timestamped or content/version-addressed Parquet:

```text
output/
  datasets/
    documents/*.parquet       one structured metadata row per document version
    chunks/*.parquet          chunk text plus FLOAT[2048] NIM embeddings
  snapshots/<run>/active_documents.parquet
  inventory/<run>/files.parquet
  atomic/<run>/
    units.parquet             review-only package boundary candidates
    members.parquet           files assigned to the deepest detected unit
    edges.parquet             parent -> nested-unit relationships
  fingerprints/<run>/
    files.parquet             streamed exact hashes + text fingerprints
    exact_groups.parquet      byte-identical SHA-256 groups
    exact_members.parquet     review-only members; no winner selected
    text_equivalent_groups.parquet
    near_text_candidates.parquet
    package_manifests.parquet deterministic whole-package fingerprints
    package_exact_groups.parquet
  receipts/*.json
  .casebible-corpus/cocoindex/ isolated incremental-processing state
```

An active snapshot identifies the current document version without deleting older derived
artifacts. This is intentional: the repository's no-delete rule is preserved, history remains
auditable, and a snapshot plus the Parquet shards can be copied to another system.

## Models verified for this build

Live NVIDIA API checks on 2026-09-06 confirmed:

- `nvidia/nemotron-3-embed-1b`: 2,048-dimensional embeddings; passage and query modes work.
- `nvidia/nemotron-3.5-lightning-30b-a3b`: chat and JSON mode work when thinking is disabled.
- `nvidia/nemotron-3-super-120b-a12b`: chat works and remains a configurable alternative.

The retired `nvidia/nemotron-3-nano-30b-a3b` is not used. Model IDs and embedding dimensions are
configuration, and changing them creates a new logical document version.

## Install and configure

```powershell
cd E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend
uv sync --extra dev
Copy-Item .env.example .env
```

Set `CASEBIBLE_SOURCE_DIR` and `CASEBIBLE_OUTPUT_DIR` in `.env`. Keep `NVIDIA_API_KEY` in the
process environment or the Windows user environment; never put it in a committed file. Text sent
for summary/embedding is processed by NVIDIA's hosted API, so choose the source scope accordingly.

## Index and summarize

Use the wrapper command for normal operation; it runs CocoIndex catch-up and writes an active
snapshot and receipt afterward.

```powershell
uv run casebible-corpus index
uv run casebible-corpus index --source 'C:\Users\matts\OneDrive\Case Bible' `
  --output 'E:\data\casebible-parquet' --source-id casebible
```

Add `--with-inventory` only when you also want a full path/stat walk and atomic-unit candidates.
That pass does not read binary file content, but it may take time on a recovery-scale tree.

Use the `casebible-corpus` wrapper for routine operation. Its executable, CocoIndex app name
(`CaseBibleCorpusNimParquet`), and state directory are intentionally separate from `ccc index`,
`ccc search`, and `~/.cocoindex_code`. The TUI also launches this module directly with an argument
array—never through `ccc` or a shell alias.

## Semantic search

```powershell
uv run casebible-corpus search "parenting time exchange schedule" --limit 10
uv run casebible-corpus serve --host 127.0.0.1 --port 8765
```

The API exposes `GET /health`, `GET /documents`, and `POST /search`. Search embeds the query with
the same NIM model, joins chunk shards to the newest active snapshot, computes DuckDB cosine
similarity, and optionally adds a small deterministic lexical reranking signal. Hits include a
relative source path and exact character offsets.

DuckDB can query the portable shards directly:

```sql
SELECT document_type, count()
FROM read_parquet('output/datasets/documents/*.parquet', union_by_name = true)
GROUP BY ALL;
```

For PostgreSQL with `pg_duckdb`, point `read_parquet` at a server-accessible local path or object
store location. Arrow writes the Parquet embedding field as a fixed-size list; DuckDB currently
reads it as `FLOAT[]`, so the search query explicitly casts it to `FLOAT[2048]` before calling
`array_cosine_similarity`. PostgreSQL remains the place for governed/canonical state if these
derived results are later promoted; these files are a portable review projection.

## Atomic and nested export units

The detector intentionally separates discovery from disposition:

```powershell
uv run casebible-corpus inventory
uv run casebible-corpus detect-units
```

It recognizes structural evidence for:

- Facebook Download Your Information roots (`your_facebook_activity`) and malformed message trees.
- Google Takeout roots, including numbered/nested variants.
- ChatGPT exports (`conversations.json` plus a companion export marker).
- iMessage exports and iOS backups (`chat.db`, message exports, or `Manifest.db` + `Info.plist`).
- Archive files and ambiguous outer collection wrappers.

Nested candidates receive parent-child edges. A child covered by a `preserve_whole` outer candidate
is marked `copy_independently=false`, preventing a later copy planner from copying nested archives
twice; children of ambiguous `defer_dissection` wrappers remain independently reviewable.
High-confidence package roots default to `preserve_whole`; malformed/ambiguous wrappers default to
`defer_dissection`. All rows remain `review_state=candidate`. Folder names are evidence for review,
not permission to move, deduplicate, or select a winner.

## Hashing, fingerprinting, and dedup review

Run inventory first, detect package boundaries, then fingerprint. The default full pass reads every
non-symlink source file but never writes source bytes:

```powershell
uv run casebible-corpus inventory
uv run casebible-corpus detect-units
uv run casebible-corpus fingerprint --scope all
```

For a faster rescue-tree reconnaissance pass, `--scope dedup-candidates` hashes only files whose
byte size occurs more than once. That is a safe exact-duplicate prefilter, but its package manifests
will remain partial when unique-size members were skipped.

The file record carries MD5 for compatibility with the existing R2 ledger, SHA-256 as the H1 raw
byte custody digest, BLAKE3 as a fast independent exact digest, and a first/middle/last BLAKE2b
sample fingerprint. Supported text also receives normalized-text SHA-256 and deterministic 64-bit
SimHash. Outputs distinguish:

- byte-exact groups (`sha256` matches);
- text-equivalent files whose serialized bytes differ;
- near-text candidates within a configurable SimHash distance; and
- complete package copies with the same deterministic member manifest.

Every group is `review_required`. MD5 and sample matches are never treated as custody proof.
Zero-byte files are `bad_zero_byte`; changed/unreadable files retain an error state and no accepted
digest. Unchanged hashes are reused only when source ID, relative path, byte size, nanosecond
modified time, and symlink state all match the prior immutable run.

Near-text output is deliberately bounded locality-sensitive candidate generation: files must share
at least one 16-bit SimHash band, bands larger than 500 members are suppressed to prevent quadratic
explosion, and the final Hamming distance must meet the configured threshold. It is useful review
evidence, not an exhaustive proof that no other near-duplicate exists.

## Terminal operator console

```powershell
uv run casebible-corpus tui
```

The keyboard-driven Textual console provides source/output controls, inventory, fingerprint scope,
atomic-unit detection, indexing/summarization, semantic search, current artifact paths, and a live
operation log. File/network/database work runs in a background worker. `Ctrl+C` cancels only the
active Case Bible child process and leaves any partial derived artifact visible for review; `q`
closes the console. It has no move, delete, winner-selection, quarantine, or evidence-promotion
action.

## Design boundaries

- No source file is written, renamed, moved, or deleted.
- Generated artifacts are immutable; a differing existing artifact causes a fail-closed error.
- Imported values and machine proposals are separate. `record_role=machine_proposal` and
  `review_state=unreviewed` are explicit columns.
- Summary coverage is recorded as `full_text` or `representative_beginning_middle_end`, with a
  coverage ratio.
- Filesystem creation/modification timestamps and model-inferred document dates are separate, with
  a date-basis field.
- Non-text package membership comes from path/stat inventory only; it is not an image/OCR claim.
- Atomic boundaries precede file-level deduplication; package fingerprints preserve whole roots and
  nested provenance before any future copy proposal.

See [the upstream example synthesis](docs/UPSTREAM-EXAMPLES-SYNTHESIS.md) and
[the data contract](docs/DATA-CONTRACT.md) for the implementation rationale and column-level model.
