#!/usr/bin/env python3
"""Content-addressed R2 to B2 payload transfer over an isolated rclone RC socket.

This runner consumes an explicit reviewed CSV or JSONL mapping. It starts one
root-only rclone daemon bound only to a Unix-domain socket, then uses structured
JSON calls with bounded concurrency. It never lists a source bucket, interpolates
object names into a shell, overwrites a destination, or deletes/moves/syncs data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence

import transfer_runner as common


PAYLOAD_STATE_ROOT = common.RUNTIME_ROOT / "payload-state"
DEST_FS = "b2:salem-data"
DEST_PREFIX = "consignatio/intake/raw-dedupe/v1/"
BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
HEX_RE = re.compile(r"^[0-9a-f]+$")
DISPOSITIONS = {"canonical", "source-identity", "held"}
ALGORITHMS = {"sha256", "md5", "unknown"}
RCD_SOCKET_ROOT = Path("/run/consignatio-r2-b2")
QUARANTINE_SOCKET_ROOT = Path("/data/consignatio/to_be_deleted/r2-b2-rcd-sockets")


@dataclass(frozen=True, slots=True)
class PayloadItem:
    source_bucket: str
    source_path: str
    content_algorithm: str
    content_digest: str
    size: int
    destination_key: str
    disposition: str
    source_identity: str
    source_md5: str
    source_etag: str

    @property
    def source_fs(self) -> str:
        return f"r2:{self.source_bucket}"

    @property
    def destination_remote(self) -> str:
        return DEST_PREFIX + self.destination_key


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: Path, timeout: float):
        super().__init__("localhost", timeout=timeout)
        self.socket_path = str(socket_path)

    def connect(self) -> None:
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(self.timeout)
        connection.connect(self.socket_path)
        self.sock = connection


class RcloneRC:
    def __init__(self, socket_path: Path, timeout_seconds: int):
        self.socket_path = socket_path
        self.timeout_seconds = timeout_seconds

    def call(self, method: str, payload: Mapping[str, object]) -> dict[str, object]:
        connection = UnixHTTPConnection(self.socket_path, self.timeout_seconds)
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        try:
            connection.request(
                "POST",
                "/" + method.lstrip("/"),
                body=body,
                headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
            )
            response = connection.getresponse()
            raw = response.read()
        finally:
            connection.close()
        try:
            decoded = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise common.TransferError(f"rclone RC returned malformed response for {method}") from exc
        if response.status >= 400 or (isinstance(decoded, dict) and decoded.get("error")):
            message = decoded.get("error") if isinstance(decoded, dict) else response.reason
            raise common.TransferError(f"rclone RC {method} failed: {message}")
        if not isinstance(decoded, dict):
            raise common.TransferError(f"rclone RC returned a non-object response for {method}")
        return decoded


class RcloneDaemon:
    def __init__(self, args: argparse.Namespace, attempt_dir: Path, env: dict[str, str]):
        self.args = args
        self.attempt_dir = attempt_dir
        self.env = env
        self.process: subprocess.Popen[bytes] | None = None
        self.log_handle = None
        self.socket_path = RCD_SOCKET_ROOT / f"rcd-{os.getpid()}-{int(time.time())}.sock"

    def __enter__(self) -> RcloneRC:
        RCD_SOCKET_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(RCD_SOCKET_ROOT, 0o700)
        if self.socket_path.exists():
            raise common.TransferError(f"refusing to replace existing RC socket: {self.socket_path}")
        self.log_handle = (self.attempt_dir / "rcd.log").open("ab", buffering=0)
        command = [
            "rclone", "rcd",
            "--config", str(common.RCLONE_CONFIG),
            "--rc-addr", f"unix://{self.socket_path}",
            "--rc-no-auth",
            "--immutable",
            "--metadata",
            "--transfers", str(self.args.workers),
            "--checkers", str(self.args.checkers),
            "--buffer-size", self.args.buffer_size,
            "--multi-thread-streams", "0",
            "--b2-chunk-size", self.args.b2_chunk_size,
            "--b2-upload-concurrency", str(self.args.b2_upload_concurrency),
            "--max-backlog", str(self.args.max_backlog),
            "--contimeout", self.args.connect_timeout,
            "--timeout", self.args.io_timeout,
            "--retries", "1",
            "--low-level-retries", str(self.args.low_level_retries),
            "--retries-sleep", self.args.retry_sleep,
        ]
        try:
            self.process = subprocess.Popen(
                command,
                env=self.env,
                stdin=subprocess.DEVNULL,
                stdout=self.log_handle,
                stderr=subprocess.STDOUT,
                close_fds=True,
                start_new_session=True,
            )
            deadline = time.monotonic() + 30
            client = RcloneRC(self.socket_path, self.args.item_timeout_seconds)
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise common.TransferError(f"rclone rcd exited during startup with {self.process.returncode}")
                if self.socket_path.exists():
                    # The parent directory is already root-only. Tighten the socket
                    # itself before the first request as defense in depth.
                    os.chmod(self.socket_path, 0o600)
                    try:
                        client.call("core/version", {})
                    except (OSError, common.TransferError):
                        time.sleep(0.1)
                        continue
                    mode = self.socket_path.stat().st_mode & 0o777
                    if mode & 0o077:
                        raise common.TransferError(f"RC socket permissions are too broad: {mode:o}")
                    return client
                time.sleep(0.1)
            raise common.TransferError("rclone rcd did not become ready within 30 seconds")
        except BaseException:
            self._stop_and_quarantine()
            raise

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._stop_and_quarantine()

    def _stop_and_quarantine(self) -> None:
        if self.process is not None and self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=5)
        if self.log_handle is not None:
            self.log_handle.close()
            self.log_handle = None
        if self.socket_path.exists():
            QUARANTINE_SOCKET_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
            destination = QUARANTINE_SOCKET_ROOT / self.socket_path.name
            os.replace(self.socket_path, destination)


def normalize_hex(value: object, *, field: str, length: int | None = None) -> str:
    text = str(value or "").strip().lower()
    if not text or not HEX_RE.fullmatch(text) or (length is not None and len(text) != length):
        expected = f" exactly {length}" if length is not None else ""
        raise common.TransferError(f"{field} must contain{expected} lowercase hexadecimal characters")
    return text


def parse_item(raw: Mapping[str, object], row_number: int) -> PayloadItem:
    bucket = str(raw.get("source_bucket", "")).strip()
    if not BUCKET_RE.fullmatch(bucket):
        raise common.TransferError(f"row {row_number}: invalid R2 source_bucket")
    try:
        source_path = common.normalize_path(str(raw.get("source_path", "")))
        destination_key = common.normalize_path(str(raw.get("destination_key", "")))
    except common.TransferError as exc:
        raise common.TransferError(f"row {row_number}: {exc}") from exc
    if not destination_key.startswith("payloads/"):
        raise common.TransferError(f"row {row_number}: destination_key must be under payloads/")
    algorithm = str(raw.get("content_algorithm", "")).strip().lower()
    disposition = str(raw.get("disposition", "")).strip().lower()
    if algorithm not in ALGORITHMS:
        raise common.TransferError(f"row {row_number}: unsupported content_algorithm {algorithm!r}")
    if disposition not in DISPOSITIONS:
        raise common.TransferError(f"row {row_number}: unsupported disposition {disposition!r}")
    try:
        size = int(str(raw.get("size", "")).strip())
    except ValueError as exc:
        raise common.TransferError(f"row {row_number}: size must be an integer") from exc
    if size < 0:
        raise common.TransferError(f"row {row_number}: size must be non-negative")
    source_identity_raw = str(raw.get("source_identity", "")).strip().lower()
    source_identity = normalize_hex(source_identity_raw, field=f"row {row_number} source_identity", length=64)
    source_md5_raw = str(raw.get("source_md5", "")).strip().lower()
    source_md5 = (
        normalize_hex(source_md5_raw, field=f"row {row_number} source_md5", length=32)
        if source_md5_raw
        else ""
    )
    source_etag = str(raw.get("source_etag", "")).strip().strip('"').lower()

    if algorithm == "sha256":
        digest = normalize_hex(raw.get("content_digest"), field=f"row {row_number} content_digest", length=64)
        expected = f"payloads/sha256/{digest[:2]}/{digest}"
        if disposition != "canonical" or destination_key != expected:
            raise common.TransferError(
                f"row {row_number}: SHA-256 canonical payload must use destination_key {expected!r}"
            )
    elif algorithm == "md5":
        digest = normalize_hex(raw.get("content_digest"), field=f"row {row_number} content_digest", length=32)
        if disposition == "canonical":
            raise common.TransferError(f"row {row_number}: MD5 cannot authorize canonical deduplication")
        prefix = "payloads/source-identity" if disposition == "source-identity" else "payloads/held"
        expected = f"{prefix}/{source_identity[:2]}/{source_identity}"
        if destination_key != expected:
            raise common.TransferError(f"row {row_number}: expected non-canonical destination_key {expected!r}")
    else:
        digest = ""
        if disposition == "canonical":
            raise common.TransferError(f"row {row_number}: unknown digest state cannot be canonical")
        prefix = "payloads/source-identity" if disposition == "source-identity" else "payloads/held"
        expected = f"{prefix}/{source_identity[:2]}/{source_identity}"
        if destination_key != expected:
            raise common.TransferError(f"row {row_number}: expected non-canonical destination_key {expected!r}")
    if disposition == "source-identity" and size <= 0:
        raise common.TransferError(f"row {row_number}: source-identity payload must have positive size")
    return PayloadItem(
        source_bucket=bucket,
        source_path=source_path,
        content_algorithm=algorithm,
        content_digest=digest,
        size=size,
        destination_key=destination_key,
        disposition=disposition,
        source_identity=source_identity,
        source_md5=source_md5,
        source_etag=source_etag,
    )


def read_mapping(path: Path, format_name: str) -> list[PayloadItem]:
    if not path.is_file():
        raise common.TransferError(f"mapping manifest is not a regular file: {path}")
    rows: list[Mapping[str, object]] = []
    if format_name == "csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise common.TransferError("CSV mapping has no header")
            rows.extend(reader)
    else:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                text = raw.strip()
                if not text or text.startswith("#"):
                    continue
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise common.TransferError(f"JSONL line {line_number}: invalid JSON") from exc
                if not isinstance(parsed, dict):
                    raise common.TransferError(f"JSONL line {line_number}: expected an object")
                rows.append(parsed)
    if not rows:
        raise common.TransferError("mapping manifest contains no payload items")
    items = [parse_item(row, index) for index, row in enumerate(rows, start=2 if format_name == "csv" else 1)]
    source_seen: set[tuple[str, str]] = set()
    destination_seen: set[str] = set()
    for item in items:
        source_key = (item.source_bucket, item.source_path)
        if source_key in source_seen:
            raise common.TransferError(f"duplicate source occurrence in mapping: {source_key!r}")
        if item.destination_key in destination_seen:
            raise common.TransferError(f"duplicate destination payload in mapping: {item.destination_key!r}")
        source_seen.add(source_key)
        destination_seen.add(item.destination_key)
    return items


def plan_hash(items: Sequence[PayloadItem]) -> str:
    digest = hashlib.sha256()
    for item in items:
        digest.update(json.dumps(asdict(item), sort_keys=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def configure_plan(run_dir: Path, args: argparse.Namespace, items: Sequence[PayloadItem]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = {
        "schema": "consignatio-r2-b2-payload-run/v1",
        "run_id": args.run_id,
        "mapping_sha256": plan_hash(items),
        "planned_count": len(items),
        "planned_bytes": sum(item.size for item in items if item.disposition != "held"),
        "created_utc": common.utc_now(),
    }
    config_path = run_dir / "run.json"
    if config_path.exists():
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        for key in ("mapping_sha256", "planned_count", "planned_bytes"):
            if existing.get(key) != config[key]:
                raise common.TransferError("run ID already exists with different immutable mapping inputs")
        return
    common.json_dump(config_path, config)
    for item in items:
        common.append_jsonl(
            run_dir / "planned.jsonl",
            {
                "recorded_utc": common.utc_now(),
                "run_id": args.run_id,
                "status": "planned",
                **asdict(item),
                "source": f"{item.source_fs}/{item.source_path}",
                "destination": f"{DEST_FS}/{item.destination_remote}",
            },
        )


def verified_destinations(run_dir: Path) -> set[str]:
    ledger = run_dir / "verified.jsonl"
    if not ledger.exists():
        return set()
    result: set[str] = set()
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        if raw:
            row = json.loads(raw)
            if row.get("status") == "verified":
                result.add(str(row.get("destination_key")))
    return result


def copied_unverified_destinations(run_dir: Path) -> set[str]:
    ledger = run_dir / "copied_unverified.jsonl"
    if not ledger.exists():
        return set()
    result: set[str] = set()
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        if raw:
            row = json.loads(raw)
            if row.get("status") == "copied_unverified":
                result.add(str(row.get("destination_key")))
    return result


def select_pending_items(
    items: Sequence[PayloadItem],
    mode: str,
    verified: set[str],
    copied_unverified: set[str],
) -> list[PayloadItem]:
    if mode == "verify":
        return [
            item
            for item in items
            if item.destination_key in copied_unverified and item.destination_key not in verified
        ]
    return [
        item
        for item in items
        if item.destination_key not in verified and item.destination_key not in copied_unverified
    ]


def rc_stat(client: RcloneRC, fs: str, remote: str) -> dict[str, object] | None:
    response = client.call(
        "operations/stat",
        {"fs": fs, "remote": remote, "opt": {"filesOnly": True, "showHash": True, "metadata": True}},
    )
    item = response.get("item")
    if item is None:
        return None
    if not isinstance(item, dict):
        raise common.TransferError("rclone stat returned malformed item")
    return item


def rc_digest(client: RcloneRC, fs: str, remote: str, algorithm: str) -> str:
    hash_type = "SHA-256" if algorithm == "sha256" else "MD5"
    response = client.call(
        "operations/hashsumfile",
        {"fs": fs, "remote": remote, "hashType": hash_type, "download": True, "base64": False},
    )
    digest = str(response.get("hash", "")).lower()
    expected_length = 64 if algorithm == "sha256" else 32
    return normalize_hex(digest, field=f"computed {algorithm}", length=expected_length)


def stat_hash(stat: Mapping[str, object], algorithm: str) -> str:
    hashes = stat.get("Hashes", stat.get("hashes", {}))
    if not isinstance(hashes, Mapping):
        return ""
    wanted = algorithm.replace("-", "").lower()
    for key, value in hashes.items():
        if str(key).replace("-", "").lower() == wanted and value:
            return str(value).strip().lower()
    return ""


def stat_etag(stat: Mapping[str, object]) -> str:
    metadata = stat.get("Metadata", stat.get("metadata", {}))
    candidates: list[object] = [stat.get("ETag"), stat.get("etag")]
    if isinstance(metadata, Mapping):
        candidates.extend(metadata.get(key) for key in ("etag", "ETag", "eTag"))
    for value in candidates:
        if value:
            return str(value).strip().strip('"').lower()
    return ""


def validate_fast_source_assertion(item: PayloadItem, source_stat: Mapping[str, object]) -> dict[str, str]:
    """Validate a cheap remote fingerprint without downloading source bytes."""
    observed_md5 = stat_hash(source_stat, "md5")
    observed_sha256 = stat_hash(source_stat, "sha256")
    observed_etag = stat_etag(source_stat)
    checks: dict[str, str] = {}

    if item.source_md5:
        if not observed_md5:
            raise common.TransferError("source MD5 assertion is present but remote stat exposes no MD5")
        if observed_md5 != item.source_md5:
            raise common.TransferError(
                f"source MD5 drift: manifest={item.source_md5} remote={observed_md5}"
            )
        checks["md5"] = observed_md5
    elif item.content_algorithm == "md5":
        if not observed_md5:
            raise common.TransferError("MD5 payload requires remote MD5 for fast validation")
        if observed_md5 != item.content_digest:
            raise common.TransferError(
                f"source MD5 drift: manifest={item.content_digest} remote={observed_md5}"
            )
        checks["md5"] = observed_md5

    if item.source_etag:
        if not observed_etag:
            raise common.TransferError("source ETag assertion is present but remote stat exposes no ETag")
        if observed_etag != item.source_etag:
            raise common.TransferError(
                f"source ETag drift: manifest={item.source_etag} remote={observed_etag}"
            )
        checks["etag"] = observed_etag

    if item.content_algorithm == "sha256" and observed_sha256:
        if observed_sha256 != item.content_digest:
            raise common.TransferError(
                f"source SHA-256 drift: manifest={item.content_digest} remote={observed_sha256}"
            )
        checks["sha256"] = observed_sha256

    if not checks:
        raise common.TransferError(
            "fast mode requires a remotely comparable SHA-256, source_md5, or source_etag assertion; "
            "use full verification when none is available"
        )
    return checks


def copy_payload(client: RcloneRC, item: PayloadItem) -> str:
    metadata_set: list[str] = []
    if item.content_algorithm == "sha256":
        metadata_set.append(f"consignatio-sha256={item.content_digest}")
    client.call(
        "operations/copyfile",
        {
            "srcFs": item.source_fs,
            "srcRemote": item.source_path,
            "dstFs": DEST_FS,
            "dstRemote": item.destination_remote,
            "_config": {
                "Immutable": True,
                "Metadata": True,
                "MetadataSet": metadata_set,
            },
        },
    )
    return "copied"


def process_payload(
    client: RcloneRC,
    item: PayloadItem,
    attempt_id: str,
    operation: str,
    verification: str,
) -> dict[str, object]:
    base: dict[str, object] = {
        "recorded_utc": common.utc_now(),
        "attempt_id": attempt_id,
        **asdict(item),
        "source": f"{item.source_fs}/{item.source_path}",
        "destination": f"{DEST_FS}/{item.destination_remote}",
    }
    if item.disposition == "held":
        return {**base, "status": "held", "reason": "digest state is not authorized for payload copy"}
    if item.disposition == "source-identity" and verification != "full":
        raise common.TransferError(
            "source-identity payload requires --verification full; fast copy is forbidden"
        )

    source_stat = rc_stat(client, item.source_fs, item.source_path)
    if source_stat is None:
        raise common.TransferError("explicit source object is missing")
    if int(source_stat.get("Size", -1)) != item.size:
        raise common.TransferError(
            f"source size drift: manifest={item.size} remote={source_stat.get('Size')}"
        )
    destination_stat = rc_stat(client, DEST_FS, item.destination_remote)
    if operation == "verify" and destination_stat is None:
        raise common.TransferError("cannot verify: destination is absent")

    if verification == "fast" and operation == "copy":
        source_assertions = validate_fast_source_assertion(item, source_stat)
        copy_state = "preexisting"
        if destination_stat is None:
            copy_state = copy_payload(client, item)
            destination_stat = rc_stat(client, DEST_FS, item.destination_remote)
        if destination_stat is None:
            raise common.TransferError("destination is absent after copy")
        if int(destination_stat.get("Size", -1)) != item.size:
            raise common.TransferError("destination size differs after copy")
        return {
            **base,
            "status": "copied_unverified",
            "copy_state": copy_state,
            "source_assertions": source_assertions,
            "destination_stat": destination_stat,
            "sha256_metadata_requested": item.content_algorithm == "sha256" and copy_state == "copied",
            "verification_required": "destination_sha256_download",
        }

    # Full mode deliberately downloads both source and destination. SHA-256 is
    # the verification currency even for conservative MD5/source-identity rows.
    if item.source_etag:
        observed_etag = stat_etag(source_stat)
        if not observed_etag or observed_etag != item.source_etag:
            raise common.TransferError(
                f"source ETag drift: manifest={item.source_etag} remote={observed_etag or 'unavailable'}"
            )
    expected_md5 = item.source_md5 or (item.content_digest if item.content_algorithm == "md5" else "")
    if expected_md5:
        source_md5 = rc_digest(client, item.source_fs, item.source_path, "md5")
        if source_md5 != expected_md5:
            raise common.TransferError(
                f"source MD5 drift: manifest={expected_md5} remote={source_md5}"
            )
    source_sha256 = rc_digest(client, item.source_fs, item.source_path, "sha256")
    if item.content_algorithm == "sha256" and source_sha256 != item.content_digest:
        raise common.TransferError(
            f"source SHA-256 drift: manifest={item.content_digest} remote={source_sha256}"
        )
    if destination_stat is None:
        if operation != "copy":
            raise common.TransferError("cannot verify: destination is absent")
        copy_state = copy_payload(client, item)
        destination_stat = rc_stat(client, DEST_FS, item.destination_remote)
    else:
        copy_state = "preexisting"
    if destination_stat is None:
        raise common.TransferError("destination is absent after copy")
    if int(destination_stat.get("Size", -1)) != item.size:
        raise common.TransferError("destination size differs after copy")
    destination_sha256 = rc_digest(client, DEST_FS, item.destination_remote, "sha256")
    if destination_sha256 != source_sha256:
        raise common.TransferError("destination SHA-256 differs from source SHA-256")
    return {
        **base,
        "status": "verified",
        "copy_state": copy_state,
        "verified_algorithm": "sha256",
        "verified_digest": destination_sha256,
        "destination_stat": destination_stat,
        "sha256_metadata_requested": item.content_algorithm == "sha256" and copy_state == "copied",
    }


def apply_memory_limit(limit_mib: int) -> None:
    if sys.platform != "linux":
        return
    import resource

    limit = limit_mib * 1024 * 1024
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    effective_hard = hard if hard != resource.RLIM_INFINITY else limit
    resource.setrlimit(resource.RLIMIT_AS, (min(limit, effective_hard), effective_hard))


def iter_bounded_results(
    executor: ThreadPoolExecutor,
    client: RcloneRC,
    items: Iterable[PayloadItem],
    attempt_id: str,
    workers: int,
    deadline: float,
    operation: str,
    verification: str,
) -> Iterator[tuple[PayloadItem, dict[str, object] | BaseException]]:
    iterator = iter(items)
    active: dict[Future[dict[str, object]], PayloadItem] = {}

    def fill() -> None:
        while len(active) < workers * 2:
            if time.monotonic() >= deadline:
                return
            try:
                item = next(iterator)
            except StopIteration:
                return
            active[
                executor.submit(process_payload, client, item, attempt_id, operation, verification)
            ] = item

    fill()
    while active:
        if time.monotonic() >= deadline:
            for future in active:
                future.cancel()
            raise common.TransferError("payload run exceeded the global duration ceiling")
        done, _ = wait(active, timeout=min(1.0, max(0.0, deadline - time.monotonic())), return_when=FIRST_COMPLETED)
        for future in done:
            item = active.pop(future)
            try:
                yield item, future.result()
            except BaseException as exc:  # returned to the single ledger writer
                yield item, exc
        fill()


def execute(args: argparse.Namespace) -> int:
    if not common.RUN_ID_RE.fullmatch(args.run_id):
        raise common.TransferError("run ID must be 1-80 safe filename characters")
    if not (1 <= args.workers <= 8 and 1 <= args.checkers <= 16):
        raise common.TransferError("workers must be 1-8 and checkers must be 1-16")
    if not (1 <= args.b2_upload_concurrency <= 2):
        raise common.TransferError("B2 upload concurrency must be 1-2 to preserve the memory bound")
    items = read_mapping(args.mapping, args.format)
    if (
        args.mode != "verify"
        and args.verification != "full"
        and any(item.disposition == "source-identity" for item in items)
    ):
        raise common.TransferError(
            "mapping contains source-identity payloads; use --verification full or a canonical-only mapping"
        )
    total_bytes = sum(item.size for item in items if item.disposition != "held")
    if total_bytes > args.max_total_bytes:
        raise common.TransferError(
            f"planned payload bytes {total_bytes} exceed ceiling {args.max_total_bytes}"
        )
    if args.mode == "probe":
        if len(items) != 1:
            raise common.TransferError("probe mode requires exactly one mapped item")
        item = items[0]
        if item.size > args.probe_max_bytes or not any(item.source_path.startswith(marker) for marker in common.PROBE_MARKERS):
            raise common.TransferError("probe must be one <=1 MiB isolated _system/canary or _system/probe source")
    elif args.mode in {"transfer", "verify"} and not common.corpus_enabled():
        raise common.TransferError(
            f"corpus execution is disabled; {common.ENABLE_FILE} must contain {common.ENABLE_PHRASE!r}"
        )

    run_dir = (PAYLOAD_STATE_ROOT / args.run_id).resolve()
    if run_dir.parent != PAYLOAD_STATE_ROOT.resolve():
        raise common.TransferError("payload state escaped the controlled state root")
    configure_plan(run_dir, args, items)
    already_verified = verified_destinations(run_dir)
    already_copied_unverified = copied_unverified_destinations(run_dir)
    if args.mode == "verify":
        # Verification never creates a destination. Only rows previously
        # recorded as copied_unverified are eligible for promotion.
        pending = select_pending_items(items, args.mode, already_verified, already_copied_unverified)
        operation = "verify"
        verification = "full"
    else:
        # A fast-copy receipt suppresses recopy but does not suppress a later
        # verify run. Full-copy resumes only destinations not already copied.
        pending = select_pending_items(items, args.mode, already_verified, already_copied_unverified)
        operation = "copy"
        verification = args.verification
    attempt_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{os.getpid()}"
    attempt_dir = run_dir / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    attempt = {
        "attempt_id": attempt_id,
        "started_utc": common.utc_now(),
        "mode": args.mode,
        "operation": operation,
        "verification": verification,
        "planned": len(items),
        "pending": len(pending),
        "planned_bytes": total_bytes,
        "workers": args.workers,
        "memory_limit_mib": args.memory_limit_mib,
        "b2_chunk_size": args.b2_chunk_size,
        "b2_upload_concurrency": args.b2_upload_concurrency,
    }
    common.json_dump(attempt_dir / "attempt.json", attempt)

    if args.mode == "dry-run":
        result = {**attempt, "finished_utc": common.utc_now(), "result": "dry-run", "copied": 0, "copied_unverified": 0, "verified": 0, "failed": 0, "held": sum(item.disposition == "held" for item in pending)}
        common.json_dump(attempt_dir / "result.json", result)
        print(json.dumps(result, sort_keys=True))
        return 0
    if not pending:
        result = {**attempt, "finished_utc": common.utc_now(), "result": "nothing-pending", "copied": 0, "copied_unverified": 0, "verified": 0, "failed": 0, "held": 0}
        common.json_dump(attempt_dir / "result.json", result)
        print(json.dumps(result, sort_keys=True))
        return 0

    apply_memory_limit(args.memory_limit_mib)
    env, secrets = common.load_secret_environment(common.B2_ENV_FILE)
    counters = {"copied": 0, "copied_unverified": 0, "verified": 0, "failed": 0, "held": 0}
    deadline = time.monotonic() + args.max_duration_seconds
    with RcloneDaemon(args, attempt_dir, env) as client:
        with ThreadPoolExecutor(max_workers=args.workers, thread_name_prefix="payload-copy") as executor:
            for item, outcome in iter_bounded_results(
                executor,
                client,
                pending,
                attempt_id,
                args.workers,
                deadline,
                operation,
                verification,
            ):
                base = {
                    "recorded_utc": common.utc_now(),
                    "run_id": args.run_id,
                    "attempt_id": attempt_id,
                    **asdict(item),
                    "source": f"{item.source_fs}/{item.source_path}",
                    "destination": f"{DEST_FS}/{item.destination_remote}",
                }
                if isinstance(outcome, BaseException):
                    counters["failed"] += 1
                    error = common.redact(str(outcome), secrets)
                    common.append_jsonl(run_dir / "failed.jsonl", {**base, "status": "failed", "error": error})
                elif outcome.get("status") == "held":
                    counters["held"] += 1
                    common.append_jsonl(run_dir / "held.jsonl", {"run_id": args.run_id, **outcome})
                elif outcome.get("status") == "copied_unverified":
                    counters["copied_unverified"] += 1
                    if outcome.get("copy_state") == "copied":
                        counters["copied"] += 1
                    common.append_jsonl(
                        run_dir / "copied_unverified.jsonl",
                        {"run_id": args.run_id, **outcome},
                    )
                else:
                    counters["verified"] += 1
                    common.append_jsonl(run_dir / "verified.jsonl", {"run_id": args.run_id, **outcome})
                    if outcome.get("copy_state") == "copied":
                        counters["copied"] += 1
                        common.append_jsonl(run_dir / "copied.jsonl", {"run_id": args.run_id, **outcome, "status": "copied"})
    result_name = "complete" if counters["failed"] == 0 else "incomplete"
    result = {**attempt, **counters, "finished_utc": common.utc_now(), "result": result_name}
    common.json_dump(attempt_dir / "result.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result_name == "complete" else 2


def status(args: argparse.Namespace) -> int:
    if not common.RUN_ID_RE.fullmatch(args.run_id):
        raise common.TransferError("invalid run ID")
    run_dir = PAYLOAD_STATE_ROOT / args.run_id
    if not (run_dir / "run.json").is_file():
        raise common.TransferError(f"unknown payload run ID: {args.run_id}")
    result = {
        "run": json.loads((run_dir / "run.json").read_text(encoding="utf-8")),
        "ledger_records": {
            name: common.ledger_count(run_dir / f"{name}.jsonl")
            for name in ("planned", "copied", "copied_unverified", "verified", "failed", "held")
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--mode", choices=("dry-run", "probe", "transfer", "verify"), required=True)
    run.add_argument(
        "--verification",
        choices=("fast", "full"),
        default="full",
        help="fast avoids payload downloads and records copied_unverified; full downloads SHA-256",
    )
    run.add_argument("--run-id", required=True)
    run.add_argument("--mapping", type=Path, required=True)
    run.add_argument("--format", choices=("csv", "jsonl"), required=True)
    run.add_argument("--workers", type=int, default=4)
    run.add_argument("--checkers", type=int, default=4)
    run.add_argument("--buffer-size", default="4M")
    run.add_argument("--b2-chunk-size", choices=("8M", "16M", "32M"), default="16M")
    run.add_argument("--b2-upload-concurrency", type=int, default=1)
    run.add_argument("--max-backlog", type=int, default=512)
    run.add_argument("--connect-timeout", default="15s")
    run.add_argument("--io-timeout", default="5m")
    run.add_argument("--low-level-retries", type=int, default=10)
    run.add_argument("--retry-sleep", default="10s")
    run.add_argument("--item-timeout-seconds", type=int, default=1800)
    run.add_argument("--max-duration-seconds", type=int, default=86400)
    run.add_argument("--memory-limit-mib", type=int, default=512)
    run.add_argument("--max-total-bytes", type=int, default=2 * 1024**4)
    run.add_argument("--probe-max-bytes", type=int, default=1024**2)
    run.set_defaults(handler=execute)
    show = subparsers.add_parser("status")
    show.add_argument("--run-id", required=True)
    show.set_defaults(handler=status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.handler(args))
    except common.TransferError as exc:
        print(json.dumps({"error": str(exc), "status": "blocked"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
