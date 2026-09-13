"""Verify an existing frozen migration partition index without graph access."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.partition_migration_occurrence_map import verify_index

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_migration_partitions.py PARTITION_INDEX")
    print(json.dumps(verify_index(Path(sys.argv[1]))))
