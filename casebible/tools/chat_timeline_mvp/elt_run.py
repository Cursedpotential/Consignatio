# Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
"""Chat ELT runner — DuckDB templates over the B2 mount, straight into Weaviate.

Owner direction 2026-09-18 20:52 / 21:05 EDT: extraction is DuckDB ELT (the versioned templates in
elt/), the searchable set is Weaviate `ChatEvents20260918` (no Postgres event tables), and the work list
is the chat candidates that the afternoon run did not already load. Type is confirmed by READING the
file (first bytes), not by its folder name.

Per file: sanitize if the format needs it -> template SQL -> event contract -> tag_events_v1.sql (person
tags + the same dedup key as the afternoon build) -> embed (NIM, batched) -> upsert into Weaviate with
uuid5(dedup_key), so an ELT event REPLACES its parser-derived twin instead of duplicating it.

State: /work/elt_state.duckdb (processed files). Progress: one line per file on stdout.
Evidence is read-only; the only writes are Weaviate objects, the state DB and the scratch sanitize file.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import traceback
import uuid
from pathlib import Path

import duckdb
import httpx

B2 = Path(os.environ.get("B2_ROOT", "/b2")) / "salem-data"
WORK = Path(os.environ.get("WORK", "/work"))
TMP = Path(os.environ.get("TMPD", "/tmpd"))
ELT = Path(os.environ.get("ELT_DIR", "/app/elt"))
RUN_ID = os.environ.get("RUN_ID", time.strftime("%Y%m%dT%H%M%S"))
WV = os.environ.get("WEAVIATE_URL", "http://100.91.190.107:8082").rstrip("/")
COLL = os.environ.get("COLLECTION", "ChatEvents20260918")
MODEL = os.environ.get("NIM_EMBED_MODEL", "nvidia/nemotron-3-embed-1b")
DIM = int(os.environ.get("NIM_EMBED_DIMENSIONS", "2048"))
NIM = os.environ.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/") + "/embeddings"
KEY = os.environ["NVIDIA_API_KEY"]
BATCH = int(os.environ.get("BATCH", "32"))
PACE = float(os.environ.get("PACE", "0.4"))  # the AI-chat run owns the embedder tonight; stay behind it
LIMIT = int(os.environ.get("LIMIT", "0"))
ONLY = {f for f in os.environ.get("FORMATS", "").split(",") if f}
NS = uuid.UUID("6f1d3a52-1c7e-4b8e-9a51-2d0e3c9b7a18")  # same namespace as the afternoon embed run
TERMS = json.load(open(os.environ["TERMS"]))

# format -> (template file, blocks, needs_xml_sanitize)
TEMPLATES = {
    "sms_backup_xml": ("elt_smsbackuprestore_v1.sql", ["sms", "mms", "call"], True),
    "calls_backup_xml": ("elt_smsbackuprestore_v1.sql", ["sms", "mms", "call"], True),
    "google_voice_html": ("elt_google_voice_html_v1.sql", ["text", "call"], False),
    "fb_messenger_html": ("elt_fb_messenger_html_v1.sql", ["*"], False),
    "imessage_html": ("elt_imessage_html_v1.sql", ["*"], False),
    "imessage_txt": ("elt_imessage_txt_v1.sql", ["*"], False),
    "mbox": ("elt_mbox_v1.sql", ["*"], False),
    "cube_acr_json": ("elt_cube_acr_json_v1.sql", ["*"], False),
}
EVENT_COLS = ["record_index", "event_ts_utc", "sort_ts", "ts_original", "ts_field", "tz_status", "event_kind",
              "conversation_id", "conversation_title", "participants", "sender", "recipients", "direction",
              "counterparty_phone", "contact_name", "body", "attachments", "member_path"]
NEW_PROPS = [("recipients", "text[]"), ("conversation_id", "text"), ("sha1", "text"), ("catalog_path", "text"),
             ("extractor", "text"), ("ingest_run_id", "text"), ("indexed_at", "date"), ("event_kind", "text"),
             ("direction", "text"), ("counterparty_phone", "text"), ("contact_name", "text"),
             ("search_text", "text"), ("attachments", "text"), ("provenance", "text[]"),
             ("record_kind", "text")]


def sniff(path: Path, guess: str) -> str | None:
    """Confirm the format by reading the file, not by its name. Returns the format to use, or None to skip."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(65536)
    except OSError as e:
        raise RuntimeError(f"unreadable: {e}")
    t = head.decode("utf-8", "replace")
    low = t.lower()
    if "<smses" in low or "<sms " in low or "<mms " in low:
        return "sms_backup_xml"
    if "<calls" in low or "<call " in low:
        return "calls_backup_xml"
    if "hchatlog" in low or ('class="tel"' in low and "<q>" in low):
        return "google_voice_html"
    if "_a6-g" in t or "_a70e" in t:
        return "fb_messenger_html"
    if "bubble from-me" in t or "bubble from-them" in t:
        return "imessage_html"
    if re.search(r"^\[\d{4}-\d{2}-\d{2} [^\]]*\] [^\n]{1,80}:\s*$", t, re.M):
        return "imessage_txt"
    if t.startswith("From ") and re.search(r"(?im)^Date: ", t):
        return "mbox"
    if guess == "cube_acr_json" and t.lstrip().startswith(("{", "[")):
        return "cube_acr_json"
    return None


