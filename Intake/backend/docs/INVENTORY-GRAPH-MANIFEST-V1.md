# Explicit inventory graph projection input

Implemented 2026-09-12. This is an opt-in adapter for existing Intake inventory
and fingerprint Parquet artifacts. It does not scan source files, hash source
content, classify containers, publish a lake manifest, or move evidence.

## Input

```json
{
  "schema": "intake-inventory-projection-v1",
  "source_id": "caller-supplied-stable-store-id",
  "declared_at": "2026-09-12T20:00:00+00:00",
  "store": {
    "root_locator": "caller-supplied-source-root",
    "store_kind": "local-volume",
    "label": "Human-readable store name"
  },
  "inventory": {
    "path": "inventory/files.parquet",
    "sha256": "REPLACE_WITH_EXACT_64_LOWERCASE_HEX_CHARACTERS"
  },
  "fingerprints": {
    "path": "fingerprints/files.parquet",
    "sha256": "REPLACE_WITH_EXACT_64_LOWERCASE_HEX_CHARACTERS"
  }
}
```

`fingerprints` is optional. Paths identify existing artifact files and resolve
relative to the manifest. They never identify files to scan. The source root,
kind, label and identity are mandatory because inventory v2 does not encode
enough information to infer a store root. The caller supplies provenance rather
than the adapter guessing it. The input file SHA-256 is the checkpoint identity.
This wrapper makes no claim that the input has been published to the lake.

The manifest is limited to 64 KiB. Each artifact is limited to 10,000 rows,
128 MiB compressed and 256 MiB declared uncompressed row-group bytes. Larger
corpora require intentionally prepared batches; this command does not choose or
create those batches. Artifact hashes are checked before and after reading.
The manifest is reread after validating both inputs. Every input row is validated
before opening the graph connection.

## Mapping

| Existing value | Graph result |
|---|---|
| Explicit store root/kind/label | Snapshot-scoped `store` |
| Inventory `source_id`, case-preserved `relative_path` | One snapshot-scoped `occurrence` per observed path |
| `byte_size`, modification time, `captured_at` | Size and observation timestamps |
| Full inventory row and optional fingerprint row | Occurrence metadata preserving imported provenance |
| `is_symlink` | `other` entry kind; never followed or given content identity |
| Fingerprint `hash_status=hashed`, raw `sha256` | Global content identity, only after matching source/path/size/nanosecond modification/symlink status |
| Shared raw hash with equal byte size | One `content`, separate `occurrence_has_content` edges |
| Unhashed/skipped/failed fingerprint | Occurrence remains present, with no content edge |

Inventory v2 contains file paths only. Directory/container nodes are not invented.
No lowercasing, basename equivalence, text hash, MD5, sampled fingerprint, or
similarity score is used to collapse raw content. Duplicate source/path rows,
traversal paths, source mismatches, artifact hash mismatches, unmatched fingerprint
paths, stale hashed stat matches and contradictory sizes for one hash fail closed.

## Replay and completion

Store and occurrence record keys include the manifest digest; later observations
cannot overwrite previous observations. Global content keys use raw SHA-256.
The content record's `snapshot` points to its first-created observation; later
snapshots reference it through their own occurrences, preserving provenance.
Only raw SHA-256 and byte size are compared for global content reuse.

Snapshot facts, imported nodes and relationships use immutable CREATE plus exact
replay checks. Operation-run transitions use conditional compare-and-set updates.
Concurrent writes that do not represent the same facts fail rather than overwrite.

A snapshot record can exist for an incomplete batch. **Consumers must require its
`produced_by` edge to a completed `operation_run` before treating it as complete.**
That edge is written only after all imported nodes and relations succeed. Failed
partial batches are retained and can be replayed. No deletion or rollback erases
their observations. An exact completed replay performs reads only. The snapshot's
`projected_at` uses manifest declaration time for stable replay and records that
basis in metadata; the operation run holds actual execution start/completion times.

## Commands

From `Intake/backend`, with the installed backend environment:

```powershell
.venv/Scripts/python.exe -m casebible_index.cli graph-project-inventory E:/path/input.json
# Explicitly opt in to graph writes after validation:
.venv/Scripts/python.exe -m casebible_index.cli graph-project-inventory E:/path/input.json --apply
```

Validation mode does not need credentials or network access. Apply mode uses the
dedicated Intake endpoint and `intake_runtime` through the existing secret bridge.
No automatic CocoIndex hook is installed. Full lake publication/checkpoint orchestration
and atomic-unit projection remain separate work.

Verification: synthetic Parquet fixtures cover exact duplicates preserving all
occurrences, missing hashes, malformed hashes, row collisions, conflicting sizes,
immutable replay, and interrupted relation writes followed by successful replay.
No live corpus has been projected by this implementation task.
