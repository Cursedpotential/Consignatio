# RESULTS — Messaging format map (SORTED-tree live recon)
> _Byline: Claude Code (PROCESS lane) · Opus 4.8 · 2026-06-27_ · LOCAL ONLY. Read-only, $0 (no cloud op, no prod write).
> **Scope:** the SORTED vault as mounted read-only at `Y:` — `Evidence/Primary Evidence/Messaging/**`.
> Complements SORT's `raw-canonical-formats-RESULTS.md` (the RAW catalog view). Where they overlap, SORT's
> raw-catalog counts are authoritative for `casebible-raw`; this file is what's actually in the **sorted** tree
> PROCESS would ingest from. Method: `find` + targeted `head`/parser probes on the live mount.

## TL;DR
The sorted messaging tree is **format-MIXED**: raw structured (SMS-XML, FB DYI JSON, Snapchat JSON) **and**
derived views (tabular CSV, transcript-marker TXT/CSV, PDF, XLSX, images). The structured parsers are
**correctly aimed** (their inputs exist); there are **3 real parser GAPS** (Snapchat, XLSX, phone call-logs)
and a unified transcript-marker grammar that one parser can cover. Best-format/dedup (spec §1) is required —
several conversations exist in 2+ formats.

## Full extension counts — `Evidence/Primary Evidence/Messaging/**`
`jpg 833 · json 487 · png 367 · csv 321 · html 302 · jpeg 223 · xml 73 · zip 46 · pdf 44 · md 35 · xlsx 30 · txt 17 · docx 13 · xsl 2 · vcf 2`

## Structured-source locations (in sorted)
| Format | Count (sorted) | Where | Canonical? |
|---|---|---|---|
| **SMS Backup & Restore XML** | 62 of 73 `.xml` in `sms/` | confirmed header `SMS Backup & Restore v10.21.003`, `<smses count="…">` | ✅ canonical SMS source → `sms_xml.py` / SBV-primary aimed correctly |
| **Facebook DYI JSON** | in `facebook/"messages (2)"/inbox/<thread>/*.json` | classic DYI layout | ✅ → `facebook_messenger_json.py` aimed correctly |
| **Snapchat JSON** | 36 in `snapchat/json` + `snapchat/2025-04-11_Export/json` | structured export | ⚠️ **GAP — no `parse.snapchat` built** |
| **phone/** | 289 `.json` + 2 `.xml` | call logs / phone records | ⚠️ format TBD — needs a parser-need check |

## Per-platform format map (what PROCESS would actually parse)
| Platform | Formats present (sorted) | Recommended parse path |
|---|---|---|
| **iMessage** | HTML (2 owner-custom variants), CSV-transcript | content-sniff: static-DOM vs script-embedded (text/regex); `[ts] Speaker:` marker for CSV. See `imessage-derisk-RESULTS.md`. |
| **SMS** | XML (canonical), `.txt` (transcript-marker), `.csv` (tabular `address,readable_date,type,body,read,contact_name`) | XML = best-format primary; `.txt`/`.csv` = derived sibling for cross-check/dedup |
| **Facebook** | DYI JSON (canonical), combined CSV (`Sender,Timestamp,Message,Source File`), XLSX, PDF, HTML | JSON = primary; CSV/XLSX/PDF = derived exhibits (XLSX **gap**, PDF needs OCR) |
| **Snapchat** | structured JSON | **gap** — build `parse.snapchat` |
| **phone** | JSON (289) + XML (2) | TBD |

## Unified transcript-marker grammar (verified)
The SMS `.txt` and the iMessage `.csv` share ONE grammar: lines `[YYYY-MM-DD HH:MM AM/PM] Speaker:`
followed by content, blank-separated. **One marker parser covers both.** Verified on 3 SMS `.txt`:
`+18109199825 = 810 msgs`, `+18103533592 = 7,406`, `+18108455244 = 11` — speakers preserved, 100% timestamps.

## Best-format / dedup (spec §1) — REQUIRED
Conversations exist in multiple formats; ingesting all = double-count. Confirmed example:
**+18103533592** present as `sms/+18103533592.txt` (**7,406 msgs**) AND the mislabeled iMessage CSV
(**7,187 msgs**). → group candidates by conversation identity, rank `structured XML/JSON > transcript-marker
> derived tabular`, ingest the best, log rejected siblings in provenance (don't delete). SORT's raw file shows
the SAME export duplicated by md5 across `Evidence/FB Exports` ↔ `court/fb` ↔ `_backup_import` → dedup-by-md5
first, then best-format.

## Provenance caveats (route by CONTENT, not folder)
- A **525-msg S&R XML is misfiled** at `facebook/recup_dir.862/f417196896.xml` (PhotoRec carve dir).
- The iMessage CSV **filename** (`8102689630`) ≠ its **content** (the +18103533592 conversation).
- SORT (00:35) sized this: **103,302** PhotoRec carve files in raw (~17%); **170 structured messaging
  files (121 unique) hide inside the carve pile** → content-route them OUT before any carve quarantine.

## Parser-gap summary handed to PIPELINE (in ORCHESTRATOR's 00:29 list)
1. **Snapchat** structured JSON — no parser. 2. **XLSX** (FB `all_messages.xlsx`, `Katrina…Combined.xlsx`)
— no parser. 3. **phone/** call-logs — format TBD. 4. PDFs (SMS/FB exhibits) — route via `documents.extract-text`
(native text → Tesseract OCR fallback). Plus the iMessage content-sniff + silent-0 hard-fail (separate file).

## Honest scope note
This is a live-mount `find`/probe recon of the SORTED tree — NOT an exhaustive parse of every file, and NOT
the raw catalog (see SORT's file for raw). Counts are as-mounted 2026-06-27. No prod write, no $, nothing ingested.
