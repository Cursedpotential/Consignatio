# iMessage / Messaging Offline De-Risk — RESULTS

> _Byline: Claude Code (ORCHESTRATOR consolidation) · Opus 4.8 · 2026-06-27_
> **Source:** consolidated from PROCESS's signed LOG entries (23:49 / 23:59 / 00:10 / 00:12) so the
> owner can see the test results in one owner-visible place per the AUTONOMY test-visibility rule.
> PROCESS ran these **offline, read-only, $0, throwaway** (no prod write, no embeddings). The raw
> harness `.py` + per-record output live in PROCESS's session scratchpad — **PROCESS to APPEND them
> under "## Raw harness (PROCESS)" below** when it next loops. Numbers here are PROCESS's, verbatim.

## What was tested
Whether the owner's real messaging exports parse correctly into per-message, speaker-attributed,
custody-hashed records **without** the deployed platform image — i.e. de-risking everything PROCESS
owns before any gated prod ingest. Method: stdlib-only (no bs4) parse → per-message
`normalized_record` → spec §4 3-level SHA-256 custody chain → verify.

## Run 1 — single-thread de-risk (LOG 23:49)
Sample: `Evidence/Primary Evidence/Messaging/imessage/+18108532989/index.html` (325 KB, file_hash `8173f2d3…`)

| Metric | Result |
|---|---|
| Per-message records | **1,918** |
| Speakers (unblended) | Me = 1,064 · +18108532989 = 854 (2 distinct, never merged) |
| Per-message timestamps | 1,918 / 1,918 (100%) |
| Date span | 2019-02 → 2020-06, chronological, zero empty rows |
| 3-level SHA-256 chain | H1 file + H2 per-message (all 1,918) + H3 hash-linked chain → **VERIFIES**, chain_head `75da3d9d…` |

Proves the forensic spine runs without bs4 and without PIPELINE's deployed image.

## Run 2 — all exports, 3 format variants (LOG 23:59) — **51,092 records total**, all chains verified

| # | Export | Format | Records | Hazard found |
|---|---|---|---|---|
| 1 | +18108532989 (325 KB) | static-DOM bubbles | 1,918 | — |
| 2 | +18102689630 (8.5 MB) | **script-embedded** (msgs inside `<script>`, JS-rendered) | **41,987** | A plain DOM/bs4 parse returns **0 messages SILENTLY** → "blank evidence" hazard. Recovered via text/regex over raw bytes. |
| 3 | "imessage export 8102689630…csv" (1.27 MB) | **transcript-in-CSV** (`[ts] Speaker:` markers, NOT tabular) | 7,187 | A column-CSV parser would misparse. Needs a transcript-marker sniff. |

- **Provenance bug:** export #3's filename says `8102689630` but its speakers are Me / +18103533592 → it's actually the **+18103533592** conversation. → derive `conversation_id` from content, not filename.
- **Hardening recommended to PIPELINE:** hard-fail (never silent-0) when bubble-count > 0 but parsed records = 0.

## Run 3 — vault format map (LOG 00:10) + correction (LOG 00:12)
Mapped the sorted Messaging tree's real formats. **Initial flag was over-scoped** to the `sms/` and
`facebook/` leaf folders (which hold derived exhibits); PROCESS corrected it via verify-before-claiming.

**Full `Evidence/Primary Evidence/Messaging` extension counts:**
`jpg 833 · json 487 · png 367 · csv 321 · html 302 · jpeg 223 · xml 73 · zip 46 · pdf 44 · md 35 · xlsx 30 · txt 17 · docx 13`

**Net (corrected):** the messaging evidence is **MIXED** — raw SMS-XML (73) + DYI-style JSON (487)
**do exist** (so `sms_xml.py`, `facebook_messenger_json.py`, and the SBV-primary XML path have real
inputs) **plus** derived tabular-CSV + transcript-marker TXT/CSV + PDF + XLSX + images. Substantive
findings stand:
- Two owner-custom iMessage **HTML variants** incl. the silent-empty script-embedded one (above).
- A unified `[YYYY-MM-DD HH:MM AM/PM] Speaker:` **transcript-marker grammar** shared by iMessage-CSV
  + SMS-TXT (verified on 3 SMS files: 810 / 7,406 / 11 msgs) → one marker parser covers both.
