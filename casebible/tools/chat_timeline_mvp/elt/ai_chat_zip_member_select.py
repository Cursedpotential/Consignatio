# Byline: Claude Code · Opus 5 · 2026-09-18
"""Choose which ZIP members are worth a byte probe, and SAY WHAT IT COSTS first.

Input:  the central-directory listing from ai_chat_zip_probe.py (stage=dir).
Output: a member worklist + a cost line (members, compressed bytes stored, head bytes to read).

Member NAME narrows what to open -- exactly the role a file extension plays for a loose file.
The format decision is still made from the member's BYTES by ai_chat_signature_probe.classify().
Known-not-chat trees are excluded by path (owner-confirmed list, 2026-09-18 21:15 EDT):
prompt/skill libraries, parser fixtures, browser tab sessions, Google Voice group HTML and
Facebook settings pages -- the last two are MESSAGE TRANSCRIPTS and belong to the other agent.
"""
from __future__ import annotations

import csv
import os
import re
import sys

HEAD = int(os.environ.get("MEMBER_HEAD_BYTES", "16384"))

INTEREST = re.compile(
    r"(conversations\.json|conversations\.jsonl|chat\.html|chat\.json|message_feedback\.json"
    r"|my ?activity\.(?:json|html)|gemini ?apps|chat-?export|chat-?memo"
    r"|\.(?:md|markdown|txt|json|html?)$)", re.I)

EXCLUDE = re.compile(
    r"(Claude-Slash-Commands-main/|System-Prompt-Library-main/|claude-context-master/"
    r"|Cool-Claude-Code-Stuff-main|Single-Shot-Brevity-Training-main/|claude-JSONL-browser-main"
    r"|Gemini_parser/data/raw_api_responses|\.smart-env/|node_modules/|\.git/"
    r"|site-packages/|/dist/|/build/|package(?:-lock)?\.json$|tsconfig[^/]*\.json$"
    r"|composer\.json$|\d+ Sessions - \d|Group Conversation - "
    r"|chat_invites_received|secret_conversations|your_chat_settings"
    # Google Photos / Takeout media sidecars -- one per image, never a chat
    # Takeout truncates the sidecar name, so match the stem, not the whole word
    r"|supplemental-met|[-.]info\.json$|/screenshot_|/received_\d"
    # Facebook/Instagram Messenger thread files are MESSAGE TRANSCRIPTS (other agent's lane)
    r"|/message_\d+\.(?:json|html)$"
    r"|\.(?:heic|heif|jpe?g|png|gif|webp|bmp|tiff?|mp4|mov|m4v|avi|mp3|m4a|wav|aae|pdf)"
    r"(?:\(\d+\))?\.json$)", re.I)

MIN_SIZE, MAX_SIZE = 200, 200 * 1024 * 1024


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    n_all = n_sel = 0
    csize = usize = 0
    with open(src, newline="", encoding="utf-8") as f, open(dst, "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=["vault_key", "sha1", "zip_member_path", "member_size"],
                           delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in csv.DictReader(f, delimiter="\t"):
            n_all += 1
            name = r.get("zip_member_path") or ""
            if not name or r.get("status") != "ok":
                continue
            try:
                ms, cs = int(r["member_size"] or 0), int(r["member_csize"] or 0)
            except ValueError:
                continue
            if not (MIN_SIZE <= ms <= MAX_SIZE):
                continue
            if EXCLUDE.search(name) or not INTEREST.search(name):
                continue
            n_sel += 1
            csize += cs
            usize += min(ms, HEAD)
            w.writerow(r)
    print(f"ZIP MEMBER SELECT: listed={n_all} selected={n_sel} "
          f"stored_bytes_of_selected={csize} ({csize/1e9:.2f} GB) "
          f"head_bytes_to_decompress={usize} ({usize/1e6:.0f} MB at {HEAD} B/member)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
