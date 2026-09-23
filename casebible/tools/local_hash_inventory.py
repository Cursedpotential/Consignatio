#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Hash a list of local files (md5 + sha256 + size + mtime) into rclone-lsjson-compatible JSON lines.

Why: `rclone lsjson --hash` on D:\\Backup fails on ~4,100 directories (Obsidian plugin dirs, `_system/`
plugin copies — Windows path/reparse issues) and silently exits early. Python's long-path-aware walk
already covered all 986k files in the zero scan, so hashing is done here instead.

Usage:
  python local_hash_inventory.py <root> <relative-path-list> <out.jsonl>
Output: one JSON object per line: {"Path","Name","Size","ModTime","Hashes":{"md5","sha256"}}.
Failures are written as {"Path","error"} and counted; the run continues. Resumable: paths already
present in <out.jsonl> are skipped.
"""
import datetime as dt
import hashlib
import json
import os
import sys
import time

CHUNK = 8 * 1024 * 1024


def long(p: str) -> str:
    return p if p.startswith("\\\\?\\") else "\\\\?\\" + os.path.abspath(p)


def main() -> int:
    root, listing, out = sys.argv[1], sys.argv[2], sys.argv[3]
    # resume: only successfully hashed paths count as done — rows that recorded an error are retried
    # (2026-09-14: 18,313 error rows from a D: device flap would otherwise have been skipped forever)
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    if "error" not in rec:
                        done.add(rec["Path"])
                except Exception:
                    pass
    rels = [l.rstrip("\n") for l in open(listing, encoding="utf-8") if l.strip()]
    todo = [r for r in rels if r not in done]
    print(f"listed={len(rels)} already_done={len(done)} todo={len(todo)}", flush=True)
    n = err = 0; t0 = time.time(); bytes_read = 0
    with open(out, "a", encoding="utf-8") as fh:
        for rel in todo:
            p = os.path.join(root, *rel.split("/"))
            lp = long(p)
            for attempt in range(4):
                try:
                    st = os.stat(lp)
                    m, s = hashlib.md5(), hashlib.sha256()
                    with open(lp, "rb") as f:
                        while True:
                            b = f.read(CHUNK)
                            if not b:
                                break
                            m.update(b); s.update(b); bytes_read += len(b)
                    # datetime.fromtimestamp() raises OSError EINVAL on Windows for pre-1970 / sentinel mtimes —
                    # exactly the recovered files with 1970-01-01 stamps (704 + 8,475 false "errors" on D:\Backup, 2026-09-14)
                    mtime = (dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(seconds=st.st_mtime)).astimezone()
                    rec = {"Path": rel, "Name": rel.rsplit("/", 1)[-1], "Size": st.st_size,
                           "ModTime": mtime.isoformat(),
                           "IsDir": False, "Hashes": {"md5": m.hexdigest(), "sha256": s.hexdigest()}}
                    break
                except (OSError, MemoryError) as e:
                    # WinError 433 (device does not exist) / 1450 (no system resources, surfaces as MemoryError):
                    # the volume is flapping — wait and retry instead of recording a false error
                    win = getattr(e, "winerror", None)
                    if attempt < 3 and (isinstance(e, MemoryError) or win in (433, 1450, 21, 1167)):
                        time.sleep(15 * (attempt + 1)); continue
                    err += 1; rec = {"Path": rel, "error": str(e)[:200]}
                    break
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
            if n % 20000 == 0:
                fh.flush()
                print(f"progress {n}/{len(todo)} errors={err} GB={bytes_read/1e9:.1f} elapsed_min={(time.time()-t0)/60:.0f}", flush=True)
    print(f"done files={n} errors={err} GB={bytes_read/1e9:.1f} minutes={(time.time()-t0)/60:.0f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
