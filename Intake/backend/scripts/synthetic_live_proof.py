"""Explicit one-note live integration proof; never accepts a corpus source path.

Creates a new synthetic collection, runs the actual CLI twice, exercises real
loopback HTTP routes, and retains receipts. No cleanup deletes files or objects.
Use the backend .venv Python. Credentials are read from environment/registry.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from casebible_index.parquet_store import write_json_immutable
from casebible_index.run_status import latest_run_status
from casebible_index.secrets import get_secret

BACKEND = Path(__file__).resolve().parents[1]
SOURCE = BACKEND / "sample_docs" / "correspondence"


def run() -> None:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    output = BACKEND / "output" / f"synthetic-live-{stamp}"
    if BACKEND.drive.upper() != "E:":
        raise RuntimeError("This Windows proof requires development storage on E:")
    files = list(SOURCE.iterdir())
    if len(files) != 1 or files[0].name != "example.txt" or files[0].stat().st_size > 4096:
        raise RuntimeError("Proof requires exactly the bounded committed example.txt")
    before_hash = hashlib.sha256(files[0].read_bytes()).hexdigest()
    key = get_secret("NVIDIA_API_KEY")
    if not key:
        raise RuntimeError("NVIDIA_API_KEY is not available")
    url = os.environ["INTAKE_WEAVIATE_URL"].rstrip("/")
    model = os.environ.get("NIM_EMBED_MODEL", "nvidia/nemotron-3-embed-1b")
    collection = "IntakeSynthetic" + stamp
    source_id = "intake-synthetic-" + stamp
    output.mkdir(parents=True, exist_ok=False)
    env = {
        **os.environ,
        "NVIDIA_API_KEY": key,
        "PYTHONDONTWRITEBYTECODE": "1",
        "TEMP": str(output),
        "TMP": str(output),
        "CASEBIBLE_SOURCE_DIR": str(SOURCE),
        "CASEBIBLE_SOURCE_ID": source_id,
        "CASEBIBLE_OUTPUT_DIR": str(output),
        "INTAKE_WEAVIATE_URL": url,
        "INTAKE_WEAVIATE_COLLECTION": collection,
        "INTAKE_WEAVIATE_TEXT_VECTOR": "text",
        "INTAKE_WEAVIATE_EMBED_MODEL": model,
        "NIM_EMBED_MODEL": model,
        "INTAKE_WEAVIATE_INDEX_ENABLED": "1",
        "INTAKE_MAX_FILE_BYTES": "4096",
        "INTAKE_MAX_EXTRACTED_CHARS": "4096",
        "INTAKE_MAX_CHUNKS_PER_FILE": "8",
        "INTAKE_MAX_INFLIGHT_FILES": "1",
        "NIM_MAX_CONCURRENCY": "1",
        "NIM_MAX_RETRIES": "0",
        "NIM_TIMEOUT_SECONDS": "30",
        "NIM_EMBED_BATCH_SIZE": "8",
        "OMP_NUM_THREADS": "1",
    }
    headers = {}
    if service_key := get_secret("INTAKE_WEAVIATE_API_KEY"):
        headers["Authorization"] = f"Bearer {service_key}"
        env["INTAKE_WEAVIATE_API_KEY"] = service_key
    receipt: dict = {
        "output": str(output),
        "collection": collection,
        "source_id": source_id,
        "weaviate": url,
        "state": "started",
    }
    print(json.dumps(receipt), flush=True)
    try:
        with httpx.Client(timeout=20, headers=headers) as client:
            existing = client.get(url + "/v1/schema")
            existing.raise_for_status()
            receipt["existing_collections"] = [c["class"] for c in existing.json()["classes"]]
            if collection in receipt["existing_collections"]:
                raise RuntimeError("Synthetic collection already exists; refusing reuse")
            schema = {
                "class": collection,
                "description": f"Intake one-note synthetic proof; {model}; no evidence data",
                "properties": [
                    {"name": name, "dataType": ["text"]}
                    for name in (
                        "source_id",
                        "source_path",
                        "document_id",
                        "chunk_id",
                        "filename",
                        "text",
                        "embed_model",
                    )
                ]
                + [{"name": "active", "dataType": ["boolean"]}],
                "vectorConfig": {"text": {"vectorizer": {"none": {}}, "vectorIndexType": "hnsw"}},
            }
            created = client.post(url + "/v1/schema", json=schema)
            created.raise_for_status()
        receipt["runs"] = []
        for number in (1, 2):
            started = time.monotonic()
            with (output / f"index-{number}.log").open("xb") as log:
                result = subprocess.run(
                    [sys.executable, "-m", "casebible_index.cli", "index"],
                    cwd=BACKEND,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=150,
                )
            status = latest_run_status(output)
            receipt["runs"].append(
                {
                    "seconds": time.monotonic() - started,
                    "exit_code": result.returncode,
                    "status": status,
                }
            )
            if (
                result.returncode
                or status.get("failure_events")
                or status.get("state") != "finished"
            ):
                raise RuntimeError(f"Index run {number} failed; inspect retained local log")
            expected = 1 if number == 1 else 0
            if status["files_transformed"] != expected:
                raise RuntimeError(f"Run {number}: expected {expected} transformed files")
            print(f"Index run {number}: transformed={expected}", flush=True)
        # Select an unused loopback port. A competing bind can still win before
        # startup; the child must stay alive and report this proof's snapshot.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with (output / "api.log").open("xb") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "casebible_index.cli",
                    "serve",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=BACKEND,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                base = f"http://127.0.0.1:{port}"
                with httpx.Client(timeout=45) as client:
                    for _ in range(40):
                        if process.poll() is not None:
                            raise RuntimeError("Proof API exited before readiness")
                        try:
                            health = client.get(base + "/health")
                            if (
                                health.status_code == 200
                                and process.poll() is None
                                and str(output) in str(health.json().get("snapshot"))
                            ):
                                break
                        except httpx.ConnectError:
                            pass
                        time.sleep(0.25)
                    else:
                        raise RuntimeError("Proof API readiness timed out")
                    receipt["searches"] = {}
                    for mode, query in (
                        ("keyword", "Synthetic scheduling note"),
                        ("hybrid", "When is the fictional review meeting scheduled?"),
                    ):
                        response = client.post(
                            base + "/filesystem/search",
                            json={"query": query, "mode": mode, "limit": 5},
                        )
                        response.raise_for_status()
                        data = response.json()
                        if len(data["hits"]) != 1 or data["hits"][0]["source_id"] != source_id:
                            raise RuntimeError(f"Unexpected {mode} search identity/count")
                        if Path(data["hits"][0]["source_path"]) != files[0]:
                            raise RuntimeError("Search source path mismatch")
                        receipt["searches"][mode] = data
                        print(f"{mode}: one verified synthetic hit", flush=True)
            finally:
                process.terminate()
                process.wait(timeout=10)
        if hashlib.sha256(files[0].read_bytes()).hexdigest() != before_hash:
            raise RuntimeError("Committed source hash changed during proof")
        receipt["state"] = "passed"
        receipt["source_unchanged"] = True
        receipt["desktop_ui_verified"] = False
    except Exception as exc:
        receipt["state"] = "failed"
        receipt["error_type"] = type(exc).__name__
        raise
    finally:
        write_json_immutable(output / "proof.json", receipt)
        print(f"Receipt: {output / 'proof.json'}", flush=True)


if __name__ == "__main__":
    run()
