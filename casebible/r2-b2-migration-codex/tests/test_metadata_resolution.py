from __future__ import annotations

import csv
import gzip
import json
import sqlite3
import sys
import unittest
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


def write_assertions(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_sha256_partition(
    path: Path, *, bucket: str, object_path: str, size: int, md5: str, sha256: str
) -> None:
    record = {
        "schema": "casebible-r2-sha256-record-v2",
        "algorithm": "SHA-256",
        "digest": sha256,
        "sourceBucket": bucket,
        "sourceKey": object_path,
        "sourceVersion": "v1",
        "sourceEtag": md5,
        "sourceSize": size,
        "md5Hash": md5,
        "computedAt": "2026-09-13T12:10:00Z",
        "computation": "unit-test",
    }
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def assertion(
    occurrence_id: str,
    field: str,
    value: object,
    key: str,
    *,
    assertion_class: str = "catalog",
    trust_score: int = 80,
) -> dict[str, object]:
    return {
        "occurrence_id": occurrence_id,
        "field": field,
        "value": value,
        "assertion_class": assertion_class,
        "source_system": "casebible-pg18",
        "source_table": "media.enrichment",
        "source_key": key,
        "confidence": 0.95,
        "trust_score": trust_score,
        "observed_at": "2026-09-13T12:00:00Z",
    }


class MetadataResolutionTests(unittest.TestCase):
    def _two_occurrence_builder(
        self,
        root: Path,
        first_path: str,
        second_path: str,
        *,
        first_digest: str = "1" * 64,
        second_digest: str = "1" * 64,
    ) -> tuple[ManifestBuilder, list[sqlite3.Row]]:
        inventory = root / "inventory-20260913T120000Z.csv.gz"
        md5 = "a" * 32
        write_inventory(
            inventory,
            [
                ("raw", first_path, 100, md5, "2021-06-01T10:00:00Z", "image/jpeg"),
                ("raw", second_path, 100, md5, "2020-05-01T10:00:00Z", "image/jpeg"),
            ],
        )
        builder = ManifestBuilder(root / "ledger.sqlite")
        builder.ingest([inventory])
        rows = builder.connection.execute(
            "SELECT * FROM occurrence ORDER BY row_number"
        ).fetchall()
        builder.record_sha256(
            rows[0]["occurrence_id"], first_digest, "streamed_byte_hash",
            "unit-test", "2026-09-13T12:10:00Z",
        )
        builder.record_sha256(
            rows[1]["occurrence_id"], second_digest, "streamed_byte_hash",
            "unit-test", "2026-09-13T12:11:00Z",
        )
        return builder, rows

    def test_recovery_occurrence_with_richer_metadata_is_primary_and_native_name_is_canonical(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            builder, rows = self._two_occurrence_builder(
                root, "DCIM/IMG_1234.jpg", "recovered_0001_IMG_1234.jpg"
            )
            try:
                metadata = root / "pg18-metadata.ndjson"
                write_assertions(
                    metadata,
                    [
                        assertion(rows[0]["occurrence_id"], "original_filename", "IMG_1234.jpg", "native-name", assertion_class="provider"),
                        assertion(rows[1]["occurrence_id"], "exif_datetime_original", "2018-04-03T09:08:07Z", "recovery-exif", assertion_class="embedded", trust_score=95),
                        assertion(rows[1]["occurrence_id"], "gps_latitude", 42.3314, "recovery-gps-lat", assertion_class="embedded", trust_score=95),
                        assertion(rows[1]["occurrence_id"], "gps_longitude", -83.0458, "recovery-gps-lon", assertion_class="embedded", trust_score=95),
                        assertion(rows[1]["occurrence_id"], "camera_model", "Pixel", "recovery-camera", assertion_class="embedded", trust_score=90),
                        assertion(rows[1]["occurrence_id"], "provider_created_at", "0001-01-01T00:00:00Z", "sentinel", assertion_class="provider", trust_score=100),
                    ],
                )
                first_import = builder.import_metadata_assertions([metadata])[0]
                second_import = builder.import_metadata_assertions([metadata])[0]
                self.assertFalse(first_import.already_imported)
                self.assertTrue(second_import.already_imported)

                output = root / "out"
                builder.build_generation(
                    output, generation_id="metadata-best-copy",
                    created_at="2026-09-13T13:00:00Z",
                )
                resolution = builder.connection.execute(
                    "SELECT * FROM current_content_metadata_resolution"
                ).fetchone()
                self.assertEqual(resolution["primary_occurrence_id"], rows[1]["occurrence_id"])
                self.assertEqual(resolution["canonical_filename"], "IMG_1234.jpg")
                self.assertEqual(
                    resolution["oldest_trustworthy_timestamp"],
                    "2018-04-03T09:08:07Z",
                )
                with (output / "payload-mapping.csv").open(encoding="utf-8") as handle:
                    payload = next(csv.DictReader(handle))
                self.assertEqual(payload["source_path"], "recovered_0001_IMG_1234.jpg")

                with (output / "metadata-resolution.csv").open(encoding="utf-8") as handle:
                    exported = list(csv.DictReader(handle))
                self.assertTrue(any(row["field_name"] == "provider_created_at" for row in exported))
                self.assertTrue(
                    any(
                        row["field_name"] == "original_filename"
                        and row["is_canonical_filename_assertion"] == "1"
                        for row in exported
                    )
                )
                self.assertTrue(
                    any(
                        row["occurrence_id"] == rows[1]["occurrence_id"]
                        and row["is_primary_metadata_donor"] == "1"
                        for row in exported
                    )
                )
            finally:
                builder.close()

    def test_competing_credible_names_remain_side_by_side_for_review(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            builder, _ = self._two_occurrence_builder(
                root, "Photos/Birthday.jpg", "Photos/Vacation.jpg"
            )
            try:
                output = root / "review"
                builder.write_metadata_resolution(
                    output, resolved_at="2026-09-13T13:00:00Z"
                )
                resolution = builder.connection.execute(
                    "SELECT * FROM current_content_metadata_resolution"
                ).fetchone()
                self.assertEqual(resolution["resolution_state"], "review_required")
                with (output / "metadata-resolution.csv").open(encoding="utf-8") as handle:
                    names = {
                        json.loads(row["value_json"])
                        for row in csv.DictReader(handle)
                        if row["field_name"] == "observed_filename"
                    }
                self.assertEqual(names, {"Birthday.jpg", "Vacation.jpg"})
            finally:
                builder.close()

    def test_bridge_inherited_recovery_donor_is_used_for_payload(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260913T120000Z.csv.gz"
            md5 = "a" * 32
            digest = "1" * 64
            write_inventory(
                inventory,
                [
                    ("raw", "DCIM/IMG_0099.jpg", 100, md5, "2021-01-01T00:00:00Z", "image/jpeg"),
                    ("raw", "recovered_7_IMG_0099.jpg", 100, md5, "2019-01-01T00:00:00Z", "image/jpeg"),
                ],
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                occurrences = builder.connection.execute(
                    "SELECT * FROM occurrence ORDER BY row_number"
                ).fetchall()
                partition = root / "sha256.ndjson"
                write_sha256_partition(
                    partition, bucket="raw", object_path="DCIM/IMG_0099.jpg",
                    size=100, md5=md5, sha256=digest,
                )
                builder.import_sha256_ledger([partition])
                builder.finalize_sha256_bridge(
                    1, 1, finalized_at="2026-09-13T12:30:00Z"
                )
                metadata = root / "metadata.ndjson"
                write_assertions(
                    metadata,
                    [
                        assertion(
                            occurrences[1]["occurrence_id"], "exif_datetime_original",
                            "2018-04-03T09:08:07Z", "recovered-exif",
                            assertion_class="embedded", trust_score=95,
                        ),
                        assertion(
                            occurrences[1]["occurrence_id"], "gps_latitude",
                            42.3314, "recovered-gps", assertion_class="embedded",
                            trust_score=95,
                        ),
                    ],
                )
                builder.import_metadata_assertions([metadata])
                output = root / "out"
                builder.build_generation(
                    output, generation_id="bridge-metadata-donor",
                    created_at="2026-09-13T13:00:00Z",
                )
                with (output / "payload-mapping.csv").open(encoding="utf-8") as handle:
                    payload = next(csv.DictReader(handle))
                self.assertEqual(payload["source_path"], "recovered_7_IMG_0099.jpg")
                self.assertEqual(
                    payload["dedupe_authority"],
                    "sha256_via_conflict_free_md5_size_bridge",
                )

    def test_byte_different_occurrences_never_share_resolution(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            builder, _ = self._two_occurrence_builder(
                root, "Photos/a.jpg", "Photos/a-recovered.jpg",
                first_digest="1" * 64, second_digest="2" * 64,
            )
            try:
                builder.resolve_metadata(resolved_at="2026-09-13T13:00:00Z")
                resolutions = builder.connection.execute(
                    """SELECT content_id, primary_occurrence_id
                       FROM current_content_metadata_resolution ORDER BY content_id"""
                ).fetchall()
                self.assertEqual(len(resolutions), 2)
                self.assertEqual(len({row["content_id"] for row in resolutions}), 2)
            finally:
                builder.close()

    def test_embedded_metadata_conflict_blocks_auto_collapse(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260913T120000Z.csv.gz"
            write_inventory(
                inventory,
                [
                    ("raw", "Photos/a.jpg", 100, "a" * 32, "2021-01-01T00:00:00Z", "image/jpeg"),
                    ("raw", "Recovery/recovered_1_a.jpg", 100, "a" * 32, "2021-01-02T00:00:00Z", "image/jpeg"),
                    ("raw", "Photos/unrelated.jpg", 101, "b" * 32, "2021-01-03T00:00:00Z", "image/jpeg"),
                ],
            )
            builder = ManifestBuilder(root / "ledger.sqlite")
            builder.ingest([inventory])
            rows = builder.connection.execute("SELECT * FROM occurrence ORDER BY row_number").fetchall()
            builder.record_sha256(rows[0]["occurrence_id"], "1" * 64, "streamed_byte_hash", "test", "2026-09-13T12:01:00Z")
            builder.record_sha256(rows[1]["occurrence_id"], "1" * 64, "streamed_byte_hash", "test", "2026-09-13T12:02:00Z")
            builder.record_sha256(rows[2]["occurrence_id"], "2" * 64, "streamed_byte_hash", "test", "2026-09-13T12:03:00Z")
            try:
                metadata = root / "embedded-conflict.ndjson"
                write_assertions(
                    metadata,
                    [
                        assertion(rows[0]["occurrence_id"], "camera_model", "Camera A", "a", assertion_class="embedded"),
                        assertion(rows[1]["occurrence_id"], "camera_model", "Camera B", "b", assertion_class="embedded"),
                    ],
                )
                builder.import_metadata_assertions([metadata])
                builder.resolve_metadata(resolved_at="2026-09-13T13:00:00Z")
                state = builder.connection.execute(
                    "SELECT resolution_state FROM current_content_metadata_resolution"
                ).fetchone()[0]
                self.assertEqual(state, "blocked_embedded_conflict")
                builder.build_generation(root / "out", generation_id="per-group-hold")
                with (root / "out" / "payload-mapping.csv").open(encoding="utf-8") as handle:
                    payloads = list(csv.DictReader(handle))
                self.assertTrue(any(row["disposition"] == "canonical" and row["source_path"] == "Photos/unrelated.jpg" for row in payloads))
                self.assertTrue(any(row["hold_reason"] == "held_embedded_metadata_conflict" for row in payloads))
                with (root / "out" / "metadata-holds.csv").open(encoding="utf-8") as handle:
                    holds = list(csv.DictReader(handle))
                self.assertEqual(holds[0]["hold_reason"], "held_embedded_metadata_conflict")
                self.assertEqual(
                    builder.connection.execute("SELECT count(*) FROM transfer_item").fetchone()[0],
                    1,
                )
            finally:
                builder.close()

    def test_payload_health_precedes_metadata_richness_and_diagnostics_do_not_add_fitness(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            builder, rows = self._two_occurrence_builder(
                root, "Photos/healthy.jpg", "Recovery/recovered_9_healthy.jpg"
            )
            try:
                metadata = root / "health.ndjson"
                write_assertions(
                    metadata,
                    [
                        assertion(rows[0]["occurrence_id"], "payload_health", "healthy", "healthy"),
                        assertion(rows[1]["occurrence_id"], "payload_health", "corrupt", "corrupt"),
                        assertion(rows[1]["occurrence_id"], "exif_datetime_original", "2017-01-01T00:00:00Z", "date", assertion_class="embedded", trust_score=95),
                        assertion(rows[1]["occurrence_id"], "gps_latitude", 42.3, "gps", assertion_class="embedded", trust_score=95),
                        assertion(rows[1]["occurrence_id"], "camera_model", "Rich Camera", "camera", assertion_class="embedded", trust_score=95),
                    ],
                )
                builder.import_metadata_assertions([metadata])
                builder.resolve_metadata(resolved_at="2026-09-13T13:00:00Z")
                resolution = builder.connection.execute(
                    "SELECT primary_occurrence_id, reasons_json FROM current_content_metadata_resolution"
                ).fetchone()
                self.assertEqual(resolution["primary_occurrence_id"], rows[0]["occurrence_id"])
                reasons = json.loads(resolution["reasons_json"])
                self.assertTrue(reasons["primary_payload_eligible"])
                self.assertEqual(reasons["primary_health_assertion_count"], 1)
            finally:
                builder.close()

    def test_exact_group_without_healthy_payload_donor_is_held(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            builder, rows = self._two_occurrence_builder(root, "Photos/a.jpg", "Photos/b.jpg")
            try:
                metadata = root / "unhealthy.ndjson"
                write_assertions(
                    metadata,
                    [
                        assertion(rows[0]["occurrence_id"], "payload_health", "corrupt", "a"),
                        assertion(rows[1]["occurrence_id"], "byte_readable", False, "b"),
                    ],
                )
                builder.import_metadata_assertions([metadata])
                builder.build_generation(root / "out", generation_id="unhealthy-group")
                self.assertEqual(
                    builder.connection.execute("SELECT count(*) FROM transfer_item").fetchone()[0],
                    0,
                )
                with (root / "out" / "payload-mapping.csv").open(encoding="utf-8") as handle:
                    payloads = list(csv.DictReader(handle))
                self.assertTrue(payloads)
                self.assertEqual(
                    {row["hold_reason"] for row in payloads},
                    {"held_no_healthy_payload_donor"},
                )
            finally:
                builder.close()

    def test_candidate_only_rows_are_preserved_without_creating_identity(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            inventory = root / "inventory-20260913T120000Z.csv.gz"
            write_inventory(
                inventory,
                [
                    ("raw", "same/path.jpg", 100, "a" * 32, "2021-01-01T00:00:00Z", "image/jpeg"),
                    ("raw", "same/path.jpg", 100, "b" * 32, "2021-01-02T00:00:00Z", "image/jpeg"),
                ],
            )
            metadata = root / "onedrive.ndjson"
            common = {
                "source_system": "onedrive-r2-export", "source_table": "catalog.od_manifest",
                "source_account": "account-a", "source_tree": "archive1",
                "source_path": "same/path.jpg", "byte_size": 100,
                "match_percent": 100, "field": "provider_modified_at",
                "value": "2021-01-01T00:00:00Z", "source_version": "v1",
            }
            write_assertions(
                metadata,
                [
                    {**common, "source_key": "snapshot-a", "snapshot_id": "scan-a", "quickxor": "qx-a"},
                    {**common, "source_key": "snapshot-b", "snapshot_id": "scan-b", "quickxor": "qx-b"},
                ],
            )
            with ManifestBuilder(root / "ledger.sqlite") as builder:
                builder.ingest([inventory])
                identities_before = builder.connection.execute(
                    "SELECT content_id, identity_status FROM content_identity ORDER BY content_id"
                ).fetchall()
                result = builder.import_metadata_assertions([metadata])[0]
                identities_after = builder.connection.execute(
                    "SELECT content_id, identity_status FROM content_identity ORDER BY content_id"
                ).fetchall()
                self.assertEqual([tuple(row) for row in identities_before], [tuple(row) for row in identities_after])
                self.assertEqual(result.assertion_count, 0)
                self.assertEqual(result.held_record_count, 2)
                staged = builder.connection.execute(
                    """SELECT source_account, source_tree, snapshot_id, source_version,
                              match_percent, quickxor_hint, disposition, raw_record
                       FROM metadata_import_record ORDER BY line_number"""
                ).fetchall()
                self.assertEqual({row["disposition"] for row in staged}, {"held_quickxor_drift"})
                self.assertEqual({row["snapshot_id"] for row in staged}, {"scan-a", "scan-b"})
                self.assertEqual({row["quickxor_hint"] for row in staged}, {"qx-a", "qx-b"})
                self.assertEqual(
                    builder.connection.execute("SELECT count(*) FROM metadata_import_candidate").fetchone()[0],
                    4,
                )

    def test_locator_metadata_binds_only_after_candidates_share_verified_sha256(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            builder, rows = self._two_occurrence_builder(
                root, "Photos/a.jpg", "Recovery/recovered_1_a.jpg"
            )
            try:
                metadata = root / "provider.ndjson"
                write_assertions(
                    metadata,
                    [{
                        "source_system": "provider", "source_table": "manifest",
                        "source_key": "tree:path:v3", "source_account": "account-a",
                        "source_tree": "tree-a", "snapshot_id": "snapshot-a",
                        "source_version": "v3", "source_bucket": "raw",
                        "source_path": "Photos/a.jpg", "byte_size": 100,
                        "md5": "a" * 32, "match_percent": 100,
                        "field": "camera_model", "value": "Pixel",
                    }],
                )
                result = builder.import_metadata_assertions([metadata])[0]
                self.assertEqual(result.bound_record_count, 1)
                record = builder.connection.execute("SELECT * FROM metadata_import_record").fetchone()
                self.assertEqual(record["disposition"], "bound_unique_verified_content")
                self.assertEqual(record["source_account"], "account-a")
                self.assertEqual(record["source_tree"], "tree-a")
                self.assertEqual(record["snapshot_id"], "snapshot-a")
                self.assertEqual(record["source_version"], "v3")
                self.assertEqual(
                    builder.connection.execute("SELECT count(*) FROM metadata_assertion").fetchone()[0],
                    1,
                )
            finally:
                builder.close()

    def test_metadata_review_output_refuses_overwrite(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            builder, _ = self._two_occurrence_builder(root, "Photos/a.jpg", "Photos/b.jpg")
            try:
                builder.write_metadata_resolution(root / "review", resolved_at="2026-09-13T13:00:00Z")
                with self.assertRaisesRegex(FileExistsError, "immutable output directory"):
                    builder.write_metadata_resolution(root / "review", resolved_at="2026-09-13T14:00:00Z")
            finally:
                builder.close()

    def test_existing_older_ledger_is_upgraded_additively(self) -> None:
        with TemporaryDirectory() as raw:
            ledger = Path(raw) / "ledger.sqlite"
            connection = sqlite3.connect(ledger)
            connection.execute(
                "CREATE TABLE schema_version(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT INTO schema_version(version, applied_at) VALUES (4, '2026-09-12T00:00:00Z')"
            )
            connection.commit()
            connection.close()
            with ManifestBuilder(ledger) as builder:
                versions = {
                    row[0] for row in builder.connection.execute(
                        "SELECT version FROM schema_version"
                    )
                }
                self.assertEqual(versions, {4, 6})
                self.assertIsNotNone(
                    builder.connection.execute(
                        """SELECT 1 FROM sqlite_master
                           WHERE type = 'table' AND name = 'metadata_assertion'"""
                    ).fetchone()
                )
                self.assertIsNotNone(
                    builder.connection.execute(
                        """SELECT 1 FROM sqlite_master
                           WHERE type = 'table' AND name = 'metadata_import_record'"""
                    ).fetchone()
                )


if __name__ == "__main__":
    unittest.main()
