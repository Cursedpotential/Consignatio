# Intake continuation handoff — 2026-09-11

<!-- Author: Codex | Platform: Codex desktop / Windows | Rev: 1 -->

## Read this first

Owner requested this handoff because paid usage is nearly exhausted until Sunday.
Do not repeat the whole investigation, restart architecture planning, or run broad
audits/tests. Continue from the verified state below. This handoff creation does
not dispatch another model, schedule work, or authorize new background spending.

**Status: PARTIAL. Native desktop runs; combined-index source is integrated and
tested, but live CocoIndex → Weaviate → desktop search proof is still outstanding.**

**The Weaviate choice is SETTLED: use 100.91.190.107:8082 (gRPC50052).** The owner
ordered the old8081 instance retired. It is gone from Coolify. Do not reopen the
choice, resurrect it, or follow historical migration holds that say preserve both.

## Product and boundaries

- Stage one is a smart file explorer for organizing a messy ~2TB collection across
  stores: dual panes, preview, natural group selection, chat assistant, powerful
  combined filesystem search, later atomic/nested units and relationship graph.
- NOT evidence candidate selection/review. That belongs to stage two. Do not gate
  ordinary browsing/moving on evidence approval, classification or indexing.
- Retain CocoIndex, Weaviate search, Surreal filesystem graph soon afterward,
  distinct Lance/Parquet lake outputs and B2 destination. No technology replacement.
- Distinct-source matching files can corroborate one another: no automatic deletion
  or collapse based on hashes, semantic similarity or differing formats.
- Filestash → OpenList WebDAV is the separate remote abstraction. Local/mounted
  paths are the initial working route, not its replacement.

## Locations / Git — do not lose dirty work

| Component | Absolute path / state |
|---|---|
| Vault repository | `E:\AI_Workspace\Projects\Propria\Consignatio` — branch `main`, HEAD `161d3c4` |
| Intake | `E:\AI_Workspace\Projects\Propria\Consignatio\Intake` |
| Backend | `E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend` |
| Actual desktop fork | `E:\AI_Workspace\Projects\Propria\Consignatio\Intake\xplorer-copilot-buildkit\xplorer-copilot` — branch `feat/acp-copilot`, HEAD `f59e6202` |
| Original legacy work | `E:\AI_Workspace\Projects\Propria\Consignatio\casebible` |

At handoff: parent1082 tracked status entries (includes prior relocation work);
fork75 dirty entries. No implementation commits/pushes were made in this run.
Do not claim all changes, reset/clean/stash, broad-stage, or modify child Git
boundaries. The fork is independent and ignored by the parent, not a gitlink.
Preserve pre-existing fork CLAUDE.md edits. Never push upstream.

Read parent and Intake AGENTS.md/AGENT_MEMORY.md and the fork's CLAUDE.md before
editing. Installed CocoIndex/Weaviate skills are at `C:\Users\matts\.agents\skills`.
CocoIndex skill is v1: App/@coco.fn/public target protocol, NOT v0 tutorials.
Some fork-referenced older think/karpathy skill names were unavailable; report
missing skills rather than pretending to load them. Do not install unnecessarily.

## Runtime — live snapshot, verify PIDs before touching

Handoff check found native PID23268, window **Intake — File Workstation**, frontend
PID23740 listening on127.0.0.1:5176, and Cargo dev-run parent27584. No rustc process
was present. Leave the open app alone unless the owner is ready for a rebuild.
Earlier observed app+six WebView processes totaled ~470MiB; this is not a fixed cap.

- Explicit runtime: `E:\AI_Workspace\.intake-dev\runtime`.
- WebView/app/local/roaming state verified on E:. Second native launch with same
  runtime refused with OS-lock error/exit1; original app remained responding.
- `scripts/intake-env.ps1`: process-local E: temp/Cargo/Rustup/npm/runtime paths;
  pinned Rust1.91.1 copied to E:, direct rustc/cargo paths; one Cargo worker;
  dev/test debug info0, incremental0.
- MSVC installed on C: is used as an existing system tool. Missing Windows SDK
  supplied by official Microsoft SDK NuGet packages10.0.28000.2705 under E:.
  VS shell emits a missing-file message before explicit SDK override; subsequent
  linker/header checks and actual builds succeed. Do not reinstall toolchains.
- Existing shared C: caches were copied, not moved/deleted. Last volume reading
  C:101.7GiB free, E:85.7GiB. Do not assume these remain current.
