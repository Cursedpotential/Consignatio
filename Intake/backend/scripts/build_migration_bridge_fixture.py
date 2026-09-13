"""Build a retained synthetic R2-to-B2 generation and Intake wrapper on E:."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

MIGRATION_SRC = Path(__file__).resolve().parents[3] / "casebible" / "r2-b2-migration-codex" / "src"
sys.path.insert(0, str(MIGRATION_SRC))

from r2_b2_manifest.builder import ManifestBuilder  # noqa: E402

from casebible_index.projections.migration_manifest import CONTRACT  # noqa: E402


def main(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    inventory = destination / "r2-inventory-20260912T160000Z.csv.gz"
    rows = [
        (
            "fixture-bucket",
            "Takeout/export.zip",
            12,
            "a" * 32,
            "2026-09-01T00:00:00Z",
            "application/zip",
        ),
        (
            "fixture-bucket",
            "junk/copy.zip",
            12,
            "a" * 32,
            "2026-09-01T00:00:00Z",
            "application/zip",
        ),
        ("fixture-bucket", "unknown/file.bin", 7, "", "", "application/octet-stream"),
    ]
    with gzip.open(inventory, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("bucket", "path", "size", "md5", "modtime", "mimetype"))
        writer.writerows(rows)
    output = destination / "generation"
    with ManifestBuilder(destination / "ledger.sqlite") as builder:
        builder.ingest([inventory])
        occurrence_ids = [
            value[0]
            for value in builder.connection.execute(
                "SELECT occurrence_id FROM occurrence WHERE md5_valid=1 ORDER BY object_path"
            )
        ]
        for occurrence_id in occurrence_ids:
            builder.record_sha256(
                occurrence_id,
                "b" * 64,
                "streamed_byte_hash",
                "synthetic-fixture",
                "2026-09-12T16:01:00Z",
                source_version="fixture-v1",
                source_etag="a" * 32,
            )
        builder.build_generation(
            output,
            destination_remote="b2:",
            destination_prefix="synthetic/not-transferable",
            generation_id="synthetic-bridge-proof",
            created_at="2026-09-12T16:02:00Z",
        )
    artifact = output / "occurrence-content-map.jsonl"
    wrapper = {
        "schema": CONTRACT,
        "declared_at": "2026-09-12T16:03:00Z",
        "generation_id": "synthetic-bridge-proof",
        "destination": "b2:synthetic/not-transferable",
        "occurrence_map": {
            "path": str(artifact.relative_to(destination)).replace("\\", "/"),
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        },
    }
    path = destination / "intake-projection.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(wrapper, stream, indent=2)
    print(path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build_migration_bridge_fixture.py NEW_DESTINATION")
    main(Path(sys.argv[1]))
