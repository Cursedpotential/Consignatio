# Byline: Claude Code · Opus 5 · 2026-09-18
"""Chat discovery -> events (timeline MVP, owner 2026-09-18 12:32 EDT).

Source: B2 only, read through the OpenList/rclone mount (/b2 in the container), scoped by
the catalog table raw_duck.chat_candidates_20260918 (exported to candidates.tsv).
Engine: DuckDB SQL templates first (read_json / read_text); the existing Probata parsers
(server/tools/parsers/messaging, copied read-only into /app/server) are the backup for
formats a template cannot stream (multi-GB SMS Backup & Restore XML, iMessage TXT/HTML,
Facebook HTML).

Incremental: state.processed keys on (sha1, extractor, version); a file whose content is
unchanged is skipped, a new or changed B2 object is extracted on the next run.
Read-only on evidence. Output: scratch DuckDB (events_raw) -> dedupe/tag -> Parquet on B2
and SurrealDB (load_surreal.py).

Person matching terms live in an UNTRACKED server file (TERMS env), never in git.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pyarrow as pa

sys.path.insert(0, "/app")  # copied Probata server/ package (backup parsers)
from server.tools.parsers.messaging import sms_xml  # backup parser (streaming)  # noqa: E402
from server.tools.parsers.messaging import imessage_txt  # backup parser  # noqa: E402
from server.tools.parsers.messaging import facebook_messenger_html  # backup parser  # noqa: E402

B2 = Path(os.environ.get("B2_ROOT", "/b2"))
WORK = Path(os.environ.get("WORK", "/work"))
DB = WORK / os.environ.get("DB_NAME", "timeline.duckdb")  # one writer per file; heavy runs use their own
VERSION = "chat-timeline-mvp-v1"
BODY_MAX = 200_000

SCHEMA = pa.schema([
    ("event_uid", pa.string()), ("source_format", pa.string()), ("extractor", pa.string()),
    ("vault_key", pa.string()), ("sha1", pa.string()), ("catalog_rel", pa.string()),
    ("member_path", pa.string()), ("record_index", pa.int64()),
    ("event_ts_utc", pa.timestamp("ms", tz="UTC")), ("sort_ts", pa.timestamp("ms")),
    ("ts_original", pa.string()), ("ts_field", pa.string()), ("tz_status", pa.string()),
    ("event_kind", pa.string()), ("conversation_id", pa.string()), ("conversation_title", pa.string()),
    ("participants", pa.list_(pa.string())), ("sender", pa.string()), ("recipients", pa.list_(pa.string())),
    ("direction", pa.string()), ("counterparty_phone", pa.string()), ("contact_name", pa.string()),
    ("body", pa.string()), ("attachments", pa.string()),
])


def _fix_fb(s):
    """Facebook exports write UTF-8 bytes as \\u00XX escapes (mojibake)."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _phone(s):
    d = re.sub(r"\D", "", s or "")
    return d[-10:] if len(d) >= 10 else (d or None)


def _row(ctx, idx, **kw):
    r = {k: None for k in SCHEMA.names}
    r.update(ctx)
    r.update(kw)
    r["record_index"] = idx
    r["extractor"] = f"{ctx['_extractor']}@{VERSION}"
    del r["_extractor"]
    r["event_uid"] = hashlib.sha256(f"{ctx['sha1']}|{ctx.get('member_path') or ''}|{idx}".encode()).hexdigest()[:32]
    if r["body"] and len(r["body"]) > BODY_MAX:
        r["body"] = r["body"][:BODY_MAX]
    ts = r.get("event_ts_utc")
    if ts is not None and r.get("sort_ts") is None:
        r["sort_ts"] = ts.replace(tzinfo=None)
    r.pop("_extractor", None)
    return r


# ---------------- DuckDB templates ----------------

