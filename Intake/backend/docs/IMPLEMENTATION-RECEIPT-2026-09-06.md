# Implementation receipt — 2026-09-06

> Byline: OpenAI Codex · 2026-09-06

## Delivered

- Standalone CocoIndex v1 text pipeline with per-file incremental memoization.
- Text extraction for plain text, Markdown, JSON/JSONL, CSV/TSV, YAML, HTML, XML, EML, RTF,
  DOCX, and text-layer PDFs; OCR, images, and other media remain deferred.
- NVIDIA-hosted NIM structured summaries with Pydantic validation and explicit machine-proposal
  provenance.
- NVIDIA-hosted NIM passage/query embeddings with dimension checks and retry/backoff.
- Immutable Parquet document/chunk shards, active snapshots, path/stat inventory, receipts, and
  DuckDB semantic/hybrid search.
- FastAPI health/document/search endpoints and Typer operator commands.
- Textual operator console for inventory, hashing, atomic discovery, indexing, and search; all long
  operations run outside the UI event loop.
- Streamed MD5/SHA-256/BLAKE3 plus sample BLAKE2b fingerprints, normalized-text SHA-256, SimHash,
  immutable duplicate reports, incremental reuse, and whole-package manifests.
- Review-only atomic package candidates, memberships, and nested containment for Facebook,
  Google Takeout, ChatGPT, iMessage/iOS backup, archives, and ambiguous recovery wrappers.
- Full upstream `examples/` synthesis pinned to CocoIndex commit
  `3b4e54c3b76a3c633a878c6ea1ae9f4ef8d15ce5`.

## Live model verification

The NVIDIA hosted endpoint was probed on 2026-09-06 without exposing the API key.

| Capability | Result |
|---|---|
| `nvidia/nemotron-3-embed-1b` | Working, 2,048 dimensions; passage/query request accepted |
| `nvidia/llama-nemotron-embed-vl-1b-v2` | Working, 2,048 dimensions; asymmetric input type required |
| `nvidia/nemotron-3.5-lightning-30b-a3b` | Working; JSON mode works with thinking disabled |
| `nvidia/nemotron-3-super-120b-a12b` | Working chat alternative |
| `nvidia/nemotron-3-nano-30b-a3b` | Retired by NVIDIA on 2026-09-01; not used |

## Verification

- `uv run ruff check .` — passed.
- `uv run pytest` — 11 passed, including exact/textual dedup, package-manifest, incremental-reuse,
  and Textual startup coverage.
- `python -m compileall -q src tests` — passed.
- Live synthetic CocoIndex catch-up — 2 documents indexed and summarized; repeat run reported both
  unchanged.
- Live synthetic semantic query — returned the two correct document chunks through DuckDB.
- Active schema audit — 2 current documents, 2 current chunks, every vector length 2,048, every
  document labeled `machine_proposal` / `unreviewed`.
- FastAPI smoke — `/health` returned 200 `ok`; `/documents` returned 200 with 2 rows.
- Inventory/atomic smoke — 2 path-only files inventoried, zero errors, and zero candidates for the
  deliberately non-package sample.
- Atomic-unit fixture test — Facebook, Takeout, ChatGPT, iMessage, archive, and nested-unit rules
  passed without reading binary content.
- Fingerprint CLI smoke — 2 files hashed with MD5/SHA-256/BLAKE3, zero errors, immutable Parquet
  reports and receipt emitted, `source_bytes_modified=false`, and a repeat run reused both hashes.
- Command isolation — `casebible-corpus` is the only installed app entry point; CocoIndex state is
  under the configured output's `.casebible-corpus/cocoindex/`, not ccc's `.cocoindex_code`.
- Secret scan — no populated API key or bearer credential found in project files.

The ignored `validation-output/` directory contains the immutable synthetic artifacts and receipts.
No real Case Bible document was sent to NVIDIA during verification. No existing repository file,
source document, database, or evidence byte was modified.

## Known boundary

This is local/static and live-API validation of the app, not a full-corpus run, PostgreSQL
registration, B2 copy plan, deployment, or Workbench integration. Atomic rows, exact groups,
textual-near matches, and package copies are discovery candidates only. Best-copy selection and any
copy action remain human-reviewed future stages.
