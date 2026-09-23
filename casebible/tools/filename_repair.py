#!/usr/bin/env python3
# Byline: Claude Code · Opus 5 · 2026-09-13
"""Repair Windows-hostile object names in ONE rclone folder, safely.

Dry run by default: lists the folder (non-recursive), computes a clean name for each
object and writes a plan (CSV). No bucket changes.

With --apply, each planned object is handled in this order, stopping at the first failure:
  1. server-side copy  <folder>/<original>  ->  <folder>/<clean name>
  2. verify the copy's size and hash (SHA-1 on B2, MD5 on R2) equal the original's
  3. server-side move  <folder>/<original>  ->  <folder>/_filename_repaired/<original>
  4. verify the archived object matches and the original key is gone
Nothing is deleted outright: originals end up under _filename_repaired/. Every step
is appended to a JSONL receipt that keeps the exact old and new names.

Names are listed and written with backend encoding None, so the raw object keys are
used. Stored names contain Mac SFM substitutes (U+F020-U+F029 for " * : < > ? \\ |,
trailing space, trailing dot), rclone escape quotes (U+201B) with fullwidth solidi,
bidi/zero-width marks and spaces before the extension.

Usage:
  python filename_repair.py "r2all:raw/AI_Chats"
  python filename_repair.py "r2all:raw/AI_Chats" --apply --confirm-count 13 --limit 1
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

RCLONE = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"
CONFIG = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
REPAIRED_DIR = "_filename_repaired"
# Receipts moved into the repo 2026-09-15; was E:/AI_Workspace/_receipts/filename-repair
DEFAULT_RECEIPTS = "E:/AI_Workspace/Projects/Propria/Consignatio/docs/receipts/filename-repair"

# Mac "Services for Macintosh" private-use substitutes -> the character they stood for.
SFM_MAP = {
    0xF020: '"', 0xF021: "*", 0xF022: ":", 0xF023: "<", 0xF024: ">",
    0xF025: "?", 0xF026: "\\", 0xF027: "|", 0xF028: " ", 0xF029: ".",
}
INVISIBLE = {0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C,
             0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0xFEFF}
WINDOWS_REPLACE = {'"': "'", "*": "", "?": "", "<": "-", ">": "-", "|": "-",
                   "\\": "-", "/": "-", "\uff0f": "-", "\u201b": ""}


def clean_name(name: str) -> str:
    """Return a Windows-safe, human-readable form of an object name."""
    chars = []
    for ch in name:
        cp = ord(ch)
        if cp in INVISIBLE or 0xF001 <= cp <= 0xF01F or cp < 0x20:
            continue
        chars.append(SFM_MAP.get(cp, ch))
    text = "".join(chars)
    text = re.sub(r":\s+", " - ", text)
    text = text.replace(":", "-")
    text = "".join(WINDOWS_REPLACE.get(ch, ch) for ch in text)
    text = re.sub(r"-{2,}", "-", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    stem, dot, ext = text.rpartition(".")
    if dot and stem and re.fullmatch(r"[A-Za-z0-9]{1,8}", ext):
        stem = stem.strip(" ")
        text = f"{stem}.{ext}"
    return text.rstrip(". ") or "unnamed"


def rclone(*args: str) -> subprocess.CompletedProcess:
    cmd = [RCLONE, *args, "--config", CONFIG, "--b2-encoding", "None", "--s3-encoding", "None"]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def list_folder(folder: str) -> list[dict]:
    result = rclone("lsjson", folder, "--files-only", "--hash")
    if result.returncode != 0:
        raise RuntimeError(f"listing {folder} failed: {result.stderr.strip()}")
    return json.loads(result.stdout or "[]")


def stat_object(path: str) -> dict | None:
    result = rclone("lsjson", "--stat", "--hash", path)
    if result.returncode == 0:
        obj = json.loads(result.stdout)
        # On bucket remotes a missing key stats as a synthetic empty directory
        # (Name "", Size -1, IsDir true) instead of erroring; treat that as absent.
        if obj.get("IsDir") or not obj.get("Name") or obj.get("Size", -1) < 0:
            return None
        return obj
    err = result.stderr.lower()
    if "not found" in err or "doesn't exist" in err or "no such" in err:
        return None
    raise RuntimeError(f"stat {path} failed: {result.stderr.strip()}")


def fingerprint(obj: dict) -> tuple[int, str, str]:
    hashes = {k: v for k, v in (obj.get("Hashes") or {}).items() if v}
    for kind in ("sha1", "md5"):
        if kind in hashes:
            return obj["Size"], kind, hashes[kind]
    raise RuntimeError(f"no sha1/md5 available for {obj.get('Path')}")


def build_plan(folder: str) -> list[dict]:
    objects = list_folder(folder)
    existing = {o["Name"] for o in objects}
    plan, claimed = [], set()
    for obj in sorted(objects, key=lambda o: o["Name"]):
        new = clean_name(obj["Name"])
        if new == obj["Name"]:
            continue
        status = "READY"
        if new in existing or new in claimed:
            status = "CONFLICT_TARGET_EXISTS"
        claimed.add(new)
        size, kind, digest = fingerprint(obj)
        plan.append({"status": status, "old": obj["Name"], "new": new,
                     "size": size, "hash_kind": kind, "hash": digest})
    return plan


def write_plan(plan: list[dict], receipts: Path, stamp: str, slug: str) -> Path:
    path = receipts / f"{stamp}-{slug}-plan.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["status", "old", "new", "size", "hash_kind", "hash"])
        writer.writeheader()
        writer.writerows(plan)
    return path


def expect_same(path: str, size: int, kind: str, digest: str) -> dict:
    obj = stat_object(path)
    if obj is None:
        raise RuntimeError(f"expected object missing: {path}")
    got_size, got_kind, got_digest = fingerprint(obj)
    if (got_size, got_kind, got_digest.lower()) != (size, kind, digest.lower()):
        raise RuntimeError(f"verification mismatch at {path}: "
                           f"{got_size}/{got_kind}/{got_digest} != {size}/{kind}/{digest}")
    return obj


def apply_plan(folder: str, plan: list[dict], receipt: Path, limit: int | None) -> int:
    done = 0
    with receipt.open("a", encoding="utf-8") as log:
        def record(step: str, row: dict, **extra) -> None:
            entry = {"time": dt.datetime.now().astimezone().isoformat(), "step": step,
                     "folder": folder, "old": row["old"], "new": row["new"],
                     "size": row["size"], "hash_kind": row["hash_kind"], "hash": row["hash"], **extra}
            log.write(json.dumps(entry, ensure_ascii=False) + "\n")
            log.flush()

        for row in plan:
            if limit is not None and done >= limit:
                break
            if row["status"] != "READY":
                record("skipped", row, reason=row["status"])
                continue
            src = f"{folder}/{row['old']}"
            dst = f"{folder}/{row['new']}"
            archive = f"{folder}/{REPAIRED_DIR}/{row['old']}"

            expect_same(src, row["size"], row["hash_kind"], row["hash"])
            if stat_object(dst) is not None:
                raise RuntimeError(f"target appeared since planning: {dst}")
            if stat_object(archive) is not None:
                raise RuntimeError(f"archive slot already occupied: {archive}")

            result = rclone("copyto", src, dst, "--immutable")
            if result.returncode != 0:
                record("copy_failed", row, stderr=result.stderr.strip())
                raise RuntimeError(f"copy failed for {src}: {result.stderr.strip()}")
            expect_same(dst, row["size"], row["hash_kind"], row["hash"])
            record("copied_and_verified", row, target=dst)

            result = rclone("moveto", src, archive, "--immutable")
            if result.returncode != 0:
                record("archive_failed", row, stderr=result.stderr.strip())
                raise RuntimeError(f"archive move failed for {src}: {result.stderr.strip()}")
            expect_same(archive, row["size"], row["hash_kind"], row["hash"])
            if stat_object(src) is not None:
                record("archive_incomplete", row, detail="original key still present")
                raise RuntimeError(f"original still present after move: {src}")
            record("archived_original", row, archive=archive)
            done += 1
            print(f"OK  {row['old']!r} -> {row['new']!r}")
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help='one rclone folder, e.g. "r2all:raw/AI_Chats" (not recursive)')
    parser.add_argument("--apply", action="store_true", help="perform the renames (default: dry run)")
    parser.add_argument("--confirm-count", type=int, help="with --apply: must equal the READY count in the fresh plan")
    parser.add_argument("--limit", type=int, help="with --apply: process at most N objects")
    parser.add_argument("--receipts", default=DEFAULT_RECEIPTS, help="directory for plan CSV and JSONL receipt")
    args = parser.parse_args()

    folder = args.folder.rstrip("/")
    receipts = Path(args.receipts)
    receipts.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", folder).strip("_")

    plan = build_plan(folder)
    plan_path = write_plan(plan, receipts, stamp, slug)
    ready = [r for r in plan if r["status"] == "READY"]
    conflicts = [r for r in plan if r["status"] != "READY"]

    for row in plan:
        print(f"{row['status']:<24} {row['old']!r}\n{'':<24} -> {row['new']!r}")
    print(f"\nfolder={folder} ready={len(ready)} conflicts={len(conflicts)} plan={plan_path}")
    print(f"estimated write ops if applied: {len(ready) * 2} server-side copies (move = copy + delete), "
          f"~{len(ready) * 6} metadata reads; no data downloaded or uploaded")

    if not args.apply:
        print("DRY RUN: no changes made.")
        return 0
    if args.confirm_count != len(ready):
        print(f"REFUSED: --confirm-count must be {len(ready)} for this fresh plan.", file=sys.stderr)
        return 2

    receipt = receipts / f"{stamp}-{slug}-receipt.jsonl"
    try:
        done = apply_plan(folder, ready, receipt, args.limit)
    except RuntimeError as exc:
        print(f"STOPPED SAFELY: {exc}\nreceipt={receipt}", file=sys.stderr)
        return 1
    print(f"applied={done} receipt={receipt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
