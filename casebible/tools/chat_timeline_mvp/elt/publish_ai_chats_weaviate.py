# Byline: Claude Code · Opus 5 · 2026-09-18
"""Publish AI-chat turns to Weaviate ChatEvents20260918 (owner 2026-09-18 20:07 EDT:
"IT ALL GOES TO WEIVIATE FIRST"). No Postgres event tables.

  record_kind = 'ai_chat'   (message transcripts -- SMS/Messenger/etc -- are 'message')
  speaker     = owner | assistant | system | other
  id          = uuid5(NS, dedup_key), so re-runs upsert and never duplicate.

PHASE controls the order the owner asked for:
  owner_priority  owner turns tagged katrina / daughter / house       (first)
  owner_rest      every remaining owner turn                          (second)
  assistant       assistant turns, for context                        (third)

Person regexes come from the UNTRACKED server file $TERMS
(/data/probata/config/timeline-mvp/terms.json). Names never enter git or logs.
Topic tags are a cheap deterministic regex pass -- no LLM classification.

Embedder: the same NIM model the collection already uses; batching is probed with a
4-text call before the bulk run (global rule: probe batching before a bulk embed).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone

import duckdb
import httpx

WORK = os.environ.get("AI_DUCKDB", "/w/ai_chats.duckdb")
WV = os.environ.get("WEAVIATE_URL", "http://100.91.190.107:8082").rstrip("/")
COLL = os.environ.get("COLLECTION", "ChatEvents20260918")
MODEL = os.environ.get("NIM_EMBED_MODEL", "nvidia/nemotron-3-embed-1b")
DIM = int(os.environ.get("NIM_EMBED_DIMENSIONS", "2048"))
NIM = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/") + "/embeddings"
KEY = os.environ["NVIDIA_API_KEY"]
BATCH = int(os.environ.get("BATCH", "64"))
PHASE = os.environ.get("PHASE", "owner_priority")
RUN = os.environ.get("INGEST_RUN_ID", "aichat-20260919")
TERMS = os.environ.get("TERMS", "/terms/terms.json")
CHUNK = int(os.environ.get("CHUNK_CHARS", "4000"))
NS = uuid.UUID("6f1d3a52-1c7e-4b8e-9a51-2d0e3c9b7a18")   # same namespace as the messaging loader

# ---- deterministic topic regexes (tracked; generic vocabulary, no private identifiers) ----
TOPICS = {
    "house":  r"\b(house|home|mortgage|foreclos\w*|evict\w*|landlord|rent(?:al|ing)?|lease|utilit\w*|"
              r"water bill|electric bill|shut ?off|deed|title company|escrow|property tax)\b",
    "court":  r"\b(court|custody|parenting ?time|friend of the court|\bFOC\b|\bCPS\b|police|\bPPO\b|"
              r"restraining order|court order|hearing|motion|attorney|lawyer|judge|referee|"
              r"docket|subpoena|deposition|guardian ad litem|\bGAL\b)\b",
    "abuse":  r"\b(abuse\w*|abusive|threat\w*|lie[sd]?|lying|manipulat\w*|alienat\w*|withh\w*|gaslight\w*|"
              r"drunk|alcohol\w*|intoxicat\w*|arrest\w*|assault\w*|harass\w*|stalk\w*|coerc\w*)\b",
    "money":  r"\b(money|job|fired|laid off|income|debt|bills?|paycheck|unemploy\w*|wages?|garnish\w*|"
              r"bankrupt\w*|loan|collections?|child support|arrears)\b",
    "health": r"\b(health|hospital|doctor|\bER\b|emergency room|medic\w*|therapy|therapist|counsel\w*|"
              r"diagnos\w*|prescription|psychiatr\w*|overdose|rehab)\b",
}


_LOCAL_FMTS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y, %I:%M:%S %p",
               "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y, %H:%M:%S", "%b %d, %Y, %I:%M:%S %p",
               "%B %d, %Y at %I:%M %p", "%Y-%m-%d"]


def parse_local(s):
    """Best-effort parse of an exporter's LOCAL wall-clock string, for ORDERING only.
    Returns an ISO string or None. The value is never published as event_ts."""
    if not s:
        return None
    s = s.strip().strip("[]()")
    for f in _LOCAL_FMTS:
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def load_person_regex():
    t = json.load(open(TERMS, encoding="utf-8"))
    out = {}
    for tag, keys in (("katrina", ("katrina_strict", "katrina_strong")),
                      ("katrina_possible", ("katrina_possible",)),
                      ("daughter", ("daughter_strong",)),
                      ("daughter_possible", ("daughter_weak",)),
                      ("catrina_landlord", ("catrina_c",))):
        pats = [t[k] for k in keys if isinstance(t.get(k), str) and t[k].strip()]
        if pats:
            out[tag] = re.compile("|".join(f"(?:{p})" for p in pats), re.I)
    return out


PERSON = load_person_regex()
TOPIC_RX = {k: re.compile(v, re.I) for k, v in TOPICS.items()}

TEXT_PROPS = ["dedup_key", "body", "sender", "speaker", "conversation_title", "conversation_id",
              "source_format", "service", "record_kind", "katrina_conf", "daughter_conf",
              "catrina_class", "tz_status", "ts_original", "vault_key", "sha1", "catalog_path",
              "zip_member_path", "extractor", "ingest_run_id", "embed_model"]
NEW_PROPS = [("speaker", "text"), ("service", "text"), ("record_kind", "text"),
             ("conversation_id", "text"), ("sha1", "text"), ("catalog_path", "text"),
             ("zip_member_path", "text"), ("extractor", "text"), ("ingest_run_id", "text"),
             ("turn_index", "int"), ("chunk_index", "int"), ("chunk_count", "int"),
             ("event_ts", "date"), ("catalog_modtime_hint", "date"), ("indexed_at", "date"),
             ("topics", "text[]")]


def ensure_props(c):
    r = c.get(f"{WV}/v1/schema/{COLL}")
    r.raise_for_status()
    have = {p["name"] for p in r.json().get("properties", [])}
    for name, dt in NEW_PROPS:
        if name not in have:
            rr = c.post(f"{WV}/v1/schema/{COLL}/properties", json={"name": name, "dataType": [dt]})
            print(f"add property {name}:{dt} -> {rr.status_code}", flush=True)


def embed(c, texts):
    last = None
    for a in range(6):
        r = c.post(NIM, headers={"Authorization": f"Bearer {KEY}"}, timeout=180,
                   json={"model": MODEL, "input": texts, "input_type": "passage",
                         "encoding_format": "float", "truncate": "END"})
        last = r
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(4 * (a + 1))
            continue
        r.raise_for_status()
        vs = [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
        assert len(vs) == len(texts) and all(len(v) == DIM for v in vs), "embedder returned wrong shape"
        return vs
    last.raise_for_status()


def chunks(body: str):
    if len(body) <= CHUNK:
        return [body]
    out, cur = [], []
    n = 0
    for para in body.split("\n"):
        if n + len(para) + 1 > CHUNK and cur:
            out.append("\n".join(cur))
            cur, n = [], 0
        cur.append(para)
        n += len(para) + 1
    if cur:
        out.append("\n".join(cur))
    return [c for c in out if c.strip()] or [body[:CHUNK]]


WHERE = {
    "owner_priority": "speaker = 'owner'",
    "owner_rest": "speaker = 'owner'",
    "assistant": "speaker <> 'owner'",
    "all": "true",
}


def main() -> int:
    con = duckdb.connect(WORK, read_only=True)
    cur = con.execute(f"""
        select vault_key, sha1, catalog_path, zip_member_path, catalog_modtime_hint, extractor,
               service, source_format, conversation_id, conversation_title, turn_index,
               speaker, body, event_ts_utc, ts_original, tz_status
        from ai_turns
        where {WHERE[PHASE]} and length(trim(coalesce(body,''))) > 0
        order by event_ts_utc nulls last, vault_key, conversation_id, turn_index""")
    cols = [d[0] for d in cur.description]

    c = httpx.Client(timeout=180)
    ensure_props(c)
    probe = embed(c, ["batching probe a", "batching probe b", "batching probe c", "batching probe d"])
    print(f"embedder batch probe: 4 texts -> {len(probe)} vectors of {len(probe[0])} dims (batching OK)", flush=True)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    n_obj = n_skip = 0
    t0 = time.time()
    pending: list[dict] = []

    def flush():
        nonlocal n_obj, pending
        if not pending:
            return
        vecs = embed(c, [p["properties"]["body"][:8000] for p in pending])
        for p, v in zip(pending, vecs):
            p["vectors"] = {"text_nim": v}
        res = c.post(f"{WV}/v1/batch/objects", json={"objects": pending})
        res.raise_for_status()
        errs = [o["result"]["errors"] for o in res.json() if o.get("result", {}).get("errors")]
        if errs:
            print("BATCH ERRORS", str(errs[0])[:400], flush=True)
        n_obj += len(pending)
        if n_obj % (BATCH * 10) < BATCH:
            print(f"published {n_obj} ({n_obj/(time.time()-t0):.0f}/s) phase={PHASE}", flush=True)
        pending = []

    while rows := cur.fetchmany(2000):
        for row in rows:
            r = dict(zip(cols, row))
            body = r["body"]
            tags = sorted(k for k, rx in TOPIC_RX.items() if rx.search(body))
            people = {k: ("strong" if rx.search(body) else None) for k, rx in PERSON.items()}
            kat = "strong" if people.get("katrina") else ("possible" if people.get("katrina_possible") else None)
            dau = "strong" if people.get("daughter") else ("possible" if people.get("daughter_possible") else None)
            cat = "landlord_candidate" if people.get("catrina_landlord") else None
            if PHASE == "owner_priority" and not (kat or dau or ("house" in tags)):
                n_skip += 1
                continue
            if PHASE == "owner_rest" and (kat or dau or ("house" in tags)):
                n_skip += 1
                continue

            parts = chunks(body)
            for ci, part in enumerate(parts):
                dk = "ai:" + hashlib.sha256(
                    "|".join([r["sha1"] or "", r["zip_member_path"] or "", r["conversation_id"] or "",
                              str(r["turn_index"]), str(ci)]).encode()).hexdigest()
                props = {
                    "dedup_key": dk, "body": part, "sender": r["speaker"], "speaker": r["speaker"],
                    "record_kind": "ai_chat", "service": r["service"], "source_format": r["source_format"],
                    "conversation_id": r["conversation_id"], "conversation_title": r["conversation_title"] or "",
                    "turn_index": int(r["turn_index"] or 0), "chunk_index": ci, "chunk_count": len(parts),
                    "tz_status": r["tz_status"] or "missing", "ts_original": r["ts_original"] or "",
                    "vault_key": r["vault_key"], "sha1": r["sha1"] or "",
                    "catalog_path": r["catalog_path"] or "", "zip_member_path": r["zip_member_path"] or "",
                    "extractor": r["extractor"], "ingest_run_id": RUN, "embed_model": MODEL,
                    "indexed_at": now, "topics": tags,
                }
                if r["event_ts_utc"]:
                    iso = r["event_ts_utc"].astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") \
                        if r["event_ts_utc"].tzinfo else r["event_ts_utc"].strftime("%Y-%m-%dT%H:%M:%SZ")
                    props["event_ts"] = iso
                    props["sort_ts"] = iso
                else:
                    # Local wall-clock with no zone (markdown/chat-memo exporters): usable for
                    # ORDERING only. sort_ts gets it; event_ts stays absent, tz_status says why.
                    naive = parse_local(r["ts_original"])
                    if naive:
                        props["sort_ts"] = naive
                if r["catalog_modtime_hint"]:
                    props["catalog_modtime_hint"] = r["catalog_modtime_hint"].isoformat().replace("+00:00", "Z")
                if kat:
                    props["katrina_conf"] = kat
                if dau:
                    props["daughter_conf"] = dau
                if cat:
                    props["catrina_class"] = cat
                pending.append({"class": COLL, "id": str(uuid.uuid5(NS, dk)), "properties": props})
                if len(pending) >= BATCH:
                    flush()
    flush()
    print(f"PUBLISH DONE phase={PHASE} objects={n_obj} skipped_other_phase={n_skip} "
          f"secs={time.time()-t0:.0f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
