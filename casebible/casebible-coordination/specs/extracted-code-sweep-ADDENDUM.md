# Extracted-code sweep addendum — sbv zip · ontologies · extractors · parsers · imessage-exporter

> _Byline: Claude Code · Fable 5 · 2026-07-03 · companion to specs/drizzle-schemas-vs-live-DIFF.md_

## 1. sbv/Salem_SMS_Tables_Complete_Deployment_2025-12-27.sql
Was a ZIP misnamed `.sql` (why DBeaver showed "corruption"). Extracted to `extracted-code/sbv/salem-sms-deployment-2025-12-27/`:
SMS_TABLES_FINAL.sql (the definitive "900+ line" consolidated schema — confirmed ancestor of the drizzle file AND of migration 0005) + DEPLOYMENT_CHECKLIST + ITERATIONS_ANALYSIS + SESSION_SUMMARY.
**New adoption candidate #9:** `messaging_behavior_patterns` (multi-message pattern SPANS: pattern_type escalation/cycle/triggered_response/time_based, start/end timestamps, severity_progression, message_ids[]). Live `analysis.finding` has subject_refs[]+MCL+court gates but LACKS the typed span/progression fields → add span columns to `finding` in 0008.

## 2. ontologies-datasets/ (7 files)
- 3 .ttl + zep v3 + temp-patterns: ALREADY consumed into migration 0006 seed. No loss.
- **unsloth_dataset.jsonl (191 labeled examples)**: register as detection EVAL SET + small-local-model fine-tune corpus (2GB-GPU lane). Durable asset.
- **dataset_loader.py**: keep two designs for Semantica wiring — Pass 1 (initial) / **Pass 2 (retrospective re-scan when patterns change)** split + modular custom-dataset dir; confirms HurtLex integration intent (matches 0008 lexicon-sync candidate). MySQL dep dead.
- test_gliner.py: stub, noise.

## 3. extractors/ (2 files)
- **unstructured_parser.py — ADOPT** as `parse.document` capability (PDF/DOCX/HTML: auto/fast/hi_res, table extraction→structured, title-chunking). Port into evidence/tools under registry mesh; deps baked into platform-tools image (cloud-primary).
- pdf_extractor.py: trivial pdfplumber wrapper, superseded.

## 4. imessage-exporter/ (upstream repo analysis)
**Owner's simplified HTML export kept ~4 of 25+ forensic fields.** chat.db (which owner HAS, laptop pending charger) additionally contains: date_read/date_delivered/is_read (notice evidence), edited/unsent history WITH prior wording, tapbacks (added/removed + target), reply-thread linkage, service type (iMessage vs SMS), per-message guid + handle person_centric_id (native dedup/identity keys), group/system events, sub-minute timestamps, attachments w/ transcription + missing-file accounting, spam/corrupt/downgraded flags.
**Plan when laptop lives:** copy chat.db + chat.db-wal + chat.db-shm + Attachments/ untouched → custody-hash → re-export via imessage-database library (typed fields → raw_data/platform_attrs) or minimally `-f html -c clone`.
**KNOWN DAMAGE (owner 2026-07-03): the attachment table/joins were lost during a prior extraction attempt.** Recovery paths, in order: (1) graft attachment+message_attachment_join from ANY older copy (Time Machine / MobileSync iPhone backup file 3d0d7e5fb2ce288813306e4d4636395e047a3d28 / D:\Backup); (2) rebuild links from message attributedBody blobs — they EMBED attachment transfer GUIDs which also appear in Attachments/ paths (no join table needed); (3) SQLite freelist/WAL undelete if DB unvacuumed; (4) timestamp fuzzy re-attach (last resort). RULE: no more writes to that DB; work on hashed copies only.

## 5. parsers/ (agent inventory — full detail in agent report, key verdicts)
NOTE: vendored repos are extensionless ZIPs; `chat-exports/parser.py` is MISFILED (it's a Google Timeline geo parser).

| Priority | Item | Fills | Verdict |
|---|---|---|---|
| 1 | `messaging/sms_backup_parser.py` | SMS/MMS/**call-log** gap; blocking-evidence derivations (type 5/6, outgoing dur=0) | Ingest-grade, streaming; reference impl beside SBV; feeds is_blocked/status_code/call_log |
| 2 | `chat-miner/chatparsers.py` | **Facebook JSON** + Instagram/Telegram/Signal/WhatsApp | Cleanest maintained ingest lib; wrap parsers → NormalizedRecord |
| 3 | `chat-exports/parser.py` (relocate) | Geo tables: 2024+ Timeline semanticSegments; **multi-device Haversine split**; waypoints | Ingest-grade; unique forensic capability; pairs with `google-takeout-location-parser` (legacy formats) |
| 4 | `messaging/gvoiceParser` | **Google Voice**: calls + texts + **voicemail transcription w/ confidence** | Only GV source; needs Python 2→3 port |
| 5 | `robust_conversation_extractor.py` | Corrupt/truncated JSON salvage (regex, not bracket parsing) | Generalize for any damaged export in evidence lane |
| — | `messenger-archive-viewer` types | FB-JSON schema blueprint + **mojibake fix** (FB double-encodes UTF-8 as latin1 — MUST re-decode) + call_duration→call_log | Schema reference (viewer itself not ingest) |
| — | `parsers.py` HTML/PDF loaders | FB-HTML + PDF-transcript fallbacks | Keep those functions; XML path duplicates #1 |
| — | TakeoutExtractor / google-photos-migrate | EXIF timestamp restoration from Photos JSON sidecars | attachment.exif enrichment, later |
| — | takeout downloaders, viewers, sms-loader.ts, pdf-imessage-parser.ts | acquisition utils / viewers / naive parsers | reference only; do NOT use for evidence |

**Still uncovered by anything in the tree: Snapchat JSON + XLSX message exports** — format_resolver (0008 item 1) is the intended attack for both.

## Consolidated 0008 scope (updated)
1 format_resolver · 2 message.hint_provenance + **is_read** · 3 app_setting + topic_code + conversation.cluster_code · 4 behavior_category.is_enabled · 5 lexicon sync (detection_pattern_set rows + convention) · 6-7 cost/prompt views (+tool_call_ledger.prompt_version) · 8 vw_message_behavior + vw_message_sms + vw_message_imessage · **9 finding span columns (pattern_type, span_start/end, severity_progression)**.
