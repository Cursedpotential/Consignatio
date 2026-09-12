# Intake filesystem index — live proof, 2026-09-11 EDT

Backend integration passed using real NVIDIA NIM, CocoIndex 1.0.21, Weaviate
1.38.7 on `http://100.91.190.107:8082`, and a temporary loopback HTTP API.
Desktop click-through is not yet verified. No actual corpus or mount was scanned.

## Results

- Only input: committed `sample_docs/correspondence/example.txt`, one fictional note.
- Collection: `IntakeSynthetic20260912T023403`; named vector `text`, explicit
  self-provided vectors (`none` vectorizer), 2048 dimensions.
- Embeddings: `nvidia/nemotron-3-embed-1b` via NVIDIA's API.
- Summary: `nvidia/nemotron-3.5-lightning-30b-a3b` via NVIDIA's API.
- Initial index: 12.94 seconds, one file observed/transformed, no failure events.
- Unchanged index: 2.07 seconds, one file observed, zero files transformed,
  no failure events. Both runs completed with state `finished`.
- Actual HTTP keyword and hybrid routes each returned the same one synthetic hit,
  correct source ID and absolute file path, finite scores 0.5230583 and 1.0.
- Parquet document has title `Synthetic scheduling note`, type `note`, document
  date `2026-01-02`, and a summary of the January 5 meeting. Content SHA-256:
  `3b9e52addd8e5c829641493040a8930d91f999f43f035b16b6504c7eca6a2385`.
- Source hash unchanged. Coverage intentionally remains `unknown`; one successful
  note is not corpus coverage, quality evaluation, or a scale benchmark.
- Initial scoped lifecycle/API/target tests: 23 passed. Expanded lifecycle/API/
  search/target/source-isolation/occurrence suite: 42 passed. Changed Python files pass Ruff.

## Bug found by live execution

The original CLI called `app.update_blocking()` without owning `coco.runtime()`.
Transformations and target writes completed, but the lifespan's final status
receipt was not emitted: it stayed `running` with initial zero counters.

The CLI now uses the documented runtime context manager, exits it before building
the active snapshot, and refuses a success receipt unless final run status is
`finished` without failure events. Regression tests check teardown ordering and
prevent publishing success for `finished_with_errors`.

First attempt and its derived objects are retained in
`output/synthetic-live-20260912T023243/` and collection
`IntakeSynthetic20260912T023243`. They were not deleted or silently replaced.
Successful proof logs, both run receipts and HTTP result payloads are retained in
`output/synthetic-live-20260912T023403/proof.json` and adjacent files, all on E:.

## Isolation and remaining work

No existing collection was written, no model ran locally, and no desktop or
unrelated worker was stopped. The temporary proof API was stopped after testing.
The runner has one file in flight, 4096-byte/text caps, eight-chunk cap, zero NIM
retries and 30-second provider timeout; subprocess timeout is 150 seconds.
There is no enforced OS memory ceiling, and the sampled process readings are not
a reliable aggregate peak measurement. Do not use this as a large-corpus runner.

Next: connect the native desktop's `INTAKE_FILESYSTEM_API_URL` to the configured
loopback API, then test the search panel and assistant search interactively.
Changing that native environment requires a fresh app launch; do not interrupt
the owner's current window without coordination. Multimodal handlers, real source
selection, resource hardening and graph work remain separate next slices.

References used: installed CocoIndex skill's programmatic runtime lifecycle;
[Weaviate named/self-provided vector documentation](https://docs.weaviate.io/weaviate/manage-collections/vector-config).
