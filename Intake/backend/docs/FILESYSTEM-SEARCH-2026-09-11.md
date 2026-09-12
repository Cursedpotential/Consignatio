# Filesystem search integration checkpoint — 2026-09-11

## Delivered and verified

The separate read-only `POST /filesystem/search` route now queries Weaviate using
its documented GraphQL hybrid/BM25 interface. Existing `/search` remains the older
Parquet/DuckDB route; it is not silently relabeled as Weaviate.

Request: `{"query":"missing export", "mode":"hybrid", "limit":20}`.
`mode: "keyword"` uses BM25 without an embedding provider call. Hybrid uses the
configured remote NIM query embedder and an explicit named vector. A later provider
adapter can replace NIM without changing Explorer's HTTP request shape.

Response includes `query`, `backend`, `collection`, `target_vector`, `coverage`,
and `hits`. Each hit has `object_id`, `source_id`, `source_path`, `document_id`,
`chunk_id`, `filename`, `text`, and `score`. Source identity and actual navigable
paths survive the boundary. Scores are Weaviate scores, not fabricated cosine
similarities. Coverage is explicitly `unknown`, not a claim of completeness.

Set server-side environment (no credentials in renderer):

- `INTAKE_WEAVIATE_URL`: origin, no `/v1` suffix
- `INTAKE_WEAVIATE_COLLECTION`: dedicated filesystem collection, not evidence
- `INTAKE_WEAVIATE_TEXT_VECTOR`: named text vector
- `INTAKE_WEAVIATE_API_KEY`: optional for unauthenticated isolated test service
- `INTAKE_WEAVIATE_EMBED_MODEL`: must equal `NIM_EMBED_MODEL` for hybrid
- Existing `NIM_EMBED_DIMENSIONS`, `NVIDIA_API_KEY`, and NIM connection settings

Collection properties must include the six string fields listed above; objects
must contain vectors from the same model/dimensions. Configuration assertions do
not replace live schema verification. Do not point this at an arbitrary existing
collection. GraphQL errors, bad response shapes and transport errors fail as 503;
provider error bodies are not exposed. Queries have a 20-second service timeout,
100-result limit, finite/nonzero vector checks, and no redirect following.

Verification: 12 synthetic adapter tests passed (0.84 seconds), covering keyword
and hybrid payloads, source navigation, malformed responses, provider errors,
vector validation, and invalid connection/collection configuration. No services,
workers, provider requests, source files, or cloud data were accessed by tests.

## Still required — not a completed combined index

- Live-service proof of the implemented CocoIndex v1 Weaviate target lifecycle
  described below (including failure/retry under actual service interruption).
- Register multiple filesystem stores and canonical occurrence identities so the
  same bucket exposed at V: and Y: is not treated as two independent copies.
- Publish actual per-store coverage, errors, checkpoints and freshness.
- Validate process-level memory on bounded fixtures before any corpus launch.
  File/chunk/concurrency caps are now implemented, but extracted compressed
  documents may expand inside third-party parsers before the text cap is checked.
- Verify dedicated service/schema/model and synthetic write→search end-to-end.
- Connect native Explorer search to the API, preserving source references into
  preview, navigation, selection and chat. Native access avoids renderer secrets.
- Add access control before exposing API beyond the isolated local host.
- Multimodal extraction/visual vectors and remote-filesystem abstraction remain
  additional integration work, not delivered by this text search boundary.

Skills read: installed CocoIndex v1 skill, Weaviate skill and hybrid reference.
Reference: https://docs.weaviate.io/weaviate/api/graphql/search-operators
and https://docs.weaviate.io/weaviate/api/graphql/additional-properties.

## Second slice — target population and resource controls

`weaviate_target.py` implements public CocoIndex v1 `TargetHandler.reconcile`,
`TargetActionSink.from_async_fn`, `register_root_target_states_provider`, and
`declare_target_state`. It does not use the removed v0 custom target API.

Set `INTAKE_WEAVIATE_INDEX_ENABLED=1` to opt in **after** provisioning a dedicated
collection. Startup checks its required property types and explicit `none`
named-vector configuration. No collection or schema is auto-created. The existing
CocoIndex file pipeline declares its chunks into this target after writing their
portable Parquet bundle. The API filters `active=true` for both search modes.