def ex_fb_messenger_json(con, path, ctx):
    ctx["_extractor"] = "duckdb:fb_messenger_json"
    rows = con.execute(
        """
        with f as (select * from read_json(?, columns={participants:'JSON', messages:'JSON', title:'VARCHAR', thread_path:'VARCHAR'},
                                           maximum_object_size=1000000000)),
             g as (select title, thread_path, participants, from_json(messages, '["JSON"]') ms from f)
        select title, thread_path, participants, generate_subscripts(ms, 1) i, unnest(ms) m from g
        """, [str(path)]).fetchall()
    out = []
    for title, thread_path, parts, i, m in rows:
        m = json.loads(m) if isinstance(m, str) else m
        plist = [_fix_fb(p.get("name")) for p in (json.loads(parts) if isinstance(parts, str) else parts or [])]
        ms = m.get("timestamp_ms")
        ts = datetime.fromtimestamp(ms / 1000, tz=timezone.utc) if ms else None
        sender = _fix_fb(m.get("sender_name"))
        att = {k: m[k] for k in ("photos", "videos", "audio_files", "files", "gifs", "sticker", "share", "reactions") if k in m}
        out.append(_row(ctx, int(i), event_ts_utc=ts, ts_original=str(ms) if ms else None, ts_field="timestamp_ms(epoch_ms,UTC)",
                        tz_status="utc_known" if ts else "missing", event_kind="message",
                        conversation_id=thread_path or title, conversation_title=_fix_fb(title),
                        participants=plist, sender=sender, recipients=[p for p in plist if p != sender],
                        direction=None, body=_fix_fb(m.get("content")),
                        attachments=json.dumps(att, ensure_ascii=False) if att else None))
    return out


_WA = [
    re.compile(r"^‎?\[(?P<d>\d{1,2}[./-]\d{1,2}[./-]\d{2,4}),? (?P<t>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap]\.?[Mm]\.?)?)\] (?P<s>[^:]{1,80}): (?P<b>.*)$"),
    re.compile(r"^‎?(?P<d>\d{1,2}[./-]\d{1,2}[./-]\d{2,4}),? (?P<t>\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap]\.?[Mm]\.?)?) - (?P<s>[^:]{1,80}): (?P<b>.*)$"),
]


def _wa_local(d, t):
    sep = "." if "." in d else ("/" if "/" in d else "-")
    a, b, y = d.split(sep)
    y = int(y) + (2000 if len(y) == 2 else 0)
    # '.' exports are day-first (EU locale); '/' exports from a US phone are month-first.
    day, mon = (int(a), int(b)) if sep == "." else (int(b), int(a))
    t2 = re.sub(r"\s", "", t.replace(".", "")).upper()  # iOS puts U+202F before AM/PM
    fmt = "%I:%M:%S%p" if t2.count(":") == 2 and t2[-1] == "M" else "%I:%M%p" if t2[-1] == "M" else "%H:%M:%S" if t2.count(":") == 2 else "%H:%M"
    tt = datetime.strptime(t2, fmt)
    return datetime(y, mon, day, tt.hour, tt.minute, tt.second), ("day_first" if sep == "." else "month_first")


def ex_whatsapp_txt(con, path, ctx):
    ctx["_extractor"] = "duckdb:whatsapp_txt"
    lines = con.execute(
        "select generate_subscripts(l, 1) i, unnest(l) line "
        "from (select string_split(replace(content, chr(13), ''), chr(10)) l from read_text(?))", [str(path)]).fetchall()
    msgs, cur = [], None
    for i, line in lines:
        m = next((p.match(line or "") for p in _WA if p.match(line or "")), None)
        if m:
            cur = {"i": i, "d": m["d"], "t": m["t"], "s": m["s"].strip("‎ "), "b": [m["b"]]}
            msgs.append(cur)
        elif cur is not None:
            cur["b"].append(line)
    senders = sorted({x["s"] for x in msgs})
    title = Path(ctx["vault_key"]).parent.name
    out = []
    for x in msgs:
        try:
            local, order = _wa_local(x["d"], x["t"])
        except Exception:
            local, order = None, "unparsed"
        out.append(_row(ctx, x["i"], event_ts_utc=None, sort_ts=local, ts_original=f"{x['d']} {x['t']}",
                        ts_field=f"line_prefix(local,{order})", tz_status="local_unknown_tz" if local else "unparsed",
                        event_kind="message", conversation_id=title, conversation_title=title, participants=senders,
                        sender=x["s"], recipients=[s for s in senders if s != x["s"]], body="\n".join(x["b"]).strip()))
    return out


