# R2 to B2 migration ledger and manifest builder

This folder is a non-destructive planning component for moving the R2 corpus to
B2. It reads bounded, timestamped `*.csv.gz` rclone inventories and writes a
SQLite ledger, deterministic rclone `--files-from` lists, a transfer manifest,
and (when the Python DuckDB module is already available) Parquet table exports.
It does **not** list remotes, read object bytes, copy, move, sync, or delete.

The current destination contract is
`b2:salem-data/consignatio/intake/raw-dedupe/v1/`. This is an Intake raw physical
deduplication area. Source bucket and path are provenance; they do not confer
sorted, reviewed, accepted, evidence, or Vault status.

## Safety and meaning

- Every CSV row is retained as an occurrence. Repeated paths, snapshots, export
  copies, and corroborating representations remain visible.
- A valid MD5 plus byte size creates only an `md5_size_candidate` cohort. MD5
  is not treated as proof of identical bytes and never authorizes physical
  duplicate suppression. Every distinct source path in an unresolved candidate
  cohort is emitted conservatively. If one MD5 occurs with multiple sizes,
  every affected row is held as an independent `md5_size_conflict`.
- Duplicate transport suppression requires a conflict-free, source-bound
  SHA-256 assertion. Assertions bind the hash to the inventory occurrence,
  bucket, path, size, observed MD5, and optional source version/ETag. Multiple
  asserted SHA-256 values for one occurrence, or one SHA-256 across different
  sizes, are held rather than reconciled automatically.
- After the caller proves that the complete expected SHA ledger was imported,
  a compact frozen `(MD5, byte size) -> SHA-256` bridge may propagate that
  content identity to other occurrences in the same cohort. Inherited rows are
  labeled `inherited_md5_size_bridge`; they are never represented as directly
  hashed. Finalization fails closed on incomplete partition or record counts,
  conflicting SHA values for one MD5+size group, a SHA associated with multiple
  sizes, or a changed assertion set. The current production completion contract
  is 256 partitions and 338,318 records; those remain explicit caller-supplied
  gates rather than hidden defaults.
- Missing and malformed MD5 values are independent pending-fingerprint content
  rows. They are never collapsed by name or size.
- A candidate representative is chosen by latest inventory timestamp and then
  a documented UTF-8 ordinal sort. It is a planning observation only. It is not
  the sole transport path until SHA-256 verification, and it is never a claim
  that the file is best, complete, original, canonical, or evidentially better.
- Folder names such as `junk`, `dupe`, `duplicates`, `quarantine`, and
  `to_be_deleted` are ordinary source observations. They do not exclude a row,
  determine quality, or authorize deletion.
- Categories and atomic-unit hints are provisional, versioned path assertions.
  They can help locate Google Takeouts, Facebook exports, ChatGPT exports,
  iMessage stores, development repositories, and nested units, but a human or a
  later stronger classifier must adjudicate them.
- The ledger is resumable through append-only status events. This component
  deliberately does not execute a transfer.

## Input contract

Each gzip-compressed CSV must have a UTC timestamp in its filename, for example:

```text
r2-inventory-20260912T120000Z.csv.gz
r2-inventory_2026-09-12T12-00-00Z.csv.gz
```

The normalized consolidated format has a header with these columns (order and
capitalization may differ):

```text
bucket,path,size,md5,modtime,mimetype
```

`bucket` and `path` must be non-empty; `size` must be a non-negative integer.
MD5, modtime, and MIME type may be empty. Inventory identity is the SHA-256 of
the compressed source file, making repeated ingestion idempotent without losing
rows from genuinely different snapshots.

Native rclone output is also accepted. The exact official contract for
`--format pshtm --hash MD5 --csv` is five **headerless** fields in this order:

```text
path,size,hash,modtime,mimetype
```

Rclone does not emit the bucket. Supply it explicitly with `--source-bucket`.
The CSV parser honors standard quoting, including commas and embedded newlines.
An embedded-newline path is retained in the ledger but held from line-oriented
`--files-from` output as `held_unsafe_path`. Empty, `ERROR`, and `UNSUPPORTED`
hash results are separately recorded and held for fingerprinting. Zero-byte
objects are retained; a valid empty-content MD5 remains only a candidate, not
proof that an unhydrated placeholder is useful, canonical, or safe to suppress.
Blank separator lines emitted between exported hash-ledger partitions are not
NDJSON records and are excluded from finalization record counts. Idempotently
re-importing an older partition repairs its stored totals while retaining any
historical `held_blank_record` row as audit history. Nonblank malformed records
remain counted and held.

Reference inventory shape (this only illustrates the read-only listing command;
the migration builder itself never runs it):

```text
rclone lsf "r2:BUCKET" -R --files-only --csv --format pshtm --hash MD5 --time-format RFC3339
```

## Ledger model

```text
inventory_batch 1─* occurrence *─1 content_identity
                            │              │
                            ├─* assertion  ├─1 candidate_representative
                            └─* strong_fingerprint_assertion
                                           │
transfer_generation 1─* transfer_item *────┘
                            │      │
                            │      └─* transfer_item_occurrence ─* occurrence
                            └─* transfer_status_event
```

