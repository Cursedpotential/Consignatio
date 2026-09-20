#!/usr/bin/env python3
# Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
"""Page the Weaviate chat-event collection to a local JSONL spool (stdlib only).

Weaviate's cursor API (?after=<uuid>) cannot filter, and GraphQL offset paging is capped at
QUERY_MAXIMUM_RESULTS, so the whole collection is spooled once and the loader then works in
priority order from the spool. Re-running is incremental: uuids already spooled are skipped
unless their indexed_at/ingest_run_id changed, which is how new ELT output gets picked up.

Env: WV_URL (default http://100.91.190.107:8082), WV_CLASS, SPOOL, PAGE.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WV = os.environ.get("WV_URL", "http://100.91.190.107:8082").rstrip("/")
CLASS = os.environ.get("WV_CLASS", "ChatEvents20260918")
SPOOL = os.environ.get("SPOOL", "/data/probata/volumes/timeline-mvp/chat_events_20260919.jsonl")
STATE = SPOOL + ".seen.json"
PAGE = int(os.environ.get("PAGE", "500"))


def get(url: str, tries: int = 5):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == tries - 1:
                raise
            print(f"retry {attempt}: {e}", flush=True)
            time.sleep(2 + 3 * attempt)


def stamp(props: dict) -> str:
    """Change marker: the extraction agent stamps ingest_run_id + indexed_at; fall back to n_sources."""
    return f"{props.get('ingest_run_id', '')}|{props.get('indexed_at', '')}|{props.get('n_sources', '')}"


def main() -> int:
    seen = {}
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            seen = json.load(fh)
    new = changed = total = 0
    after = None
    t0 = time.time()
    with open(SPOOL, "a", encoding="utf-8") as out:
        while True:
            qs = {"class": CLASS, "limit": PAGE}
            if after:
                qs["after"] = after
            page = get(f"{WV}/v1/objects?{urllib.parse.urlencode(qs)}")
            objs = page.get("objects") or []
            if not objs:
                break
            for o in objs:
                total += 1
                uid, props = o["id"], o.get("properties") or {}
                mark = stamp(props)
                if uid in seen:
                    if seen[uid] == mark:
                        continue
                    changed += 1
                else:
                    new += 1
                seen[uid] = mark
                out.write(json.dumps({"uuid": uid, "p": props}, ensure_ascii=False) + "\n")
            after = objs[-1]["id"]
            if total % 10000 < PAGE:
                print(f"paged {total} ({total / max(time.time() - t0, 1):.0f}/s) new={new} changed={changed}", flush=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(seen, fh)
    os.replace(tmp, STATE)
    print(f"FETCH DONE seen={total} new={new} changed={changed} spool={SPOOL} secs={time.time() - t0:.0f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