def ex_google_chat_json(con, path, ctx):
    ctx["_extractor"] = "duckdb:google_chat_json"
    rows = con.execute(
        "select unnest(from_json(messages, '[\"JSON\"]')) m from read_json(?, columns={messages:'JSON'})", [str(path)]).fetchall()
    conv = Path(ctx["vault_key"]).parent.name
    out = []
    for i, (m,) in enumerate(rows):
        m = json.loads(m) if isinstance(m, str) else m
        raw = m.get("created_date")
        ts = None
        if raw:
            for fmt in ("%A, %B %d, %Y at %I:%M:%S %p %Z",):
                try:
                    ts = datetime.strptime(raw.replace(" ", " "), fmt).replace(tzinfo=timezone.utc) if raw.rstrip().endswith("UTC") else None
                except ValueError:
                    ts = None
        cr = m.get("creator") or {}
        out.append(_row(ctx, i, event_ts_utc=ts, sort_ts=None, ts_original=raw, ts_field="created_date",
                        tz_status="utc_known" if ts else ("unparsed" if raw else "missing"), event_kind="message",
                        conversation_id=conv, conversation_title=conv, participants=None,
                        sender=f"{cr.get('name')} <{cr.get('email')}>" if cr else None, body=m.get("text"),
                        attachments=json.dumps(m.get("attached_files")) if m.get("attached_files") else None))
    return out


def ex_ai_conversations_json(con, path, ctx):
    """ChatGPT (mapping graph) or Claude (chat_messages) conversations.json."""
    ctx["_extractor"] = "duckdb:ai_conversations_json"
    convs = con.execute("select unnest(from_json(content, '[\"JSON\"]')) c from read_text(?)", [str(path)]).fetchall()
    out, idx = [], 0
    for (c,) in convs:
        c = json.loads(c) if isinstance(c, str) else c
        title = c.get("title") or c.get("name")
        cid = c.get("id") or c.get("uuid") or c.get("conversation_id")
        if "mapping" in c:
            nodes = [n.get("message") for n in (c.get("mapping") or {}).values() if n.get("message")]
            nodes.sort(key=lambda m: m.get("create_time") or 0)
            for m in nodes:
                parts = (m.get("content") or {}).get("parts") or []
                text = "\n".join(p for p in parts if isinstance(p, str)).strip()
                if not text:
                    continue
                ct = m.get("create_time")
                ts = datetime.fromtimestamp(ct, tz=timezone.utc) if ct else None
                out.append(_row(ctx, idx, event_ts_utc=ts, ts_original=str(ct) if ct else None, ts_field="create_time(epoch_s,UTC)",
                                tz_status="utc_known" if ts else "missing", event_kind="ai_chat_turn", conversation_id=cid,
                                conversation_title=title, sender=(m.get("author") or {}).get("role"), body=text))
                idx += 1
        else:
            for m in c.get("chat_messages") or []:
                text = m.get("text") or "\n".join(x.get("text", "") for x in m.get("content") or [] if isinstance(x, dict))
                raw = m.get("created_at")
                ts = datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else None
                out.append(_row(ctx, idx, event_ts_utc=ts, ts_original=raw, ts_field="created_at(ISO)",
                                tz_status="utc_known" if ts and ts.tzinfo else "missing", event_kind="ai_chat_turn",
                                conversation_id=cid, conversation_title=title, sender=m.get("sender"), body=text))
                idx += 1
    return out