def load_blocks(name: str) -> dict[str, str]:
    raw = (ELT / name).read_text(encoding="utf-8")
    parts = re.split(r"^-- @block (\w+)\s*$", raw, flags=re.M)
    if len(parts) == 1:
        return {"*": raw.strip().rstrip(";")}
    return {parts[i]: parts[i + 1].strip().rstrip(";") for i in range(1, len(parts), 2)}


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("install webbed from community; load webbed; install zipfs from community; load zipfs")
    con.execute(f"set memory_limit='{os.environ.get('DUCK_MEM', '6GB')}'; set temp_directory='{TMP}'; set threads=4")
    for k in ("katrina_strict", "katrina_possible", "catrina_c", "landlord_context", "nickname",
              "daughter_strong", "daughter_weak", "kinship", "custody", "housing"):
        con.execute(f"set variable {k} = ?", [TERMS[k]])
    con.execute("set variable katrina_phones_confirmed = ?", [TERMS["katrina_phones_confirmed"]])
    return con


def embed(client: httpx.Client, texts: list[str]) -> list[list[float]]:
    for attempt in range(5):
        r = client.post(NIM, headers={"Authorization": f"Bearer {KEY}"}, timeout=180,
                        json={"model": MODEL, "input": texts, "input_type": "passage",
                              "encoding_format": "float", "truncate": "END"})
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
        vs = [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
        assert len(vs) == len(texts) and all(len(v) == DIM for v in vs)
        return vs
    r.raise_for_status()
    raise RuntimeError("embed failed")


def ensure_schema(client: httpx.Client) -> None:
    r = client.get(f"{WV}/v1/schema/{COLL}")
    r.raise_for_status()
    have = {p["name"] for p in r.json().get("properties", [])}
    for name, dt in NEW_PROPS:
        if name not in have:
            resp = client.post(f"{WV}/v1/schema/{COLL}/properties", json={"name": name, "dataType": [dt]})
            print(f"add property {name}: {resp.status_code}", flush=True)


def publish(client: httpx.Client, rows: list[dict]) -> int:
    """Embed + upsert one batch. Katrina/daughter rows are ordered first by the caller."""
    texts = []
    for r in rows:
        t = (r["body"] or "").strip()
        if not t:
            t = " ".join(x for x in [r.get("conversation_title"), r.get("event_kind"), r.get("direction"),
                                     ("attachments: " + r["attachments"]) if r.get("attachments") else None] if x)
        texts.append(t[:8000] or "(empty)")
    vecs = embed(client, texts)
    objs = []
    for r, v, t in zip(rows, vecs, texts):
        props = {
            "dedup_key": r["dedup_key"], "body": r["body"], "search_text": t, "sender": r["sender"],
            "conversation_title": r["conversation_title"], "conversation_id": r["conversation_id"],
            "source_format": r["source_format"], "event_kind": r["event_kind"], "direction": r["direction"],
            "counterparty_phone": r["counterparty_phone"], "contact_name": r["contact_name"],
            "katrina_ref_type": r["katrina_ref_type"], "katrina_conf": r["katrina_conf"],
            "daughter_conf": r["daughter_conf"], "catrina_class": r["catrina_class"], "tz_status": r["tz_status"],
            "ts_original": r["ts_original"], "vault_key": r["vault_key"], "sha1": r["sha1"],
            "catalog_path": r["catalog_rel"], "extractor": r["extractor"], "ingest_run_id": RUN_ID,
            "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "embed_model": MODEL,
            "record_kind": "message",  # owner glossary 21:08: message transcripts, not AI chats
            "attachments": r["attachments"], "n_sources": 1,
            "provenance": [f"{r['vault_key']}|{r['member_path'] or ''}|{r['record_index']}|{r['extractor']}"],
        }
        if r["participants"]:
            props["participants"] = [p for p in r["participants"] if p]
        if r["recipients"]:
            props["recipients"] = [p for p in r["recipients"] if p]
        if r["sort_ts_final"]:
            props["sort_ts"] = r["sort_ts_final"].isoformat() + "Z"
        objs.append({"class": COLL, "id": str(uuid.uuid5(NS, r["dedup_key"])),
                     "properties": {k: v for k, v in props.items() if v is not None},
                     "vectors": {"text_nim": v}})
    resp = client.post(f"{WV}/v1/batch/objects", json={"objects": objs}, timeout=180)
    resp.raise_for_status()
    errs = [o["result"]["errors"] for o in resp.json() if o.get("result", {}).get("errors")]
    if errs:
        print("  weaviate batch errors:", str(errs[0])[:300], flush=True)
    return len(objs) - len(errs)


def extract_file(con: duckdb.DuckDBPyConnection, path: Path, fmt: str, row: dict) -> int:
    tpl, blocks, needs_sanitize = TEMPLATES[fmt]
    src = str(path)
    if needs_sanitize:
        dst = str(TMP / "sanitized.xml")
        sql = (ELT / "elt_xml_sanitize_v1.sql").read_text(encoding="utf-8")
        con.execute(sql.replace("{{SRC}}", src.replace("'", "''")).replace("{{DST}}", dst))
        src = dst
    avail = load_blocks(tpl)
    con.execute("drop table if exists ev_in")
    first = True
    for name in (blocks if blocks != ["*"] else list(avail)):
        if name not in avail:
            continue
        body = avail[name].replace("{{SRC}}", src.replace("'", "''"))
        select = f"""select * exclude (record_index), record_index,
                       '{row['vault_key'].replace("'", "''")}' as vault_key, '{row['sha1']}' as sha1,
                       '{(row.get('catalog_rel_example') or '').replace("'", "''")}' as catalog_rel,
                       '{fmt}' as source_format, '{tpl[:-4]}' as extractor
                     from ({body})"""
        try:
            con.execute(f"{'create table ev_in as' if first else 'insert into ev_in by name'} {select}")
            first = False
        except duckdb.Error as e:
            if "does not contain" in str(e) or "no records" in str(e).lower():
                continue
            raise
    if first:
        return 0
    con.execute((ELT / "tag_events_v1.sql").read_text(encoding="utf-8"))
    return con.execute("select count(*) from ev_tagged").fetchone()[0]


def main() -> int:
    state = duckdb.connect(str(WORK / "elt_state.duckdb"))
    state.execute("create table if not exists processed(vault_key varchar, sha1 varchar, fmt varchar, "
                  "template varchar, n_events bigint, n_published bigint, status varchar, error varchar, "
                  "seconds double, run_id varchar, done_at timestamptz)")
    done = {r[0] for r in state.execute("select sha1 from processed where status in ('ok','skip')").fetchall()}
    work = list(csv.DictReader(open(WORK / "elt_worklist.tsv", encoding="utf-8"), delimiter="\t"))
    if ONLY:
        work = [w for w in work if w["format_guess"] in ONLY]
    client = httpx.Client(timeout=180)
    ensure_schema(client)
    t0 = time.time()
    probe = embed(client, ["batching probe a", "batching probe b", "batching probe c", "batching probe d"])
    print(f"embed batch probe: 4 texts -> {len(probe)} vectors of {len(probe[0])} dims in one call", flush=True)
    n_done = n_pub = 0
    for i, row in enumerate(work, 1):
        if row["sha1"] in done:
            continue
        if LIMIT and n_done >= LIMIT:
            break
        path = B2 / row["vault_key"]
        t1 = time.time()
        status = "ok"
        err = None
        n_ev = n_ok = 0
        try:
            fmt = sniff(path, row["format_guess"])
            if fmt is None or fmt not in TEMPLATES:
                status, err = "skip", f"content not a supported chat format (guess={row['format_guess']})"
            else:
                con = connect()
                n_ev = extract_file(con, path, fmt, row)
                if n_ev:
                    cur = con.execute(
                        "select dedup_key, record_index, event_ts_utc, sort_ts_final, ts_original, tz_status, "
                        "event_kind, conversation_id, conversation_title, participants, sender, recipients, "
                        "direction, counterparty_phone, contact_name, body, attachments, member_path, vault_key, "
                        "sha1, catalog_rel, source_format, extractor, katrina_ref_type, katrina_conf, "
                        "catrina_class, daughter_conf from ev_tagged "
                        "order by (katrina_conf = 'strong') desc, (daughter_conf is not null) desc, sort_ts_final")
                    cols = [d[0] for d in cur.description]
                    while batch := cur.fetchmany(BATCH):
                        n_ok += publish(client, [dict(zip(cols, b)) for b in batch])
                        time.sleep(PACE)
                con.close()
        except Exception as e:  # recorded per file, never silent
            status, err = "error", f"{type(e).__name__}: {e}"[:1500]
            traceback.print_exc()
        dt = time.time() - t1
        state.execute("insert into processed values (?,?,?,?,?,?,?,?,?,?,now())",
                      [row["vault_key"], row["sha1"], row["format_guess"], TEMPLATES.get(row["format_guess"], ("", ))[0],
                       n_ev, n_ok, status, err, dt, RUN_ID])
        n_done += 1
        n_pub += n_ok
        print(f"[{i}/{len(work)}] {status} {row['format_guess']} events={n_ev} published={n_ok} {dt:.1f}s "
              f"size={row['size']} key=...{row['vault_key'][-70:]}", flush=True)
    print(f"RUN DONE run_id={RUN_ID} files={n_done} published={n_pub} elapsed={time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
