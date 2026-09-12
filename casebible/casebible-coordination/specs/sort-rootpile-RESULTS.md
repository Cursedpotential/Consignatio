# SORT — root-pile sort RESULTS (owner-visible verification)
> _Byline: Claude Code · Opus 4.8 · 2026-06-27_ · **LOCAL ONLY — no secrets (file paths only).**
> Published per the STANDING RULE (LOG 00:05): verification output goes to a shared owner-visible path, not a private scratchpad.
> Lane: 🟦 SORT. This consolidates the EXECUTED root-pile sort (2026-06-25) + the parked human-review decisions the owner needs to make.

## What ran (human-approved, executed 2026-06-25 11:55)
Type-first sort of the raw-ROOT pile (the enriched ∩ at-R2-root intersection). **COPY-ONLY, never delete.**
- Tool: `cb_execute_typefirst.py` (server-side `rclone copyto … --s3-no-check-bucket`, 8 workers).
- Input ledger: `D:/casebible/exports/sort_proposal_typefirst_root_20260625.csv` (dry-run proposal, pass-3 refined).
- Generator of the proposal: `cb_typefirst_ledger.py`. Full verbatim logic in `specs/sort-dedupe-handoff-content.md`.

## Verified outcome (verify-before-claiming)
| Metric | Value |
|---|---|
| Content files COPIED raw → `casebible-sorted` | **364** (type-first; 13 top-level type folders) |
| Obvious junk COPIED raw → `casebible-quarantine/_root_cleanup_2026-06-25/` | **35** |
| raw root after run | **INTACT at 401 objects** (all copies) |
| Deletes | **0** (HARD RULE: never delete; raw is the archive of record) |
| Errors | **0** |
| `needs_review` items routed + tagged in place (not blocked) | **195** |
| Existing sorted content (AI Chats/ 400, Evidence/ 3,646, etc.) | **UNCHANGED** (run was additive only) |

- Provenance (executed) ledger — every `old_path → new_path` + status: `D:/casebible/exports/sort_executed_typefirst_root_20260625.csv`.
- Note: 364-vs-365 reconciliation = one duplicate enrichment record copied twice to the same destination path → no loss, idempotent.
- Freeze on `casebible-sorted` (LOCKS 10:24) held throughout; PROCESS's content-hash reads stay valid (additive run, no path churn to existing content).

## Routing breakdown (from the refined proposal ledger, pass 3)
ROUTE → sorted **362**: Tools & Platform 81 · Knowledge 79 · Evidence 77 · Inbox/triage 47 · Legal 41 · Exports & Bundles 27 · Entities 8 · Documents 2.
- **Evidence by SOURCE:** messaging (fb 13 / sms 7 / imsg 3 / phone 1 / misc 23) · records-data 17 · media 4 · screenshots 4 · public-record 3 · financial 1 · audio 1.
- **QUARANTINE 35** (only obvious junk): shader-junk 18 · flagged-junk 13 · installer 4.
- Pass-3 rescue: the model over-flagged junk → rescued ~9 real-content false positives (`data.json`=139pg PDF, `content.zip`=227 PDFs, `place_id_db.json`=geolocation DB, `enriched_timeline_human_readable.csv`, …); quarantine dropped 61→35. All rescues flagged `needs_review`.

## ⏳ PARKED — needs owner decision (now that you're reviewing)
1. **Confirm the ~9 junk→content rescues** (listed above) — keep in their rescued type buckets, or re-quarantine any?
2. **23 unsourced messaging** files — Evidence/messaging/misc; want a source-attribution pass, or leave as misc?
3. **Tools & Platform code set (~81 incl. ~16 case scripts)** — split into: case-own tooling (keep) vs third-party utilities (`fclones`/`zoplicate`/etc → quarantine or archive?) vs junk. Needs a case-tool-vs-third-party judgment pass.
4. **195 `needs_review`** items — routed + tagged in place; want a refinement pass, or accept current placement?
5. **Optional raw-root tidy** — copy now-sorted originals into `raw/_moved_2026-06-25/` (preserving structure, still COPY-only, your "moved folder" pattern)? Default = leave raw untouched.

## Next SORT work (all owner-gated)
- Ingest AI conversations → Milvus `casebible_ai_conversations` (small embeddings $ — $-gated).
- Domain→type **re-bucket of the EXISTING ~4,262 sorted files** (esp. the 3,646 in Evidence/ that are really messaging) — **held**: owner's folder-structure rework is in flight; will sequence after that lands to avoid conflict.
- Cloud handoff: verbatim logic delivered (`specs/sort-dedupe-handoff-content.md`); PIPELINE creating branch `agent-handoff/sort-dedupe`.