def ex_text_document(con, path, ctx):
    """Markdown/JSON chat file with no reliable per-turn grammar: one searchable document event,
    no timestamp invented (tz_status=missing)."""
    ctx["_extractor"] = "duckdb:text_document"
    (content,) = con.execute("select content from read_text(?)", [str(path)]).fetchone()
    return [_row(ctx, 0, ts_field=None, tz_status="missing", event_kind="document",
                 conversation_id=ctx["vault_key"], conversation_title=Path(ctx["vault_key"]).name, body=content)]


# ---------------- backup parsers (existing Probata modules) ----------------

def ex_sms_xml(con, path, ctx):
    """SMS Backup & Restore sms-*.xml / calls-*.xml. Multi-GB with inline base64 MMS parts, so the
    webbed read_xml DOM template cannot hold it; stream with the existing sms_xml mapping."""
    ctx["_extractor"] = "parser:sms_xml"
    out, idx = [], 0
    for _e, elem in ET.iterparse(str(path), events=("end",)):
        tag = elem.tag.lower()
        if tag in sms_xml._TAGS:
            a = dict(elem.attrib)
            rec = sms_xml._map(tag, a, elem)
            if rec is not None:
                recips = None
                if tag == "mms":
                    recips = [x.attrib.get("address") for x in elem.iter("addr") if x.attrib.get("type") == "151"]
                ms = a.get("date")
                ts = rec.occurred_at
                owner_sent = rec.role == sms_xml.OWNER
                other = rec.conversation_id
                out.append(_row(ctx, idx, event_ts_utc=ts, ts_original=f"date={ms}; readable_date={a.get('readable_date')}",
                                ts_field="date(epoch_ms,UTC)", tz_status="utc_known" if ts else "missing",
                                event_kind="call" if tag == "call" else "message",
                                conversation_id=_phone(a.get("address") or a.get("number")) or other,
                                conversation_title=other, participants=["owner", other],
                                sender="owner" if owner_sent else other, recipients=[other] if owner_sent else ["owner"] if not recips else recips,
                                direction=rec.attrs.get("direction") or rec.attrs.get("call_type"),
                                counterparty_phone=_phone(a.get("address") or a.get("number")),
                                contact_name=a.get("contact_name"), body=rec.content,
                                attachments=json.dumps(rec.attrs.get("attachments")) if rec.attrs.get("attachments") else None))
            idx += 1
        if tag in sms_xml._TAGS or tag in ("smses", "calls"):
            elem.clear()
    return out


def _from_records(ctx, recs, kind="message"):
    """recs: JSON-safe record dicts from the parser's records_out()."""
    out = []
    for i, rec in enumerate(recs):
        raw = rec.get("occurred_at")
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else None
        tzs = "utc_known" if ts and ts.tzinfo else ("local_unknown_tz" if ts else "missing")
        attrs = rec.get("attrs") or {}
        att = {k: v for k, v in attrs.items() if "attach" in k}
        out.append(_row(ctx, i, event_ts_utc=ts if tzs == "utc_known" else None,
                        sort_ts=ts.replace(tzinfo=None) if ts else None, ts_original=attrs.get("raw_timestamp") or raw,
                        ts_field="parser_occurred_at", tz_status=tzs, event_kind=rec.get("record_type") or kind,
                        conversation_id=rec.get("conversation_id"), conversation_title=rec.get("conversation_id"),
                        participants=[str(p) for p in rec.get("participants") or []], sender=rec.get("role"),
                        body=rec.get("content"), attachments=json.dumps(att, default=str) if att else None))
    return out


def ex_imessage_txt(con, path, ctx):
    ctx["_extractor"] = "parser:imessage_txt"
    res = imessage_txt.parse({"path": str(path)})
    return _from_records(ctx, res.get("records") or [])


def ex_fb_messenger_html(con, path, ctx):
    ctx["_extractor"] = "parser:facebook_messenger_html"
    res = facebook_messenger_html.parse({"path": str(path)})
    return _from_records(ctx, res.get("records") or [])


