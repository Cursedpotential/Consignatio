# Byline: Claude Code · Opus 5 · 2026-09-18
"""Classify AI-chat candidates by CONTENT SIGNATURE (owner 2026-09-18 20:13 EDT:
"The folder names don't mean shit man").

Reads a bounded head (default 16 KiB) of every candidate object through the read-only
B2 mount and decides the format from the bytes. File extension chose WHICH objects are
worth a range read (ai_chat_discovery_20260918.sql); it never decides the format.

For ZIPs the central directory is read (end-of-file reads only, no decompression of the
whole archive); member names then select which members get a byte probe, and the member's
own bytes decide its format -- the same two-step as loose files.

Output: TSV -> raw_duck.ai_chat_signatures_20260918 / raw_duck.ai_chat_zip_members_20260918.
Read-only on evidence. Nothing is written to B2 by this script.

Signatures
  chatgpt_conversations_json  ChatGPT export: mapping{} + author.role
  claude_conversations_json   Claude export: chat_messages[] + sender
  gemini_activity_json        Takeout My Activity JSON with a Gemini/Bard header
  gemini_activity_html        Takeout My Activity HTML with a Gemini/Bard header
  chatgpt_chat_html           ChatGPT export chat.html (jsonData = [ ... "mapping")
  ai_generic_json             JSON carrying role/content turn arrays
  ai_markdown_transcript      md/txt with >=2 distinct speaker markers, >=4 marker lines
"""
from __future__ import annotations

import concurrent.futures as cf
import csv
import io
import os
import re
import sys
import time
import zipfile
from pathlib import Path

B2 = Path(os.environ.get("B2_ROOT", "/srv/openlist/b2/salem-data"))
HEAD = int(os.environ.get("HEAD_BYTES", "16384"))
WORKERS = int(os.environ.get("WORKERS", "24"))
MEMBER_HEAD = int(os.environ.get("MEMBER_HEAD_BYTES", "16384"))
ZIP_MEMBER_MAX = int(os.environ.get("ZIP_MEMBER_MAX", "4000"))  # members probed per zip

# --- speaker markers for plain transcripts -------------------------------------------
# Two shapes, both anchored at start of line:
#   inline   "You said:", "**User:**", "> Assistant:", "User: [2025-11-12 19:31:34] ..."
#   heading  "### 🤖 Assistant (9:31:04 AM)", "## User", "You (11/12/2025, 7:31:34 PM)"
# A parenthesised or bracketed timestamp between the speaker and the colon is allowed and
# is what several exporters (Google_Gemini_*, Claude-Conversation-*, chat-memo_*) carry.
_OWNER = r"(?:you said|user|human|me|prompt|matt|question|you)"
_ASSIST = r"(?:chatgpt said|gemini said|claude said|assistant|chatgpt|claude|gemini|bard|copilot|perplexity|deepseek|grok|qwen|gpt-?4o?|model|answer|response|ai)"
_PRE = r"^[ \t]{0,3}(?:#{1,6}[ \t]*)?(?:>[ \t]*)?(?:[-*][ \t]*)?(?:\*\*|__)?[ \t]*(?:[^\x00-\x7F][ \t]*)*"
_TS = r"(?:[ \t]*\([^)\n]{0,48}\))?(?:[ \t]*\[[^\]\n]{0,48}\])?"
_POST_INLINE = r"[ \t]*(?:\*\*|__)?[ \t]*[:：]"
_POST_HEAD = r"[ \t]*(?:\*\*|__)?[ \t]*[:：]?[ \t]*$"

_M = [
    ("owner", re.compile(f"{_PRE}{_OWNER}{_TS}(?:{_POST_INLINE}|{_POST_HEAD})", re.I | re.M)),
    ("assistant", re.compile(f"{_PRE}{_ASSIST}{_TS}(?:{_POST_INLINE}|{_POST_HEAD})", re.I | re.M)),
]

# AI provider hosts that identify a clipping as a real chat (front-matter `source:`/`url:`)
_CLIP_SRC = re.compile(
    rb'(?:^|\n)\s*(?:source|url|link|permalink)\s*:\s*["\'<]?https?://(?:www\.)?'
    rb'((?:gemini|bard)\.google\.com|chatgpt\.com|chat\.openai\.com|claude\.ai|'
    rb'(?:www\.|playground\.)?perplexity\.ai|copilot\.microsoft\.com|grok\.com|x\.com/i/grok|'
    rb'chat\.qwen\.ai|venice\.ai|chat\.deepseek\.com|poe\.com|you\.com)',
    re.I)
_PPLX = re.compile(rb'r2cdn\.perplexity\.ai|LLM served by Perplexity', re.I)

_JSON_ROLE = re.compile(rb'"role"\s*:\s*"(?:user|assistant|system|human|model)"', re.I)
_JSON_CONTENT = re.compile(rb'"(?:content|text|parts)"\s*:', re.I)


