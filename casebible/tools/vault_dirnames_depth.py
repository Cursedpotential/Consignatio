#!/usr/bin/env python3
"""Byline: Claude Code · Fable 5.1 · 2026-09-16

Read-only. Streams a `rclone lsjson -R --files-only` listing of vault/v1 and
prints the distinct directory names at depth 1..N (relative to the listing
root) with file counts and bytes, so the name-normalization regex can be
written from the real names instead of guesses.

usage: vault_dirnames_depth.py <lsjson.json> [max_depth=3]
"""
import json, sys, collections

path = sys.argv[1]
maxd = int(sys.argv[2]) if len(sys.argv) > 2 else 3

files = collections.Counter()
bytes_ = collections.Counter()
# ijson may not be installed; the file is ~500 MB, json.load is fine on the VPS.
with open(path, "rb") as f:
    items = json.load(f)
for it in items:
    parts = it["Path"].split("/")
    size = it.get("Size", 0) or 0
    for d in range(1, min(maxd, len(parts) - 1) + 1):
        key = "/".join(parts[:d])
        files[key] += 1
        bytes_[key] += size

for d in range(1, maxd + 1):
    rows = [(k, files[k], bytes_[k]) for k in files if k.count("/") == d - 1]
    rows.sort(key=lambda r: (-r[2], r[0].lower()))
    print(f"\n=== depth {d}: {len(rows)} dirs ===")
    for k, n, b in rows:
        print(f"{b/1e9:10.2f} GB {n:9d} files  {k}")
