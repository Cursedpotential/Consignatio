#!/usr/bin/env python3
"""Bounded, manifest-only R2 to B2 copy runner for Consignatio.

The runner never discovers corpus objects. It accepts an explicit files-from
manifest, copies with ``rclone copy`` (never sync/move/delete), and emits
append-only planned/copied/verified/failed ledgers. Corpus execution is
disabled unless a separately managed enable file contains the exact gate
phrase documented below.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


RUNTIME_ROOT = Path(__file__).resolve().parent
STATE_ROOT = RUNTIME_ROOT / "state"
B2_ENV_FILE = Path("/data/consignatio/secrets/rclone-b2.env")
RCLONE_CONFIG = Path("/home/ubuntu/.config/rclone/rclone.conf")
ENABLE_FILE = RUNTIME_ROOT / "ENABLE_CORPUS_TRANSFER"
ENABLE_PHRASE = "ENABLE_CORPUS_TRANSFER=YES"
APPROVED_DEST_PREFIX = "b2:salem-data/consignatio/intake/raw-dedupe/v1/"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
PROBE_MARKERS = ("_system/canary/", "_system/probe/")


class TransferError(RuntimeError):
    """A fail-closed validation or execution error."""


@dataclass(frozen=True)
class Item:
    path: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def normalize_path(raw: str) -> str:
    value = raw.rstrip("\r\n")
    if not value or value.startswith("#"):
        raise ValueError("blank-or-comment")
    if "\\" in value or "\x00" in value or "\n" in value or "\r" in value:
        raise TransferError(f"unsafe manifest path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/"):
        raise TransferError(f"absolute manifest path is forbidden: {value!r}")
    if any(part in ("", ".", "..") for part in path.parts):
        raise TransferError(f"non-canonical manifest path is forbidden: {value!r}")
    return path.as_posix()


def load_manifest(path: Path) -> list[Item]:
    if not path.is_file():
        raise TransferError(f"manifest is not a regular file: {path}")
    items: list[Item] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, raw in enumerate(handle, start=1):
            candidate = raw.rstrip("\r\n")
            if not candidate or candidate.startswith("#"):
                continue
            try:
                normalized = normalize_path(candidate)
            except TransferError as exc:
                raise TransferError(f"manifest line {line_number}: {exc}") from exc
            if normalized in seen:
                raise TransferError(f"duplicate manifest path at line {line_number}: {normalized!r}")
            seen.add(normalized)
            items.append(Item(normalized))
    if not items:
        raise TransferError("manifest contains no object paths")
    return items


def validate_roots(source_root: str, dest_root: str) -> tuple[str, str]:
    source = source_root.rstrip("/")
    dest = dest_root.rstrip("/") + "/"
    if not source.startswith("r2:"):
        raise TransferError("source root must use the r2: remote")
    if not dest.startswith(APPROVED_DEST_PREFIX):
        raise TransferError(
            f"destination root must remain under {APPROVED_DEST_PREFIX!r}"
        )
    return source, dest.rstrip("/")


def validate_probe(items: Sequence[Item]) -> None:
    if len(items) != 1:
        raise TransferError("probe mode requires exactly one manifest object")
    if not any(items[0].path.startswith(marker) for marker in PROBE_MARKERS):
        raise TransferError(
            "probe object must be isolated under _system/canary/ or _system/probe/"
        )


def corpus_enabled() -> bool:
    try:
        return ENABLE_FILE.read_text(encoding="utf-8").strip() == ENABLE_PHRASE
    except FileNotFoundError:
        return False


def load_secret_environment(path: Path) -> tuple[dict[str, str], list[str]]:
    if not path.is_file():
        raise TransferError(f"restricted B2 environment file is missing: {path}")
    env = os.environ.copy()
    secret_values: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if not separator or not key or not key.replace("_", "").isalnum():
            raise TransferError(f"invalid environment assignment for key {key!r}")
        parsed = shlex.split(value, posix=True)
        if len(parsed) != 1:
            raise TransferError(f"environment value for {key!r} is not scalar")
        env[key] = parsed[0]
        if parsed[0]:
            secret_values.append(parsed[0])
    required = {"RCLONE_CONFIG_B2_TYPE", "RCLONE_CONFIG_B2_ACCOUNT", "RCLONE_CONFIG_B2_KEY"}
    missing = sorted(required.difference(env))
    if missing:
        raise TransferError(f"restricted B2 environment is missing keys: {', '.join(missing)}")
    return env, secret_values


def redact(text: str, secrets: Iterable[str]) -> str:
    result = text
    for secret in secrets:
        if secret:
            result = result.replace(secret, "<redacted>")
    return result[-8000:]


def json_dump(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def append_jsonl(path: Path, payload: dict[str, object]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def manifest_bytes(items: Sequence[Item]) -> bytes:
    return ("\n".join(item.path for item in items) + "\n").encode("utf-8")


def load_verified(run_dir: Path) -> set[str]:
    ledger = run_dir / "verified.jsonl"
    verified: set[str] = set()
    if not ledger.exists():
        return verified
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        if not raw:
            continue
        row = json.loads(raw)
        if row.get("status") == "verified" and isinstance(row.get("path"), str):
            verified.add(row["path"])
    return verified


def parse_combined(path: Path) -> dict[str, str]:
    results: dict[str, str] = {}
    if not path.exists():
        return results
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if len(raw) >= 3 and raw[1] == " " and raw[0] in "=-+*!":
            results[raw[2:]] = raw[0]
    return results


def run_process(
    command: Sequence[str], *, env: dict[str, str], timeout_seconds: int, secrets: Iterable[str]
) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        return completed.returncode, redact(completed.stdout, secrets)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout if isinstance(exc.stdout, str) else ""
        raise TransferError(
            f"command exceeded wall timeout ({timeout_seconds}s): {redact(output, secrets)}"
        ) from exc


def rclone_common(args: argparse.Namespace) -> list[str]:
    return [
        "--config", str(RCLONE_CONFIG),
        "--transfers", str(args.transfers),
        "--checkers", str(args.checkers),
        "--buffer-size", args.buffer_size,
        "--multi-thread-streams", "0",
        "--max-backlog", str(args.max_backlog),
        "--contimeout", args.connect_timeout,
        "--timeout", args.io_timeout,
        "--retries", "1",
        "--low-level-retries", str(args.low_level_retries),
        "--retries-sleep", args.retry_sleep,
    ]


def join_locator(root: str, path: str) -> str:
    return f"{root.rstrip('/')}/{path}"


def configure_run(
    *, run_dir: Path, args: argparse.Namespace, items: Sequence[Item], source_root: str, dest_root: str
) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    planned = manifest_bytes(items)
    manifest_hash = hashlib.sha256(planned).hexdigest()
    config = {
        "schema": "consignatio-r2-b2-transfer-run/v1",
        "run_id": args.run_id,
        "source_root": source_root,
        "dest_root": dest_root,
        "manifest_sha256": manifest_hash,
        "planned_count": len(items),
        "created_utc": utc_now(),
    }
    config_path = run_dir / "run.json"
    manifest_path = run_dir / "planned.files-from"
    if config_path.exists():
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        immutable = ("source_root", "dest_root", "manifest_sha256", "planned_count")
        if any(existing.get(key) != config[key] for key in immutable):
            raise TransferError("run ID already exists with different immutable inputs")
    else:
        json_dump(config_path, config)
        manifest_path.write_bytes(planned)
        for item in items:
            append_jsonl(
                run_dir / "planned.jsonl",
                {
                    "recorded_utc": utc_now(),
                    "run_id": args.run_id,
                    "path": item.path,
                    "source": join_locator(source_root, item.path),
                    "destination": join_locator(dest_root, item.path),
                    "status": "planned",
                },
            )
    return manifest_path


def preflight_probe(
    *, args: argparse.Namespace, manifest_path: Path, source_root: str,
    env: dict[str, str], secrets: Sequence[str], attempt_dir: Path
) -> None:
    size_output = attempt_dir / "probe-size.json"
    command = [
        "rclone", "size", source_root,
        "--files-from-raw", str(manifest_path),
        "--json",
        "--config", str(RCLONE_CONFIG),
    ]
    rc, output = run_process(command, env=env, timeout_seconds=120, secrets=secrets)
    if rc != 0:
        raise TransferError(f"probe preflight failed: {output}")
    size_output.write_text(output, encoding="utf-8")
    payload = json.loads(output)
    if payload.get("count") != 1:
        raise TransferError(f"probe preflight resolved {payload.get('count')} objects, expected 1")
    size = int(payload.get("bytes", -1))
    if size < 0 or size > args.probe_max_bytes:
        raise TransferError(f"probe size {size} exceeds ceiling {args.probe_max_bytes}")


def run_transfer(args: argparse.Namespace) -> int:
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise TransferError("run ID must be 1-80 safe filename characters")
    if not (1 <= args.transfers <= 8 and 1 <= args.checkers <= 16):
        raise TransferError("transfers must be 1-8 and checkers must be 1-16")
    items = load_manifest(args.manifest)
    source_root, dest_root = validate_roots(args.source_root, args.dest_root)
    if args.mode == "probe":
        validate_probe(items)
    elif args.mode == "transfer" and not corpus_enabled():
        raise TransferError(
            f"corpus execution is disabled; {ENABLE_FILE} must contain {ENABLE_PHRASE!r}"
        )

    run_dir = (STATE_ROOT / args.run_id).resolve()
    if run_dir.parent != STATE_ROOT.resolve():
        raise TransferError("run state escaped the controlled state root")
    manifest_path = configure_run(
        run_dir=run_dir,
        args=args,
        items=items,
        source_root=source_root,
        dest_root=dest_root,
    )
    already_verified = load_verified(run_dir)
    pending = [item for item in items if item.path not in already_verified]
    attempt_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{os.getpid()}"
    attempt_dir = run_dir / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, mode=0o700)
    pending_manifest = attempt_dir / "pending.files-from"
    pending_manifest.write_bytes(manifest_bytes(pending) if pending else b"")
    summary = {
        "attempt_id": attempt_id,
        "started_utc": utc_now(),
        "mode": args.mode,
        "planned": len(items),
        "already_verified": len(already_verified),
        "pending": len(pending),
    }
    json_dump(attempt_dir / "attempt.json", summary)
    if not pending:
        print(json.dumps({**summary, "result": "nothing-pending"}, sort_keys=True))
        return 0

    env, secrets = load_secret_environment(B2_ENV_FILE)
    if args.mode == "probe":
        preflight_probe(
            args=args,
            manifest_path=pending_manifest,
            source_root=source_root,
            env=env,
            secrets=secrets,
            attempt_dir=attempt_dir,
        )

    copy_combined = attempt_dir / "copy.combined"
    copy_errors = attempt_dir / "copy.errors"
    copy_command = [
        "rclone", "copy", source_root, dest_root,
        "--files-from-raw", str(pending_manifest),
        "--combined", str(copy_combined),
        "--error", str(copy_errors),
        "--immutable",
        "--metadata",
        "--no-traverse",
        "--max-duration", args.max_duration,
        "--max-transfer", args.max_transfer,
        "--cutoff-mode", "CAUTIOUS",
        *rclone_common(args),
    ]
    if args.mode == "dry-run":
        copy_command.append("--dry-run")
    copy_rc, copy_output = run_process(
        copy_command,
        env=env,
        timeout_seconds=args.wall_timeout_seconds,
        secrets=secrets,
    )
    (attempt_dir / "copy.log").write_text(copy_output, encoding="utf-8")

    if args.mode == "dry-run":
        json_dump(
            attempt_dir / "result.json",
            {**summary, "finished_utc": utc_now(), "copy_rc": copy_rc, "result": "dry-run"},
        )
        print(json.dumps({**summary, "copy_rc": copy_rc, "result": "dry-run"}, sort_keys=True))
        return 0 if copy_rc == 0 else 2

    check_combined = attempt_dir / "verify.combined"
    check_errors = attempt_dir / "verify.errors"
    check_command = [
        "rclone", "check", source_root, dest_root,
        "--files-from-raw", str(pending_manifest),
        "--one-way",
        "--combined", str(check_combined),
        "--error", str(check_errors),
        "--no-traverse",
        *rclone_common(args),
    ]
    check_command.append("--download" if args.verification == "download" else "--size-only")
    check_rc, check_output = run_process(
        check_command,
        env=env,
        timeout_seconds=args.wall_timeout_seconds,
        secrets=secrets,
    )
    (attempt_dir / "verify.log").write_text(check_output, encoding="utf-8")

    copy_state = parse_combined(copy_combined)
    verify_state = parse_combined(check_combined)
    verified_count = copied_count = failed_count = 0
    for item in pending:
        common = {
            "recorded_utc": utc_now(),
            "run_id": args.run_id,
            "attempt_id": attempt_id,
            "path": item.path,
            "source": join_locator(source_root, item.path),
            "destination": join_locator(dest_root, item.path),
        }
        symbol = verify_state.get(item.path)
        if symbol == "=":
            verified_count += 1
            append_jsonl(
                run_dir / "verified.jsonl",
                {**common, "status": "verified", "verification": args.verification},
            )
            if copy_state.get(item.path) in {"+", "*"}:
                copied_count += 1
                append_jsonl(run_dir / "copied.jsonl", {**common, "status": "copied"})
        else:
            failed_count += 1
            append_jsonl(
                run_dir / "failed.jsonl",
                {
                    **common,
                    "status": "failed",
                    "copy_symbol": copy_state.get(item.path),
                    "verify_symbol": symbol,
                    "copy_rc": copy_rc,
                    "verify_rc": check_rc,
                },
            )
    result = {
        **summary,
        "finished_utc": utc_now(),
        "copy_rc": copy_rc,
        "verify_rc": check_rc,
        "copied": copied_count,
        "verified": verified_count,
        "failed": failed_count,
        "verification": args.verification,
        "result": "complete" if failed_count == 0 and copy_rc == 0 and check_rc == 0 else "incomplete",
    }
    json_dump(attempt_dir / "result.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "complete" else 2


def ledger_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)


def show_status(args: argparse.Namespace) -> int:
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise TransferError("invalid run ID")
    run_dir = STATE_ROOT / args.run_id
    if not (run_dir / "run.json").is_file():
        raise TransferError(f"unknown run ID: {args.run_id}")
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    attempts: Counter[str] = Counter()
    attempts_root = run_dir / "attempts"
    if attempts_root.exists():
        for result_path in attempts_root.glob("*/result.json"):
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            attempts[str(payload.get("result", "unknown"))] += 1
    status = {
        "run": run,
        "ledger_records": {
            name: ledger_count(run_dir / f"{name}.jsonl")
            for name in ("planned", "copied", "verified", "failed")
        },
        "attempt_results": dict(sorted(attempts.items())),
    }
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="validate, dry-run, probe, or gated transfer")
    run.add_argument("--mode", choices=("dry-run", "probe", "transfer"), required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--source-root", required=True)
    run.add_argument("--dest-root", required=True)
    run.add_argument("--verification", choices=("size", "download"), default="size")
    run.add_argument("--transfers", type=int, default=4)
    run.add_argument("--checkers", type=int, default=4)
    run.add_argument("--buffer-size", default="4M")
    run.add_argument("--max-backlog", type=int, default=512)
    run.add_argument("--connect-timeout", default="15s")
    run.add_argument("--io-timeout", default="5m")
    run.add_argument("--low-level-retries", type=int, default=10)
    run.add_argument("--retry-sleep", default="10s")
    run.add_argument("--max-duration", default="2h")
    run.add_argument("--max-transfer", default="250G")
    run.add_argument("--wall-timeout-seconds", type=int, default=7500)
    run.add_argument("--probe-max-bytes", type=int, default=1048576)
    run.set_defaults(handler=run_transfer)
    status = subparsers.add_parser("status", help="summarize append-only run ledgers")
    status.add_argument("--run-id", required=True)
    status.set_defaults(handler=show_status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.handler(args))
    except TransferError as exc:
        print(json.dumps({"error": str(exc), "status": "blocked"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
