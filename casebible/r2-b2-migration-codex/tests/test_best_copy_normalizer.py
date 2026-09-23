from __future__ import annotations

import csv
import gzip
import json
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


HEADERS = {
    "r2_occurrence": ["bucket", "path", "name", "size", "md5", "modtime", "mimetype", "tier", "_src_file", "loaded_at"],
    "atomic_path_index": ["store", "account_key", "container", "path", "name", "byte_size", "md5", "sha1", "sha256", "quickxor", "mtime_text", "source_variant_key", "source_row_count", "source_refs", "indexed_at"],
    "onedrive_manifest": ["tree", "path", "size", "modtime", "quickxor", "scan_file", "scanned_at"],
    "gdrive_manifest": ["path", "name", "size", "mime_type", "mod_time", "drive_id", "sha256", "md5", "sha1", "account", "_src_file", "loaded_at"],
    "local_files": ["source", "path", "name", "size", "_src_file", "loaded_at"],
    "legacy_hashes": ["source_table", "path", "size", "md5", "_src_file", "loaded_at"],
    "recovery_links": ["source_table", "missing_path", "missing_md5", "size", "onedrive_path", "source_copies", "tree", "src_file", "loaded_at"],
    "media_metadata": ["source_table", "file_id", "source_path", "metadata_json", "observed_at"],
    "derived_dates": ["source_table", "source_path", "filename", "size", "asserted_date", "date_source", "_src_file", "loaded_at"],
}


def write_gzip_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


class BestCopyNormalizerTests(unittest.TestCase):
    def test_duckdb_only_normalizes_and_manifest_builder_is_the_resolver(self) -> None:
        try:
            import duckdb
        except ImportError:
            self.skipTest("duckdb not installed")
        with TemporaryDirectory() as raw:
            root = Path(raw)
            pg = root / "pg"
            pg.mkdir()
            md5 = "a" * 32
            sha256 = "1" * 64
            common_path = "Photos/a.jpg"
            source_rows = {
                "r2_occurrence": [["raw", common_path, "a.jpg", 100, md5, "2021-01-02T00:00:00Z", "image/jpeg", "raw", "pg", "2026-09-13T00:00:00Z"]],
                "atomic_path_index": [["r2", "acct", "raw", common_path, "a.jpg", 100, md5, "", sha256, "qx", "2021-01-02T00:00:00Z", "v", 1, "[]", "2026-09-13T00:00:00Z"]],
                "onedrive_manifest": [["archive1", common_path, 100, "2021-01-02T00:00:00Z", "qx", "scan-1", "2026-09-13"]],
                "gdrive_manifest": [["unused", "unused", 1, "text/plain", "2021-01-01", "d", "", "", "", "acct", "pg", "2026-09-13"]],
                "local_files": [["D-current", common_path, "a.jpg", 100, "pg", "2026-09-13T00:00:00Z"]],
                "legacy_hashes": [["legacy", common_path, 100, md5, "pg", "2026-09-13T00:00:00Z"]],
                "recovery_links": [["recovery", "missing", md5, 100, common_path, "[]", "archive1", "pg", "2026-09-13T00:00:00Z"]],
                "media_metadata": [["media.enrichment", "file-1", common_path, json.dumps({"bytes": 100, "title": "Photo A", "read_error": None}), "2026-09-13T00:00:00Z"]],
                "derived_dates": [["raw_duck.resolved", common_path, "a.jpg", 100, "2020-05-01", "filename", "pg", "2026-09-13T00:00:00Z"]],
            }
            for name, header in HEADERS.items():
                write_gzip_csv(pg / f"{name}.csv.gz", header, source_rows[name])

            sha_path = root / "sha256_metadata.csv.gz"
            sha_header = [
                "sha256", "md5", "byte_size", "source_bucket", "source_path",
                "filename", "file_type", "content_type", "custom_mtime",
                "source_uploaded_at", "source_version", "source_etag",
                "storage_class", "computed_at", "computation",
                "custom_metadata_json", "http_metadata_json",
            ]
            write_gzip_csv(
                sha_path,
                sha_header,
                [[sha256, md5, 100, "raw", common_path, "a.jpg", "jpg", "image/jpeg",
                  "2021-01-02T00:00:00Z", "2021-01-03T00:00:00Z", "v1", md5,
                  "STANDARD", "2026-09-13T00:00:00Z", "test", "{}", "{}"]],
            )

            output = root / "out"
            script = Path(__file__).resolve().parents[1] / "tools" / "build_best_copy_duckdb.py"
            command = [
                sys.executable, str(script), "--pg-export-dir", str(pg),
                "--sha-metadata", str(sha_path), "--output-dir", str(output),
                "--limit", "1",
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)

            connection = duckdb.connect(str(output / "normalization.duckdb"), read_only=True)
            try:
                names = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
            finally:
                connection.close()
            self.assertIn("normalization_contract", names)
            self.assertNotIn("exact_content_candidate", names)
            self.assertNotIn("best_copy_resolution", names)

            ledger = sqlite3.connect(output / "manifest-ledger.sqlite")
            try:
                disposition, account, tree, snapshot = ledger.execute(
                    """SELECT disposition, source_account, source_tree, snapshot_id
                       FROM metadata_import_record
                       WHERE source_system = 'onedrive-r2-export'"""
                ).fetchone()
                self.assertEqual(disposition, "bound_unique_verified_content")
                self.assertEqual((account, tree, snapshot), ("archive1", "archive1", "scan-1"))
                self.assertGreater(ledger.execute("SELECT count(*) FROM metadata_assertion").fetchone()[0], 0)
            finally:
                ledger.close()

            receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["authority"], "ManifestBuilder SQLite ledger; DuckDB normalizes and extracts only")
            self.assertIn("no local hydration", receipt["onedrive_policy"])
            self.assertTrue((output / "metadata-review" / "metadata-resolution.csv").is_file())

            repeated = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("immutable output directory is not empty", repeated.stderr)


if __name__ == "__main__":
    unittest.main()
