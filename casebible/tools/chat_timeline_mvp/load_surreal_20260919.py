#!/usr/bin/env python3
# Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
"""Load the chat-event graph from the Weaviate spool into Intake SurrealDB (generation _20260919).

Order: Katrina first, then daughter-tagged, then everything else (owner 2026-09-18 20:14 EDT).
Idempotent: every id is derived from the event's dedup_key, so re-runs upsert instead of duplicating.

Write discipline, after the 2026-09-18 hangs (RocksDB write-buffer-manager stall, see
docs/URGENT-TODO.md "Surreal hang fix + timeline graph load"):
  * one BEGIN..COMMIT request per batch instead of seven requests, so the round trips stop dominating
  * pacing driven by the server's real RSS (/metrics), not a fixed sleep
  * ALTER TABLE .. COMPACT checkpoint every COMPACT_EVERY events (flush + history trim)
  * the engine LOG is checked for "Stalling writes"/"Stopping writes" at each checkpoint
  * a health probe between batches, and a hard stop on the first request timeout - never retry a
    wedged database

No names in this file. Identity mapping comes from an untracked terms file on the host
(TERMS, default /data/probata/config/timeline-mvp/terms.json).

Env: SURREAL_URL/USER/PASS, SPOOL, SOURCES (tsv from resolve_sources_20260919.sh), STATE,
     PHASES, BATCH, MAX_BYTES, RSS_PAUSE, RSS_STOP, COMPACT_EVERY, LIMIT.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any

T = "_20260919"
BASE = os.environ.get("SURREAL_URL", "http://100.91.190.107:8473").rstrip("/")
USER = os.environ["SURREAL_USER"]
PASS = os.environ["SURREAL_PASS"]
SPOOL = os.environ.get("SPOOL", "/data/probata/volumes/timeline-mvp/chat_events_20260919.jsonl")
SOURCES = os.environ.get("SOURCES", "/data/probata/volumes/timeline-mvp/sources_20260919.tsv")
STATE = os.environ.get("STATE", "/data/probata/volumes/timeline-mvp/load_state_20260919.json")
TERMS = os.environ.get("TERMS", "/data/probata/config/timeline-mvp/terms.json")
ROCKS_LOG = os.environ.get("ROCKS_LOG", "/data/consignatio/volumes/surreal-intake/intake.db/LOG")
BATCH = int(os.environ.get("BATCH", "250"))
MAX_BYTES = int(os.environ.get("MAX_BYTES", "250000"))
MAX_BODY = int(os.environ.get("MAX_BODY", "400000"))  # whole request; the server closes the
# connection (broken pipe) on an oversized /sql body, which is not a wedge - it is retried smaller
RSS_PAUSE = int(os.environ.get("RSS_PAUSE", str(700 * 1024 * 1024)))
RSS_STOP = int(os.environ.get("RSS_STOP", str(1200 * 1024 * 1024)))
COMPACT_EVERY = int(os.environ.get("COMPACT_EVERY", "25000"))
REQ_TIMEOUT = float(os.environ.get("REQ_TIMEOUT", "120"))
PHASES = os.environ.get("PHASES", "katrina,daughter,rest").split(",")
LIMIT = int(os.environ.get("LIMIT", "0"))

AUTH = "Basic " + base64.b64encode(f"{USER}:{PASS}".encode()).decode()
HDRS = {"surreal-ns": "consignatio", "surreal-db": "intake", "Accept": "application/json",
        "Authorization": AUTH, "Content-Type": "text/plain"}

TXN_HEAD = "BEGIN TRANSACTION;\n"
TXN_TAIL = "\nCOMMIT TRANSACTION;"

_DT = re.compile(r'"__DT__([^"]*)__"')
_RID = re.compile(r'"__RID__([a-z_0-9]+):([^"]*)__"')


class Wedged(Exception):
    """The server stopped answering. Stop the load; do not retry."""


class TooBig(Exception):
    """The server refused/closed on this request body. Retry it in smaller pieces."""


def md5(*parts: str) -> str:
    return hashlib.md5("|".join(p or "" for p in parts).encode()).hexdigest()


def rid(table: str, key: str) -> str:
    return f"__RID__{table}{T}:{key}__"


def lit(obj: Any) -> str:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    s = _DT.sub(lambda m: f'd"{m.group(1)}"', s)
    return _RID.sub(lambda m: f"{m.group(1)}:⟨{m.group(2)}⟩", s)


def sql(body: str, timeout: float | None = None) -> list:
    req = urllib.request.Request(BASE + "/sql", data=body.encode("utf-8"), headers=HDRS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout or REQ_TIMEOUT) as r:
            out = json.loads(r.read().decode())
    except (BrokenPipeError, ConnectionResetError) as e:
        raise TooBig(str(e)) from e
    except (TimeoutError, urllib.error.URLError) as e:
        if isinstance(e, urllib.error.HTTPError):
            if e.code in (413, 431):
                raise TooBig(f"HTTP {e.code}") from e
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:400].decode(errors='replace')}") from e
        if isinstance(getattr(e, "reason", None), (BrokenPipeError, ConnectionResetError)):
            raise TooBig(str(e.reason)) from e
        raise Wedged(f"request timed out / unreachable: {e}") from e
    bad = [x for x in out if x.get("status") != "OK"]
    if bad:
        raise RuntimeError(str(bad[0])[:600])
    return out


def healthy() -> bool:
    try:
        with urllib.request.urlopen(BASE + "/health", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def rss() -> int:
    try:
        with urllib.request.urlopen(BASE + "/metrics", timeout=5) as r:
            for line in r.read().decode().splitlines():
                if line.startswith("surrealdb_process_memory_bytes"):
                    return int(float(line.rsplit(" ", 1)[1]))
    except Exception:
        pass
    return 0


def log_stalls() -> list[str]:
    try:
        with open(ROCKS_LOG, encoding="utf-8", errors="replace") as fh:
            return [ln.strip() for ln in fh if "Stalling writes" in ln or "Stopping writes" in ln]
    except OSError:
        return []


# ---------------------------------------------------------------- identities
def digits(s: str) -> str:
    d = re.sub(r"\D", "", s or "")
    return d[-10:] if len(d) >= 10 else d


class Identities:
    """Maps a handle as written in the data to a person. Patterns come from the untracked terms file."""

    def __init__(self, terms: dict):
        def rx(key):
            v = terms.get(key)
            return re.compile(v, re.I) if isinstance(v, str) and v else None

        self.katrina = rx("katrina_strict") or rx("katrina_strong")
        self.daughter = rx("daughter_strong")
        self.catrina = rx("catrina_c")
        self.katrina_labels = {x.strip().lower() for x in terms.get("katrina_participant_names") or []}
        self.katrina_phones = {digits(x) for x in terms.get("katrina_phones_possible") or [] if digits(x)}
        self.katrina_emails = {x.strip().lower() for x in terms.get("katrina_emails_possible") or []}
        self.owner_labels = {"owner", "me", "matt salem", "matthew salem"}

    def person_for(self, label: str) -> tuple[str, str, str, str | None]:
        """-> (person_key, person_name, kind, alias_conf)"""
        low = (label or "").strip().lower()
        dig = digits(label)
        if low in self.owner_labels:
            return "owner", "Matt Salem", "identity", None
        if low in self.katrina_labels or (self.katrina and self.katrina.search(label or "")):
            return "katrina", label.strip(), "identity", "merged"
        if dig and dig in self.katrina_phones:
            return "katrina", label.strip(), "identity", "possible"
        if low in self.katrina_emails:
            return "katrina", label.strip(), "identity", "possible"
        if self.daughter and self.daughter.search(label or ""):
            return "daughter", label.strip(), "identity", "merged"
        if self.catrina and self.catrina.search(label or ""):
            return "catrina_landlord", label.strip(), "identity", "possible"
        return md5(low), label.strip(), "participant", None


PERSON_NAMES = {"katrina": None, "daughter": None, "catrina_landlord": None, "owner": "Matt Salem"}
ABOUT_KATRINA = {"name_mention", "nickname", "possible_surname_or_short_name"}


# ---------------------------------------------------------------- batching
def build_batch(rows: list[dict], ids: Identities, sources: dict) -> tuple[list[str], int]:
    persons: dict[str, dict] = {}
    aliases: dict[str, dict] = {}
    convs: dict[str, dict] = {}
    srcs: dict[str, dict] = {}
    events: list[dict] = []
    e_sent, e_in, e_to, e_from, e_alias, e_about = [], [], [], [], [], []

    def person(label: str) -> str:
        pkey, pname, kind, aconf = ids.person_for(label)
        known = PERSON_NAMES.get(pkey, "__none__")
        persons.setdefault(pkey, {"id": rid("tl_person", pkey), "kind": kind,
                                  "name": known if known != "__none__" and known else pname})
        akey = md5((label or "").strip().lower())
        aliases.setdefault(akey, {"id": rid("tl_alias", akey), "label": (label or "").strip(),
                                  "person": rid("tl_person", pkey),
                                  "kind": "phone" if digits(label) else "name",
                                  **({"conf": aconf} if aconf else {})})
        e_alias.append({"id": rid("tl_has_alias", md5(pkey, akey)),
                        "in": rid("tl_person", pkey), "out": rid("tl_alias", akey)})
        return pkey

    for p in rows:
        key = p["dedup_key"]
        fmt = p.get("source_format")
        title = p.get("conversation_title") or ""
        ck = md5(fmt or "", title)
        convs[ck] = {"id": rid("tl_conversation", ck), "title": title, "fmt": fmt,
                     "participants": p.get("participants") or []}
        sender = (p.get("sender") or "").strip()
        spk = person(sender) if sender else None
        vk = p.get("vault_key")
        if vk:
            sk = md5(vk)
            sha1, cmd5, crel = sources.get(vk, (None, None, None))
            srcs[sk] = {k: v for k, v in
                        {"id": rid("tl_source", sk), "vault_key": vk, "sha1": sha1,
                         "md5": cmd5, "catalog_rel": crel}.items() if v is not None}
            e_from.append({"id": rid("tl_from_file", md5(key, sk)),
                           "in": rid("tl_event", key), "out": rid("tl_source", sk)})
        ev = {"id": rid("tl_event", key), "ts": f"__DT__{p['sort_ts']}__" if p.get("sort_ts") else None,
              "fmt": fmt, "body": p.get("body"), "sender_name": sender or None,
              "sender": rid("tl_alias", md5(sender.lower())) if sender else None,
              "sender_person": rid("tl_person", spk) if spk else None,
              "conv": rid("tl_conversation", ck), "katrina": p.get("katrina_ref_type"),
              "katrina_conf": p.get("katrina_conf"), "daughter_conf": p.get("daughter_conf"),
              "catrina_class": p.get("catrina_class"), "n_src": p.get("n_sources")}
        events.append({k: v for k, v in ev.items() if v is not None})
        e_in.append({"id": rid("tl_in", key), "in": rid("tl_event", key), "out": rid("tl_conversation", ck)})
        if spk:
            e_sent.append({"id": rid("tl_sent", key), "in": rid("tl_person", spk), "out": rid("tl_event", key)})
        for part in p.get("participants") or []:
            if not part or part.strip() == sender:
                continue
            pk = person(part)
            e_to.append({"id": rid("tl_to", md5(key, pk)), "in": rid("tl_event", key),
                         "out": rid("tl_person", pk)})
        if p.get("daughter_conf"):
            persons.setdefault("daughter", {"id": rid("tl_person", "daughter"), "kind": "identity"})
            e_about.append({"id": rid("tl_about", md5(key, "daughter")), "in": rid("tl_event", key),
                            "out": rid("tl_person", "daughter"), "conf": p["daughter_conf"], "role": "daughter"})
        if p.get("katrina_ref_type") in ABOUT_KATRINA:
            persons.setdefault("katrina", {"id": rid("tl_person", "katrina"), "kind": "identity"})
            e_about.append({"id": rid("tl_about", md5(key, "katrina")), "in": rid("tl_event", key),
                            "out": rid("tl_person", "katrina"), "conf": p.get("katrina_conf") or "weak",
                            "role": "mention"})
        if p.get("catrina_class"):
            persons.setdefault("catrina_landlord", {"id": rid("tl_person", "catrina_landlord"), "kind": "identity"})
            e_about.append({"id": rid("tl_about", md5(key, "catrina_landlord")), "in": rid("tl_event", key),
                            "out": rid("tl_person", "catrina_landlord"),
                            "conf": "strong" if p["catrina_class"] == "catrina_landlord" else "possible",
                            "role": "landlord"})

    stmts = []
    stmts += inserts(f"tl_person{T}", list(persons.values()), "name = $input.name, kind = $input.kind")
    stmts += inserts(f"tl_alias{T}", list(aliases.values()), "label = $input.label, person = $input.person")
    stmts += inserts(f"tl_conversation{T}", list(convs.values()),
                     "title = $input.title, fmt = $input.fmt, participants = $input.participants")
    stmts += inserts(f"tl_source{T}", list(srcs.values()),
                     "vault_key = $input.vault_key, sha1 = $input.sha1, md5 = $input.md5, catalog_rel = $input.catalog_rel")
    stmts += inserts(f"tl_event{T}", events,
                     "ts = $input.ts, fmt = $input.fmt, body = $input.body, sender_name = $input.sender_name, "
                     "sender = $input.sender, sender_person = $input.sender_person, conv = $input.conv, "
                     "katrina = $input.katrina, katrina_conf = $input.katrina_conf, "
                     "daughter_conf = $input.daughter_conf, catrina_class = $input.catrina_class, "
                     "n_src = $input.n_src")
    for table, items in ((f"tl_sent{T}", e_sent), (f"tl_in{T}", e_in), (f"tl_to{T}", e_to),
                         (f"tl_from_file{T}", e_from), (f"tl_has_alias{T}", dedup(e_alias)),
                         (f"tl_about{T}", e_about)):
        stmts += relations(table, items)
    return stmts, len(events)


def dedup(items: list[dict]) -> list[dict]:
    out = {}
    for it in items:
        out[it["id"]] = it
    return list(out.values())


def chunks(items: list[dict]) -> list[list[dict]]:
    out, cur, size = [], [], 0
    for it in items:
        s = lit(it)
        if cur and size + len(s.encode()) > MAX_BYTES:
            out.append(cur)
            cur, size = [], 0
        cur.append(it)
        size += len(s.encode()) + 1
    if cur:
        out.append(cur)
    return out


def inserts(table: str, items: list[dict], upd: str) -> list[str]:
    return [f"INSERT INTO {table} {lit(c)} ON DUPLICATE KEY UPDATE {upd};" for c in chunks(items)]


def relations(table: str, items: list[dict]) -> list[str]:
    return [f"INSERT RELATION IGNORE INTO {table} {lit(c)};" for c in chunks(dedup(items))]


def send_stmts(stmts: list[str]) -> None:
    """Send the batch as transactions that each stay under the server's request-body limit."""
    group: list[str] = []
    size = 0
    for st in stmts:
        if group and size + len(st.encode()) > MAX_BODY:
            send_group(group)
            group, size = [], 0
        group.append(st)
        size += len(st.encode())
    if group:
        send_group(group)


