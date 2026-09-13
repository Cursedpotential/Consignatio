"""Read-only logical table parity check; prints no records or credentials."""

from __future__ import annotations

import argparse
import json
import re
import subprocess

from casebible_index.projections.surreal import REQUIRED_TABLES


def snapshot(namespace: str, database: str) -> dict:
    for identifier in (namespace, database):
        if not re.fullmatch(r"[a-zA-Z0-9_]+", identifier):
            raise ValueError("Invalid target identifier")
    entries = []
    for table in sorted(REQUIRED_TABLES):
        rows = f"(SELECT * FROM {table} ORDER BY id)"
        entries.append(
            f"{table}: {{count:array::len({rows}),"
            f"logical_state_sha256:crypto::sha256(<string>{rows})}}"
        )
    query = "RETURN {" + ",".join(entries) + "};\n"
    command = (
        "docker exec -i $(docker ps -q --filter "
        "label=com.docker.compose.service=surreal-intake) /surreal sql "
        f"--endpoint http://127.0.0.1:8000 --namespace {namespace} --database {database} "
        "--json --log none"
    )
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "ovh-files", command],
        input=query,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    if result.returncode:
        raise RuntimeError("Remote parity query failed")
    payload = json.loads(result.stdout)
    if isinstance(payload, list) and len(payload) == 1:
        payload = payload[0]
    if isinstance(payload, dict) and payload.get("status") == "OK":
        payload = payload["result"]
    if not isinstance(payload, dict) or set(payload) != REQUIRED_TABLES:
        raise ValueError("Unexpected parity response")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("namespace")
    parser.add_argument("database")
    args = parser.parse_args()
    if not all(value.startswith("restore_drill_") for value in (args.namespace, args.database)):
        raise ValueError("Comparison target must be a restore-drill namespace and database")
    live = snapshot("consignatio", "intake")
    restored = snapshot(args.namespace, args.database)
    mismatches = [table for table in sorted(REQUIRED_TABLES) if live[table] != restored[table]]
    print(
        json.dumps(
            {
                "tables_compared": len(REQUIRED_TABLES),
                "mismatches": mismatches,
                "live_counts": {key: value["count"] for key, value in live.items()},
                "logical_parity": not mismatches,
            }
        )
    )
    raise SystemExit(1 if mismatches else 0)