- No local inference, corpus workers or backend API server started by this work.

Future launch (close existing Intake before rebuilding changed native source):

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\xplorer-copilot-buildkit\xplorer-copilot" && pwsh -NoProfile -File scripts/start-intake.ps1
```

Do not use root phase-two Vite1420 or generic `pnpm dev` (starts extra services).
Do not call the app/index command `ccc`; that belongs to a different indexer.

## Implemented and tested

- Per-pane selection/preview keyed by pane + tab/path. Focus preserves groups;
  navigation clears only that pane; stale async setters cannot resurrect selection.
  Toolbar/sidebar/chat derive active pane. Legacy behavior preserved outside Intake.
- Chat selection manifest includes exact metadata and700-entry regression; no
  automatic content reads to construct chat context. ACTIVE PREVIEW can read bytes,
  including mounted remote files. Metadata-only discussion: open chat without preview.
- Lazy chat keep-alive retains conversation/draft through preview/collapse;
  hidden polling/keyboard/workspace awareness pauses. Submitted replies may finish.
- Intake-only **Preview + chat** toggle, existing vertical resizer + keyboard arrows,
  constrained split, short-window fallback. Not a general docking redesign.
- Left Search panel and assistant `search_files` use native `filesystem_index_search`
  → HTTP `POST /filesystem/search` → Weaviate. Keyword/hybrid, source IDs/paths,
  scores/snippets, explicit unknown coverage, bounded errors. No scan fallback.
- Three index searches per model response / five model iterations; bounded snippets.
- Native Portkey config/env-reference handling, remote-only fallback guards, bounded
  concurrency/timeouts/response sizes; no renderer provider credentials.
- CocoIndex v1 Weaviate target: deterministic writes, unchanged skip, retirement via
  active=false, NEVER DELETE. Schema validation only; no auto collection creation.
- Bounds cover CocoIndex fingerprint reads too: defaults8MiB file,1M extracted
  chars,512chunks,2inflight. NOT an OS memory ceiling or decompression-bomb solution.
- Source-scoped OS locks, explicit V/Y alias registry, honest checkpoint/status API.
  Independent stores' byte-identical files produce distinct searchable occurrences;
  matching V/Y scopes converge. Keep index roots nonoverlapping for now.
- Paste fix avoids destructive replacement default, separates skipped results.
  Mixed-success cut still clears clipboard too broadly: NONDESTRUCTIVE and explicitly
  accepted for MVP. rclone/Ultracopier transfer evaluation is post-MVP.
- Updater hook disables timers/manual check/install in Intake. Native plugin guard
  added and Cargo-checked AFTER current executable started. Current native binary
  still has plugin; guard becomes effective at next rebuild/launch. Do not interrupt
  owner's current work merely to apply it. Frontend protection can apply through HMR.

Proof: 70 scoped frontend tests,40 backend tests,7 native tests; TypeScript and
scoped ESLint pass. Pinned Cargo check and executable build succeeded (8m51s initial
executable build); final binary check passed after native updater guard. Warnings
remain: unused imports/dead code. No broad cargo fix or full-suite test was used.

**Not verified:** actual native click-through, selection-to-live-chat exchange,
live Weaviate indexing/search, real corpus/multimodal processing or deployed graph.
Computer Use skill was read but its required node_repl runtime was unavailable;
do not report process/window existence as visual acceptance.

## Remote provider and Weaviate — exact state

- Portkey gateway `http://100.72.169.40:8787`; remote provider `https://ollama.com/v1`;
  model `portkey:nemotron-3-super`. Launcher sets native + Vite model selectors.
- Config `scripts/intake-portkey-chat.json` uses literal `$OLLAMA_API_KEY` reference.
  Existing key read only in memory from `C:\Users\matts\.secrets\probata.env`;
  same existing store also has NVIDIA_API_KEY. Never print/copy key values.
- Real synthetic Portkey Super probe returned HTTP200/contentOK/finish stop with
  output budget1024. Ultra timed out45s; Super budget128 yielded empty reasoning-only
  output. Native adapter uses4096. Do not repeat model selection blindly.
- Remaining Weaviate: `http://100.91.190.107:8082`, gRPC50052, version1.38.7,
  Coolify `data-weaviate-native-v1`, UUID `v43tfq25o7i561n4lnc124p2`.
  Bind data `/data/probata/volumes/weaviate-native-v1`; readiness200 verified.
