# Byline: Claude Code · Opus 5 · 2026-09-18
"""ZIP pass for AI-chat discovery, in two bounded stages so the byte cost is known
BEFORE anything is decompressed in bulk.

  stage=dir    read the ZIP central directory only (end-of-file reads; no member is
               decompressed) and emit one row per member: name, uncompressed size,
               compressed size, crc32, modtime. This is the cheap index.
  stage=probe  given an explicit member list, decompress only the first
               MEMBER_HEAD_BYTES of each named member and classify it by content
               using the same signature rules as the loose-file probe.

Read-only on evidence; nothing is written to B2.
Usage:
  ai_chat_zip_probe.py dir   <candidates.tsv> <out.tsv> [limit]
  ai_chat_zip_probe.py probe <members.tsv>    <out.tsv> [limit]
"""
from __future__ import annotations

import concurrent.futures as cf
import csv
import os
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai_chat_signature_probe import classify  # noqa: E402  (same signature rules)

B2 = Path(os.environ.get("B2_ROOT", "/srv/openlist/b2/salem-data"))
WORKERS = int(os.environ.get("WORKERS", "16"))
MEMBER_HEAD = int(os.environ.get("MEMBER_HEAD_BYTES", "16384"))
MAX_MEMBERS = int(os.environ.get("MAX_MEMBERS", "200000"))

DIR_COLS = ["vault_key", "sha1", "zip_size", "zip_member_path", "member_size",
            "member_csize", "member_crc", "member_modtime", "status"]
PROBE_COLS = ["vault_key", "sha1", "zip_member_path", "member_size", "signature", "why", "status"]


def zip_dir(rec: dict) -> list[dict]:
    key = rec["vault_key"]
    base = {"vault_key": key, "sha1": rec.get("sha1"), "zip_size": rec.get("size")}
    out = []
    try:
        with zipfile.ZipFile(B2 / key) as z:
            for i, info in enumerate(z.infolist()):
                if i >= MAX_MEMBERS:
                    out.append({**base, "zip_member_path": None, "status": f"truncated_at_{MAX_MEMBERS}"})
                    break
                if info.is_dir() or info.file_size < 200:
                    continue
                dt = info.date_time
                out.append({**base, "zip_member_path": info.filename, "member_size": info.file_size,
                            "member_csize": info.compress_size, "member_crc": info.CRC,
                            "member_modtime": f"{dt[0]:04d}-{dt[1]:02d}-{dt[2]:02d}T{dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}",
                            "status": "ok"})
            if not out:
                out.append({**base, "zip_member_path": None, "status": "empty"})
    except Exception as e:
        out.append({**base, "zip_member_path": None, "status": f"error:{type(e).__name__}:{str(e)[:100]}"})
    return out


def zip_probe_group(item) -> list[dict]:
    """item = (vault_key, [member rows]) -- one ZipFile open per archive."""
    key, members = item
    out = []
    try:
        z = zipfile.ZipFile(B2 / key)
    except Exception as e:
        return [{"vault_key": key, "sha1": m.get("sha1"), "zip_member_path": m["zip_member_path"],
                 "member_size": m.get("member_size"), "signature": None,
                 "why": f"open-error:{type(e).__name__}", "status": "error"} for m in members]
    with z:
        for m in members:
            n = m["zip_member_path"]
            try:
                with z.open(n) as mf:
                    h = mf.read(MEMBER_HEAD)
                ml = n.lower()
                mc = ("json" if ml.endswith((".json", ".jsonl", ".ndjson"))
                      else "html" if ml.endswith((".html", ".htm", ".xhtml")) else "text")
                sig, why = classify(h, mc)
                out.append({"vault_key": key, "sha1": m.get("sha1"), "zip_member_path": n,
                            "member_size": m.get("member_size"), "signature": sig, "why": why, "status": "ok"})
            except Exception as e:
                out.append({"vault_key": key, "sha1": m.get("sha1"), "zip_member_path": n,
                            "member_size": m.get("member_size"), "signature": None,
                            "why": f"{type(e).__name__}:{str(e)[:100]}", "status": "error"})
    return out


def main() -> int:
    stage, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    with open(src, newline="", encoding="utf-8") as f:
        recs = list(csv.DictReader(f, delimiter="\t"))
    if stage == "dir":
        recs = [r for r in recs if r.get("probe_class") == "zip"]
    if limit:
        recs = recs[:limit]

    t0, done = time.time(), 0
    if stage == "dir":
        cols, work, fn = DIR_COLS, recs, zip_dir
        total = len(recs)
    else:
        g = defaultdict(list)
        for r in recs:
            g[r["vault_key"]].append(r)
        cols, work, fn = PROBE_COLS, list(g.items()), zip_probe_group
        total = len(work)

    n_rows = 0
    with open(dst, "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for rows in ex.map(fn, work):
                for row in rows:
                    w.writerow(row)
                n_rows += len(rows)
                done += 1
                if done % 50 == 0:
                    el = time.time() - t0
                    print(f"{stage} {done}/{total} rows={n_rows} {done/el:.1f}/s "
                          f"eta={(total-done)/max(done/el,0.01)/60:.1f}m", flush=True)
    print(f"ZIP {stage.upper()} DONE archives={total} rows={n_rows} secs={time.time()-t0:.0f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