def classify(head: bytes, probe_class: str) -> tuple[str | None, str]:
    """Return (signature, why). head is the first HEAD bytes of the object."""
    h = head
    low = h.lower()

    # A JSON signature only counts if the object actually IS JSON: a markdown design doc that
    # quotes "chat_messages" is not a Claude export (hit live 2026-09-18 on FOREMAN_WORK_ORDER.md).
    is_json_doc = h.lstrip(b"\xef\xbb\xbf \t\r\n")[:1] in (b"[", b"{")

    if probe_class in ("json", "text") and is_json_doc:
        if b'"mapping"' in h and (b'"author"' in h or b'"create_time"' in h):
            return "chatgpt_conversations_json", "mapping+author/create_time"
        if b'"chat_messages"' in h and b'"sender"' in h:
            return "claude_conversations_json", "chat_messages+sender"
        if b'"header"' in h and (b'"Gemini Apps"' in h or b'"Bard"' in h or b'"Gemini"' in h) and b'"time"' in h:
            return "gemini_activity_json", "header Gemini/Bard + time"
        if _JSON_ROLE.search(h) and _JSON_CONTENT.search(h):
            return "ai_generic_json", "role+content turn array"

    if probe_class in ("html", "text"):
        if b"jsonData" in h and b'"mapping"' in h:
            return "chatgpt_chat_html", "jsonData + mapping"
        if (b"gemini apps" in low or b">bard<" in low or b"bard</" in low) and b"mdl-" in low:
            return "gemini_activity_html", "takeout activity html + Gemini/Bard"

    if probe_class == "text":
        # "Chat Memo - All Conversations" exporter: per-message timestamps, many conversations
        if (b"Chat Memo" in h and b"Total Conversations:" in h) or \
           (b"Total Conversations:" in h and b"Platform:" in h and b"URL:" in h):
            return "ai_chat_memo_txt", "chat-memo header (Total Conversations/Platform/URL)"

    if probe_class in ("text", "html"):
        try:
            txt = h.decode("utf-8", "replace")
        except Exception:
            txt = ""
        hits = {k: len(rx.findall(txt)) for k, rx in _M}
        if hits["owner"] >= 2 and hits["assistant"] >= 2:
            return "ai_markdown_transcript", f"markers owner={hits['owner']} assistant={hits['assistant']}"

        # Web-clipper / single-answer clippings. The name is often just the first sentence of
        # the prompt (owner 2026-09-18 21:22 EDT), so the DISCRIMINATOR is the front-matter
        # `source:` host or a provider watermark -- never the file name.
        m = _CLIP_SRC.search(h)
        if m:
            return "ai_clipped_markdown", f"front-matter source host {m.group(1).decode('ascii', 'replace')}"
        if _PPLX.search(h):
            return "ai_clipped_markdown", "perplexity watermark"

    return None, "no-signature"


def head_bytes(p: Path, n: int) -> bytes:
    with p.open("rb") as f:
        return f.read(n)


ZIP_INTEREST = re.compile(
    r"(conversations\.json|conversations\.jsonl|chat\.html|chat\.json|message_feedback\.json"
    r"|my ?activity\.(json|html)|users\.json|projects\.json"
    r"|\.(md|markdown|txt)$|\.json$|\.html?$)",
    re.I,
)


def probe_one(rec: dict) -> list[dict]:
    key = rec["vault_key"]
    p = B2 / key
    out = []
    base = {k: rec.get(k) for k in ("vault_key", "size", "sha1", "ext", "probe_class",
                                    "catalog_rel", "catalog_path", "catalog_modtime_hint")}
    try:
        if rec["probe_class"] == "zip":
            with zipfile.ZipFile(p) as z:
                names = z.namelist()
                interesting = [n for n in names if not n.endswith("/") and ZIP_INTEREST.search(n)][:ZIP_MEMBER_MAX]
                n_probed = 0
                for n in interesting:
                    try:
                        info = z.getinfo(n)
                        if info.file_size < 200:
                            continue
                        with z.open(n) as mf:
                            mh = mf.read(MEMBER_HEAD)
                        ml = n.lower()
                        mc = ("json" if ml.endswith((".json", ".jsonl", ".ndjson"))
                              else "html" if ml.endswith((".html", ".htm")) else "text")
                        sig, why = classify(mh, mc)
                        n_probed += 1
                        if sig:
                            out.append({**base, "zip_member_path": n, "member_size": info.file_size,
                                        "signature": sig, "why": why, "status": "ok"})
                    except Exception as e:  # member-level failure does not fail the zip
                        out.append({**base, "zip_member_path": n, "member_size": None,
                                    "signature": None, "why": f"member-error:{type(e).__name__}",
                                    "status": "member_error"})
                if not out:
                    out.append({**base, "zip_member_path": None, "member_size": None,
                                "signature": None,
                                "why": f"zip members={len(names)} interesting={len(interesting)} probed={n_probed} no-signature",
                                "status": "ok"})
        else:
            h = head_bytes(p, HEAD)
            sig, why = classify(h, rec["probe_class"])
            out.append({**base, "zip_member_path": None, "member_size": None,
                        "signature": sig, "why": why, "status": "ok"})
    except Exception as e:
        out.append({**base, "zip_member_path": None, "member_size": None, "signature": None,
                    "why": f"{type(e).__name__}: {str(e)[:120]}", "status": "error"})
    return out


COLS = ["vault_key", "size", "sha1", "ext", "probe_class", "catalog_rel", "catalog_path",
        "catalog_modtime_hint", "zip_member_path", "member_size", "signature", "why", "status"]


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    only = sys.argv[3] if len(sys.argv) > 3 else None       # probe_class filter
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    with open(src, newline="", encoding="utf-8") as f:
        recs = [r for r in csv.DictReader(f, delimiter="\t")]
    if only:
        recs = [r for r in recs if r["probe_class"] == only]
    if limit:
        recs = recs[:limit]
    for r in recs:
        r["size"] = int(r["size"]) if r.get("size") else None

    t0, done, found = time.time(), 0, 0
    with open(dst, "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for rows in ex.map(probe_one, recs):
                for row in rows:
                    w.writerow(row)
                    if row["signature"]:
                        found += 1
                done += 1
                if done % 2000 == 0:
                    el = time.time() - t0
                    print(f"probed {done}/{len(recs)} sig={found} {done/el:.0f}/s eta={(len(recs)-done)/max(done/el,0.01)/60:.1f}m",
                          flush=True)
    print(f"PROBE DONE n={len(recs)} signatures={found} secs={time.time()-t0:.0f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
