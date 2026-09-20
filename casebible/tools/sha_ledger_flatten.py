#!/usr/bin/env python3
# Byline: Claude Code · Opus 5 · 2026-09-13
"""Flatten exported SHA-256 ledger partitions (casebible-r2-sha256-record-v2 NDJSON) to a TSV for loading.

Reads NDJSON from stdin (for example `zcat hash-ledger-partitions/*.ndjson.gz | python3 sha_ledger_flatten.py OUT.tsv`)
and writes one line per record: digest, source bucket, source key, lowercase unquoted ETag, source size.
Backslashes, tabs and newlines are escaped for PostgreSQL COPY text format. Read-only with respect to the ledger.
"""
import json
import sys


def pg_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: sha_ledger_flatten.py OUT.tsv < records.ndjson", file=sys.stderr)
        return 2
    written = malformed = 0
    with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as out:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            def text(name: str) -> str:
                # Blank only when absent: a sourceSize of 0 (0-byte object) must stay "0".
                value = record.get(name)
                return "" if value is None else str(value)

            etag = text("sourceEtag").strip('"').lower()
            fields = [text("digest"), text("sourceBucket"), text("sourceKey"), etag, text("sourceSize")]
            out.write("\t".join(pg_text(f) for f in fields) + "\n")
            written += 1
    print(f"flattened={written} malformed={malformed}")
    return 0 if malformed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
