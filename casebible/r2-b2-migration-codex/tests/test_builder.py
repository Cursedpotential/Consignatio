from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import sqlite3
import sys
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from r2_b2_manifest.builder import ManifestBuilder  # noqa: E402


HEADERS = ("bucket", "path", "size", "md5", "modtime", "mimetype")


def write_inventory(path: Path, rows: list[tuple[object, ...]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADERS)
        writer.writerows(rows)


def write_native_inventory(path: Path, rows: list[tuple[object, ...]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerows(rows)


def hash_ledger_record(
    bucket: str = "a",
    key: str = "file.bin",
    size: int = 5,
    md5: str = "a" * 32,
    digest: str = "1" * 64,
) -> dict[str, object]:
    return {
        "schema": "casebible-r2-sha256-record-v2",
        "algorithm": "SHA-256",
        "digest": digest,
        "sourceBucket": bucket,
        "sourceKey": key,
        "sourceVersion": "version-1",
        "sourceEtag": md5,
        "sourceSize": size,
        "fullPath": f"s3://{bucket}/{key}",
        "md5Hash": md5,
        "sourceChecksums": {"md5": md5},
        "computedAt": "2026-09-12T16:00:00Z",
        "computation": "synthetic-test",
    }


def write_ledger_partition(path: Path, records: list[bytes], compressed: bool) -> None:
    opener = gzip.open if compressed else Path.open
    with opener(path, "wb") as handle:
        for record in records:
            handle.write(record)
            if not record.endswith(b"\n"):
                handle.write(b"\n")


class ManifestBuilderTests(unittest.TestCase):
    def test_completed_conflict_free_bridge_maps_three_occurrences_to_one_payload(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            md5 = "a" * 32
            digest = "1" * 64
            write_inventory(
                inventory,
                [
                    ("bucket-a", "one/file.bin", 5, md5, "", ""),
                    ("bucket-b", "two/file.bin", 5, md5, "", ""),
                    ("bucket-c", "three/file.bin", 5, md5, "", ""),
                ],
            )
            partition = root / "hash-ledger-part-0001.ndjson.gz"
            write_ledger_partition(
                partition,
                [
                    json.dumps(
                        hash_ledger_record(
                            bucket="bucket-b", key="two/file.bin", size=5,
                            md5=md5, digest=digest,
                        ),
                        separators=(",", ":"),
                    ).encode("utf-8")
                ],
                compressed=True,
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                builder.import_sha256_ledger([partition])
                finalized = builder.finalize_sha256_bridge(
                    1, 1, finalized_at="2026-09-12T16:30:00Z"
                )
                self.assertEqual(finalized.bridge_group_count, 1)
                self.assertFalse(finalized.already_finalized)
                identities = builder.connection.execute(
                    "SELECT DISTINCT content_id FROM occurrence"
                ).fetchall()
                self.assertEqual([row[0] for row in identities], [f"sha256:{digest}:5"])
                builder.build_generation(
                    root / "out", generation_id="bridge",
                    created_at="2026-09-12T16:31:00Z",
                )
                authority = builder.connection.execute(
                    "SELECT dedupe_authority FROM transfer_item WHERE generation_id = 'bridge'"
                ).fetchone()[0]
                self.assertEqual(
                    authority, "sha256_via_conflict_free_md5_size_bridge"
                )
            with (root / "out" / "payload-mapping.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                payload_rows = list(csv.DictReader(handle))
            self.assertEqual(len(payload_rows), 1)
            self.assertEqual(payload_rows[0]["source_bucket"], "bucket-b")
            self.assertEqual(payload_rows[0]["source_path"], "two/file.bin")
            self.assertEqual(payload_rows[0]["source_md5"], md5)
            self.assertEqual(payload_rows[0]["source_etag"], md5)
            self.assertEqual(payload_rows[0]["source_version"], "version-1")
            self.assertEqual(
                payload_rows[0]["dedupe_authority"],
                "sha256_via_conflict_free_md5_size_bridge",
            )
            with (root / "out" / "occurrence-content-map.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                occurrence_rows = list(csv.DictReader(handle))
            self.assertEqual(len(occurrence_rows), 3)
            self.assertEqual(
                sorted(row["assertion_basis"] for row in occurrence_rows),
                ["direct", "inherited_md5_size_bridge", "inherited_md5_size_bridge"],
            )
            self.assertEqual(
                {row["destination_key"] for row in occurrence_rows},
                {f"payloads/sha256/11/{digest}"},
            )

    def test_incomplete_or_conflicting_import_cannot_finalize_bridge(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            md5 = "a" * 32
            write_inventory(inventory, [("bucket-a", "file.bin", 5, md5, "", "")])
            partition = root / "hash-ledger-part-0001.ndjson"
            write_ledger_partition(
                partition,
                [json.dumps(hash_ledger_record(bucket="bucket-a", md5=md5, digest="1" * 64)).encode("utf-8")],
                compressed=False,
            )
            with ManifestBuilder(root / "incomplete.sqlite") as builder:
                builder.ingest([inventory])
                builder.import_sha256_ledger([partition])
                with self.assertRaisesRegex(ValueError, "partition count mismatch"):
                    builder.finalize_sha256_bridge(2, 1)
                with self.assertRaisesRegex(ValueError, "record count mismatch"):
                    builder.finalize_sha256_bridge(1, 2)
                self.assertEqual(
                    builder.connection.execute(
                        "SELECT COUNT(*) FROM sha256_md5_size_bridge"
                    ).fetchone()[0],
                    0,
                )

            conflict_partition = root / "hash-ledger-part-0002.ndjson"
            write_ledger_partition(
                conflict_partition,
                [
                    json.dumps(hash_ledger_record(bucket="bucket-a", md5=md5, digest="2" * 64)).encode("utf-8"),
                    json.dumps(hash_ledger_record(bucket="bucket-a", md5=md5, digest="3" * 64)).encode("utf-8"),
                ],
                compressed=False,
            )
            with ManifestBuilder(root / "conflict.sqlite") as builder:
                builder.ingest([inventory])
                builder.import_sha256_ledger([conflict_partition])
                with self.assertRaisesRegex(ValueError, "conflicting SHA-256"):
                    builder.finalize_sha256_bridge(1, 2)
                self.assertEqual(
                    builder.connection.execute(
                        "SELECT COUNT(*) FROM sha256_bridge_finalization"
                    ).fetchone()[0],
                    0,
                )

    def test_bulk_sha256_ledger_import_is_source_bound_and_idempotent(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            write_inventory(inventory, [("a", "file.bin", 5, "a" * 32, "", "")])
            partition = root / "hash-ledger-part-0001.ndjson.gz"
            write_ledger_partition(
                partition,
                [json.dumps(hash_ledger_record(), separators=(",", ":")).encode("utf-8")],
                compressed=True,
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                first = builder.import_sha256_ledger([partition])[0]
                second = builder.import_sha256_ledger([partition])[0]
                self.assertFalse(first.already_imported)
                self.assertTrue(second.already_imported)
                self.assertEqual((first.row_count, first.bound_count, first.held_count), (1, 1, 0))
                assertion = builder.connection.execute(
                    """SELECT f.sha256, f.source_version, f.source_etag,
                              i.disposition, p.source_sha256
                       FROM strong_fingerprint_assertion f
                       JOIN fingerprint_import_binding b USING (fingerprint_assertion_id)
                       JOIN fingerprint_import_assertion i USING (import_assertion_id)
                       JOIN fingerprint_import_partition p USING (partition_id)"""
                ).fetchone()
                self.assertEqual(assertion["sha256"], "1" * 64)
                self.assertEqual(assertion["source_version"], "version-1")
                self.assertEqual(assertion["source_etag"], "a" * 32)
                self.assertEqual(assertion["disposition"], "bound")
                self.assertEqual(len(assertion["source_sha256"]), 64)
                identity = builder.connection.execute(
                    "SELECT identity_status FROM content_identity WHERE content_id IN (SELECT content_id FROM occurrence)"
                ).fetchone()[0]
                self.assertEqual(identity, "sha256_verified")
                self.assertEqual(
                    builder.connection.execute(
                        "SELECT COUNT(*) FROM fingerprint_import_assertion"
                    ).fetchone()[0],
                    1,
                )

    def test_bulk_import_records_every_malformed_deferred_and_conflicting_row(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            write_inventory(inventory, [("a", "file.bin", 5, "a" * 32, "", "")])
            valid_a = hash_ledger_record(digest="2" * 64)
            valid_b = hash_ledger_record(digest="3" * 64)
            wrong_schema = hash_ledger_record()
            wrong_schema["schema"] = "casebible-r2-sha256-record-v1"
            wrong_algorithm = hash_ledger_record()
            wrong_algorithm["algorithm"] = "SHA-1"
            invalid_digest = hash_ledger_record()
            invalid_digest["digest"] = "not-a-digest"
            invalid_locator = hash_ledger_record()
            invalid_locator["sourceSize"] = -1
            invalid_md5 = hash_ledger_record()
            invalid_md5["md5Hash"] = "missing"
            field_conflict = hash_ledger_record()
            field_conflict["sourceChecksums"] = {"md5": "f" * 32}
            deferred = hash_ledger_record()
            deferred.pop("computedAt")
            unmatched = hash_ledger_record(key="not-in-inventory.bin")
            json_records = [
                b"",
                b"{not-json}",
                json.dumps([]).encode("utf-8"),
                *(json.dumps(value, separators=(",", ":")).encode("utf-8") for value in (
                    wrong_schema, wrong_algorithm, invalid_digest, invalid_locator,
                    invalid_md5, field_conflict, deferred, unmatched, valid_a, valid_b,
                )),
            ]
            partition = root / "hash-ledger-part-0002.ndjson"
            write_ledger_partition(partition, json_records, compressed=False)
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                result = builder.import_sha256_ledger([partition])[0]
                self.assertEqual(result.row_count, len(json_records) - 1)
                self.assertEqual(result.bound_count, 0)
                self.assertEqual(result.held_count, len(json_records) - 1)
                dispositions = {
                    row[0]
                    for row in builder.connection.execute(
                        "SELECT disposition FROM fingerprint_import_assertion"
                    )
                }
                self.assertTrue(
                    {
                        "held_malformed_json", "held_non_object",
                        "held_schema_mismatch", "held_algorithm_mismatch",
                        "held_invalid_digest", "held_invalid_locator", "held_invalid_md5",
                        "held_source_field_conflict", "held_deferred_missing_computed_at",
                        "held_unmatched_occurrence", "held_digest_conflict",
                    }.issubset(dispositions)
                )
                self.assertEqual(
                    builder.connection.execute(
                        "SELECT COUNT(*) FROM strong_fingerprint_assertion"
                    ).fetchone()[0],
                    2,
                )
                builder.build_generation(
                    root / "out", generation_id="bulk-conflict",
                    created_at="2026-09-12T16:30:00Z",
                )
                status = builder.connection.execute(
                    "SELECT status FROM transfer_item_current_status"
                ).fetchone()[0]
                self.assertEqual(status, "held_sha256_assertion_conflict")

    def test_idempotent_reimport_repairs_historical_blank_separator_counts(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            write_inventory(inventory, [("a", "file.bin", 5, "a" * 32, "", "")])
            partition = root / "hash-ledger-part.ndjson.gz"
            write_ledger_partition(
                partition,
                [json.dumps(hash_ledger_record()).encode("utf-8")],
                compressed=True,
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                first = builder.import_sha256_ledger([partition])[0]
                with builder.connection:
                    builder.connection.execute(
                        """INSERT INTO fingerprint_import_assertion(
                               import_assertion_id, partition_id, line_number,
                               raw_sha256, raw_record, disposition, detail_json,
                               asserted_at
                           ) VALUES ('historical-blank', ?, 2, ?, '\n',
                                     'held_blank_record', '{}',
                                     '2026-09-12T16:00:00Z')""",
                        (first.partition_id, "0" * 64),
                    )
                    builder.connection.execute(
                        """UPDATE fingerprint_import_partition
                           SET row_count = 2, bound_count = 1, held_count = 1
                           WHERE partition_id = ?""",
                        (first.partition_id,),
                    )
                repaired = builder.import_sha256_ledger([partition])[0]
                self.assertTrue(repaired.already_imported)
                self.assertEqual(
                    (repaired.row_count, repaired.bound_count, repaired.held_count),
                    (1, 1, 0),
                )
                self.assertEqual(
                    builder.connection.execute(
                        """SELECT COUNT(*) FROM fingerprint_import_assertion
                           WHERE disposition = 'held_blank_record'"""
                    ).fetchone()[0],
                    1,
                )

    def test_preserves_occurrences_and_md5_candidates_do_not_suppress_paths(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "r2-inventory-20260912T120000Z.csv.gz"
            exact = "a" * 32
            conflict = "b" * 32
            empty_md5 = "d41d8cd98f00b204e9800998ecf8427e"
            rows = [
                ("bucket-a", "junk/Takeout/Drive/report.pdf", 12, exact, "2025-01-01T00:00:00Z", "application/pdf"),
                ("bucket-b", "to_be_deleted/copy.pdf", 12, exact, "2025-01-02T00:00:00Z", "application/pdf"),
                ("bucket-a", "missing/name.txt", 4, "", "", "text/plain"),
                ("bucket-a", "bad/name.txt", 4, "not-md5", "", "text/plain"),
                ("bucket-a", "conflict/one.bin", 7, conflict, "", "application/octet-stream"),
                ("bucket-b", "conflict/two.bin", 8, conflict, "", "application/octet-stream"),
                ("bucket-a", "zero/unhydrated-placeholder.bin", 0, empty_md5, "", "application/octet-stream"),
                ("bucket-a", "unavailable/error.bin", 5, "ERROR", "", "application/octet-stream"),
                ("bucket-a", "unavailable/unsupported.bin", 6, "UNSUPPORTED", "", "application/octet-stream"),
            ]
            write_inventory(inventory, rows)
            ledger = root / "ledger.sqlite"
            output = root / "out"
            with ManifestBuilder(ledger) as builder:
                self.assertEqual(builder.ingest([inventory]), 1)
                self.assertEqual(builder.ingest([inventory]), 0)
                result = builder.build_generation(
                    output, generation_id="test-generation", created_at="2026-09-12T12:30:00Z"
                )
                self.assertEqual(result.occurrence_count, 9)
                self.assertEqual(result.sha256_verified_content_count, 0)
                self.assertEqual(result.md5_candidate_content_count, 2)
                self.assertEqual(result.held_content_count, 6)
                self.assertEqual(result.files_from_count, 3)
                if importlib.util.find_spec("duckdb") is not None:
                    self.assertTrue(result.parquet_written)
                    import duckdb

                    parquet_connection = duckdb.connect(":memory:")
                    try:
                        parquet_count = parquet_connection.execute(
                            "SELECT COUNT(*) FROM read_parquet(?)",
                            [str(output / "parquet" / "occurrence.parquet")],
                        ).fetchone()[0]
                    finally:
                        parquet_connection.close()
                    self.assertEqual(parquet_count, 9)
                counts = builder.connection.execute(
                    "SELECT identity_status, COUNT(*) AS n FROM content_identity GROUP BY identity_status"
                ).fetchall()
                self.assertEqual(
                    {row["identity_status"]: row["n"] for row in counts},
                    {
                        "md5_size_candidate": 2,
                        "hash_error": 1,
                        "hash_unsupported": 1,
                        "invalid_hash": 1,
                        "md5_size_conflict": 2,
                        "missing_hash": 1,
                    },
                )
                assert_count = builder.connection.execute(
                    "SELECT COUNT(*) FROM assertion WHERE provisional = 1"
                ).fetchone()[0]
                self.assertGreaterEqual(assert_count, 7)
            self.assertEqual(
                (output / "files-from" / "all.txt").read_text(encoding="utf-8"),
                "bucket-a/junk/Takeout/Drive/report.pdf\n"
                "bucket-a/zero/unhydrated-placeholder.bin\n"
                "bucket-b/to_be_deleted/copy.pdf\n",
            )
            with ManifestBuilder(ledger) as builder:
                repeat = builder.build_generation(
                    root / "out-repeat",
                    generation_id="test-generation",
                    created_at="2026-09-12T12:30:00Z",
                )
                self.assertEqual(repeat.files_from_count, result.files_from_count)
            self.assertEqual(
                (output / "files-from" / "all.txt").read_bytes(),
                (root / "out-repeat" / "files-from" / "all.txt").read_bytes(),
            )
            self.assertEqual(
                (output / "transfer-manifest.csv").read_bytes(),
                (root / "out-repeat" / "transfer-manifest.csv").read_bytes(),
            )
            with closing(sqlite3.connect(ledger)) as connection:
                preserved = connection.execute(
                    """SELECT COUNT(*) FROM occurrence o
                       JOIN transfer_item_occurrence m USING (occurrence_id)
                       WHERE o.object_path = 'to_be_deleted/copy.pdf'"""
                ).fetchone()[0]
            self.assertEqual(preserved, 1)
            manifest = (output / "transfer-manifest.csv").read_text(encoding="utf-8")
            self.assertIn("held_md5_size_conflict", manifest)
            self.assertIn("md5_candidate_no_suppression", manifest)

    def test_native_rclone_pshtm_csv_preserves_quoted_delimiters_and_newlines(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "native-20260912T120000Z.csv.gz"
            write_native_inventory(
                inventory,
                [
                    ("folder/comma,name.txt", 3, "e" * 32, "2026-09-12T12:00:00Z", "text/plain"),
                    ("folder/line\nbreak.txt", 4, "", "2026-09-12T12:00:01Z", "text/plain"),
                    ("zero.bin", 0, "UNSUPPORTED", "", "application/octet-stream"),
                ],
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory], source_bucket="source-bucket")
                paths = [
                    row[0]
                    for row in builder.connection.execute(
                        "SELECT object_path FROM occurrence ORDER BY row_number"
                    )
                ]
                self.assertEqual(
                    paths,
                    ["folder/comma,name.txt", "folder/line\nbreak.txt", "zero.bin"],
                )
                result = builder.build_generation(
                    root / "out", generation_id="native", created_at="2026-09-12T12:30:00Z"
                )
                self.assertEqual(result.files_from_count, 1)
                statuses = {
                    row[0]
                    for row in builder.connection.execute(
                        "SELECT status FROM transfer_item_current_status"
                    )
                }
                self.assertIn("held_unsafe_path", statuses)
                self.assertIn("held_hash_unsupported", statuses)

    def test_only_source_bound_sha256_suppresses_duplicate_transport_paths(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            write_inventory(
                inventory,
                [
                    ("a", "first/file.bin", 5, "f" * 32, "", "application/octet-stream"),
                    ("b", "second/file.bin", 5, "f" * 32, "", "application/octet-stream"),
                ],
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                occurrence_ids = [
                    row[0]
                    for row in builder.connection.execute(
                        "SELECT occurrence_id FROM occurrence ORDER BY bucket"
                    )
                ]
                for occurrence_id in occurrence_ids:
                    builder.record_sha256(
                        occurrence_id,
                        "1" * 64,
                        "source_sha256_ledger",
                        "synthetic-test",
                        "2026-09-12T12:15:00Z",
                        source_version="v1",
                        source_etag="etag-1",
                    )
                result = builder.build_generation(
                    root / "out", generation_id="sha", created_at="2026-09-12T12:30:00Z"
                )
                self.assertEqual(result.sha256_verified_content_count, 1)
                self.assertEqual(result.files_from_count, 1)
                item = builder.connection.execute(
                    "SELECT dedupe_authority FROM transfer_item WHERE generation_id = 'sha'"
                ).fetchone()
                self.assertEqual(item[0], "sha256_verified")
                mapped = builder.connection.execute(
                    "SELECT COUNT(*) FROM transfer_item_occurrence"
                ).fetchone()[0]
                self.assertEqual(mapped, 2)
                with (root / "out" / "payload-mapping.csv").open(
                    "r", encoding="utf-8", newline=""
                ) as handle:
                    payload_rows = list(csv.DictReader(handle))
                self.assertEqual(len(payload_rows), 1)
                self.assertEqual(payload_rows[0]["content_algorithm"], "sha256")
                self.assertEqual(payload_rows[0]["content_digest"], "1" * 64)
                self.assertEqual(payload_rows[0]["disposition"], "canonical")
                self.assertEqual(
                    payload_rows[0]["destination_key"],
                    f"payloads/sha256/11/{'1' * 64}",
                )
                self.assertEqual(payload_rows[0]["source_version"], "v1")
                self.assertEqual(payload_rows[0]["source_etag"], "etag-1")
                self.assertEqual(len(payload_rows[0]["source_identity"]), 64)
                with (root / "out" / "occurrence-content-map.csv").open(
                    "r", encoding="utf-8", newline=""
                ) as handle:
                    occurrence_rows = list(csv.DictReader(handle))
                self.assertEqual(len(occurrence_rows), 2)
                self.assertEqual(
                    {row["mapping_status"] for row in occurrence_rows},
                    {"canonical", "deduplicated_occurrence"},
                )
                self.assertEqual(
                    {row["destination_key"] for row in occurrence_rows},
                    {f"payloads/sha256/11/{'1' * 64}"},
                )

    def test_payload_mapping_routes_only_safe_nonconflicting_non_sha_sources(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            older = root / "inventory-20260912T120000Z.csv.gz"
            newer = root / "inventory-20260912T130000Z.csv.gz"
            write_inventory(
                older,
                [
                    ("bucket-a", "md5-only.bin", 5, "a" * 32, "", ""),
                    ("bucket-a", "missing-hash.bin", 7, "", "", ""),
                    ("bucket-a", "zero.bin", 0, "d41d8cd98f00b204e9800998ecf8427e", "", ""),
                    ("bucket-a", "drift.bin", 5, "b" * 32, "", ""),
                    ("bucket-a", "_system/probe/control.bin", 8, "e" * 32, "", ""),
                    ("bucket-a", "conflict-a.bin", 5, "f" * 32, "", ""),
                    ("bucket-a", "conflict-b.bin", 6, "f" * 32, "", ""),
                ],
            )
            write_inventory(
                newer,
                [("bucket-a", "drift.bin", 6, "c" * 32, "", "")],
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([older, newer])
                zero_occurrence = builder.connection.execute(
                    "SELECT occurrence_id FROM occurrence WHERE object_path = 'zero.bin'"
                ).fetchone()[0]
                control_occurrence = builder.connection.execute(
                    "SELECT occurrence_id FROM occurrence WHERE object_path = '_system/probe/control.bin'"
                ).fetchone()[0]
                builder.record_sha256(
                    zero_occurrence, "0" * 64, "streamed_byte_hash", "test",
                    "2026-09-12T13:30:00Z",
                )
                builder.record_sha256(
                    control_occurrence, "1" * 64, "streamed_byte_hash", "test",
                    "2026-09-12T13:31:00Z",
                )
                builder.build_generation(
                    root / "out", generation_id="held-policy",
                    created_at="2026-09-12T14:00:00Z",
                )
            with (root / "out" / "payload-mapping.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertFalse(any(row["disposition"] == "canonical" for row in rows))
            self.assertFalse(any(row["destination_key"].startswith("payloads/sha256/") for row in rows))
            md5_row = next(row for row in rows if row["source_path"] == "md5-only.bin")
            self.assertEqual(md5_row["content_algorithm"], "md5")
            self.assertEqual(md5_row["disposition"], "source-identity")
            self.assertEqual(md5_row["hold_reason"], "")
            self.assertEqual(
                md5_row["destination_key"],
                f"payloads/source-identity/{md5_row['source_identity'][:2]}/{md5_row['source_identity']}",
            )
            missing_row = next(row for row in rows if row["source_path"] == "missing-hash.bin")
            self.assertEqual(missing_row["content_algorithm"], "unknown")
            self.assertEqual(missing_row["disposition"], "source-identity")
            zero_row = next(row for row in rows if row["source_path"] == "zero.bin")
            self.assertEqual(zero_row["content_algorithm"], "unknown")
            self.assertEqual(zero_row["hold_reason"], "held_zero_byte")
            control_row = next(
                row for row in rows if row["source_path"] == "_system/probe/control.bin"
            )
            self.assertEqual(control_row["disposition"], "held")
            self.assertEqual(control_row["hold_reason"], "held_control_path")
            conflict_rows = [row for row in rows if row["source_path"].startswith("conflict-")]
            self.assertEqual({row["disposition"] for row in conflict_rows}, {"held"})
            self.assertEqual(
                {row["hold_reason"] for row in conflict_rows}, {"held_md5_size_conflict"}
            )
            drift_rows = [row for row in rows if row["source_path"] == "drift.bin"]
            self.assertEqual(len(drift_rows), 1)
            self.assertEqual(drift_rows[0]["hold_reason"], "held_source_location_drift")
            with (root / "out" / "occurrence-content-map.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                occurrence_rows = list(csv.DictReader(handle))
            self.assertEqual(len(occurrence_rows), 8)
            self.assertEqual(
                next(row for row in occurrence_rows if row["source_path"] == "md5-only.bin")["mapping_status"],
                "source_identity",
            )
            self.assertEqual(
                next(row for row in occurrence_rows if row["source_path"] == "missing-hash.bin")["mapping_status"],
                "source_identity",
            )
            self.assertEqual(
                [row["mapping_status"] for row in occurrence_rows if row["source_path"] == "drift.bin"],
                ["held_source_location_drift", "held_source_location_drift"],
            )

    def test_conflicting_sha256_assertions_are_held(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            write_inventory(inventory, [("a", "file.bin", 5, "a" * 32, "", "")])
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                occurrence_id = builder.connection.execute(
                    "SELECT occurrence_id FROM occurrence"
                ).fetchone()[0]
                builder.record_sha256(
                    occurrence_id, "2" * 64, "streamed_byte_hash", "test-a",
                    "2026-09-12T12:01:00Z",
                )
                builder.record_sha256(
                    occurrence_id, "3" * 64, "streamed_byte_hash", "test-b",
                    "2026-09-12T12:02:00Z",
                )
                result = builder.build_generation(
                    root / "out", generation_id="conflict", created_at="2026-09-12T12:30:00Z"
                )
                self.assertEqual(result.files_from_count, 0)
                status = builder.connection.execute(
                    "SELECT status FROM transfer_item_current_status"
                ).fetchone()[0]
                self.assertEqual(status, "held_sha256_assertion_conflict")

    def test_nested_atomic_hints_are_retained_as_provisional_assertions(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory_2026-09-12T12-00-00Z.csv.gz"
            write_inventory(
                inventory,
                [("exports", "recovery/Takeout/Drive/dev/app/package.json", 9, "c" * 32, "", "application/json")],
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                rows = builder.connection.execute(
                    """SELECT label, grouping_key, provisional, rule_version
                       FROM assertion WHERE assertion_kind = 'atomic_unit_hint'
                       ORDER BY label"""
                ).fetchall()
                self.assertEqual({row["label"] for row in rows}, {"development_repository", "google_takeout"})
                self.assertTrue(all(row["provisional"] == 1 for row in rows))
                self.assertTrue(all(row["rule_version"] for row in rows))

    def test_status_history_is_append_only_and_transition_checked(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260912T120000Z.csv.gz"
            write_inventory(inventory, [("a", "file.txt", 1, "d" * 32, "", "text/plain")])
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                builder.build_generation(root / "out", generation_id="g", created_at="2026-09-12T12:00:00Z")
                item = builder.connection.execute("SELECT transfer_item_id FROM transfer_item").fetchone()[0]
                builder.mark_status(item, "queued", recorded_at="2026-09-12T12:01:00Z")
                builder.mark_status(item, "copying", recorded_at="2026-09-12T12:02:00Z")
                builder.mark_status(item, "copied", recorded_at="2026-09-12T12:03:00Z")
                builder.mark_status(item, "verified", recorded_at="2026-09-12T12:04:00Z")
                current = builder.connection.execute(
                    "SELECT status, sequence_number FROM transfer_item_current_status"
                ).fetchone()
                self.assertEqual((current["status"], current["sequence_number"]), ("verified", 5))
                with self.assertRaises(ValueError):
                    builder.mark_status(item, "copying")


if __name__ == "__main__":
    unittest.main()
