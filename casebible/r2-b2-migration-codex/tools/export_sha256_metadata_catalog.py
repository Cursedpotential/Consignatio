"""Export the existing R2 SHA-256 ledger as a metadata-rich CSV shard.

The corpus bytes are never read.  A bounded remote Python reader validates the
256 already-exported NDJSON-gzip partitions and streams the ledger records over
SSH.  The workstation writes a new gzip shard and receipt on E: without
overwriting any prior artifact.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REMOTE_READER = r'''
import csv
import glob
import gzip
import json
import os
import re
import sys

root = sys.argv[1]
expected = int(sys.argv[2])
paths = sorted(glob.glob(os.path.join(root, '[0-9a-f][0-9a-f].ndjson.gz')))
if len(paths) != 256:
    raise SystemExit(f'expected 256 partitions, found {len(paths)}')

digest_re = re.compile(r'^[0-9a-fA-F]{64}$')
md5_re = re.compile(r'^[0-9a-fA-F]{32}$')
writer = csv.writer(sys.stdout, lineterminator='\n')
writer.writerow((
    'sha256', 'md5', 'byte_size', 'source_bucket', 'source_path',
    'filename', 'file_type', 'content_type', 'custom_mtime',
    'source_uploaded_at', 'source_version', 'source_etag', 'storage_class',
    'computed_at', 'computation', 'custom_metadata_json', 'http_metadata_json',
))
count = 0
for path in paths:
    with gzip.open(path, 'rt', encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or row.get('schema') != 'casebible-r2-sha256-record-v2':
                raise ValueError(f'{path}:{line_number}: invalid schema')
            digest = str(row.get('digest') or '').lower()
            md5 = str(row.get('md5Hash') or '').lower()
            size = row.get('sourceSize')
            if not digest_re.fullmatch(digest):
                raise ValueError(f'{path}:{line_number}: invalid SHA-256')
            if md5 and not md5_re.fullmatch(md5):
                raise ValueError(f'{path}:{line_number}: invalid MD5')
            if not isinstance(size, int) or size < 0:
                raise ValueError(f'{path}:{line_number}: invalid sourceSize')
            custom = row.get('customMetadata') or {}
            http = row.get('httpMetadata') or {}
            writer.writerow((
                digest, md5, size, row.get('sourceBucket') or '',
                row.get('sourceKey') or '', row.get('fileName') or '',
                row.get('fileType') or '', http.get('contentType') or '',
                custom.get('mtime') or '', row.get('sourceUploadedAt') or '',
                row.get('sourceVersion') or '', row.get('sourceEtag') or '',
                row.get('storageClass') or '', row.get('computedAt') or '',
                row.get('computation') or '',
                json.dumps(custom, sort_keys=True, separators=(',', ':')),
                json.dumps(http, sort_keys=True, separators=(',', ':')),
            ))
            count += 1
if count != expected:
    raise SystemExit(f'expected {expected} records, found {count}')
'''


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--host", default="ovh-files")
    parser.add_argument(
        "--remote-root",
        default="/data/consignatio/migrations/r2-to-b2/hash-ledger-partitions",
    )
    parser.add_argument("--expected-records", type=int, default=338_318)
    args = parser.parse_args()

    target = args.output.resolve()
    receipt = target.with_suffix(target.suffix + ".receipt.json")
    if target.exists() or receipt.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    process = subprocess.Popen(
        [
            "ssh", args.host,
            f"sudo -n python3 - {args.remote_root} {args.expected_records}",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    process.stdin.write(REMOTE_READER.encode("utf-8"))
    process.stdin.close()

    digest = hashlib.sha256()
    uncompressed_bytes = 0
    with gzip.open(target, "xb", compresslevel=1) as output:
        for block in iter(lambda: process.stdout.read(1024 * 1024), b""):
            digest.update(block)
            uncompressed_bytes += len(block)
            output.write(block)
    stderr = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"SHA metadata export failed ({return_code}): {stderr[-2000:]}")

    result = {
        "schema": "casebible-r2-sha256-metadata-export-v1",
        "source": "r2:casebible-hash-ledger/sha256/v2",
        "partition_count": 256,
        "record_count": args.expected_records,
        "exported_at": utc_now(),
        "sha256_uncompressed_csv": digest.hexdigest(),
        "uncompressed_bytes": uncompressed_bytes,
        "compressed_bytes": target.stat().st_size,
        "output": str(target),
    }
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
