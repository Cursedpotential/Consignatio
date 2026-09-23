"""Command line interface for the manifest builder."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .builder import ManifestBuilder


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="ingest inventories and freeze a manifest generation")
    build.add_argument("--ledger", type=Path, required=True)
    build.add_argument("--output-dir", type=Path, required=True)
    build.add_argument("--inventory", type=Path, action="append", required=True)
    build.add_argument(
        "--source-bucket",
        help="required for native headerless rclone --format pshtm CSV; one bucket per invocation",
    )
    build.add_argument("--destination-remote", default="b2:")
    build.add_argument(
        "--destination-prefix", default="consignatio/intake/raw-dedupe/v1"
    )
    build.add_argument("--generation-id")
    build.add_argument("--created-at")

    status = subcommands.add_parser("mark-status", help="append a validated resumable status event")
    status.add_argument("--ledger", type=Path, required=True)
    status.add_argument("--transfer-item", required=True)
    status.add_argument("--status", required=True)
    status.add_argument("--detail")
    status.add_argument("--recorded-at")

    fingerprint = subcommands.add_parser(
        "record-sha256", help="append a source-bound strong fingerprint assertion"
    )
    fingerprint.add_argument("--ledger", type=Path, required=True)
    fingerprint.add_argument("--occurrence", required=True)
    fingerprint.add_argument("--sha256", required=True)
    fingerprint.add_argument(
        "--method",
        required=True,
        choices=("source_sha256_ledger", "streamed_byte_hash", "destination_readback"),
    )
    fingerprint.add_argument("--verifier", required=True)
    fingerprint.add_argument("--verified-at", required=True)
    fingerprint.add_argument("--source-version")
    fingerprint.add_argument("--source-etag")

    bulk = subcommands.add_parser(
        "import-sha256-ledger",
        help="stream one or more R2 hash-ledger v2 NDJSON partitions",
    )
    bulk.add_argument("--ledger", type=Path, required=True)
    bulk.add_argument(
        "--ledger-partition",
        type=Path,
        action="append",
        required=True,
        help="repeat for each caller-resolved .ndjson or .ndjson.gz partition",
    )

    bridge = subcommands.add_parser(
        "finalize-sha256-bridge",
        help="freeze a complete conflict-free MD5+size to SHA-256 bridge",
    )
    bridge.add_argument("--ledger", type=Path, required=True)
    bridge.add_argument("--expected-partition-count", type=int, required=True)
    bridge.add_argument("--expected-record-count", type=int, required=True)
    bridge.add_argument("--finalized-at")

    metadata = subcommands.add_parser(
        "import-metadata",
        help="import provenance-bearing PG18/provider/sidecar metadata assertions",
    )
    metadata.add_argument("--ledger", type=Path, required=True)
    metadata.add_argument(
        "--assertion-partition", type=Path, action="append", required=True
    )

    resolve = subcommands.add_parser(
        "resolve-metadata",
        help="resolve exact-content metadata donors and export reviewable assertions",
    )
    resolve.add_argument("--ledger", type=Path, required=True)
    resolve.add_argument("--output-dir", type=Path, required=True)
    resolve.add_argument("--resolved-at")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    with ManifestBuilder(args.ledger) as builder:
        if args.command == "build":
            builder.ingest(args.inventory, source_bucket=args.source_bucket)
            result = builder.build_generation(
                args.output_dir,
                destination_remote=args.destination_remote,
                destination_prefix=args.destination_prefix,
                generation_id=args.generation_id,
                created_at=args.created_at,
            )
            print(json.dumps(asdict(result), sort_keys=True))
        elif args.command == "mark-status":
            builder.mark_status(
                args.transfer_item, args.status, args.detail, args.recorded_at
            )
            print(json.dumps({"transfer_item_id": args.transfer_item, "status": args.status}, sort_keys=True))
        elif args.command == "record-sha256":
            assertion_id = builder.record_sha256(
                args.occurrence,
                args.sha256,
                args.method,
                args.verifier,
                args.verified_at,
                source_version=args.source_version,
                source_etag=args.source_etag,
            )
            print(json.dumps({"fingerprint_assertion_id": assertion_id}, sort_keys=True))
        elif args.command == "import-sha256-ledger":
            results = builder.import_sha256_ledger(args.ledger_partition)
            print(json.dumps([asdict(result) for result in results], sort_keys=True))
        elif args.command == "finalize-sha256-bridge":
            result = builder.finalize_sha256_bridge(
                args.expected_partition_count,
                args.expected_record_count,
                finalized_at=args.finalized_at,
            )
            print(json.dumps(asdict(result), sort_keys=True))
        elif args.command == "import-metadata":
            results = builder.import_metadata_assertions(args.assertion_partition)
            print(json.dumps([asdict(result) for result in results], sort_keys=True))
        else:
            count = builder.write_metadata_resolution(
                args.output_dir, resolved_at=args.resolved_at
            )
            print(json.dumps({"resolution_count": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
