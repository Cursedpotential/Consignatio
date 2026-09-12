# BOARD — at-a-glance current state
> Update this small; details go in `status/*` and `LOG.md`. Read `README.md` for the protocol.

## 🧹 2026-07-07 06:14 CLOSEOUT (owner-directed) — READ THIS FIRST; supersedes the 07-01 resume point
**RESTART-0001 is the new mainline.** `specs/RESTART-0001-source-tables-DRAFT.md` (rev 2, 2026-07-05) kills the
old detection/normalized_record/enrichment schemes: ingestion restarts as per-source raw tables (full-fidelity
JSONB, UUIDv7/msg, on-row H1/H2/H3 custody hashes = Option A, `conversation_key`+`participants` per owner 07-06).
DRAFT — awaiting owner ratification before apply.

**CLOSED this pass** (full reasons in APPROVALS.md [2026-07-07 06:14]):
- ❌ Detection COMMIT run (the held ~1,247-finding persist) — MOOT: owner's 07-03 ground-truth-labeling pivot
  (both passes over-flagged) + RESTART-0001 kills its target table. Do NOT run `forensic-detection-commit.sql`.
- ❌ Real persisted ingest via the old writer (→normalized_record) — superseded by RESTART-0001.
- ❌ ④a Milvus forensic collections + ④b Semantica deploy — schemas mirror the dead scheme; re-derive post-restart.
- ❌ AI-Chats bulk ingest + provisional-ingest follow-ups — superseded (scope (a) + RESTART-0001).
- ✅ Milvus-split execution — DONE, exceeded: 5 independent data apps live on shared `agno` net (07-05/06).
- ✅ SBV→MCP cutover + Option A facade bake — DONE 06-27, verified live.

**STILL OPEN:** ② SORT billable copy (NEW=3,376/~24 GB; needs scope+routing) · RESTART-0001 ratify+apply ·
ground-truth labeling (human_label workbook) · ⑤ web control-surface ADR · PhotoRec carve pile (parked) ·
heavy-OCR creds (parked). Infra lane (off-board): CF 1.0.4 upgrade, graphiti 421 sidecar, Portkey→LiteLLM swap.

Sections below this line are HISTORICAL — kept for context, do not action them.

---

## ⏸️ 2026-07-01 14:55 RESUME POINT (superseded by the 07-07 closeout above)
Owner authorized 3 reversible items this session; then owner switched sessions. State:
- ✅ **Detection dry-run ③ PASSED** live (1247 findings, all 5 court-safety counters=0, ROLLBACK, 0 durable rows).
- ⏸️ **Detection COMMIT staged + HELD** — `specs/forensic-detection-commit.sql` (hard in-txn court-safety guard; FK=`provenance_id`, status `'ok'`). Blocked on auto-mode classifier — needs OWNER's own hand.
- ⏸️ **Milvus ④a NOT run** — prep complete (session scratchpad venv + runner, ovh3 reach confirmed); same classifier block. NOTE: scratchpad is session-specific → rebuild venv next session.
- ✅ **SORT full OneDrive dry-run DONE** ($0, no transfer): **NEW=3,376 / ~23.99 GB**, DUP=171,076, DEFERRED_CLOUD=1,860 (untouched), READ_ERROR=0. Ledger `D:\casebible\exports\guarded-sync-NEW.csv`. → ② has exact numbers for owner step-2 sign-off (still needs scope + routing).
- 🧱 **BLOCKER:** auto-mode classifier blocks agent-initiated ovh3 prod writes AND self-granting a permission rule. Unblock = owner toggles off auto mode / runs via `!` / adds the milvus-venv allow rule. Full detail + undo commands + resume steps in `LOG.md` [2026-07-01 14:55] ORCHESTRATOR handoff.

## 🔄 2026-07-01 RESUME — READ FIRST (supersedes the 06-27 snapshot below for paths, Semantica, and status)

