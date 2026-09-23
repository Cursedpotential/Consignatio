#!/usr/bin/env python3
# Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
"""Build the vault_key -> (sha1, md5, catalog path) map for the chat-event loader.

The catalog is the source of truth for what a file is and where it came from (owner rule
2026-09-16), so a source_file node is never vault-key-only. Weaviate stores the vault key
("consignatio/vault/v1/<rel>"); the catalog's vault_objects is keyed by <rel>, and the original
location comes from source_occurrences joined on the content md5.

Writes SQL to SQLF, runs it read-only in the catalog container, writes a TSV to OUT.
Env: SPOOL, OUT, SQLF, PG.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

SPOOL = os.environ.get("SPOOL", "/data/probata/volumes/timeline-mvp/chat_events_20260919.jsonl")
OUT = os.environ.get("OUT", "/data/probata/volumes/timeline-mvp/sources_20260919.tsv")
SQLF = os.environ.get("SQLF", "/data/probata/volumes/timeline-mvp/resolve_sources_20260919.sql")
PG = os.environ.get("PG", "fgz1n7useplhk0t91uk7k1aw")
PREFIX = os.environ.get("VAULT_PREFIX", "consignatio/vault/v1/")

SQL = """WITH want(vault_key) AS (VALUES {vals}),
     stripped AS (SELECT vault_key, regexp_replace(vault_key, '^{prefix}', '') AS key FROM want)
SELECT s.vault_key,
       coalesce(v.sha1, b.sha1, ''),
       coalesce(v.md5, ''),
       coalesce((SELECT so.source || '/' || so.scope || '/' || so.path
                   FROM raw_duck.source_occurrences so
                  WHERE v.md5 IS NOT NULL AND so.md5 = v.md5 AND so.scope <> ''
                  ORDER BY so.recorded_at LIMIT 1),
                (SELECT so.source || '/' || so.path
                   FROM raw_duck.source_occurrences so
                  WHERE v.md5 IS NOT NULL AND so.md5 = v.md5
                  ORDER BY so.recorded_at LIMIT 1), '')
  FROM stripped s
  LEFT JOIN raw_duck.vault_objects v ON v.key = s.key
  LEFT JOIN raw_duck.b2_objects b ON b.key = s.vault_key;
"""


def main() -> int:
    keys = set()
    with open(SPOOL, encoding="utf-8") as fh:
        for line in fh:
            v = json.loads(line)["p"].get("vault_key")
            if v:
                keys.add(v)
    print(f"distinct vault_keys: {len(keys)}", file=sys.stderr)
    vals = ",".join("('" + k.replace("'", "''") + "')" for k in sorted(keys))
    with open(SQLF, "w", encoding="utf-8") as fh:
        fh.write(SQL.format(vals=vals, prefix=PREFIX))
    with open(SQLF, "rb") as stdin, open(OUT, "wb") as stdout:
        subprocess.run(["docker", "exec", "-i", PG, "psql", "-U", "postgres", "-d", "casebible",
                        "-v", "ON_ERROR_STOP=1", "-qAt", "-F", "\t"],
                       stdin=stdin, stdout=stdout, check=True)
    rows = sha = md5 = cat = 0
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows += 1
            sha += bool(len(f) > 1 and f[1])
            md5 += bool(len(f) > 2 and f[2])
            cat += bool(len(f) > 3 and f[3])
    print(f"rows={rows} with_sha1={sha} with_md5={md5} with_catalog_path={cat} -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
