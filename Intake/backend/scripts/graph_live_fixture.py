"""Generate a retained three-file synthetic inventory for explicit live graph proof.

Does not connect to a database. Output directory must be new; nothing is replaced.
Run graph-project-inventory separately to authorize database writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from casebible_index.fingerprints import _schema
from casebible_index.inventory import INVENTORY_SCHEMA, INVENTORY_SCHEMA_VERSION
from casebible_index.projections.inventory_manifest import CONTRACT


def generate(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    source = destination / "synthetic-source"
    source.mkdir()
    now = datetime.now(UTC)
    source_id = "synthetic-graph-proof-" + now.strftime("%Y%m%dT%H%M%S%fZ")
    rows, fingerprints = [], []
    for name in ("copy-one.txt", "copy-two.txt", "metadata-only.txt"):
        data = b"Synthetic Intake graph integration fixture. Not evidence.\n"
        path = source / name
        with path.open("xb") as stream:
            stream.write(data)
        stat = path.stat()
        row = {
            "source_id": source_id,
            "relative_path": name,
            "filename": name,
            "extension": ".txt",
            "byte_size": stat.st_size,
            "source_created_at": now,
            "source_modified_at": datetime.fromtimestamp(stat.st_mtime, UTC),
            "source_modified_ns": stat.st_mtime_ns,
            "is_symlink": False,
            "captured_at": now,
            "schema_version": INVENTORY_SCHEMA_VERSION,
        }
        rows.append(row)
        if name != "metadata-only.txt":
            fingerprints.append(
                {**row, "sha256": hashlib.sha256(data).hexdigest(), "hash_status": "hashed"}
            )
    inventory = destination / "inventory.parquet"
    fingerprint = destination / "fingerprints.parquet"
    pq.write_table(pa.Table.from_pylist(rows, schema=INVENTORY_SCHEMA), inventory)
    pq.write_table(pa.Table.from_pylist(fingerprints, schema=_schema()), fingerprint)
    manifest = {
        "schema": CONTRACT,
        "source_id": source_id,
        "declared_at": now.isoformat(),
        "store": {
            "root_locator": source.resolve().as_uri(),
            "store_kind": "synthetic-fixture",
            "label": "SYNTHETIC integration proof - not source evidence",
        },
        "inventory": {
            "path": inventory.name,
            "sha256": hashlib.sha256(inventory.read_bytes()).hexdigest(),
        },
        "fingerprints": {
            "path": fingerprint.name,
            "sha256": hashlib.sha256(fingerprint.read_bytes()).hexdigest(),
        },
    }
    manifest_path = destination / "manifest.json"
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
    return manifest_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(generate(args.destination))
