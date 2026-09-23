# Byline: Claude Code · Opus 5 · 2026-09-18
"""Load the deduplicated timeline (timeline_build.duckdb) into Intake's SurrealDB.

Order: Katrina (strong) + daughter-tagged events first, then the landlord/ambiguous sets, then the rest,
so the priority timelines are queryable before the long tail finishes (owner 12:45 EDT "readable before
searchable"). Idempotent: ids are the dedup_key; re-runs update tags/provenance in place.
Env: SURREAL_URL, SURREAL_USER, SURREAL_PASS, WORK, PHASE (priority|rest|all), BATCH.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb
import httpx

WORK = Path(os.environ.get("WORK", "/work"))
URL = os.environ.get("SURREAL_URL", "http://100.91.190.107:8473").rstrip("/") + "/sql"
AUTH = (os.environ["SURREAL_USER"], os.environ["SURREAL_PASS"])
HDR = {"surreal-ns": "consignatio", "surreal-db": "intake", "Accept": "application/json"}
BATCH = int(os.environ.get("BATCH", "400"))
PHASE = os.environ.get("PHASE", "all")
T = "_20260918"

_DT = re.compile(r'"__DT__([^"]*)__"')
_RID = re.compile(r'"__RID__([a-z_0-9]+):([^"]*)__"')


def dt(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        s = v.isoformat()
        if v.tzinfo is None:
            s += "Z"  # sort_ts is naive; it is UTC when tz_status=utc_known, else local-unknown (flagged)
        return f"__DT__{s}__"
    return v


def rid(table, key):
    return f"__RID__{table}{T}:{key}__"


def sql_literal(obj):
    s = json.dumps(obj, ensure_ascii=False, default=str)
    s = _DT.sub(lambda m: f'd"{m.group(1)}"', s)
    return _RID.sub(lambda m: f"{m.group(1)}:⟨{m.group(2)}⟩", s)


def key(*parts):
    return hashlib.md5("|".join(p or "" for p in parts).encode()).hexdigest()


def run(client, q):
    for attempt in range(5):
        try:
            r = client.post(URL, content=q.encode("utf-8"), auth=AUTH, headers=HDR, timeout=REQ_TIMEOUT)
            r.raise_for_status()
            bad = [x for x in r.json() if x.get("status") != "OK"]
            if bad:
                raise RuntimeError(str(bad[0])[:800])
            time.sleep(PACE)
            return
        except httpx.TimeoutException:
            # surreal-intake wedged twice on 2026-09-18 under bulk INSERT; never keep hammering a hung DB.
            print("SURREAL UNRESPONSIVE: request timed out; loader stopping without retry", flush=True)
            raise SystemExit(3)
        except (httpx.HTTPError, RuntimeError) as e:
            if attempt == 4:
                raise
            print("retry", attempt, e, flush=True)
            time.sleep(2 + attempt * 3)


REQ_TIMEOUT = float(os.environ.get("REQ_TIMEOUT", "60"))
PACE = float(os.environ.get("PACE", "0.3"))  # seconds between requests
MAX_BYTES = int(os.environ.get("MAX_BYTES", "700000"))  # surreal-intake rejects larger /sql bodies (413)


def send(client, head, items, tail):
    """One INSERT per chunk, each request body kept under MAX_BYTES."""
    chunk, size = [], 0
    for it in items:
        lit = sql_literal({k: v for k, v in it.items() if v is not None})  # JSON null is NULL, not NONE
        if chunk and size + len(lit.encode()) > MAX_BYTES:
            run(client, f"{head} [{','.join(chunk)}] {tail};")
            chunk, size = [], 0
        chunk.append(lit)
        size += len(lit.encode()) + 1
    if chunk:
        run(client, f"{head} [{','.join(chunk)}] {tail};")


TAGS = ["katrina_ref_type", "katrina_conf", "catrina_class", "daughter_conf", "custody_hit", "housing_hit",
        "n_sources", "provenance"]


def main():
    con = duckdb.connect(str(WORK / "timeline_build.duckdb"), read_only=True)
    where = {
        "priority": "katrina_conf is not null or daughter_conf is not null or catrina_class is not null",
        "rest": "not (katrina_conf is not null or daughter_conf is not null or catrina_class is not null)",
        "all": "true",
    }[PHASE]
    q = f"""
      select e.*, p.prov from events_dedup e
      join (select dedup_key, list({{'vault_key': vault_key, 'sha1': sha1, 'catalog_rel': catalog_rel, 'member_path': member_path,
                                    'record_index': record_index, 'ts_original': ts_original, 'ts_field': ts_field,
                                    'extractor': extractor, 'source_format': source_format}}) prov
            from event_provenance group by dedup_key) p using (dedup_key)
      where {where}
      order by (katrina_conf = 'strong') desc nulls last, (daughter_conf is not null) desc, sort_ts
    """
    cur = con.execute(q)
    cols = [d[0] for d in cur.description]
    client = httpx.Client()
    n = 0
    t0 = time.time()
    while True:
        rows = cur.fetchmany(BATCH)
        if not rows:
            break
        evs, convs, persons, srcs, r_in, r_from, r_sent = [], {}, {}, {}, [], [], []
        for row in rows:
            r = dict(zip(cols, row))
            k = r["dedup_key"]
            conv_k = key(r["source_format"] if r["counterparty_phone"] is None else "phone", r["counterparty_phone"] or r["conversation_id"] or r["conversation_title"])
            convs[conv_k] = {"id": rid("tl_conversation", conv_k), "title": r["conversation_title"], "conversation_id": r["conversation_id"],
                             "counterparty_phone": r["counterparty_phone"], "source_format": r["source_format"]}
            ev = {c: r[c] for c in cols if c not in ("prov", "dedup_key", "custody_hit", "housing_hit")}
            ev.update(id=rid("tl_event", k), dedup_key=k, sort_ts=dt(r["sort_ts"]), event_ts_utc=dt(r["event_ts_utc"]),
                      custody_hit=bool(r["custody_hit"]), housing_hit=bool(r["housing_hit"]), provenance=r["prov"],
                      conversation=rid("tl_conversation", conv_k))
            evs.append(ev)
            r_in.append({"id": rid("tl_in", k), "in": rid("tl_event", k), "out": rid("tl_conversation", conv_k)})
            if r["sender"]:
                pk = key(r["sender"].strip().lower())
                persons[pk] = {"id": rid("tl_person", pk), "label": r["sender"].strip()}
                r_sent.append({"id": rid("tl_sent", k), "in": rid("tl_person", pk), "out": rid("tl_event", k)})
            for p in r["prov"]:
                srcs[p["sha1"]] = {"id": rid("tl_source", p["sha1"]), "vault_key": p["vault_key"], "sha1": p["sha1"],
                                   "catalog_rel": p["catalog_rel"], "source_format": p["source_format"]}
                fk = key(k, p["sha1"], p["member_path"], str(p["record_index"]))
                r_from.append({"id": rid("tl_from", fk), "in": rid("tl_event", k), "out": rid("tl_source", p["sha1"]),
                               "record_index": p["record_index"], "member_path": p["member_path"],
                               "ts_original": p["ts_original"], "ts_field": p["ts_field"], "extractor": p["extractor"]})
        upd = ", ".join(f"{c} = $input.{c}" for c in TAGS)
        send(client, f"INSERT INTO tl_conversation{T}", list(convs.values()), "ON DUPLICATE KEY UPDATE title = $input.title")
        send(client, f"INSERT INTO tl_person{T}", list(persons.values()), "ON DUPLICATE KEY UPDATE label = $input.label")
        send(client, f"INSERT INTO tl_source{T}", list(srcs.values()), "ON DUPLICATE KEY UPDATE vault_key = $input.vault_key")
        send(client, f"INSERT INTO tl_event{T}", evs, f"ON DUPLICATE KEY UPDATE {upd}")
        send(client, f"INSERT RELATION IGNORE INTO tl_in{T}", r_in, "")
        send(client, f"INSERT RELATION IGNORE INTO tl_from{T}", r_from, "")
        send(client, f"INSERT RELATION IGNORE INTO tl_sent{T}", r_sent, "")
        n += len(rows)
        if n % (BATCH * 25) < BATCH:
            print(f"loaded {n} events ({n / (time.time() - t0):.0f}/s)", flush=True)
    print(f"LOAD DONE phase={PHASE} events={n} secs={time.time() - t0:.0f}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
