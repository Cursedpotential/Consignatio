# Consignatio R2 to B2 transfer runtime

This directory contains guarded physical-copy and verification modes. It does not classify
objects and does not treat names such as `junk`, `quarantine`, `duplicate`, or
`to_be_deleted` as truth. Its only input is an explicitly reviewed files-from
or payload-mapping manifest produced by the current inventory and deduplication
ledger.

- `transfer_runner.py` preserves every reviewed occurrence at its source-relative
  path. It is the conservative recovery fallback.
- `payload_runner.py` physically deduplicates reviewed representatives into
  content-addressed `payloads/` keys. It starts one rclone daemon bound only to a
  root-only Unix socket and sends structured JSON RC calls, avoiding hundreds of
  thousands of process startups and all shell interpolation of object names.

## Invariants

- Source discovery is out of scope: the runner never lists a bucket or builds a
  manifest.
- Source locators must use `r2:`.
- Destinations must remain below
  `b2:salem-data/consignatio/intake/raw-dedupe/v1/`. This namespace is an
  Intake physical-deduplication landing area. It confers no Vault, evidence,
  classification, review, or acceptance status.
- The only mutating rclone operation is immutable `copyfile`; the runner contains no
  sync, move, purge, or delete operation.
- Existing destination objects are immutable. A differing object at the same
  locator fails instead of being overwritten.
- The B2 credential is loaded internally from the root-only
  `/data/consignatio/secrets/rclone-b2.env`; credentials are never command-line
  arguments or ledger fields.
- Planned, copied-unverified, verified, and failed outcomes are append-only JSONL
  ledgers. `copied_unverified` is deliberately not called verified.
- Reusing a run ID never recopies an entry already present in either the
  copied-unverified or verified ledger. A separate `verify` run promotes only
  copied-unverified entries after downloaded destination SHA-256 matches.
- Default bounds are four transfers, four checkers, a 4 MiB rclone buffer,
  disabled multi-thread streams, a 16 MiB B2 chunk with one upload worker per
  transfer, a 512-object backlog, a 24-hour run duration, and a 2 TiB manifest
  ceiling. B2 chunk size is restricted to 8, 16, or 32 MiB and per-file B2
  upload concurrency to one or two so multipart buffering cannot silently erase
  the process memory bound. Operators may lower these bounds per run.
- Corpus execution is fail-closed. `transfer` and `verify` modes cannot run until the exact
  enable phrase is placed in the enable file after explicit approval.

## Mapped payload contract

The preferred physical-deduplication input is CSV or JSONL with these fields:

- `source_bucket`, `source_path` — one explicitly selected R2 representative.
- `content_algorithm`, `content_digest` — `sha256`, `md5`, or `unknown`.
- `source_md5`, `source_etag` — optional source assertions from the governed
  inventory/hash ledger. At least one remotely comparable SHA-256, MD5, or ETag
  assertion is required for fast copy.
- `size` — exact source bytes recorded by the governed ledger.
- `source_identity` — 64 lowercase hex characters identifying the occurrence.
- `disposition` — `canonical`, `source-identity`, or `held`.
- `destination_key` — explicit relative key below `payloads/`.

Strong SHA-256 items must use `payloads/sha256/HH/FULL_SHA256`.

`--verification fast` is the same-day bulk-copy path. It validates the current
source size and a remotely exposed hash/ETag against the manifest, performs an
immutable `copyfile`, asks rclone to write `consignatio-sha256` object metadata
for SHA-256 rows when the backend supports metadata-setting, and validates only
destination presence and size. Its terminal copy state is
`copied_unverified`; it never writes a verified receipt and never downloads the
payload merely to hash it.

`--verification full` retains the audit/probe behavior: it downloads source and
destination, computes SHA-256 for both, and writes `verified` only when they
match (and when the manifest SHA-256 matches for canonical rows). It is much
more expensive and remains the default so the fast path must be selected
explicitly. `--mode verify` is the resumable second pass: it considers only
items already in `copied_unverified.jsonl`, never invokes `copyfile`, and
promotes them to `verified.jsonl` only after full SHA-256 comparison.

MD5 never authorizes canonical equality. An MD5-only item must either be held
at `payloads/held/HH/SOURCE_IDENTITY` or copied conservatively to
`payloads/source-identity/HH/SOURCE_IDENTITY`. A positive-size unknown-digest
item may use that same source-identity namespace. Every source-identity row is
noncanonical and requires `--verification full`; a fast run containing even
one such row is rejected before the plan or daemon is created. Use a
canonical-only mapping for fast SHA-256 bulk copy. Zero-byte, unsafe,
`_system` control-path, source-location-drift, and conflicting rows stay held.
The mapping must select one representative per destination; duplicate
destination keys are rejected before the daemon starts.