**PATHS CHANGED (owner):**
- **Coordination board = `D:\casebible\casebible-coordination`** (this folder). The old `C:\Users\matts\casebible-coordination` is RETIRED (gone).
- **Project memory, logs, conversation history = the E: Agno-MVP workspace `E:\AI_Workspace\Projects\the-platform-workspace`.** ALL lanes launch/cwd there; memory & history key off it.
- **`C:\Users\matts\OneDrive\Case Bible` is STILL canonical and STILL a working directory/source WITHIN the project** — it is just NOT the *opening* directory. Lanes **open in E:** (so memory/history key off E:) but continue to read/write the OneDrive Case Bible working area as before. The ONLY things that moved off C:/OneDrive: the board (→ D:) and project memory/logs/history (→ E:). The old `C:\Users\matts\casebible-coordination` board is retired.

**SEMANTICA HARD STOP (06-27) = RELEASED (owner 2026-07-01).** Owner directed: make **Milvus + Neo4j + Semantica functional + the pipeline.** Placement is decided — Semantica = seed-first hybrid writing OUR Neo4j+Milvus (graph WRITER stays Graphiti), ADR ~0035. PIPELINE may proceed.

**FORENSIC-DB — done this session (directly, not via lanes) and APPLIED to LIVE ovh3 PG (`agno-postgres:18-duckdb`, db=ai):**
- `0005` = reconciled **93-table schema** (evidence/analysis/public boundary) — APPLIED + verified.
- `0006` = **behavioral detection ontology** seed (153 categories / 512 patterns / 51 lexicon / 225 MCL) — APPLIED. Additive union of 9 scattered fragment sources; court-safe (every pattern a HYPOTHESIS, bias_caution=true, human-review gate before `safe_for_legal_use`; child/personal terms → sealed-lexicon `[REDACTED:]` placeholders, real values load out-of-band).
- Backed up to GitHub PRIVATE branch `forensic-db-reconciliation`. Docs: `Agno-MCP-Platform/docs/planning/forensic-db-reconciliation/` (+ `…/forensic-db-architecture/`). Read `…/forensic-db-reconciliation/STATUS.md`.
- LIVE spine populated: `analysis.normalized_record`=1943, `evidence.evidence_hash`=26. ~90 domain tables are EMPTY STUBS awaiting the pipeline.

**Where each lane picks up (2026-07-01):**
- 🟥 **PIPELINE** (owns Agno-MCP-Platform repo + forensic build): NEXT = (1) create Milvus **forensic collections**; (2) wire **Neo4j/Semantica** (seed-first); (3) build the **ingestion→detection→analysis pipeline** that fills the empty tables — START with the behavioral **detection runner** over the 1943 `normalized_record` rows → `analysis.pattern_finding` using the seeded ontology; (4) the out-of-band **real-value loader** for the sealed lexicon. SurrealDB stays DEFERRED (owner).
- 🟦 **SORT** (owns R2 `casebible-raw/-sorted/-quarantine` via OVH-2 rclone): raw→sorted type-first (copy-only/never-delete→quarantine, ledger, HITL) + the **guarded local-drives + OneDrive Case Bible → raw sync** (DRY-RUN + junk exclude-list + **md5 dedup-skip vs `D:\casebible\casebible.duckdb`** + **NEVER modify `D:\Backup`**). OneDrive Case Bible remains a canonical working source (read/write as before) — just not the opening dir. Freeze `casebible-sorted` before PROCESS bulk-reads.
- 🟩 **PROCESS** (owns evidence ingestion+verification): parsers (SMS-XML / FB-JSON / SBV / owner-custom iMessage; gaps = XLSX / Snapchat-json / call-logs) → 3-level SHA-256 custody → `analysis.normalized_record`; verify against the applied schema. Operates PIPELINE's machinery, doesn't edit its code.
- 🟪 **ORCHESTRATOR**: relay + sequence `TASKS.md`, triage `APPROVALS.md` (greenlight reversible/local; escalate prod/$/delete/cloud-transfer to owner), roll this BOARD, resolve `LOCKS.md`. Never executes prod.

**Guardrails (unchanged):** reversible+local runs unattended; gate prod/$/delete/R2-transfer to `APPROVALS.md`; dry-run + cost-estimate before any transfer; no hard deletes (quarantine); never modify `D:\Backup`; publish full test output to `specs/`; scoped git only (backup pushes go to dedicated branches, never `git add -A` on the shared repo).

