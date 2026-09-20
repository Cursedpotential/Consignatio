#!/usr/bin/env python3
# Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
"""Link each event to the next event in the same conversation (tl_next_20260919).

Runs after the loader. Idempotent: the edge id is the source event's key, so a re-run
updates the same rows. Reads one conversation at a time, paged, using the (conv, ts) index,
and writes with the same discipline as the loader (RSS pacing, health probe, stop on timeout).

Env: SURREAL_URL/USER/PASS, PAGE, WRITE_BATCH, STATE_NEXT.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_surreal_20260919 import T, Wedged, healthy, lit, log_stalls, rid, rss, sql  # noqa: E402

PAGE = int(os.environ.get("PAGE", "5000"))
WRITE_BATCH = int(os.environ.get("WRITE_BATCH", "2000"))
STATE_NEXT = os.environ.get("STATE_NEXT", "/data/probata/volumes/timeline-mvp/next_state_20260919.json")
RSS_PAUSE = int(os.environ.get("RSS_PAUSE", str(700 * 1024 * 1024)))


def main() -> int:
    done = set()
    if os.path.exists(STATE_NEXT):
        with open(STATE_NEXT, encoding="utf-8") as fh:
            done = set(json.load(fh))
    convs = sql(f"SELECT VALUE id FROM tl_conversation{T};")[0]["result"]
    print(f"{len(convs)} conversations, {len(done)} already linked", flush=True)
    total = 0
    t0 = time.time()
    for ci, conv in enumerate(convs):
        if conv in done:
            continue
        ids: list[str] = []
        start = 0
        while True:
            q = (f"SELECT VALUE record::id(id) FROM tl_event{T} WHERE conv = {conv} "
                 f"ORDER BY ts START {start} LIMIT {PAGE};")
            page = sql(q, timeout=300)[0]["result"]
            ids.extend(page)
            if len(page) < PAGE:
                break
            start += PAGE
        edges = [{"id": rid("tl_next", a), "in": rid("tl_event", a), "out": rid("tl_event", b)}
                 for a, b in zip(ids, ids[1:])]
        for i in range(0, len(edges), WRITE_BATCH):
            if not healthy():
                raise Wedged("health probe failed")
            while rss() > RSS_PAUSE:
                time.sleep(2)
            chunk = edges[i:i + WRITE_BATCH]
            sql(f"INSERT RELATION IGNORE INTO tl_next{T} {lit(chunk)};", timeout=300)
            total += len(chunk)
        done.add(conv)
        tmp = STATE_NEXT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(sorted(done), fh)
        os.replace(tmp, STATE_NEXT)
        if ci % 20 == 0 or len(edges) > 1000:
            print(f"conv {ci + 1}/{len(convs)} events={len(ids)} edges={total} "
                  f"({total / max(time.time() - t0, 1):.0f}/s) rss={rss() / 1e6:.0f}MB", flush=True)
    print(f"NEXT DONE edges={total} secs={time.time() - t0:.0f} stalls={len(log_stalls())}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Wedged as e:
        print(f"SURREAL UNRESPONSIVE: {e}; stopping without retry", flush=True)
        sys.exit(3)