The rclone daemon binds only to `/run/consignatio-r2-b2/*.sock`, inherits the
root-only B2 environment, and has no TCP listener. The Python client calls
`operations/stat`, `operations/hashsumfile`, and `operations/copyfile` over that
socket with JSON. At most eight requests may run concurrently; the default is
four. Submission stays at two worker windows so the future queue is bounded.

## Manifest contract

The manifest is UTF-8 files-from format: one path relative to the selected R2
source root per line. Blank lines and lines beginning with `#` are ignored.
Absolute paths, backslashes, traversal components, control characters, and
duplicate paths are rejected. Destination layout preserves each relative path.

Generate manifests from the governed inventory/deduplication ledger. Do not
generate them by rescanning R2 through this runtime.

## Validation

```bash
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 -m unittest -v test_transfer_runner.py test_payload_runner.py
```

## Dry run

Dry run validates inputs and asks rclone to plan the explicit manifest without
writing B2:

```bash
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 transfer_runner.py run --mode dry-run --run-id DRY_RUN_ID --manifest /absolute/path/reviewed.files-from --source-root r2:SOURCE_BUCKET --dest-root b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/SOURCE_BUCKET
```

## Isolated probe

Probe mode permits exactly one object no larger than 1 MiB. Its relative path
must start with `_system/canary/` or `_system/probe/`. Use download verification
for a byte-level comparison:

```bash
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 transfer_runner.py run --mode probe --verification download --run-id PROBE_RUN_ID --manifest /absolute/path/one-probe.files-from --source-root r2:SOURCE_BUCKET --dest-root b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/SOURCE_BUCKET
```

Mapped-payload dry-run and isolated probe:

```bash
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 payload_runner.py run --mode dry-run --run-id PAYLOAD_DRY_RUN_ID --format jsonl --mapping /absolute/path/reviewed-payloads.jsonl
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 payload_runner.py run --mode probe --run-id PAYLOAD_PROBE_ID --format jsonl --mapping /absolute/path/one-isolated-probe.jsonl
```

Dry-run mode performs validation and records the immutable plan without opening
the RC socket or reading remote objects. Probe mode permits one source no larger
than 1 MiB whose path begins `_system/canary/` or `_system/probe/`.

## Corpus execution gate

The enable file is intentionally absent. Only after explicit approval, create
`/data/consignatio/migrations/r2-to-b2/runtime/ENABLE_CORPUS_TRANSFER` with mode
`0600`, owned by root, containing exactly:

```text
ENABLE_CORPUS_TRANSFER=YES
```

Then use `--mode transfer` with a reviewed manifest. Removing or changing that
phrase closes the gate. This runtime never creates the gate itself.

Same-day bulk copy is explicit and records no false verification claim:

```bash
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 payload_runner.py run --mode transfer --verification fast --run-id PAYLOAD_RUN_ID --format jsonl --mapping /absolute/path/reviewed-payloads.jsonl
```

Resume verification later under the same immutable run ID and mapping:

```bash
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 payload_runner.py run --mode verify --run-id PAYLOAD_RUN_ID --format jsonl --mapping /absolute/path/reviewed-payloads.jsonl
```

Both `transfer` and `verify` require the corpus enable gate. Re-running fast
transfer skips copied-unverified and verified destinations. Re-running verify
skips verified destinations but retains copied-unverified destinations as its
pending set.

## Status and receipts

```bash
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 transfer_runner.py status --run-id RUN_ID
cd /data/consignatio/migrations/r2-to-b2/runtime && sudo python3 payload_runner.py status --run-id RUN_ID
```

Receipts are written below `state/RUN_ID/`:

- `run.json` — immutable roots and manifest fingerprint.
- `planned.files-from` and `planned.jsonl` — exact requested objects.
- `copied.jsonl` — objects copied during a full run and subsequently verified.
- `copied_unverified.jsonl` — fast-copy receipts with validated source
  assertions and destination stat/size, still pending downloaded SHA-256
  verification.
- `verified.jsonl` — destination objects verified by the requested method.
- `failed.jsonl` — paths not verified, including rclone result symbols.
- `held.jsonl` — mapped payloads that intentionally remain held because their
  digest state is not authorized for canonical copy.
- `attempts/ATTEMPT_ID/` — bounded command logs and rclone combined/error
  reports for reconstruction.

`size` verification is operationally cheap and checks explicit source and
destination sizes. `download` verification streams both sides for a byte-level
comparison and should be used for probes and risk-based audit samples; using it
for an entire corpus materially increases reads and transfer time.
