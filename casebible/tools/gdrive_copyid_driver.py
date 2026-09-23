#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Copy Google Drive files to B2 by Drive file ID (path-independent). Runs ON the VPS.

Why: gd_salemnet has duplicate top-level folder names (two "Takeout" roots, etc.). rclone resolves a path
to ONE folder, so files under the other are silently "not found" and skipped — a path-based
`rclone copy --files-from` reports success having copied nothing. `rclone backend copyid` addresses
each file by its immutable Drive ID and copies it to an explicit destination path.

Usage (on VPS):
  python3 gdrive_copyid_driver.py <remote> <idmap.tsv> <dest-prefix> [--batch 10] [--only missing.txt]
    remote       e.g. gd_salemnet:
    idmap.tsv    lines: <driveId>\t<relative path>\t<size>
    dest-prefix  e.g. b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/gdrive/salemnet
    --only FILE  restrict to relative paths listed in FILE (one per line), e.g. the missing set
Env: RCLONE_CONFIG must point at the Drive config; RCLONE_CONFIG_B2_* provide the b2 remote.
Writes a JSONL receipt next to the idmap. A failed batch (rclone exit != 0) is retried file-by-file;
files that still fail are recorded as "failed" and the run CONTINUES (exit code 1 at the end) —
re-run with --only <list of failed paths> to retry them. (Docstring corrected 2026-09-14; it used to
claim the run stops on the first failed batch.)
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys


EXTRA_ARGS: list[str] = []  # e.g. ["--drive-export-formats", "pdf"] for native exports (set from --rclone-args)


def run_copyid(remote: str, pairs: list[tuple[str, str]]) -> subprocess.CompletedProcess:
    args = ["rclone", "backend", "copyid", remote]
    for file_id, dest in pairs:
        args += [file_id, dest]
    return subprocess.run(args + ["--immutable"] + EXTRA_ARGS, capture_output=True, text=True, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("remote")
    ap.add_argument("idmap")
    ap.add_argument("dest_prefix")
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--only")
    ap.add_argument("--dest-is-full", action="store_true",
                    help="idmap column 2 is already the full destination path relative to dest_prefix's folder (native exports)")
    ap.add_argument("--rclone-args", default="", help="extra rclone flags, space-separated, e.g. '--drive-export-formats pdf'")
    a = ap.parse_args()
    if a.rclone_args:
        EXTRA_ARGS.extend(a.rclone_args.split())

    only = None
    if a.only:
        only = {l.rstrip("\n") for l in open(a.only, encoding="utf-8") if l.strip()}
    # idmaps written by gdrive_occurrences_load.py are PG CSV with quote char \x01: a Drive name holding a tab or
    # newline (Drive allows both) arrives quoted, and a raw split() handed rclone a mangled id/dest (32 false 404s
    # on 2026-09-14). \x01 never occurs in a real name and older, unquoted idmaps parse identically.
    import csv
    rows = []
    with open(a.idmap, encoding="utf-8", newline="") as fh:
        for parts in csv.reader(fh, delimiter="\t", quotechar="\x01", doublequote=True):
            if len(parts) < 2:
                continue
            # rclone lists a multi-parent Drive file once per path with ID "fileID<TAB>parentID"; copyid wants the file ID
            file_id, rel = parts[0].split("\t")[0], parts[1]
            if only is not None and rel not in only:
                continue
            rows.append((file_id, rel))
    receipt = os.path.splitext(a.idmap)[0] + f".copyid-{dt.datetime.now():%Y%m%d-%H%M%S}.receipt.jsonl"
    ok = failed = 0
    with open(receipt, "a", encoding="utf-8") as log:
        def rec(status, items, detail=""):
            log.write(json.dumps({"time": dt.datetime.now().astimezone().isoformat(), "status": status,
                                  "items": items, "detail": detail[-500:]}, ensure_ascii=False) + "\n")
            log.flush()
        for i in range(0, len(rows), a.batch):
            batch = rows[i:i + a.batch]
            pairs = [(fid, f"{a.dest_prefix.rstrip('/')}/{rel}") for fid, rel in batch]
            r = run_copyid(a.remote, pairs)
            if r.returncode == 0:
                ok += len(batch); rec("ok", [rel for _, rel in batch])
            else:
                # retry file-by-file so one bad file does not sink the batch
                for (fid, rel), pair in zip(batch, pairs):
                    r1 = run_copyid(a.remote, [pair])
                    if r1.returncode == 0:
                        ok += 1; rec("ok", [rel])
                    else:
                        failed += 1; rec("failed", [rel], r1.stderr)
                        print(f"FAILED {rel[-90:]} :: {r1.stderr.strip()[-160:]}", file=sys.stderr)
            if (i // a.batch) % 50 == 0:
                print(f"progress ok={ok} failed={failed} of {len(rows)}", flush=True)
    print(f"done ok={ok} failed={failed} total={len(rows)} receipt={receipt}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
