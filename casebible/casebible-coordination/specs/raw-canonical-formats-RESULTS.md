# SORT — RAW canonical messaging formats (answer to PROCESS's confirm, LOG 00:10)
> _Byline: Claude Code · Opus 4.8 · 2026-06-27_ · **LOCAL ONLY — no secrets (R2 keys only).**
> Published per the STANDING RULE (verification → owner-visible path + linked in LOG). Lane: 🟦 SORT (owns casebible-raw + catalog).
> Method: read-only query of the local R2 catalog `D:/casebible/casebible.duckdb` table `r2_files` (md5, path) — **590,560 raw keys**. $0, no cloud op.

## TL;DR
**YES — the canonical structured source formats (SMS-XML and Facebook DYI JSON) DO live in `casebible-raw`.**
The derived CSV / TXT / PDF / XLSX that PROCESS found in the *sorted* messaging subtree are **secondary/derived**, not the only inputs.
Per spec §1 best-format (structured > derived), the structured parsers (`sms_xml.py`, `facebook_messenger_json.py`) have valid REAL inputs — they should run against the **raw canonical** files; treat the sorted CSV/TXT as the lower-priority sibling for cross-check/dedup.

## SMS-XML (SMS Backup & Restore) — PRESENT in raw
- **460 `.xml`** total in raw (**189 distinct by md5** → heavy duplication). 122 match sms/backup name patterns.
- Canonical locations:
  - `Evidence/SMS Backup and Restore/` (27)
  - `_backup_import/xml/` (188 .xml; many SMS)
  - `_backup_import/Documents/Court/Phone Records/Messages with Katrina/SMS backup/` (19) · `Evidence/Phone Records/Messages with Katrina/SMS backup/` (17)
  - `_backup_import/Documents/Court/Phone Records/Phone Data/SMS/` (10) · `Evidence/Phone Records/Phone Data/SMS/` (7) · `_backup_import/Documents/Court/Call data/SMS/` (6)
  - `Evidence/messaging/_TO_SORT/` (9)

## Facebook DYI JSON — PRESENT in raw
- **485 `message_*.json`** (**336 distinct by md5**); 719 facebook/messenger `.json` total. Full DYI tree present:
  `…/your_facebook_activity/messages/inbox/<thread>/message_N.json`.
- Multiple dated DYI export roots (the owner pulled several): `facebook-potentiallycursed85-` dated **2024-08-04, 2024-09-02, 2025-08-18, 2025-12-03**, under:
  - `Evidence/FB Exports/…` (incl. `Katrina FB Data/…`), `Evidence_&_Timelines/…`
  - `court/fb/…` (several subfolders) and mirrored under `_backup_import/Documents/Court/FB DATA/…`

## Why the sorted tree looked XML/JSON-free
The executed root-pile sort (2026-06-25) covered only the raw **root pile**; the messaging EXPORTS live in nested subfolders, not root. The existing pre-restructure sorted `Evidence/` (domain layout) carried the **derived** CSV/TXT/PDF/XLSX into `Evidence/Primary Evidence/Messaging/{sms,facebook}` — the canonical raw XML/JSON were never promoted into sorted. The upcoming messaging re-bucket should bring the **raw canonical** formats into sorted as the best-format primary.

## Implications (for PROCESS + PIPELINE)
1. `sms_xml.py` (and the SBV→MCP SMS-XML primary) and `facebook_messenger_json.py` are NOT dead ends — point them at the **raw** keys above, not the sorted derived tree.
2. **Best-format/dedup (spec §1):** per conversation there can be raw-XML/JSON **and** derived CSV/TXT (e.g. PROCESS's +18103533592 = sorted .txt 7406 msgs vs the CSV 7187 msgs) — group by conversation, pick the structured canonical, log the rejected sibling. md5 shows the SAME export duplicated across `Evidence/FB Exports` ↔ `court/fb` ↔ `_backup_import` → de-dup by md5 (189/460 xml, 336/485 fb-json are unique) before parsing.
3. SORT will make the canonical raw XML/JSON the promoted primary when the messaging re-bucket runs (held pending owner's folder-structure rework).

## Caveat
These are **catalog keys** (the raw dedup snapshot as of the catalog build 2026-06-23). A live `rclone lsf` of `casebible-raw` (read-only, cheap) can re-confirm exact current keys before any parse run if needed — flag me and I'll run it.

---

## Addendum (00:35) — "route by content, not folder" sizing
Triggered by PROCESS's provenance oddity (a 525-msg S&R XML misfiled at `facebook/recup_dir.862/f417196896.xml`). Same catalog, read-only, $0. Sizes how much structured evidence is misfiled, so the owner's folder-structure rework + SORT's messaging re-bucket can plan for **content-based routing**.

| Finding | Count | Note |
|---|---|---|
| Files in PhotoRec **carve dirs** (`recup_dir*`) in raw | **103,302** (~17% of the 590,560 raw keys) | Disk-recovery fragments — a huge LOW-SIGNAL mass; owner decision needed (most → quarantine/archive). |
| ↳ of those, structured messaging (`.xml`/`.json`) | **170** (121 distinct by md5) | Real evidence HIDING in the carve pile — must be content-routed OUT before any carve-bulk quarantine. |
| `.xml` NOT under an sms/ or "SMS backup" or `_backup_import/xml/` path | 173 | Most are non-SMS XML (configs, `f\d+.xml` shader junk, etc.), not misfiled SMS — verify by content. |
| ↳ `.xml` mislanded under a `facebook/` or `court/fb/` path | **2** | The PROCESS-flagged carve case + 1 more → route by S&R content header, not the `facebook/` folder. |
| `.xml` under `snapchat/` or `imessage/` paths | 0 | No SMS-XML cross-filed into those platforms. |
| Snapchat structured `.json` (raw) | **25** | (PROCESS saw 36 on the live mount.) **Parser GAP — no parse.snapchat exists.** |
| `/phone/`-path `.json` / `.xml` (raw catalog) | 0 / 0 | NOT "no phone data" — raw uses different folder names (`Phone Records`, `Call data`, `Phone Data/SMS`); PROCESS found 289 .json + 2 .xml in the *sorted* `phone/` tree. **Caveat: raw↔sorted path naming differs — needs a content check, don't conclude absence.** |

**SORT takeaways for the re-bucket (held until owner's folder-structure rework):**
1. Cross-platform XML misfiling is otherwise **low-volume** (2 cases) — the route-by-content fix is cheap beyond the carve pile.
2. The **103k carve pile** is the big item: classify by CONTENT first (rescue the 121 unique structured-msg files + any other real evidence), THEN the owner can decide bulk-quarantine/archive of the remaining carve fragments. NEVER bulk-quarantine the carve dir blind — evidence is mixed in.
3. Snapchat parser gap + the raw/sorted `phone/` naming mismatch are handed to PIPELINE/PROCESS (already in ORCHESTRATOR's 00:29 gap list).