Each chunk ID is the existing deterministic UUID derived from document version,
chunk ordinal and text hash. Target identity also includes origin and collection.
Replayed creation/update converges on that ID. Unchanged fingerprints skip writes;
uncertain prior states reapply. HTTP failures escape the sink, leaving CocoIndex
responsible for retry/reconciliation on the next update. A removed declaration
marks the derived object `active=false`, preserving its bytes and metadata. It
never issues DELETE or modifies source files. Returning sources reactivate their
matching chunk IDs. Stale rows remain available for later audit outside search.

Resource defaults (all adjustable in server environment):

| Setting | Default |
|---|---:|
| `INTAKE_MAX_FILE_BYTES` | 8 MiB |
| `INTAKE_MAX_EXTRACTED_CHARS` | 1,000,000 characters |
| `INTAKE_MAX_CHUNKS_PER_FILE` | 512 |
| `INTAKE_MAX_INFLIGHT_FILES` | 2 CocoIndex inflight components (allowed 1–8) |

Oversized source metadata fails before reading. Actual reads stop at cap+1 to
detect growth. Crucially, `BoundedLocalFile` applies this limit to **CocoIndex's
own initial fingerprint reads**, which happen before `process_file` executes.
Violations fail explicitly rather than indexing truncated text as complete.
These are workload bounds, not an OS-enforced hard memory ceiling; parser
isolation and decompression-bomb protection remain required before arbitrary
recovery archives/documents are processed at scale.

App names are now `IntakeFilesystem_<source-id-hash>`, preventing separate source
IDs sharing output state from retiring each other's targets. **This is a new app
identity and does not reuse old `CaseBibleCorpusNimParquet` memo history**: expect
fresh work/provider cost when first explicitly run. Old state/artifacts are not
deleted. Each store must have a stable distinct source ID; V:/Y: aliases of the
same bucket must use the same identity, not be independently indexed as copies.
Concurrent writers with the same source ID are now excluded by an OS lock
(details below). Do not change target origin/collection while old declarations
remain: mismatched cleanup identity fails rather than writing into another store.

### Explicit minimum collection schema

Example name only; choose the dedicated instance's real name during provisioning:

```json
{
  "class": "IntakeFilesystemChunks",
  "properties": [
    {"name":"source_id", "dataType":["text"]},
    {"name":"source_path", "dataType":["text"]},
    {"name":"document_id", "dataType":["text"]},
    {"name":"chunk_id", "dataType":["text"]},
    {"name":"filename", "dataType":["text"]},
    {"name":"text", "dataType":["text"]},
    {"name":"embed_model", "dataType":["text"]},
    {"name":"active", "dataType":["boolean"]}
  ],
  "vectorConfig": {
    "text_nim": {
      "vectorizer":{"none":{}},
      "vectorIndexType":"hnsw",
      "vectorIndexConfig":{"distance":"cosine"}
    }
  }
}
```

Readiness requires a reachable Weaviate instance with this dedicated schema,
read/write-scoped credential, NIM credentials/model access, and matching named
vector/model/dimensions. API origin and secrets remain backend-only. No endpoint
or credential was assumed or provisioned in this change.

**Verification:** 18 scoped tests passed in 2.26 seconds; Ruff clean. Includes
actual CocoIndex v1 engine test with a recording sink, proving first declaration,
unchanged skip, then missing declaration retirement. Its small LMDB state is
retained under `backend/output/synthetic-target-tests/` on E: (16 MiB initial map)
instead of deleting test files. HTTP transport tests cover create, replay update,
retirement, resurrection and service failure. Source tests prove pre-read and
pre-fingerprint rejection. No live Weaviate, NIM or source corpus was accessed.

Protocol reference: https://cocoindex.io/docs/advanced_topics/custom_target_connector/
and object update reference: https://docs.weaviate.io/weaviate/manage-objects/update.

## Third slice — source aliases, process lock and honest run status

