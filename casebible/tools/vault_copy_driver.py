# Byline: Claude Code · Opus 5 · 2026-09-15 08:35 EDT (session propria-79)
"""Server-side copy of the vault merge plan into the new vault prefix on B2, through one `rclone rcd`.

Owner 2026-09-15: "new dir so nothing is deleted or overwritten make a copy" (04:55) · "do all the moves up till now" (08:31).
Runs ON ovh-files, detached. Every copy is server-side inside the same bucket (B2 b2_copy_file / copy_part), with
rclone's `Immutable` set so an existing destination with different content is refused, never overwritten. Nothing is
deleted. rclone handles B2 name encoding, so manifest keys are the names rclone lists (raw_duck.b2_objects).

Manifest: CSV with header canonical_key,dest_key,size (keys relative to the bucket).
Ledger:   SQLite, one row per dest_key (ok | error), so a restart resumes.

  copy:    vault_copy_driver.py copy   --manifest m.csv --ledger l.sqlite --config rclone.conf [--limit N] [--dry-run]
  verify:  vault_copy_driver.py verify --manifest m.csv --listing lsjson.json --prefix consignatio/vault/v1/
"""
import argparse
import csv
import json
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

RC_ADDR = "127.0.0.1:5572"


def rc_call(path, body, timeout=7200):
    req = urllib.request.Request(
        f"http://{RC_ADDR}{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except ValueError:
            return exc.code, {"error": str(exc)}
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        return 0, {"error": str(exc)}


def start_rcd(config, log_file):
    proc = subprocess.Popen(
        ["rclone", "rcd", "--rc-no-auth", "--rc-addr", RC_ADDR, "--config", config,
         "--log-file", log_file, "--log-level", "INFO", "--retries", "3", "--low-level-retries", "10"]
    )
    for _ in range(60):
        status, _ = rc_call("/rc/noop", {}, timeout=5)
        if status == 200:
            return proc
        time.sleep(1)
    proc.terminate()
    sys.exit("rclone rcd did not come up on " + RC_ADDR)


def read_manifest(path):
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def copy_one(fs, row, dry_run):
    body = {
        "srcFs": fs, "srcRemote": row["canonical_key"],
        "dstFs": fs, "dstRemote": row["dest_key"],
        "_config": {"Immutable": True, "DryRun": dry_run},
    }
    last = None
    for attempt in range(5):
        status, out = rc_call("/operations/copyfile", body)
        if status == 200:
            return row["dest_key"], "ok", ""
        last = f"{status} {out.get('error', out)}"
        if status in (400, 404) and "immutable" in str(out).lower():
            break  # destination exists with different content: refuse, never overwrite
        time.sleep(min(60, 2 ** attempt))
    return row["dest_key"], "error", last


def cmd_copy(args):
    db = sqlite3.connect(args.ledger)
    db.execute("pragma journal_mode=wal")
    db.execute("create table if not exists done (dest_key text primary key, status text, err text, ts real)")
    finished = {r[0] for r in db.execute("select dest_key from done where status = 'ok'")}
    proc = start_rcd(args.config, args.rclone_log)
    fs = f"{args.remote}:{args.bucket}"
    submitted = ok = err = 0
    started = time.time()
    try:
        with ThreadPoolExecutor(args.workers) as pool:
            pending = set()
            for row in read_manifest(args.manifest):
                if row["dest_key"] in finished:
                    continue
                if args.limit and submitted >= args.limit:
                    break
                pending.add(pool.submit(copy_one, fs, row, args.dry_run))
                submitted += 1
                if len(pending) >= args.workers * 4:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    ok, err = record(db, done, ok, err, args.dry_run)
                    if (ok + err) % 1000 < len(done):
                        report(ok, err, started)
            while pending:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                ok, err = record(db, done, ok, err, args.dry_run)
    finally:
        db.commit()
        proc.terminate()
    report(ok, err, started)
    print(f"FINISHED submitted={submitted} ok={ok} error={err} dry_run={args.dry_run}", flush=True)
    return 0 if err == 0 else 2


def record(db, futures, ok, err, dry_run):
    for fut in futures:
        dest, status, msg = fut.result()
        if status == "ok":
            ok += 1
        else:
            err += 1
            print(f"ERROR {dest}: {msg}", flush=True)
        if not dry_run:
            db.execute("insert or replace into done values (?, ?, ?, ?)", (dest, status, msg, time.time()))
    db.commit()
    return ok, err


def report(ok, err, started):
    rate = (ok + err) / max(time.time() - started, 1)
    print(f"progress ok={ok} error={err} rate={rate:.1f}/s", flush=True)


def cmd_verify(args):
    with open(args.listing, encoding="utf-8") as fh:
        listed = {args.prefix + item["Path"]: item["Size"] for item in json.load(fh)}
    if args.baseline:  # keys that existed under the prefix before this copy (never ours, never deleted)
        with open(args.baseline, encoding="utf-8") as fh:
            for line in fh:
                listed.pop(line.rstrip("\n"), None)
    only = None
    if args.ledger:  # verify just the objects the ledger says were copied (test batches, partial runs)
        db = sqlite3.connect(args.ledger)
        only = {r[0] for r in db.execute("select dest_key from done where status = 'ok'")}
    expected = present = missing = mismatch = 0
    for row in read_manifest(args.manifest):
        if only is not None and row["dest_key"] not in only:
            continue
        expected += 1
        size = listed.pop(row["dest_key"], None)
        if size is None:
            missing += 1
            if missing <= 20:
                print("MISSING", row["dest_key"])
        elif int(size) != int(row["size"]):
            mismatch += 1
            print("SIZE_MISMATCH", row["dest_key"], size, row["size"])
        else:
            present += 1
    extra = len(listed)
    verdict = "PASS" if missing == 0 and mismatch == 0 and extra == 0 else "FAIL"
    print(f"VERIFY {verdict} expected={expected} present={present} missing={missing} size_mismatch={mismatch} extra={extra}")
    return 0 if verdict == "PASS" else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("copy")
    c.add_argument("--manifest", required=True)
    c.add_argument("--ledger", required=True)
    c.add_argument("--config", required=True)
    c.add_argument("--rclone-log", default="rclone-rcd.log")
    c.add_argument("--remote", default="b2")
    c.add_argument("--bucket", default="salem-data")
    c.add_argument("--workers", type=int, default=32)
    c.add_argument("--limit", type=int, default=0)
    c.add_argument("--dry-run", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("--manifest", required=True)
    v.add_argument("--listing", required=True)
    v.add_argument("--prefix", default="consignatio/vault/v1/")
    v.add_argument("--ledger", default="", help="only verify dest keys recorded ok in this ledger")
    v.add_argument("--baseline", default="", help="file of keys present before the copy; not counted as extra")
    args = ap.parse_args()
    sys.exit(cmd_copy(args) if args.cmd == "copy" else cmd_verify(args))


if __name__ == "__main__":
    main()
