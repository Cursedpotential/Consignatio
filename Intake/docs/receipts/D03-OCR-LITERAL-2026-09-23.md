<!-- Updated by: Codex (D03 Case Bible search) | Date: 2026-09-23 | Rev: 2 | Platform: Codex / win32 | Changes: record clean PR base and rerun | Context: remote main advanced during D03 verification -->

# D03 OCR literal verification receipt

**Acceptance link:** `AC-W-W19`, `D03-C01` (bounded image search slice).
**Implementation source:** `codex/d03-ocr-literal-20260923` from Consignatio `main@0d002d46c3440a37655ecef17acab14688fbab0b`.
**Review branch:** `codex/d03-ocr-literal-pr-20260923`, with only the D03 commit transplanted onto remote `main@b2be221de35a846fe023df934d46170108c79b50`. The two unpublished local `main` commits are excluded.
**Scope:** `Intake/backend/src/casebible_index/image_search.py` and its focused tests. The source catalog, index, source files, and evidence records were not changed.

## Implemented

The image searcher treats Weaviate BM25 output as candidates. It returns an `ocr_literal` hit only when the query is a substring of retained `ocr_text` after Unicode NFC normalization, case folding, and collapsing Unicode whitespace. Punctuation remains significant; substring matching can occur within a word. The result gives the original OCR text's zero-based, end-exclusive character offsets and a nearby excerpt. It preserves `object_id`, `source_id`, `source_path`, and `content_sha256` so byte-identical occurrences remain separate results.

Single-vector and MaxSim candidates remain `visual_similarity` hits, even when their OCR field happens to contain the query. Their scores are labeled by basis and are ranked within a separate channel. No OCR span is asserted for a vector-only result. All hits report `region_status=not_recorded`; the current image index does not persist region coordinates. A BM25 candidate without a verified phrase is excluded from the literal result set. The configured result limit still bounds retrieval, so a miss does not prove absence from the source or full index.

## Reproducible checks

- `tests/test_image_search_literal.py`: four synthetic tests cover Unicode/whitespace offsets, two distinct paths with one content hash, BM25 false positives, semantic-only/vector-only results, and a long verified phrase that remains visible in the excerpt. `4 passed`.
- Focused integration with the existing occurrence fixture and filesystem API: `21 passed`.
- Full `Intake/backend` Python suite from the isolated D03 worktree: `111 passed, 2 dependency deprecation warnings`.
- Full `Intake/backend` Python suite rerun on the final review base: `123 passed, 2 dependency deprecation warnings`. Ruff and `git diff --check origin/main...HEAD` passed there.
- Ruff on the changed source and test: passed. `git diff --check`: passed.
- Official Gitleaks `8.30.0` Windows x64 release asset checksum matched the published SHA-256 `54fe94f644b832dd08e8c3a5915efb3bfa862386d59fb27ca0792cb687a83573`. `gitleaks dir --redact=100` over `Intake/backend`: about 1.59 MB scanned, no leaks found. Redacted report stored outside the branch under `E:\AI_Workspace\Projects\Propria\_worktrees\d03-temp\gitleaks-backend-dir-final.json`.
- The same official binary scanned the transplanted D03 code commit before this receipt update using `gitleaks git --redact=100 --log-opts=origin/main..HEAD`: one commit, about 11.80 KB, no leaks found. Redacted report is outside the branch at `E:\AI_Workspace\Projects\Propria\_worktrees\d03-temp\gitleaks-d03-commit.json`.
- Read-only occurrence fixture: `tests/fixtures/occurrences/store-a/note.txt` and `store-b/note.txt` have the same SHA-256 `342517e5e37df307faf82dac660c75df686b4f5904692218ca7557efee858b83`; the existing `test_occurrence_identity.py` asserts that these retain distinct occurrences. This fixture proves occurrence semantics, not image OCR accuracy.

## Open acceptance boundaries

This slice has no live corpus or deployed index proof. D02's authoritative occurrence/version/member/open locator is not yet in the image result contract; `source_id` plus relative `source_path` is provisional provenance and cannot alone authorize source opening. OCR regions are not generated or stored here, so no region is highlighted. Coverage, index freshness, partial failure/recovery, native and browser opening, and Process linkage remain separate D03/D12 acceptance work. A successful search query is not an index-completeness receipt, and nothing here accepts or promotes evidence.
