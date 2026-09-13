import tempfile
import unittest
from pathlib import Path

import transfer_runner as runner


class ManifestTests(unittest.TestCase):
    def test_loads_files_from_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.txt"
            manifest.write_text("# explicit\nfolder/a.txt\nfolder/b c.pdf\n", encoding="utf-8")
            self.assertEqual([item.path for item in runner.load_manifest(manifest)], ["folder/a.txt", "folder/b c.pdf"])

    def test_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.txt"
            manifest.write_text("../escape.txt\n", encoding="utf-8")
            with self.assertRaises(runner.TransferError):
                runner.load_manifest(manifest)

    def test_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.txt"
            manifest.write_text("a.txt\na.txt\n", encoding="utf-8")
            with self.assertRaises(runner.TransferError):
                runner.load_manifest(manifest)


class GuardTests(unittest.TestCase):
    def test_destination_must_stay_in_approved_prefix(self):
        with self.assertRaises(runner.TransferError):
            runner.validate_roots("r2:casebible-raw", "b2:salem-data/outside")

    def test_source_must_be_r2(self):
        with self.assertRaises(runner.TransferError):
            runner.validate_roots("od:anywhere", runner.APPROVED_DEST_PREFIX)

    def test_intake_raw_dedupe_prefix_is_the_only_approved_destination(self):
        source, destination = runner.validate_roots(
            "r2:casebible-raw",
            "b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/casebible-raw",
        )
        self.assertEqual(source, "r2:casebible-raw")
        self.assertEqual(
            destination,
            "b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/casebible-raw",
        )
        with self.assertRaises(runner.TransferError):
            runner.validate_roots(
                "r2:casebible-raw",
                "b2:salem-data/consignatio/vault/v1/source-buckets/casebible-raw",
            )

    def test_probe_is_exactly_one_isolated_object(self):
        runner.validate_probe([runner.Item("_system/probe/tiny.txt")])
        with self.assertRaises(runner.TransferError):
            runner.validate_probe([runner.Item("ordinary/file.txt")])
        with self.assertRaises(runner.TransferError):
            runner.validate_probe([
                runner.Item("_system/probe/one.txt"),
                runner.Item("_system/probe/two.txt"),
            ])


if __name__ == "__main__":
    unittest.main()
