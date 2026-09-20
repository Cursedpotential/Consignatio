"""Byline: Codex | 2026-09-20. Bounded metadata readers and append-only writers."""
from __future__ import annotations

import base64
import configparser
import csv
import hashlib
import gzip
import io
import json
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def write_records(path, rows):
    """Lossless JSON records in Parquet; typed SQL views are provided separately."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    schema = pa.schema([("record", pa.string())])
    count = 0
    with pq.ParquetWriter(path, schema, compression="zstd") as writer:
        batch = []
        for row in rows:
            batch.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            count += 1
            if len(batch) == 5000:
                writer.write_table(pa.table({"record": batch}, schema=schema)); batch = []
        if batch:
            writer.write_table(pa.table({"record": batch}, schema=schema))
    return count


def records(path):
    for batch in pq.ParquetFile(path).iter_batches(batch_size=5000):
        for value in batch.column(0).to_pylist():
            yield json.loads(value)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class Postgres:
    def __init__(self, host="ovh-files-ts", container="fgz1n7useplhk0t91uk7k1aw"):
        self.host, self.container = host, container

    def command(self, writable=False):
        options = "-c statement_timeout=600000 -c lock_timeout=10000"
        if not writable:
            options += " -c default_transaction_read_only=on"
        command = f"docker exec -i -e 'PGOPTIONS={options}' {self.container} psql -X -q -U postgres -d casebible -v ON_ERROR_STOP=1"
        return ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=15", self.host, command]

    def rows(self, select):
        if not select.lstrip().upper().startswith("SELECT ") or ";" in select:
            raise ValueError("Only one SELECT is accepted")
        command = self.command()
        command[-1] = "bash -o pipefail -c " + shlex.quote(command[-1] + " | gzip -c")
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.stdin.write(("COPY (SELECT row_to_json(q)::text FROM (" + select + ") q) TO STDOUT WITH (FORMAT CSV);").encode("utf-8"))
        proc.stdin.close()
        try:
            for row in csv.reader(io.TextIOWrapper(gzip.GzipFile(fileobj=proc.stdout), encoding="utf-8")):
                yield json.loads(row[0])
            error = proc.stderr.read().decode("utf-8", errors="replace")
            if proc.wait():
                raise RuntimeError("Read-only database query failed: " + error[:500])
        finally:
            if proc.poll() is None:
                proc.terminate()
            proc.stdout.close(); proc.stderr.close()

    def remote_read(self, path):
        # All callers supply one of the explicit known migration receipt paths.
        if not path.startswith("/data/consignatio/migrations/") or any(c in path for c in "'\n\r;|"):
            raise ValueError("Not an allowed receipt path")
        result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", self.host,
                                 "sudo -n cat '" + path + "'"], capture_output=True, timeout=60)
        if result.returncode:
            raise RuntimeError("Known migration receipt unavailable")
        return result.stdout.decode("utf-8-sig")


class B2:
    ALLOWED = {"b2_list_buckets", "b2_list_file_names", "b2_list_file_versions",
               "b2_list_unfinished_large_files", "b2_list_parts"}

    def __init__(self, config, remote="b2", bucket="salem-data"):
        cfg = configparser.ConfigParser(interpolation=None)
        try:
            cfg.read(config)
        except (configparser.Error, OSError):
            raise RuntimeError("Rclone configuration unavailable or invalid") from None
        self.credentials = cfg
        section = cfg[remote]
        basic = base64.b64encode((section["account"] + ":" + section["key"]).encode()).decode()
        request = urllib.request.Request("https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
                                         headers={"Authorization": "Basic " + basic})
        self.auth = self.request(request)
        allowed = self.auth.get("allowed", {})
        if allowed.get("namePrefix") or allowed.get("bucketName") not in (None, bucket):
            raise RuntimeError("Cannot certify full bucket inventory with restricted credentials")
        self.bucket = next(b for b in self.call("b2_list_buckets", {"accountId": self.auth["accountId"]})["buckets"] if b["bucketName"] == bucket)

    @staticmethod
    def request(request):
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return json.load(response)
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 2 or getattr(exc, "code", 500) in (400, 401, 403, 404):
                    raise RuntimeError("Metadata API failed: " + str(getattr(exc, "code", type(exc).__name__))) from None
                time.sleep(2 ** attempt)

    def call(self, method, args):
        if method not in self.ALLOWED:
            raise ValueError("B2 mutation or content API prohibited")
        request = urllib.request.Request(self.auth["apiUrl"] + "/b2api/v2/" + method,
                    data=json.dumps(args).encode(), headers={"Authorization": self.auth["authorizationToken"], "Content-Type": "application/json"})
        return self.request(request)

    def files(self, versions=False):
        method = "b2_list_file_versions" if versions else "b2_list_file_names"
        args = {"bucketId": self.bucket["bucketId"], "maxFileCount": 10000}
        seen = set()
        while True:
            page = self.call(method, args)
            yield from page["files"]
            cursor = page.get("nextFileName")
            if not cursor:
                break
            token = (cursor, page.get("nextFileId"))
            if token in seen:
                raise RuntimeError("Repeated B2 pagination cursor")
            seen.add(token)
            args["startFileName"] = cursor
            if versions:
                args["startFileId"] = page["nextFileId"]