- Old app `data-weaviate-files`, UUID `o97r85b7nagwjuncs4oo07hs`: STOPPED then
  DELETED via Coolify at explicit owner direction. API404 confirmed. Never restore
  it to satisfy an obsolete hold. Old8081 no longer serves.
- Old data moved to `/data/probata/to_be_deleted/weaviate-old-8081-o97r85b7nagwjuncs4oo07hs`.
  Recoverable; only owner permanently deletes. Move did not free disk space.
- Before retirement: all seven populated/shared collection counts matched3035total;
  old-only EvidenceChunkV1 was empty. Earlier receipt contains full semantic/query
  parity. No existing collection was modified for Intake. No Intake collection yet.
- Downstream clients were NOT repointed; configs still using8081 need scoped updates.
  Do not sweep unrelated apps or restart services without an authorized change.
- Coolify operations through skill/API, not direct Docker lifecycle commands.
  SSH alias `ovh-files-ts` targets100.91.190.107. Remote hosts were never restarted.

## Next steps, in order — do not start from scratch

1. Read this and narrow receipts below. Verify current Git/process state cheaply.
2. Use8082; do not ask which server. Read Weaviate create-collection reference and
   backend schema contract. Provision a NEW dedicated synthetic Intake collection,
   preserving all existing collections; explicit external named vector, not default
   automatic embedding. Verify NIM model/dimension access with minimal fictional input.
3. Execute `backend/docs/SYNTHETIC-LIVE-PROOF.md`: committed fictional one-file input,
   4KiB caps,8chunks,1inflight,1NIM request at a time, fresh output on E:. Its old
   "physical instance pending" language is superseded by this handoff. Check free
   loopback18765 before serving. No automatic expansion to mounts/corpus.
4. Verify keyword and hybrid hits, source identity, unchanged repeat/checkpoints.
   Bind native `INTAKE_FILESYSTEM_API_URL` to that API and optional native token.
   Search API has no established external auth: keep loopback, don't expose publicly.
5. Native smoke: **Split right** topbar; **AI Chat** right rail; **Preview + chat**
   header. Left **Search** is new index. Right **Content Search** is legacy tokenizer.
   Topbar **New Chat** creates a chat file, not standalone chat. Verify selection
   across panes, draft retention, preview, real remote reply and assistant search.
6. After bounded proof, agree first real source scope; harden parser/resource limits
   before large corpus run. Then Surreal filesystem graph (separate evidence DB),
   atomic units/sidecars, multimodal handlers and remote abstraction.

## Read only what you need

- `docs/XPLORER-FIRST-2026-09-11.md`: native/build/runtime/provider receipts.
- `docs/RECEIPT-2026-09-11-SELECTION-CHAT.md`: UI/search/chat changes and limitations.
- Fork `apps/src-tauri/INTAKE-RUNTIME.md`: isolation, launch, pane/updater receipts.
- `backend/docs/FILESYSTEM-SEARCH-2026-09-11.md`: target/schema/identity/locks.
- `backend/docs/SYNTHETIC-LIVE-PROOF.md`: exact bounded live commands.
- `docs/WEAVIATE-OLD-INSTANCE-STOPPED-2026-09-11.md`: superseding retirement authority.
- `backend/docs/MASTER-TODO.md`: backlog; older pending-server statements are stale.
- Full plans only as needed: `backend/docs/UNIFIED-WORKBENCH-PLAN.md` and HTML;
  existing system-design HTML contains original cookbook/Surreal graph mapping.

## Standing safeguards and deferred items

All development storage on E:, mount caches on D: by explicit exception. No host
reboot/shutdown/sleep/logoff. No permanent deletion. No cloud hydration as a side
effect of tests, no local inference, no MemSearch/ccc/global-settings changes.
Local mounts previously V:performance / Y:metadata, all R2 buckets consolidated.
Performance launcher30GiB but earlier live mount50GiB; metadata10GiB. Do not restart
mounts to reconcile this while owner may be using them; inspect only if relevant.
Remote abstraction lives in sibling Probata planning: Filestash over OpenList,
not SFTPGo; previous service status was document-derived, not freshly verified.
Consult owner before OCR/LibreOffice/hosted Docling/other previously considered
handler choices. Face/multimodal provider policy and lake publication remain work.

Keep costs bounded: no broad corpus scan, no parallel paid research just to read
this handoff, no repeated full build once scoped source checks suffice. If resuming
implementation with workers, assign disjoint files and preserve concurrent edits.