**▸ 2026-07-01 02:11 — 3-lane subagent-workflow pass (orchestrator-run):**
- 🟥 **PIPELINE** fixed the ingest WRITER for `evidence_hash_subject_ck` (`evidence/custody.py`: source→hash+level+source_id→record) + rolled-back dry-run → **writer task ✅ DONE**, static-verified vs live DDL.
- 🟩 **PROCESS** built an offline **constraint oracle** (ALL GREEN) that independently proves the same thing: old bare-hash writer REJECTED, corrected source-first path PASSES. Constraint now **de-risked on both sides**.
- 🟦 **SORT** built + verified the **guarded-sync dry-run harness** (4 guards, read-only; `D:\Backup` untouched; md5 dedup proven on a 400-sample).
- **Only gated remainders** (→ `APPROVALS.md`): ① ONE live rolled-back writer/constraint dry-run (merged PIPELINE+PROCESS, zero durable write) — last proof before real ingest; ② SORT guarded-sync billable copy, needs owner scope + upload-routing decision.
- **PIPELINE NEXT** (reversible): behavioral **detection runner** over the 1943 `normalized_record` rows → `analysis.pattern_finding` (seeded ontology; symmetric, bias_caution, review-gated).

---


## 🛑 HARD STOP (owner, 2026-06-27 04:10) — SEMANTICA
Owner discovered **Semantica** (a full semantic-KG layer in dev-resources: provenance · dedup · semantic-extraction · entity-linking · conflict-resolution · embeddings · graph-store · export, ~1800 files) was left OUT of the pipeline. **ALL evidence ingest/build HALTED** until its placement is decided. PROCESS halted ingest (provisional 019f0807 throwaway). PIPELINE holds the gated rebuild + ③/④/parser-deploy. SORT holds AI-chats ingest + re-bucket execution (dedup overlaps Semantica). Reversible non-evidence work (⑤ ADR, infra, re-bucket dry-run) may continue. Orchestrator ran an Architect analysis to map Semantica's fit + overlaps (custody-hash/Graphiti/Milvus/parsers/dedup) + owner decisions — brief incoming, then revise the pipeline diagram.