`source_runtime.py` holds a nonblocking OS file lock for the complete CocoIndex
lifespan, before service startup and through target application/teardown. Windows
uses `msvcrt.locking`, POSIX uses `flock`; no new dependency. A second process for
the same case-normalized source ID fails with `SourceBusyError`. Process exit
releases the OS lock. The small `.lock` file remains intentionally; its presence
does not indicate an active worker. No stale PID guessing or lock-file deletion.

Default lock directory is this backend's `output/.source-locks`, independent of
configured per-run output. `INTAKE_LOCK_DIR` can explicitly override it. All
workers referring to one source must use the same lock directory. This is a
single-machine exclusion mechanism, not a distributed/cloud lock.

`INTAKE_SOURCE_REGISTRY` points to a small explicit JSON registry. The committed
`source-registry.example.json` represents the owner's confirmed V:/Y: aliases of
the r2all combined mount, with V: as preferred read path. It is **not enabled**
automatically. Both `V:/raw/small` and `Y:/raw/small` resolve to V: and the same
source scope ID `r2all/raw/small`, without listing/accessing either mount.
V:/Y: indexing without the registry fails before source reads; conflicting custom
source IDs and ambiguous overlapping registry roots are rejected. This affects
index launch only, not ordinary Explorer browsing. Registry matching is Windows
path-aware and case-insensitive. Separate direct remote adapters remain separate.

**Scope boundary:** choose nonoverlapping index roots. Indexing a whole registered
root and separately indexing a nested subfolder are not yet unified into a single
occurrence model; they must not be launched as concurrent scopes. This minimal
registry solves equivalent mount aliases, not every nested-source overlap.

`GET /filesystem/status` reports the latest immutable run/checkpoint receipt:
source identity/path, run ID, started/reported times, state, supported files
observed, files transformed, files without usable text, and failure-event count.
It returns `coverage: "unknown"` and `unchanged_files: null`. Failure events can
include multiple engine callbacks for one underlying failure; they are not a
deduplicated failed-file count. Transform completion is not claimed as verified
remote target persistence. Reports are written at start/end, each 25 successful
transformations, and first/every 25th failure event. No per-file file rewrite.
Abrupt process termination may leave a last `running` receipt: its `reported_at`
is a checkpoint, not a liveness heartbeat. No invented completeness percentage.

The older Parquet snapshot builder and `/search` remain single-source-oriented;
their newest-snapshot behavior must not be interpreted as combined coverage.
Weaviate's new filesystem route queries the dedicated combined collection.

**Verification:** 22 targeted tests passed in 1.39 seconds, including a real child
process denied the same-source lock while the parent holds it, successful lock
reacquisition after release, mount-alias convergence without mount I/O, and honest
status serialization. All synthetic artifacts stay in backend/output on E:.
No mount access, live provider calls, or background worker startup occurred.

## Occurrence identity audit — synthetic regression

No identity correction was necessary for **independent stores**. The existing
chain is occurrence-aware:

`source_id + relative_path → document UUID → version UUID → chunk UUID → Weaviate object UUID`

`logical_version_id` includes document UUID before content hash/timestamps/models.
Chunk UUID includes that version UUID, chunk ordinal and text hash. Therefore
matching content hashes do not collapse distinct store occurrences. Artifact
fingerprints may match across stores; they are not used as Weaviate object IDs.

Added `tests/test_occurrence_identity.py`:

- Actual CocoIndex engine + actual `process_file` transforms two committed,
  byte-identical fictional fixtures in independent store directories. Only NIM
  execution and HTTP transport are mocked. Two Weaviate objects are written and
  search returns two distinct source IDs, absolute source paths and chunk IDs.
- Pure-table regression holds content hash, timestamp, relative path, extracted
  text, vectors, models and enrichment equal. Changing only store identity still
  yields distinct document/version/chunk UUIDs, while artifact hashes match.
- V:/Y: alias registry resolves matching scope to one root/identity and document
  UUID, without contacting either mount.

Native query bridge compatibility is also verified: nonblank queries with leading
and trailing whitespace are returned **exactly as received**. Only all-whitespace
queries are rejected; request normalization does not break exact query matching.

**Verification:** five focused suites total **40 passed in 2.20 seconds**; Ruff
clean. Test input fixtures contain no real corpus data. All generated Parquet/state
remains under backend/output on E:. No live provider or mounted source access.
