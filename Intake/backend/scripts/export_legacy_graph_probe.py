"""Export at most 25 historical metadata rows, read-only, without opening objects.

Output is a new manifest, never an object-copy or B2 operation. This retains
original location keys, historical metadata and explicit query provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

QUERY = """
SELECT coalesce(jsonb_agg(to_jsonb(selected)), '[]'::jsonb)
FROM (
 SELECT r.* FROM raw_duck.r2_files r
 WHERE r.bucket = 'casebible-raw'
 AND EXISTS (
   SELECT 1 FROM inventory.atomic_path_index i
   WHERE i.store='r2' AND i.account_key='' AND i.container=r.bucket
     AND i.path=replace(r.path, chr(92), '/')
 )
 AND NOT EXISTS (
   SELECT 1 FROM rootcsv.isolated_credentials c
   WHERE c.bucket=r.bucket AND c.path=r.path
 )
 AND NOT EXISTS (
   SELECT 1 FROM rootcsv.excluded e WHERE e.bucket=r.bucket AND e.path=r.path
 )
 ORDER BY r.path COLLATE "C", r.size, r.md5
 LIMIT 25
) selected;
""".strip()


def export(destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError("Manifest destination already exists")
    script = "BEGIN READ ONLY; SET LOCAL statement_timeout='20s';\n" + QUERY + "\nCOMMIT;"
    completed = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=10",
            "ovh-files",
            "docker exec -i fgz1n7useplhk0t91uk7k1aw psql -U postgres -d casebible "
            "-X -A -t -q -v ON_ERROR_STOP=1",
        ],
        input=script,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=40,
    )
    if completed.returncode:
        raise RuntimeError("Read-only legacy query failed; no manifest written")
    rows = json.loads(completed.stdout)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 25:
        raise ValueError("Unexpected historical selection size")
    document = {
        "schema": "intake-legacy-catalog-projection-v1",
        "imported_at": datetime.now(UTC).isoformat(),
        "catalog_locator": "postgresql://ovh-files/casebible/raw_duck.r2_files",
        "source_query": QUERY,
        "selection_scope": "Bounded historical atomic-hint metadata proof; not live completeness",
        "source_roots": {
            "casebible-raw": {
                "root_locator": "r2:casebible-raw",
                "store_kind": "historical-r2-catalog",
                "label": "Historical R2 raw catalog - 25-row graph proof, not live census",
            }
        },
        "rows": rows,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
    return {
        "manifest": str(destination),
        "rows": len(rows),
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.destination)))