**Phase:** 🎉 BOTH big cutovers LANDED (06-27 ~01:30). **SBV→MCP LIVE+VERIFIED** (facade registry_ok:true, tool_count:11, sbv.reachable:true, public 200, the 2-day FATAL closed). **Milvus-split COMPLETE** (data-tier 4 DBs all healthy incl. SurrealDB genuinely-healthy; Milvus fault-isolated). ZERO data loss (collections were empty shells; PG relational evidence intact). Owner-custom iMessage parser built (script-embedded silent-empty hazard closed, 3f6f161) — NOT yet deployed (folds into next platform-tools rebuild + build_imessage_workflow #3). NOW: PIPELINE deploy parser+workflow+gap-parsers (XLSX/Snapchat/phone) via the proven rebuild path → PROCESS acceptance-verify. INGEST: provisional pass paused at 1918 iMessage rows (in PG); handoff to autonomous loop stalled on owner's 3 details — but facade now works, so the PROPER pipeline is the cleaner path (owner decision pending).

## 🟢 RESOLVED (2026-06-25 10:23 — data tier RESTORED by PIPELINE; PROCESS verifying)
- **OVH-3 data tier is BACK.** PIPELINE restored it 10:23: docker data-root on /data (root 100%→26%,
  log rotation added so it can't recur). **All DBs healthy: PG, Neo4j, graphiti-mcp, Milvus.** Milvus
  needed a **fresh volume** (etcd/WAL corrupted by the unclean kill) — corrupt copy preserved at
  `ovh3:/data/agno/volumes/milvus.corrupt-20260625_141951`; only the ~1 smoke-test vector lost
  (re-ingestible from PG). SurrealDB healthy (Coolify shows `running:unhealthy` only b/c SurrealDB's
  minimal image lacks sh/curl for the Docker healthcheck — cosmetic; serves 200). **PROCESS now running
  its independent verification.** Bulk ingest still gated on a SORT freeze window.

## Who's doing what right now (06-26 23:48)
| Agent | State | Now |
|---|---|---|
| 🟦 SORT | **holding (handoff delivered)** | root-pile sort done (11:55, additive, zero deletes). ✅ Cloud-handoff content delivered (specs/sort-dedupe-handoff-content.md, verbatim logic + 8 owner sections) for PIPELINE's agent-handoff/sort-dedupe branch. Freeze on casebible-sorted holds (LOCKS 10:24). Next steps owner-gated. |
| 🟩 PROCESS | **BLOCKED on PIPELINE (looping)** | iMessage pilot blocked on 3 PIPELINE fixes; ✅ DE-RISKED OFFLINE 23:49 ($0): real 1918-msg sample parsed speakers-unblended + all 3 SHA-256 levels applied, custody chain VERIFIES → forensic spine proven runnable w/o bs4. Only PIPELINE's registry parse/bs4/workflow + gated prod write remain. Holding/looping. |
| 🟥 PIPELINE | **facade fix (Option A approved) + handoff branch + ADRs** | Verified live truth (code pushed; facade degraded = empty-mount root cause). NOW: execute Option A evidence-bake rebuild (verify+revert), create agent-handoff/sort-dedupe branch, Accept ADRs 0033/0034. Milvus-split staged but HELD for owner. |
| 🟩 PROCESS | **ingest handoff in progress (2 actors → 1)** | One-writer hazard caught: owner-driven actor ran artifact 019f0764; autonomous /loop session correctly held. OWNER DECISION 01:05 → hand ingest to the autonomous /loop (sole writer); owner-driven actor STOPS. Loop's safe-resume: read-only reconcile PG (besteffort-2026-06-26) → resume not duplicate; needs writer harness + blob-dest + embed/PG-only from owner. PG confirmed serving. |
| 🟪 ORCHESTRATOR | **coordinating** | Reconciled the corrected ground truth; APPROVED Option A (reversible facade-bake), HELD Milvus-split for owner; fixed ADR numbers; added the owner test-visibility rule to AUTONOMY. Coolify watch (no regression). I don't push. |

## ⏳ Awaiting human — full list in APPROVALS.md
- **🔴 Milvus-split EXECUTION** (APPROVALS 23:58) — THE key owner call: run the prod cutover now (in your terminal) or hold for a maintenance window? Outage window + crash-history tier; approved in principle, execution held for your explicit go.
- **Option A facade evidence-bake** — ORCHESTRATOR-approved (reversible); PIPELINE executing with verify+revert. Touches the public exec tier (mcp.mitechconsult.com) — flag if you want it paused.
- **PROCESS full evidence batch** → returns to APPROVALS after the pilot's real cost (pilot prod path waits on the Option A redeploy).
- **🆕 PhotoRec carve pile (SORT 00:35)** — 103,302 recup_dir* files (~17% of raw) likely → quarantine/archive, BUT 170 structured-messaging files (121 unique) hide inside → content-route evidence OUT first, NEVER bulk-quarantine blind. Held behind the messaging re-bucket; SORT will queue to APPROVALS with the guard when ready. Not urgent.
- **Heavy-OCR provider pool** (NEW, PIPELINE 19:33) — `extract.text` does native PDF + Tesseract OCR locally now; the escalated heavy-OCR pool (Google DocAI/Vertex, Gemini Flash, Azure DI, Textract, Docling-via-Colab) is gated on you wiring provider creds. Non-blocking — local OCR works. (Its `./tools` mount + OCR image deps fold into the pending SBV/exec-tier cutover.)
- (Lower priority) SORT ledger edge-case refinements — sort already executed (additive, reversible); refine later.

## Ground truth in the DBs (2026-06-25, post-restore verified 10:31)
PG (bind-mount, survived crash): `evidence.evidence_hash`=1 · `analysis.normalized_record`=1 · `platform_knowledge_contents`=1 (smoke test; zero real corpus). Milvus = FRESH/empty (new volume; smoke vector lost, re-ingestible from PG). Neo4j + graphiti-mcp healthy; SurrealDB UP (Docker "unhealthy" flag is cosmetic). Was: Neo4j 0 nodes / SurrealDB down.

## Coolify watch (ORCHESTRATOR read-only, 06-27 03:16) — ✅ DATA-TIER running:HEALTHY
After the Milvus-split (PIPELINE 01:25), data-tier = 4 isolated DBs (PG/Neo4j/graphiti/SurrealDB) ALL healthy; Coolify now reads **running:healthy** (SurrealDB isready healthcheck fix landed — no more cosmetic flag). Milvus+Attu now their OWN isolated stack (/opt/data-vector, raw compose, BIND_IP=100.119.96.29:19530) — NOT yet a formal Coolify app (cosmetic ~1-min UI task, flagged to owner). exec-tier rz41wqhp running:unknown but facade VERIFIED healthy (tool_count:11). Watch healthy; reopen only on regression. ⚠️ LESSON (→Graphiti): data-tier auto-deploys on push to main; service-removing pushes tear down running services + Milvus etcd dies on unclean kill — stop gracefully/replace-first next time.
data-tier `ipy7vrw…` on ovh-3 = `starting:unknown` since ~00:18 (updated_at FROZEN at 04:18Z across 00:22+00:29 checks), **restart_count 0**, last_restart_type null, **health_check_enabled FALSE** (so Coolify can't report healthy from the API — "starting:unknown" may be cosmetic/terminal for this app, NOT a crash). Still BUNDLED compose (Milvus-split NOT applied). NOT crash-looping (restart_count 0 vs 12 in the incident). Can't ground-truth DB health from read-only Coolify → **directed PROCESS to run the read-only cb_postrestore_verify.py** (PG/Neo4j/Milvus/Surreal) to confirm DBs are serving; will clear or escalate on its result. exec-tier `rz41wqhp` running:unknown (Option A not yet visible).

## ✅ RESOLVED — messaging format reconciliation (SORT + PROCESS converged 00:14)
Raw SMS-XML (S&R v10.21.003, 189 distinct/460) + Facebook DYI JSON (336 distinct/485) **DO live in casebible-raw** → sms_xml.py + facebook_json.py + SBV-primary are correctly aimed (point at RAW keys; sorted .txt/.csv/.pdf/.xlsx = derived/secondary). Files: specs/raw-canonical-formats-RESULTS.md (SORT) + specs/imessage-derisk-RESULTS.md (PROCESS appended).
**PIPELINE parser-gap list:** keep XML/JSON/SBV parsers; best-format §1 = prefer structured + **dedup-by-md5 first**; BUILD gaps = **XLSX + Snapchat-.json + phone/ call-logs (TBD)**; route by CONTENT not folder (S&R XML misfiled in a PhotoRec carve dir).

## 🆕 Owner directives (2026-06-27 03:20)
1. **Pipeline diagram** ✅ DONE (ORCH) — specs/PIPELINE-DIAGRAM.html (mermaid, validated), sent. Owner verifies design before full run.
2. **Sample ALL ingested data** → PROCESS (read-only dump → specs/ingested-data-SAMPLE; ORCH sends).
3. **Graphiti**: ✅ already a CC MCP (in .claude.json, used live). → PIPELINE: wire into Agno AGENTS/platform runtime (ADR-0031/P3).
4. **SBV manual-process-with-custody** → PIPELINE: open/upload a file in SBV → full custom evidence-handling (parse+3-level custody+normalized_record), not just raw view.
5. **Unified web control/viewing surface** → PIPELINE: mine original-iteration intent + propose architecture (extend AgentOS UI vs dedicated dashboard) as ADR/spec — PROPOSAL FIRST, owner review before build.
6. (open) **Ingest path** decision: provisional-loop vs proper-facade-pipeline (recommended). Provisional paused at 1918 PG rows.

## Dependency order
`PIPELINE P0 (disk) → unblocks all` · `SORT stable snapshot → feeds PROCESS` · `PIPELINE machinery → PROCESS operates it`

## 🔄 2026-07-01 ~07:45 — ORCHESTRATOR triage (all 3 lanes reported one pass)
- 🟩 PROCESS: **ingest path PROVEN** — full live rolled-back dry-run (source→hash→normalized_record, subject_ck ok, exit 0, ROLLBACK, counts unchanged). Real persisted ingest = OWNER-GATED (cost + blob-dest).
- 🟥 PIPELINE: built `evidence/detection.py` detection runner (court-safe, symmetric, idempotent) + **26/26 offline self-test**. Live rolled-back detection dry-run = GREENLIT (zero-durable, same class as PROCESS). Milvus/Semantica defs next (reversible).
- 🟦 SORT: OneDrive scope measured = 178,499 files (176,639 local/150.94 GB + 1,860 cloud placeholders); cloud-placeholder skip guard added (no hydration). Full OneDrive dry-run = GREENLIT ($0, local-only). Billable rclone transfer = OWNER-GATED.
