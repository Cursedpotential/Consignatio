# Byline: Claude Code · Opus 5 · 2026-09-18
"""Embed deduplicated chat events (NIM, batched) into a dedicated Weaviate collection for hybrid search.

Runs AFTER the Surreal load (owner 12:45: timelines readable before searchable). Same embedder as Intake
(nvidia/nemotron-3-embed-1b, 2048-d, input_type=passage; the batching was probed with a 4-text call on 2026-09-18).
Object id = uuid5(dedup_key), so re-runs are idempotent. PHASE=priority|rest|all.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

import duckdb
import httpx

WORK = Path(os.environ.get("WORK", "/work"))
WV = os.environ.get("WEAVIATE_URL", "http://100.91.190.107:8082").rstrip("/")
COLL = os.environ.get("COLLECTION", "ChatEvents20260918")
MODEL = os.environ.get("NIM_EMBED_MODEL", "nvidia/nemotron-3-embed-1b")
DIM = int(os.environ.get("NIM_EMBED_DIMENSIONS", "2048"))
NIM = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/") + "/embeddings"
KEY = os.environ["NVIDIA_API_KEY"]
BATCH = int(os.environ.get("BATCH", "64"))
PHASE = os.environ.get("PHASE", "priority")
NS = uuid.UUID("6f1d3a52-1c7e-4b8e-9a51-2d0e3c9b7a18")

TEXT = ["dedup_key", "body", "sender", "conversation_title", "source_format", "katrina_ref_type", "katrina_conf",
        "daughter_conf", "catrina_class", "tz_status", "ts_original", "vault_key", "embed_model"]

SCHEMA = {
    "class": COLL,
    "description": "Chat timeline MVP events (2026-09-18); rebuildable from B2 via chat_timeline_mvp",
    "properties": [{"name": n, "dataType": ["text"]} for n in TEXT]
    + [{"name": "participants", "dataType": ["text[]"]}, {"name": "sort_ts", "dataType": ["date"]},
       {"name": "n_sources", "dataType": ["int"]}],
    "vectorConfig": {"text_nim": {"vectorizer": {"none": {}}, "vectorIndexType": "hnsw"}},
}


def ensure_schema(c):
    r = c.get(f"{WV}/v1/schema/{COLL}")
    if r.status_code == 404:
        c.post(f"{WV}/v1/schema", json=SCHEMA).raise_for_status()
        print("created collection", COLL, flush=True)


def embed(c, texts):
    for a in range(5):
        r = c.post(NIM, headers={"Authorization": f"Bearer {KEY}"}, timeout=120,
                   json={"model": MODEL, "input": texts, "input_type": "passage", "encoding_format": "float", "truncate": "END"})
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (a + 1))
            continue
        r.raise_for_status()
        vs = [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
        assert len(vs) == len(texts) and all(len(v) == DIM for v in vs)
        return vs
    r.raise_for_status()


def main():
    con = duckdb.connect(str(WORK / "timeline_build.duckdb"), read_only=True)
    where = {"priority": "katrina_conf is not null or daughter_conf is not null or catrina_class is not null",
             "rest": "not (katrina_conf is not null or daughter_conf is not null or catrina_class is not null)",
             "all": "true"}[PHASE]
    cur = con.execute(f"""select dedup_key, body, sender, conversation_title, source_format, katrina_ref_type, katrina_conf,
                                 daughter_conf, catrina_class, tz_status, ts_original, vault_key, participants, sort_ts, n_sources
                          from events_dedup where ({where}) and length(trim(coalesce(body, ''))) > 0 order by sort_ts""")
    cols = [d[0] for d in cur.description]
    c = httpx.Client(timeout=120)
    ensure_schema(c)
    n, t0 = 0, time.time()
    while rows := cur.fetchmany(BATCH):
        recs = [dict(zip(cols, r)) for r in rows]
        vecs = embed(c, [(r["body"] or "")[:8000] for r in recs])
        objs = []
        for r, v in zip(recs, vecs):
            props = {k: r[k] for k in TEXT if k in r and r[k] is not None}
            props["embed_model"] = MODEL
            if r["participants"]:
                props["participants"] = [p for p in r["participants"] if p]
            if r["sort_ts"]:
                props["sort_ts"] = r["sort_ts"].isoformat() + "Z"
            props["n_sources"] = int(r["n_sources"])
            objs.append({"class": COLL, "id": str(uuid.uuid5(NS, r["dedup_key"])), "properties": props,
                         "vectors": {"text_nim": v}})
        res = c.post(f"{WV}/v1/batch/objects", json={"objects": objs})
        res.raise_for_status()
        errs = [o["result"]["errors"] for o in res.json() if o.get("result", {}).get("errors")]
        if errs:
            print("batch errors", str(errs[0])[:500], flush=True)
        n += len(objs)
        if n % (BATCH * 20) < BATCH:
            print(f"embedded {n} ({n / (time.time() - t0):.0f}/s)", flush=True)
    print(f"EMBED DONE phase={PHASE} objects={n}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