def send_group(group: list[str]) -> None:
    try:
        sql(TXN_HEAD + "\n".join(group) + TXN_TAIL)
    except TooBig as e:
        if len(group) == 1:
            raise RuntimeError(f"single statement rejected ({e}); statement is {len(group[0])} bytes") from e
        if not healthy():
            raise Wedged("server unhealthy after an oversized request") from e
        print(f"splitting group of {len(group)} statements after: {e}", flush=True)
        half = len(group) // 2
        send_group(group[:half])
        send_group(group[half:])


# ---------------------------------------------------------------- main
def phase_of(p: dict) -> str:
    if p.get("katrina_conf") == "strong" and p.get("katrina_ref_type") != "group_participant":
        return "katrina"
    if p.get("daughter_conf"):
        return "daughter"
    return "rest"


def load_state() -> dict:
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"done": {}, "events": 0}


def save_state(st: dict) -> None:
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh)
    os.replace(tmp, STATE)


def main() -> int:
    ids = Identities(json.load(open(TERMS, encoding="utf-8")))
    sources: dict[str, tuple[str | None, str | None, str | None]] = {}
    if os.path.exists(SOURCES):
        with open(SOURCES, encoding="utf-8") as fh:
            for line in fh:
                f = (line.rstrip("\n").split("\t") + ["", "", ""])[:4]
                if f[0]:
                    sources[f[0]] = (f[1] or None, f[2] or None, f[3] or None)
    print(f"terms loaded, {len(sources)} source files resolved from the catalog", flush=True)

    buckets: dict[str, list[dict]] = {"katrina": [], "daughter": [], "rest": []}
    seen: set[str] = set()
    with open(SPOOL, encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)["p"]
            k = p.get("dedup_key")
            if not k or k in seen:
                continue
            seen.add(k)
            buckets[phase_of(p)].append(p)
    for b in buckets.values():
        b.sort(key=lambda x: x.get("sort_ts") or "")
    print("spool: " + ", ".join(f"{k}={len(v)}" for k, v in buckets.items()), flush=True)

    st = load_state()
    t0, done_total = time.time(), st.get("events", 0)
    since_compact = 0
    for phase in PHASES:
        rows = buckets.get(phase) or []
        start = st["done"].get(phase, 0)
        if start >= len(rows):
            print(f"phase {phase}: already complete ({start})", flush=True)
            continue
        print(f"phase {phase}: {len(rows) - start} to load (from {start})", flush=True)
        i = start
        while i < len(rows):
            if not healthy():
                raise Wedged("health probe failed before batch")
            used = rss()
            if used > RSS_STOP:
                raise Wedged(f"server RSS {used / 1e6:.0f} MB over stop threshold")
            waited = 0
            while used > RSS_PAUSE and waited < 60:
                time.sleep(2)
                waited += 2
                used = rss()
            batch = rows[i:i + BATCH]
            stmts, n = build_batch(batch, ids, sources)
            send_stmts(stmts)
            i += len(batch)
            done_total += n
            since_compact += n
            st["done"][phase] = i
            st["events"] = done_total
            save_state(st)
            if done_total % (BATCH * 20) < BATCH:
                print(f"{phase}: {i}/{len(rows)} total={done_total} "
                      f"({done_total / max(time.time() - t0, 1):.0f}/s) rss={used / 1e6:.0f}MB", flush=True)
            if since_compact >= COMPACT_EVERY:
                since_compact = 0
                before = rss()
                sql(f"ALTER TABLE tl_event{T} COMPACT;", timeout=600)
                stalls = log_stalls()
                print(f"CHECKPOINT total={done_total} rss {before / 1e6:.0f}->{rss() / 1e6:.0f}MB "
                      f"stall_lines={len(stalls)}{' ' + stalls[-1] if stalls else ''}", flush=True)
            if LIMIT and done_total >= LIMIT:
                print(f"LIMIT {LIMIT} reached", flush=True)
                return 0
        print(f"phase {phase} COMPLETE at {i}", flush=True)
    print(f"LOAD DONE events={done_total} secs={time.time() - t0:.0f} stalls={len(log_stalls())}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Wedged as e:
        print(f"SURREAL UNRESPONSIVE: {e}; stopping without retry (state saved)", flush=True)
        sys.exit(3)