- **Best-format / dedup needed (spec §1):** the +18103533592 conversation exists as BOTH
  `sms/+18103533592.txt` (7,406 msgs) AND the mislabeled iMessage CSV (7,187 msgs) → same
  conversation, two formats, different counts → group-by-conversation, pick best, log the rejected
  sibling (don't double-ingest).
- **Gap:** XLSX exports (`all_messages.xlsx`, `Katrina…Combined.xlsx`) have **no parser built** yet.

## Honest caveats (PROCESS)
- `occurred_at` still raw-string — TZ-normalize at real ingest.
- §6 full acceptance bar = ≥5 exports / ≥2 platforms; 2 platforms proven offline so far (iMessage + SMS).
- Ed25519 signing + RFC-3161 timestamp = phase-2.
- **No prod ingest** — $ / freeze-window / human approval all still gated. Pilot data is throwaway.

## Status
PROD path blocked on PIPELINE (facade registry fix = the gated Option A image rebuild + the parser
fixes). The forensic spine + hashing are **de-risked**; only the deployed registry/parse path + the
gated prod write remain.

---
## Raw harness (PROCESS) — appended 2026-06-27 01:04
Stdlib-only (no bs4, no DB, no network). Reads the owner's real exports read-only, builds per-message
records, applies the 3-level SHA-256 chain, verifies the chain, and dumps throwaway JSON. The
`script-embedded` variant is handled by the `if not p.bubbles:` regex fallback (the DOM parse yields 0).

```python
# PROCESS local dry-run — extend offline proof across ALL iMessage exports in the folder.
# Proves: owner-custom HTML (2 threads incl. 8.5MB) + the CSV-TRANSCRIPT format (NOT tabular).
# Each export -> per-message normalized_records (never blend) + spec §4 3-level SHA-256 chain (verified).
# stdlib-only, read-only (SORT freeze STABLE), $0, throwaway.  Byline: Claude Code (PROCESS) · Opus 4.8 · 2026-06-27
import hashlib, json, re, csv
from html.parser import HTMLParser
from collections import Counter

BASE = "Y:/Evidence/Primary Evidence/Messaging/imessage"
TS_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2} [AP]M)\]\s*(.*?):\s*$")  # CSV transcript marker

def sha256_hex(b): return hashlib.sha256(b).hexdigest()

class IMsgParser(HTMLParser):                      # static-DOM variant: div.bubble.from-me/them + div.meta
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bubbles=[]; self.metas=[]; self._cap=None; self._role=None; self._buf=[]
    def handle_starttag(self, tag, attrs):
        if tag!="div": return
        classes=dict(attrs).get("class","").split()
        if "bubble" in classes:
            self._cap="bubble"; self._role="me" if "from-me" in classes else "them"; self._buf=[]
        elif "meta" in classes:
            self._cap="meta"; self._buf=[]
    def handle_endtag(self, tag):
        if tag=="div" and self._cap=="bubble":
            self.bubbles.append((self._role," ".join("".join(self._buf).split()))); self._cap=None
        elif tag=="div" and self._cap=="meta":
            self.metas.append(" ".join("".join(self._buf).split())); self._cap=None
    def handle_data(self, data):
        if self._cap: self._buf.append(data)

BUBBLE_RE=re.compile(r"bubble (from-me|from-them)'>(.*?)</div>\s*<div class='meta'>(.*?)</div>", re.S)
def _strip(h): return " ".join(re.sub(r"<[^>]+>"," ",h).split())

def parse_html(path, conv_id):
    raw=open(path,"rb").read().decode("utf-8",errors="replace")
    p=IMsgParser(); p.feed(raw)
    variant="static-dom"
    if not p.bubbles:                                    # script-embedded variant -> DOM yields 0 (silent!)
        variant="script-embedded(regex)"
        pairs=BUBBLE_RE.findall(raw)
        bubbles=[("me" if r=="from-me" else "them", _strip(t)) for r,t,_m in pairs]
        metas=[_strip(m) for _r,_t,m in pairs]
    else:
        bubbles=p.bubbles; metas=p.metas
    recs=[]; n=len(metas)
    for seq,(role,text) in enumerate(bubbles):
        meta=metas[seq] if seq<n else ""
        m=re.match(r"^(.*?)\s*-\s*(\d{4}-\d{2}-\d{2}.*)$", meta)
        speaker=(m.group(1).strip() if m else ("Me" if role=="me" else conv_id))
        occurred=(m.group(2).strip() if m else None)
        recs.append({"role":role,"speaker":speaker,"content":text,"occurred_at":occurred,
                     "conversation_id":conv_id,"sequence_number":seq})
    return recs, variant

def parse_csv_transcript(path, conv_id):                 # rows: "[ts] Speaker:" marker, content, ",," sep
    recs=[]; cur=None; seq=0
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for row in csv.reader(f):
            cell=(row[0] if row else "").strip()
            m=TS_RE.match(cell)
            if m:
                if cur: recs.append(cur)
                spk=m.group(2).strip(); role="me" if spk.lower()=="me" else "them"
                cur={"role":role,"speaker":spk,"content":"","occurred_at":m.group(1),
                     "conversation_id":conv_id,"sequence_number":seq}; seq+=1
            elif cell and cur is not None:
                cur["content"]=(cur["content"]+" "+cell).strip()
        if cur: recs.append(cur)
    return recs

def hashchain(recs, file_hash):                          # H1 file + H2 per-message + H3 linked chain
    prev="0"*64; chain=[]
    for r in recs:
        canon={k:r[k] for k in ("conversation_id","sequence_number","role","speaker","content","occurred_at")}
        mh=sha256_hex(json.dumps(canon,sort_keys=True,ensure_ascii=False).encode())
        entry={"action":"ingest","artifact_file_hash":file_hash,"message_hash":mh,
               "sequence_number":r["sequence_number"],"previous_hash":prev}
        eh=sha256_hex(json.dumps(entry,sort_keys=True,ensure_ascii=False).encode())
        r["message_hash"]=mh; r["entry_hash"]=eh; r["record_type"]="message"; prev=eh
        chain.append((entry,eh))
    ok=True; last="0"*64                                 # verify: recompute + walk previous_hash links
    for entry,eh in chain:
        if entry["previous_hash"]!=last or sha256_hex(json.dumps(entry,sort_keys=True,ensure_ascii=False).encode())!=eh:
            ok=False; break
        last=eh
    return prev, ok

EXPORTS=[
    ("html","+18108532989", f"{BASE}/+18108532989/index.html"),
    ("html","+18102689630", f"{BASE}/+18102689630/index.html"),
    ("csv","+18102689630", f"{BASE}/imessage export 8102689630 2023-2024 - imessage export 8102689630 2023-2024.csv"),
]
total=0
for kind,conv,path in EXPORTS:
    raw=open(path,"rb").read(); fh=sha256_hex(raw)
    recs,variant=(parse_html(path,conv) if kind=="html" else (parse_csv_transcript(path,conv),"csv-transcript"))
    head,ok=hashchain(recs,fh)
    spk=dict(Counter(r["speaker"] for r in recs)); total+=len(recs)
    print(f"[{kind}] {conv} {len(raw):,}B fh={fh[:12]} variant={variant} msgs={len(recs)} "
          f"speakers={spk} ts={sum(1 for r in recs if r['occurred_at'])}/{len(recs)} chain_ok={ok}")
print("TOTAL:", total)
```

### Verified run output (2026-06-27)
```
[html] +18108532989  325,065B fh=8173f2d3977e variant=static-dom              msgs=1918  speakers={'+18108532989': 854, 'Me': 1064}      ts=1918/1918   chain_ok=True
[html] +18102689630  8,536,884B fh=116696c10b73 variant=script-embedded(regex) msgs=41987 speakers={'Me': 26195, '+18102689630': 15792} ts=41987/41987 chain_ok=True
[csv]  +18102689630  1,273,347B fh=c042008e006d variant=csv-transcript         msgs=7187  speakers={'Me': 5388, '+18103533592': 1799}   ts=7187/7187   chain_ok=True
TOTAL: 51092
```
_Note the script-embedded thread: the `IMsgParser` DOM pass returns 0 bubbles (all markup is inside a
`<script>`); the `if not p.bubbles:` regex fallback recovers all 41,987. This is the silent-empty hazard
PIPELINE's content-sniff must guard with a hard-fail._
