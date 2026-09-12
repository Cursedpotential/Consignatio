# PROVEN extraction for the OWNER's CUSTOM imessage-exporter HTML format.
# PROCESS verified on Evidence/Primary Evidence/Messaging/imessage/+18108532989/index.html (325KB):
#   1918 per-message records, speakers preserved (Me=1064 / +18108532989=854), per-message timestamps.
# PIPELINE: port this into evidence/tools/imessage_html.py — the deployed parser rejects this format
# because it expects STOCK imessage-exporter (div.message>div.sent/received); the owner CUSTOMIZED their
# exporter (the "iMessage Exporter Fix" chat). Structure below.
#
# FORMAT:
#   <div class='message-container'> ... per message:
#     <div style='text-align: left|right;'>
#        <div class='bubble from-them|from-me'>TEXT</div>
#        <div class='meta'>SENDER - YYYY-MM-DD HH:MM AM/PM</div>
#     </div>
#   from-me  -> speaker = "Me" (owner)         ; from-them -> speaker = the phone # (in .meta + folder name)
#   attachments: <a class='attachment-link' href=...>
# Byline: Claude Code (PROCESS) - Opus 4.8 - 2026-06-26
import re
from bs4 import BeautifulSoup
from collections import Counter

def parse_owner_imessage_html(path: str, conversation_id: str):
    soup = BeautifulSoup(open(path, encoding="utf-8", errors="replace").read(), "html.parser")
    recs = []
    for seq, b in enumerate(soup.select("div.bubble")):
        cls = b.get("class", [])
        role = "me" if "from-me" in cls else "them"          # me = owner, them = other party
        text = b.get_text(" ", strip=True)
        meta = b.find_next_sibling("div", class_="meta")
        mt = meta.get_text(" ", strip=True) if meta else ""
        m = re.match(r"^(.*?)\s*-\s*(\d{4}-\d{2}-\d{2}.*)$", mt)
        speaker = (m.group(1).strip() if m else ("Me" if role == "me" else "?"))
        occurred_at = (m.group(2).strip() if m else "")      # "YYYY-MM-DD HH:MM AM/PM" -> normalize to TZ-aware
        att = b.find_next_sibling("a", class_="attachment-link")
        recs.append({
            "record_type": "message", "conversation_id": conversation_id, "sequence_number": seq,
            "role": role, "speaker": speaker, "content": text, "occurred_at": occurred_at,
            "attrs": {"attachment": att.get("href") if att else None},
        })
    return recs

if __name__ == "__main__":
    F = "/r2/Evidence/Primary Evidence/Messaging/imessage/+18108532989/index.html"
    r = parse_owner_imessage_html(F, "+18108532989")
    print("messages:", len(r), "| speakers:", dict(Counter(x["speaker"] for x in r)))
