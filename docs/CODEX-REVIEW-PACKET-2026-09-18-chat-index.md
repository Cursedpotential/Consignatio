<!-- tags: review, handoff, codex, intake, consignatio, elt, duckdb, weaviate, surrealdb, cocoindex, chats, owner-directive -->
# Codex review packet — chat index work of 2026-09-18

> _Byline: Claude Code · Fable 5.1 · 2026-09-18 21:20 EDT. Written for Codex to check. Status is stated as it is, not as hoped._

## 1. Status in one line

**The index app is NOT done.** No CocoIndex-based index over the catalog files exists as a running thing. What exists tonight is a set of DuckDB scripts, a partly loaded Weaviate collection, a Postgres staging copy, and a search panel in the hosted Intake app.

> **Correction 2026-09-18 22:42 EDT (Claude Code · Opus 5):** this packet's framing is scope-inverted — it treats the chat ELT as the work and the CocoIndex app as a follow-up (§4 row "the CocoIndex app that was supposed to be the indexer", §7 Q1). Superseded by the owner-confirmed sequence: CocoIndex discovery over the ENTIRE corpus first → owner selects → Go-engine intake in place. See `docs/transcripts/2026-09-18-codex-cocoindex-super-index-review-correction.md`, `…-codex-owner-cocoindex-discovery-first-architecture.md`, `…-codex-route-from-tonight-to-architecture.md`. The SMS row in §4 is also incomplete: the sanitize template later reproduced 11,676 records but is locator-only for MMS attachments (blocking defect, `docs/URGENT-TODO.md` 22:09–22:20). §6's discriminators (front-matter `source:` host, turn markers) are the signature knowledge Build 4 absorbs.

## 2. What the owner asked for (his words)

- 12:32 EDT: "we need the ccc based super app we were creating to start indexing the directories most likely to have chats… get the minimum needed to get coco index and duckdb working to catalog and index and make searchable anywhere there may be chats… so when I get home we can build a master timeline."
- 21:05 EDT: "identify directories and inventory of chats in them. Use the DuckDB extraction template… to write a couple of queries. Run it against those files in place. And load it so I could scan it and put something together for this weekend."
- 21:08 EDT glossary: **"Chats are my conversations with AI about these situations. Message transcripts are SMS messages with Katrina and other people."** Two different things.
- 21:10 / 21:14 EDT: "folders don't mean shit"; "many chats are just the first sentence of the first prompt."
- Process rulings (dated quotes): `docs/receipts/PIPELINE-HISTORY-2026-09-18.md`. Tonight's path by owner decision 20:52: DuckDB ELT templates (DuckDB engine, not pg_duckdb, not parsers) → Weaviate first → SurrealDB for timelines/entities/graph. Precommit preview waived for tonight only.

## 3. What went wrong today (so you can check the fixes, not the story)

1. "Chats" was read as messaging all day. Loaded: 551,877 events, of which **2,559 are AI-chat turns**.
2. The afternoon run used the Probata parsers for SMS/calls XML, iMessage and FB HTML (against the ELT ruling), landed events in Postgres as the store, put Weaviate second, and loaded SurrealDB directly (it hung 3 times).
3. Chat files were picked by guessed format and then by folder-name ranking. Both invalid.
4. CocoIndex was not used at all.
5. The Go engine's ELT lane cannot do this yet (code-verified): `modules/engine/parser/registry.go` has no DuckDB entry; `activities/elt_structured.go` handles csv + ndjson only, is pg_duckdb-bound, and is not wired into `profferworker` (`activities/register.go:222-227`).

## 4. Code to review (paths from `E:\AI_Workspace\Projects\Propria`)