EXTRACTORS = {
    "fb_messenger_json": ex_fb_messenger_json, "instagram_json": ex_fb_messenger_json,
    "whatsapp_txt": ex_whatsapp_txt, "google_chat_json": ex_google_chat_json,
    "ai_conversations_json": ex_ai_conversations_json, "ai_chat_file": ex_text_document,
    "sms_backup_xml": ex_sms_xml, "calls_backup_xml": ex_sms_xml,
    "imessage_txt": ex_imessage_txt, "fb_messenger_html": ex_fb_messenger_html,
}
PRIORITY = ["fb_messenger_json", "ai_conversations_json", "ai_chat_file", "google_chat_json", "whatsapp_txt",
            "instagram_json", "fb_messenger_html", "imessage_txt", "calls_backup_xml", "sms_backup_xml"]


def main():
    terms = json.load(open(os.environ["TERMS"]))
    kat = re.compile(terms["katrina_strong"], re.I)
    only = set(filter(None, os.environ.get("ONLY_FORMATS", "").split(",")))
    con = duckdb.connect(str(DB))
    con.execute("create table if not exists processed(sha1 varchar, extractor varchar, vault_key varchar, source_format varchar, "
                "n_events bigint, status varchar, error varchar, seconds double, done_at timestamptz)")
    con.execute("create table if not exists events_raw as select * from (select 1) where false")
    if con.execute("select count(*) from information_schema.columns where table_name='events_raw'").fetchone()[0] <= 1:
        con.execute("drop table events_raw")
        con.register("empty", pa.Table.from_pylist([], schema=SCHEMA))
        con.execute("create table events_raw as select * from empty")
        con.unregister("empty")
    cands = list(csv.DictReader(open(WORK / "candidates.tsv", encoding="utf-8"), delimiter="\t"))
    cands = [c for c in cands if c["format_guess"] in EXTRACTORS and (not only or c["format_guess"] in only)]
    # Katrina-first, then format priority, then small files first.
    cands.sort(key=lambda c: (0 if kat.search(c["vault_key"]) or "Messages with Katrina" in c["vault_key"] else 1,
                              PRIORITY.index(c["format_guess"]), int(c["size"] or 0)))
    seen = {(r[0], r[1]) for r in con.execute("select sha1, extractor from processed where status='ok'").fetchall()}
    total = len(cands)
    for n, c in enumerate(cands, 1):
        fn = EXTRACTORS[c["format_guess"]]
        ex_tag = f"{fn.__name__}@{VERSION}"
        if (c["sha1"], ex_tag) in seen and not os.environ.get("FORCE"):
            continue
        path = B2 / "salem-data" / c["vault_key"]
        ctx = {"source_format": c["format_guess"], "vault_key": c["vault_key"], "sha1": c["sha1"],
               "catalog_rel": c.get("catalog_rel_example") or None, "member_path": None}
        t0 = time.time()
        try:
            rows = fn(con, path, ctx)
            if rows:
                con.register("batch", pa.Table.from_pylist(rows, schema=SCHEMA))
                con.execute("delete from events_raw where sha1 = ? and source_format = ?", [c["sha1"], c["format_guess"]])
                con.execute("insert into events_raw select * from batch")
                con.unregister("batch")
            status, err, nev = "ok", None, len(rows)
        except Exception as e:  # recorded, never silent
            status, err, nev = "error", f"{type(e).__name__}: {e}"[:2000], 0
            traceback.print_exc()
        dt = time.time() - t0
        con.execute("delete from processed where sha1=? and extractor=?", [c["sha1"], ex_tag])
        con.execute("insert into processed values (?,?,?,?,?,?,?,?,now())",
                    [c["sha1"], ex_tag, c["vault_key"], c["format_guess"], nev, status, err, dt])
        print(f"[{n}/{total}] {status} {c['format_guess']} events={nev} {dt:.1f}s size={c['size']} sha1={c['sha1'][:10]}", flush=True)
        con.execute("checkpoint") if n % 50 == 0 else None
    con.execute("checkpoint")
    print("EXTRACT DONE", flush=True)


if __name__ == "__main__":
    main()
