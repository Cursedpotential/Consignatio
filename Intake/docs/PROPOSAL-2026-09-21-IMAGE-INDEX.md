---
title: Image and screenshot index for Intake — proposal with live probe results
date: 2026-09-21
status: proposal — owner picks the embedder and the first run size
tags: [intake, cocoindex, weaviate, surrealdb, maxsim, colpali, jina, ocr, tesseract, screenshots, images, faces, proposal]
---

# Image and screenshot index for Intake

> _Byline: Claude Code · Fable 5.1 · 2026-09-21_

## Owner direction (2026-09-21 05:52 EDT)

Borrow from four CocoIndex examples — [image search](https://cocoindex.io/docs/examples/image-search/),
[image search with ColPali](https://cocoindex.io/docs/examples/image-search-colpali/),
[multi-format indexing](https://cocoindex.io/docs/examples/multi-format-indexing/),
[face recognition](https://cocoindex.io/docs/examples/face-recognition/) — but:

- **Weaviate** holds the vectors, scored with **MaxSim**.
- **SurrealDB** holds extracted entities and metadata.
- The embedder is a **cheap hosted** ColPali- or CLIP-class model (the servers are CPU-only).
- **Tesseract is the fallback** for text.
- Earlier the same night: screenshot text must become discoverable and searchable; original timestamps and the
  phone/camera model are critical for ordering shots of one conversation.

## What exists today

- Intake's indexer skips every image: `backend/src/casebible_index/config.py` lists no image extension and
  `extractors.py` says "OCR is intentionally deferred". Plan item CBX-P8-003 (screenshot OCR) is unbuilt.
- All four examples use the CocoIndex **v1** API (`coco.App`, `@coco.fn(memo=True)`, `mount_each`) — the same API
  Intake's `pipeline.py` already uses. They write to Qdrant; Intake already has its own Weaviate target
  (`weaviate_target.py`), so the target is swapped, not the flow shape.
- Live Weaviate (`data-weaviate-native-v1`, ovh-files) is **1.38.7** and already has these modules enabled:
  `multi2multivec-jinaai`, `multi2vec-jinaai`, `multi2vec-nvidia`, `multi2vec-voyageai`, `multi2vec-cohere`,
  `multi2vec-google`, `text2multivec-jinaai`. Multi-vector MaxSim needs no new infrastructure.
- Working tools to reuse (built 2026-09-21 in the legal workdesk, registered in ContextForge as gateway `advocatio`):
  exiftool metadata for any file, original-time resolution with named source and conflict flag, Tesseract OCR with
  line boxes. Source: `Legal-desktop/api/legal_workspace/services/{metadata,original_time,ocr}.py`.

## Live probe, one synthetic 1080×700 screenshot (2026-09-21 ~10:10 UTC, keys already in `~/.secrets`)

| Model | Result | Vector | Cost signal | Latency |
|---|---|---|---|---|
| Jina `jina-embeddings-v4`, `return_multivector: true` | works | **759 × 128 (multi-vector, MaxSim-ready)**; a text query returns 8 × 128 in the same space | 9,750 tokens per image | 4.4 s |
| Jina `jina-embeddings-v4`, single | works | 2048 | 9,750 tokens | 1.8 s |
| NVIDIA NIM `nvidia/llama-nemotron-embed-vl-1b-v2` (`input_type: passage`) | works | 2048, single | 1,802 tokens; existing NIM key | 0.9 s |
| Voyage `voyage-multimodal-3` | works | 1024, single | 756,000 pixels; account has a 150B-pixel free allowance | 0.6 s |
| NVIDIA NIM `nvidia/nvclip`, `nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1` | **404 — listed but not provisioned for this account** | — | — | — |

Not probed: Cohere embed-v4, Google Vertex multimodal, hosted ColQwen endpoints (no serverless pay-per-image offer
was found). Jina's price per token and its data-retention terms were **not confirmed from a primary page** in this
pass; a web summary calling the API "free" is not trusted here.

## Size of the job (catalog, read-only, same night)

677,730 image occurrence rows / 416 GB. Rows named like screenshots: 26,208 → **14,948 unique files, 9.04 GB**.
Every row carries `recorded_modtime` and `source_metadata` (a further original-time candidate).

Multi-vector storage is the real cost: 759 × 128 float32 ≈ 0.39 MB per image → ~5.8 GB for 14,948 screenshots,
~78 GB for 200,000 images, before compression. Weaviate's multi-vector encoding/quantization has to be switched on
for anything beyond the screenshot set. Tokens: ~146 M for the screenshot set at the probed size; tall phone
screenshots will cost more per image.

## Proposed shape

One CocoIndex v1 app beside the text indexer, reading the same catalog source:

1. **Per image** (memoized by content hash, so duplicates embed once): exiftool metadata → original time + device;
   page image → embedder → Weaviate object with a named multi-vector (`maxsim`) plus hash, path, original time.
2. **Text:** the vision embedding is primary for finding; **Tesseract fallback** supplies literal text (stored as a
   derivative, never equated with native-export text) so exact words, names and numbers are keyword-searchable.
3. **PDFs:** rendered to page images and embedded the same way (multi-format example).
4. **Faces:** one row per face with its box (face-recognition example). Separate step — it uses dlib on CPU and
   raises its own privacy questions; not in the first cut.
5. **SurrealDB:** image node → device, original-time candidates, OCR entities (people, phone numbers, dates),
   conversation-series links; the Weaviate object id is the join key.

## Decisions for the owner

1. **Embedder.** A (default): Jina v4 multi-vector — the only hosted option probed that gives true MaxSim, and
   Weaviate already has the module. B: NIM `llama-nemotron-embed-vl-1b-v2` single-vector on the existing key — cheapest
   and fastest, no MaxSim. C: both — NIM single-vector for everything, Jina multi-vector for screenshots and documents
   only.
2. **Before any evidence image leaves the servers:** confirm the chosen provider's retention/training terms from its
   own page. Not done yet.
3. **First run.** 20-file proof → the 14,948 named screenshots → wider sets only after storage compression is on.