| What | Where | State |
|---|---|---|
| Afternoon MVP (extract.py, build_timeline.sql, loaders, search.py, Dockerfile) | `Consignatio` branch `chat-timeline-mvp-20260918` @ `67cf9bd`, `casebible/tools/chat_timeline_mvp/` | committed, not merged. Uses parsers for XML/HTML. |
| Message-transcript ELT templates: `elt_smsbackuprestore_v1`, `elt_xml_sanitize_v1`, `elt_imessage_html_v1`, `elt_imessage_txt_v1`, `elt_fb_messenger_html_v1`, `elt_google_voice_html_v1`, `elt_mbox_v1`, `tag_events_v1`, `elt_run.py`, `chat_elt_worklist_20260918.sql`, `chat_directories_20260918.sql` | worktree `_worktrees/consignatio-chat-dirs-20260918` (branch `chat-dirs-index-20260918`), `casebible/tools/chat_timeline_mvp/elt/` | **uncommitted, in progress, unverified.** SMS template must reproduce 11,676 records on `/data/test_data/smsbackuprestore/export-20251206/sms-20251206203434.xml`; DuckDB `read_xml` rejected that file as invalid XML before the sanitize step existed. |
| AI-chat ELT templates: `elt_ai_chatgpt_v1`, `elt_ai_claude_v1`, `elt_ai_gemini_activity_v1`, `elt_ai_generic_json_v1`, `elt_ai_markdown_transcript_v1`, `_envelope.sql`, `ai_chat_signature_probe.py`, `ai_chat_zip_probe.py`, `run_ai_elt.py`, `publish_ai_chats_weaviate.py` | worktree `_worktrees/consignatio-ai-chats-20260918` (branch `ai-chats-narratives-20260918`), same `elt/` folder | **uncommitted, in progress, unverified.** |
| AI-chat discovery queries (read-only, catalog) | `Consignatio/casebible/tools/ai_chat_name_patterns_20260918.sql`, `ai_chat_sample_keys_20260918.sql`, `ai_chat_pattern_counts_20260918.sql`, `ai_chat_sentence_names_20260918.sql`, `ai_chat_first_prompt_names_20260918.sql` | uncommitted on `main` |
| Hosted Intake engine + search panel | fork `Consignatio/Intake/xplorer-copilot-buildkit/xplorer-copilot`, branch `feat/hosted-intake-engine` (remote `private`), head `499de6cb`; engine crate `apps/intake-engine/` | live at `https://homepage.tilapia-skilift.ts.net/progress/intake/xplorer/`. Search = left "Search files" tab. Known defects: right-rail "Content Search" still the donor's dead screen + 422 polling; Enter does not submit. |
| The CocoIndex app that was supposed to be the indexer | `Consignatio/Intake/backend/src/casebible_index/` (pipeline.py, weaviate_target.py, filesystem_search.py, projections/surreal.py; last commit `393d369`, 2026-09-13) | **never deployed to a VPS, never pointed at B2.** |
| SurrealDB hang diagnosis + lean config + loader design | `docs/URGENT-TODO.md` entries 20:20–20:34 EDT | RocksDB WriteBufferManager stall (144 MiB limit vs 128 MiB retained memtable history). Fix proposed: 8 MiB write buffer, 64 MiB block cache, jobs 4, COMPACT checkpoints, 250-event transactions. Apply state: check the log, not this line. |

## 5. Data state (ovh-files, 100.91.190.107)

- Catalog PG container `fgz1n7useplhk0t91uk7k1aw`, db `casebible`, schema `raw_duck`: `chat_candidates_20260918` (6,431, name-guessed), `chat_events_20260918` (551,742), `chat_event_provenance_20260918` (1,081,919), views `timeline_*_20260918`, `chat_directories_20260918` + `chat_dir_files_20260918` (folder-name ranking, invalid), `ai_chat_probe_20260918` (104,740 json/text/html/zip files with catalog paths).
- Weaviate `ChatEvents20260918` on `data-weaviate-native-v1` (:8082): 106,496 objects from the afternoon run; missing recipients, sha1, catalog path, ingest_run_id.
- SurrealDB `surreal-intake` (ns consignatio / db intake): partial `tl_*_20260918` tables (~21k events). Backup `consignatio-intake-20260919T001442Z.surql`.

## 6. AI-chat findings from the catalog (names as leads, first bytes read in place)

Confirmed shapes: `chat-memo_*.txt` (242 ChatGPT conversations, per-message timestamps) · `conversations.json` (Claude official export, 61 MB) · `ChatGPT - <title>` · `gemini_<slug>_<timestamp>.md` · `Google_Gemini_<date>.md` · `Gemini - <title>` / `Gem=<title>` JSON+MD · Takeout Gemini Apps `MyActivity` · `Claude - <title> - Claude.md` · `Claude-Conversation-<ts>.txt` · `Perplexity Playground*.md` · `chat-export-<epoch>.json` (Qwen/Open WebUI). About 170 files + 122 folder leads, ~235 MB.

First-prompt names (owner's lead, confirmed): 129 files whose stem is cut at ~50 characters and 22 cut with "…", e.g. Obsidian clippings with `source: https://gemini.google.com/app/<id>` and `author: [[Gemini]]` front matter, and Perplexity answers starting with the Perplexity logo `<img>`. The same name rule also catches web clippings that are NOT chats (e.g. a voter-records page) — **the front-matter `source:` host (gemini.google.com, chatgpt.com, claude.ai, perplexity.ai) is the reliable discriminator**, plus turn markers ("You said", "**You said:**", "### 🤖 Assistant", "User: [timestamp]").

Not chats: prompt-library / slash-command repos, `Gemini_parser/data/raw_api_responses`, `.smart-env/*.ajson`, browser "N Sessions" JSON, Google Voice group HTML, FB chat-settings HTML, zips uploaded into Gemini Apps.

## 7. What I would like Codex to check

1. Is tonight's path (standalone DuckDB templates → Weaviate → SurrealDB) the right minimal reading of the owner's rulings, and what is the smallest step that makes the CocoIndex app (`Intake/backend`) the real indexer over the same file list?
2. The ELT templates in the two worktrees: correctness of each `elt_*_v1.sql` against real files, timestamp handling (never invented), dedup key, provenance fields.
3. The SMS `read_xml` failure on the 1.3 GB file and the sanitize approach.
4. The SurrealDB stall analysis and the lean RocksDB settings.
5. The AI-chat discriminator in section 6 — better signatures you already know from the 09-06/09-13 work.
6. The Go engine gap in section 3.5 — the order to close it after the weekend.

## 8. Log

Everything above is recorded, with times, in `Consignatio/docs/URGENT-TODO.md` (2026-09-18 sections). Names of the minor are kept out of git and logs.