The transfer generation freezes the inventory-set digest, rule version,
destination, deterministic representative, and initial hold/planned status.
Status transitions are validated and appended; completed history is never
rewritten.

`transfer_item.dedupe_authority` makes the physical-copy decision explicit:
`sha256_verified` may collapse verified duplicate paths;
`md5_candidate_no_suppression` emits every distinct path; pending/conflict rows
are held. A bucket/path observed with different content identities across
snapshots is `held_source_location_drift` because a current-path copy cannot
reliably retrieve a historical version.

## Build a generation

Run from this folder. Keep runtime files on the designated E: development drive.

```powershell
$env:UV_CACHE_DIR='E:\AI_Workspace\.cache\uv'; $env:TEMP='E:\AI_Workspace\.tmp'; $env:TMP=$env:TEMP; uv run --no-project -- python -m r2_b2_manifest.cli build --ledger 'E:\AI_Workspace\runtime\r2-b2\ledger.sqlite' --output-dir 'E:\AI_Workspace\runtime\r2-b2\generation-001' --inventory 'E:\AI_Workspace\inventories\r2-inventory-20260912T120000Z.csv.gz' --generation-id 'r2-b2-2026-09-12-001'
```

For source-tree execution without installing the package, add:

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src')
```

Generated files:

- `files-from/all.txt`: source paths as `bucket/object-path`, sorted bytewise.
- `files-from/by-bucket/*.txt`: object paths relative to one source bucket.
- `files-from/buckets.csv`: exact bucket-to-list mapping.
- `transfer-manifest.csv`: every transfer item, including held items.
- `payload-mapping.csv` and `payload-mapping.jsonl`: the explicit contract for
  `remote-runtime/payload_runner.py`. A positive-size, conflict-free SHA-256
  identity has exactly one canonical row at
  `payloads/sha256/HH/FULL_SHA256`. A positive-size, addressable,
  non-conflicting occurrence without authoritative SHA-256 instead receives a
  unique `payloads/source-identity/HH/SOURCE_IDENTITY` row. The runner permits
  that row only with full source/destination SHA-256 verification; it never
  participates in canonical deduplication. Zero-byte, `_system` control-path,
  conflicting, unsafe-path, and source-location-drift rows remain held.
- `occurrence-content-map.csv` and `occurrence-content-map.jsonl`: every
  inventory occurrence mapped to its content identity and eventual payload (or
  explicit hold). SHA-256 transport deduplication therefore never erases the
  provenance of corroborating paths or repeated snapshots.
- `parquet/*.parquet`: ledger tables, only when `import duckdb` succeeds.

The files are inputs to a separately reviewed transfer runner. Never point them
at `rclone move`, `sync`, or a delete command.

## Add a strong fingerprint assertion

This records a hash that was computed elsewhere by a separately governed,
bounded byte reader or imported from a valid source SHA-256 ledger. It does not
read the object itself:

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src'); uv run --no-project -- python -m r2_b2_manifest.cli record-sha256 --ledger 'E:\AI_Workspace\runtime\r2-b2\ledger.sqlite' --occurrence 'occ:...' --sha256 '<64-hex>' --method source_sha256_ledger --verifier 'casebible-hash-ledger-v2' --verified-at '2026-09-12T16:00:00Z' --source-version '<optional-version>' --source-etag '<optional-etag>'
```

Valid methods are `source_sha256_ledger`, `streamed_byte_hash`, and
`destination_readback`. The assertion is append-only. If a later assertion
disagrees, reconciliation holds the occurrence instead of selecting a winner.

## Finalize the SHA-256 identity bridge

Only after all expected hash-ledger partitions have been imported, freeze the
compact bridge explicitly:

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src'); uv run --no-project -- python -m r2_b2_manifest.cli finalize-sha256-bridge --ledger 'E:\AI_Workspace\runtime\r2-b2\ledger.sqlite' --expected-partition-count 256 --expected-record-count 338318
```

The command compares both counts to the imported ledger, checks both conflict
classes, fingerprints the exact partition and direct-assertion sets, and then
creates one bridge row per conflict-free MD5+size group. It never clones a
direct SHA assertion onto inferred occurrences. A later import makes the frozen
bridge stale and blocks generation rather than silently extending its authority.

## Resume status

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src'); uv run --no-project -- python -m r2_b2_manifest.cli mark-status --ledger 'E:\AI_Workspace\runtime\r2-b2\ledger.sqlite' --transfer-item 'transfer:...' --status queued
```

Normal path: `planned -> queued -> copying -> copied -> verified`. Retryable
errors may return to queued/copying. Held fingerprint/conflict states cannot be
silently advanced by this tool; a future, versioned fingerprint reconciliation
must create a new generation.

## Synthetic verification

```powershell
cd 'E:\AI_Workspace\Projects\Propria\Consignatio\casebible\r2-b2-migration-codex'; $env:PYTHONPATH=(Join-Path $PWD 'src'); $env:UV_CACHE_DIR='E:\AI_Workspace\.cache\uv'; $env:TEMP=(Join-Path $PWD '.tmp'); $env:TMP=$env:TEMP; New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null; uv run --no-project -- python -m unittest discover -s tests -v
```
