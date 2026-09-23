# Byline: Claude Code · Opus 5 · 2026-09-18
"""Hybrid (BM25 + NIM vector) search over ChatEvents20260918.

usage: python search.py "<query>" [katrina|daughter|all] [limit]
Prints sort_ts, source_format, sender, tags and the event id (dedup_key); add SHOW_BODY=1 to print text.
"""
import json
import os
import sys

import httpx

WV = os.environ.get("WEAVIATE_URL", "http://100.91.190.107:8082").rstrip("/")
COLL = os.environ.get("COLLECTION", "ChatEvents20260918")
q = sys.argv[1]
scope = sys.argv[2] if len(sys.argv) > 2 else "all"
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
r = httpx.post("https://integrate.api.nvidia.com/v1/embeddings", timeout=60,
               headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}"},
               json={"model": "nvidia/nemotron-3-embed-1b", "input": [q], "input_type": "query", "encoding_format": "float"})
r.raise_for_status()
vec = r.json()["data"][0]["embedding"]
where = {"katrina": '{path:["katrina_conf"], operator:Equal, valueText:"strong"}',
         "daughter": '{path:["daughter_conf"], operator:IsNull, valueBoolean:false}'}.get(scope)
gql = f"""{{ Get {{ {COLL}(limit:{limit}, hybrid:{{query:{json.dumps(q)}, alpha:0.5, targetVectors:["text_nim"], vector:{json.dumps(vec)}}}
  {"where:" + where if where else ""}) {{ dedup_key sort_ts source_format sender katrina_ref_type daughter_conf body _additional {{ score }} }} }} }}"""
res = httpx.post(f"{WV}/v1/graphql", json={"query": gql}, timeout=60).json()
if res.get("errors"):
    sys.exit(json.dumps(res["errors"])[:1000])
for o in res["data"]["Get"][COLL]:
    line = f"{o['sort_ts']}  {o['source_format']:<18} {str(o.get('katrina_ref_type')):<14} {str(o.get('daughter_conf')):<7} id={o['dedup_key'][:12]} score={o['_additional']['score']}"
    print(line + (("\n    " + (o.get("body") or "")[:300]) if os.environ.get("SHOW_BODY") else ""))
