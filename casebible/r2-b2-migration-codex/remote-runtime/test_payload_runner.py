import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import payload_runner as runner


SOURCE_ID = "a" * 64
SHA = "b" * 64
MD5 = "c" * 32


def row(**overrides):
    base = {
        "source_bucket": "casebible-raw",
        "source_path": "folder/file.txt",
        "content_algorithm": "sha256",
        "content_digest": SHA,
        "size": "12",
        "destination_key": f"payloads/sha256/{SHA[:2]}/{SHA}",
        "disposition": "canonical",
        "source_identity": SOURCE_ID,
    }
    base.update(overrides)
    return base


class MappingTests(unittest.TestCase):
    def test_canonical_sha256_mapping(self):
        item = runner.parse_item(row(), 1)
        self.assertEqual(item.destination_remote, runner.DEST_PREFIX + row()["destination_key"])
        self.assertTrue(
            item.destination_remote.startswith("consignatio/intake/raw-dedupe/v1/")
        )
        self.assertNotIn("consignatio/vault/v1/", item.destination_remote)

    def test_md5_cannot_be_canonical(self):
        with self.assertRaises(runner.common.TransferError):
            runner.parse_item(row(content_algorithm="md5", content_digest=MD5), 1)

    def test_md5_source_identity_is_noncanonical(self):
        item = runner.parse_item(
            row(
                content_algorithm="md5",
                content_digest=MD5,
                disposition="source-identity",
                destination_key=f"payloads/source-identity/{SOURCE_ID[:2]}/{SOURCE_ID}",
            ),
            1,
        )
        self.assertEqual(item.disposition, "source-identity")

    def test_unknown_digest_must_be_held(self):
        item = runner.parse_item(
            row(
                content_algorithm="unknown",
                content_digest="",
                disposition="held",
                destination_key=f"payloads/held/{SOURCE_ID[:2]}/{SOURCE_ID}",
            ),
            1,
        )
        self.assertEqual(item.disposition, "held")

    def test_unknown_digest_can_use_positive_source_identity(self):
        item = runner.parse_item(
            row(
                content_algorithm="unknown",
                content_digest="",
                disposition="source-identity",
                destination_key=f"payloads/source-identity/{SOURCE_ID[:2]}/{SOURCE_ID}",
            ),
            1,
        )
        self.assertEqual(item.disposition, "source-identity")
        self.assertEqual(item.content_digest, "")

    def test_source_identity_zero_byte_is_rejected(self):
        with self.assertRaises(runner.common.TransferError):
            runner.parse_item(
                row(
                    content_algorithm="unknown",
                    content_digest="",
                    size="0",
                    disposition="source-identity",
                    destination_key=f"payloads/source-identity/{SOURCE_ID[:2]}/{SOURCE_ID}",
                ),
                1,
            )

    def test_duplicate_payload_destination_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.jsonl"
            second = row(source_path="other/file.txt")
            path.write_text(json.dumps(row()) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
            with self.assertRaises(runner.common.TransferError):
                runner.read_mapping(path, "jsonl")

    def test_traversal_rejected(self):
        with self.assertRaises(runner.common.TransferError):
            runner.parse_item(row(source_path="../escape.txt"), 1)


class RCClientTests(unittest.TestCase):
    def test_rc_socket_path_is_unix_only(self):
        socket_root = runner.RCD_SOCKET_ROOT.as_posix()
        self.assertTrue(socket_root.startswith("/run/"))
        self.assertNotIn("http://", socket_root)

    def test_bulk_defaults_stay_memory_bounded(self):
        parser = runner.build_parser()
        args = parser.parse_args(
            [
                "run",
                "--mode",
                "transfer",
                "--verification",
                "fast",
                "--run-id",
                "bulk",
                "--mapping",
                "mapping.jsonl",
                "--format",
                "jsonl",
            ]
        )
        self.assertEqual(args.b2_chunk_size, "16M")
        self.assertEqual(args.b2_upload_concurrency, 1)
        self.assertEqual(args.max_total_bytes, 2 * 1024**4)


class FakeClient:
    def __init__(self, destination_exists=False):
        self.destination_exists = destination_exists
        self.calls = []

    def call(self, method, payload):
        self.calls.append((method, payload))
        if method == "operations/copyfile":
            self.destination_exists = True
            return {}
        raise AssertionError(f"unexpected direct RC call: {method}")


class PayloadStateTests(unittest.TestCase):
    def setUp(self):
        self.item = runner.parse_item(row(source_etag="etag-1"), 1)
        self.source_stat = {"Size": 12, "ETag": "etag-1", "Hashes": {}}
        self.destination_stat = {"Size": 12, "ID": "b2-file-id"}

    def stat_side_effect(self, client, fs, remote):
        if fs == runner.DEST_FS:
            return self.destination_stat if client.destination_exists else None
        return self.source_stat

    def test_fast_copy_never_claims_verified(self):
        client = FakeClient()
        with patch.object(runner, "rc_stat", side_effect=self.stat_side_effect), patch.object(
            runner, "rc_digest", side_effect=AssertionError("fast mode must not download hashes")
        ):
            result = runner.process_payload(client, self.item, "attempt", "copy", "fast")
        self.assertEqual(result["status"], "copied_unverified")
        self.assertEqual(result["copy_state"], "copied")
        self.assertTrue(result["sha256_metadata_requested"])
        self.assertNotIn("verified_digest", result)
        copy_payload = next(payload for method, payload in client.calls if method == "operations/copyfile")
        self.assertIn(
            f"consignatio-sha256={SHA}",
            copy_payload["_config"]["MetadataSet"],
        )

    def test_fast_preexisting_is_not_recopied_or_verified(self):
        client = FakeClient(destination_exists=True)
        with patch.object(runner, "rc_stat", side_effect=self.stat_side_effect), patch.object(
            runner, "rc_digest", side_effect=AssertionError("fast mode must not download hashes")
        ):
            result = runner.process_payload(client, self.item, "attempt", "copy", "fast")
        self.assertEqual(result["status"], "copied_unverified")
        self.assertEqual(result["copy_state"], "preexisting")
        self.assertFalse(any(method == "operations/copyfile" for method, _ in client.calls))

    def test_verify_promotes_only_after_destination_sha256_match(self):
        client = FakeClient(destination_exists=True)
        with patch.object(runner, "rc_stat", side_effect=self.stat_side_effect), patch.object(
            runner, "rc_digest", side_effect=[SHA, SHA]
        ):
            result = runner.process_payload(client, self.item, "attempt", "verify", "full")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["verified_algorithm"], "sha256")
        self.assertEqual(result["verified_digest"], SHA)
        self.assertFalse(any(method == "operations/copyfile" for method, _ in client.calls))

    def test_verify_mismatch_cannot_claim_verified(self):
        client = FakeClient(destination_exists=True)
        with patch.object(runner, "rc_stat", side_effect=self.stat_side_effect), patch.object(
            runner, "rc_digest", side_effect=[SHA, "d" * 64]
        ):
            with self.assertRaises(runner.common.TransferError):
                runner.process_payload(client, self.item, "attempt", "verify", "full")

    def test_resume_separates_copy_from_verification(self):
        copied = {self.item.destination_key}
        self.assertEqual(
            runner.select_pending_items([self.item], "transfer", set(), copied),
            [],
            "a copied_unverified payload must not be recopied",
        )
        self.assertEqual(
            runner.select_pending_items([self.item], "verify", set(), copied),
            [self.item],
            "a copied_unverified payload remains pending for verification",
        )
        self.assertEqual(
            runner.select_pending_items([self.item], "verify", copied, copied),
            [],
            "a verified payload must not be verified again",
        )

    def test_source_identity_fast_copy_fails_before_remote_access(self):
        item = runner.parse_item(
            row(
                content_algorithm="unknown",
                content_digest="",
                disposition="source-identity",
                destination_key=f"payloads/source-identity/{SOURCE_ID[:2]}/{SOURCE_ID}",
            ),
            1,
        )
        with patch.object(
            runner, "rc_stat", side_effect=AssertionError("fast mode must fail before remote access")
        ):
            with self.assertRaises(runner.common.TransferError):
                runner.process_payload(FakeClient(), item, "attempt", "copy", "fast")

    def test_unknown_source_identity_full_copy_verifies_source_and_destination_sha256(self):
        item = runner.parse_item(
            row(
                content_algorithm="unknown",
                content_digest="",
                disposition="source-identity",
                destination_key=f"payloads/source-identity/{SOURCE_ID[:2]}/{SOURCE_ID}",
            ),
            1,
        )
        client = FakeClient()
        with patch.object(runner, "rc_stat", side_effect=self.stat_side_effect), patch.object(
            runner, "rc_digest", side_effect=[SHA, SHA]
        ):
            result = runner.process_payload(client, item, "attempt", "copy", "full")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["verified_algorithm"], "sha256")
        self.assertEqual(result["verified_digest"], SHA)
        self.assertEqual(result["copy_state"], "copied")

    def test_fast_run_rejects_mixed_mapping_before_plan_or_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            mapping = Path(directory) / "mapping.jsonl"
            mapping.write_text(
                json.dumps(
                    row(
                        content_algorithm="unknown",
                        content_digest="",
                        disposition="source-identity",
                        destination_key=f"payloads/source-identity/{SOURCE_ID[:2]}/{SOURCE_ID}",
                    )
                ) + "\n",
                encoding="utf-8",
            )
            args = runner.build_parser().parse_args(
                [
                    "run", "--mode", "dry-run", "--verification", "fast",
                    "--run-id", "reject-source-identity-fast", "--mapping", str(mapping),
                    "--format", "jsonl",
                ]
            )
            with self.assertRaises(runner.common.TransferError):
                runner.execute(args)


if __name__ == "__main__":
    unittest.main()
