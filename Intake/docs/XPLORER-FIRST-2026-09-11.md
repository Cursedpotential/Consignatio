# Working file manager first

Owner correction: live local/cloud filesystem organization is phase one. Existing
Intake metadata review is phase two. Do not require case/evidence classification,
indexing, hand-selected candidate imports or acceptance records to browse and move.

## Source findings

The independent fork is under `xplorer-copilot-buildkit/xplorer-copilot/`.
Existing source implements recursive split panes, cross-tab selection, bulk
cut/copy/paste, previews, chat/agent panels, native file-operation tools and Google
Drive HTTP operations. This is source evidence, not yet runtime verification.
Native OneDrive/S3/rclone adapters were not found in the bounded source inspection.

Do not build another splitter or basic file manager until these existing paths
are running and their gaps are measured.

## Bootstrap findings

- Dependencies were absent; no native executable was found in the usual debug path.
- CI uses pnpm 10; host default resolves pnpm 11 and ignores package overrides.
- Install uses pnpm 10, frozen lockfile, ignored lifecycle scripts and low network
  concurrency. Completion must be verified separately.
- Visual Studio C++ Build Tools are installed under
  `C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools`; `link.exe` is not
  on the ordinary shell PATH. Use the supported build environment when compiling.
- `dev:app` is desktop plus frontend. Default `dev` also starts marketplace;
  marketplace is not required for this file-manager milestone.
- Frontend is configured for 127.0.0.1:5174; native dev URL uses localhost:5174.

## First smoke test

Owner clarification, 2026-09-11: first usable slice is desktop navigation,
group selection, preview, and selection-aware chat. Combined filesystem
CocoIndex/Weaviate search remains required for the MVP. Local mounts are the
initial route, not a replacement for the separate remote-filesystem abstraction.
The non-destructive mixed-result cut clipboard issue is accepted for MVP;
transfer-engine replacement and clipboard reconciliation are post-MVP work.
Keep rclone and Ultracopier on the evaluation list in backend/docs/MASTER-TODO.md.
The move tests below are follow-up transfer verification, not a prerequisite
for opening the workstation and discussing selections.

Use disposable files to validate native operation: two folders, split navigation,
multi-selection, copy/move, refresh, collisions, skipped items, and failure reporting.
Then repeat with selection-aware chat and a connected cloud route. No actual
owner files have been moved as part of the source investigation.

## Defect found

`apps/client/src/lib/paste-helpers.ts` defaults missing conflict decisions to replace,
deletes destination before transfer, and counts skipped files as success. Assigned
a narrow correction with mocked regression tests before live operation testing.
Do not conflate this ordinary correctness fix with evidence approval restrictions.

## Execution receipt

### Original materials reconciled

Read ZIP entries without extracting or overwriting local work. The supplied
`C:/Users/matts/Downloads/xplorer-copilot-buildkit.zip` contains 20 files:
17 match the local build kit byte-for-byte (SHA-256 comparison); README.md,
CLAUDE.md and docs/00-PREFLIGHT.md differ. The original BUILD_GUIDE.md, phase/tool
documents and scaffold source match. Document instructions remain reference
material and do not override current owner directions.

The existing synthesized system-design HTML explicitly maps
`meeting_notes_to_surrealdb_graph` to native graph target/relation creation.
The filesystem graph separation is restored in AGENTS and DEVELOPMENT, not a
new technology choice. Its store/location/unit relationships are independent
of the downstream evidence-analysis database.

### Native verification follow-up

The repository pins Rust 1.91.1. Initial Cargo invocation caused Rustup to try
installing that toolchain before Cargo's offline flag took effect; those attempts
were interrupted. The repository pin was not changed. Installed `stable` is used
only as a process-local diagnostic override. Offline dependency resolution found
missing `bincode`; a locked online check with one compilation worker followed.
Do not describe this diagnostic as a completed pinned-toolchain build.

### Disk-pressure stop

Owner reported C: capacity pressure. The one-worker native check was interrupted
during dependency compilation; no completed native check/build is claimed.
Source and native target are on E:, but TEMP/TMP point to C:/Users/matts/AppData/Local/Temp.
CARGO_HOME and RUSTUP_HOME were unset, so their normal user-profile locations
were used. The initial build setup therefore did not isolate all writes to E:.

Read-only volume check: C: approximately 38 GiB free, E: approximately 43 GiB,
D: approximately 236 GiB. C/D/E are separate physical disks. Do not bulk-relocate
caches into E: without capacity planning. Resume build only after resolving
scratch/cache placement. No global environment changes or cache deletion made.

- Filtered root dependency install completed: pnpm 10.34.5, frozen lockfile,
  ignore lifecycle scripts, network concurrency 2, child concurrency 1.
- Modified only fork `apps/client/src/lib/paste-helpers.ts` and its existing
  `apps/client/src/__tests__/lib/paste-helpers.test.ts` test file. Existing fork
  CLAUDE.md changes were preserved.
- Scoped Vitest: 16 tests passed. Fork TypeScript `tsc --noEmit`: passed.
- Missing conflict decisions no longer default to deletion/replacement. Skip is
  counted separately. Ordinary non-conflicting copy/move and keep-both remain.
- Replacement currently reports unsupported rather than deleting the destination;
  implement recoverable replacement before declaring conflict handling complete.
- Mixed-result cut clipboard reconciliation remains open: the caller currently
  clears all cut entries after any success. Native transfer race protection is
  not established by mocked tests.
- No native build/launch, provider connection, or actual file move verified yet.
  No server, indexer or background application left running by this work.

### Resumed integration — 2026-09-11

Owner authorized continuous parallel MVP implementation. Native runtime isolation,
selection-aware remote chat, and CocoIndex/Weaviate integration have separate
agent ownership; parent owns build setup and end-to-end verification.

- Pinned Rust 1.91.1 was copied (not moved) to
  `E:\AI_Workspace\.intake-dev\toolchains\1.91.1`; existing registry cache copied
  to task-local E: Cargo home. Shared C: caches remain untouched.
- Initial offline compile proved the host linker/Windows SDK environment was
  incomplete. Visual Studio's official developer shell exposes the linker;
  Microsoft SDK NuGet packages `Microsoft.Windows.SDK.CPP` and `.x64`, pinned
  at `10.0.28000.2705`, supply headers/libraries/tools under E: without a global
  installation. Package downloads total approximately 204 MiB compressed.
- Fork `scripts/intake-env.ps1` configures process-local E: tool/cache/temp/runtime
  paths and one Cargo worker. No persistent user/machine environment changes.
- Native offline compilation resumed; completion is still unverified.
- Combined scoped frontend verification: 20 tests passed (16 paste + 4 selection
  manifest). Manifest test covers 700 entries without automatic content reads.
- Isolated Vite frontend is serving HTTP 200 at `http://127.0.0.1:5176`.
  This is frontend availability, not a successful native desktop launch.
- Real Portkey synthetic probe: `http://100.72.169.40:8787/v1/chat/completions`
  with an inline config for remote `https://ollama.com/v1`, model
  `nemotron-3-super`, returned HTTP 200, content `OK`, finish reason `stop`.
  No corpus content submitted. Ultra probe timed out at 45 seconds; Super with
  128 output tokens returned empty content, while 1024 completed successfully.
  Credentials were read in memory from existing owner secret storage, never
  printed or copied into source. Saved config uses a literal environment reference.
- Recovered remote abstraction: Filestash over OpenList WebDAV, detailed in
  Probata `docs/planning/2026-09-08-cloud-services-phase-2-plan.md`. The accompanying
  TODO records OpenList/Drive/OneDrive setup and Filestash queued. This is dated
  documentation, not current deployment verification. Mounts remain an initial
  route and do not replace that abstraction.

### Integrated verification checkpoint — 2026-09-11, continued

- Main-agent combined frontend run: **35 tests passed across six files**:
  paste handling, selection manifest, filesystem-index SDK, chat index adapter,
  chat tool-loop integration, and the search panel. Synthetic/mocked boundaries;
  this is not a live desktop interaction test.
- Assistant `search_files` actions in Intake now call the combined index instead
  of recursively searching the filesystem. Three searches per response and five
  model iterations are bounded; source paths/identities survive tool feedback.
- Native Cargo check is still compiling dependencies with one worker. At this
  checkpoint C: had 101.8 GiB and E: 87.5 GiB free; no corpus worker was launched.
- Two live Weaviate instances responded in read-only readiness checks. The owner
  was asked to choose 8081 or 8082 for a dedicated Intake collection. No schema or
  existing evidence objects were modified while that choice remains outstanding.
- Installed Computer Use skill was inspected, but its required `node_repl`
  runtime is unavailable in this task. No automated desktop clicks or visual
  acceptance are claimed; native build/startup verification can proceed.

### Native check passed; executable build started

- Pinned Rust 1.91.1 `cargo check --locked --offline -j 1` passed after fixing
  two missing AppHandle borrows in `sync.rs`. Eleven warnings remain (unused
  imports/dead code); no automated broad `cargo fix` was applied.
- Actual environment preflight confirmed rustc, Cargo, Cargo home, target,
  TEMP/TMP and runtime paths all on E:. VS developer-shell initialization emits
  a missing-file message before the explicit NuGet SDK override; linker/header
  checks and compilation subsequently succeed. This warning is not concealed.
- Launcher execution caught duplicate Node resolutions in PATH; select the first
  resolved executable explicitly instead of passing an array to Start-Process.
- Only the task-owned frontend PID19660 was stopped after command/start-time
  verification. Replacement frontend PID23740 serves HTTP200 on loopback5176.
- Native executable build started through Tauri with the Intake configuration,
  remote chat configuration and isolated runtime. Desktop window/interaction is
  not yet verified. No other application's process or mount was stopped.
- Main reran all four new backend suites: **36 passed in 2.39 seconds**.

### Native launch proof — 2026-09-11 21:19 EDT

- Tauri executable build finished successfully in 8m51s, with one compiler worker.
- `xplorer.exe` PID23268, built in the E: fork, exposes window
  **Intake — File Workstation**. Windows reports `Responding=True`; observed
  native working set 35–49 MiB (not total WebView/child-process memory).
- WebView parent and child command lines point to
  `E:\AI_Workspace\.intake-dev\runtime\webview`; runtime app/local/roaming data
  directories and instance lock are under the same E: runtime root.
- A second explicit native launch with the same profile failed before startup
  with the expected OS-lock error and exit1. Original app remained responding.
- Integrated scoped frontend runs total **66 passing tests** (35 selection/search/
  paste, 22 sidebar/context, 9 per-pane selection). Final TypeScript check passed.
- Main reran five backend suites including occurrence identities: **40 passed
  in 2.02 seconds**. Matching bytes from independent stores retain distinct
  occurrences; V:/Y: alias identity converges without mount access.
- Native unit tests are in progress. Offline attempt identified missing locked
  `tokio-test`0.4.5; the subsequent locked test invocation downloaded that declared
  dependency to E: and compiles with test debug information disabled.
- Startup exposed an inherited upstream updater request returning an error.
  Intake-profile suppression is assigned; no update was installed.
- This proves native startup/process/profile isolation, not visual rendering or
  click-through acceptance. Computer Use runtime is unavailable. The first real
  selection-to-chat and live Weaviate round trips remain explicit verification.

### Final verification checkpoint — 2026-09-11 21:25 EDT

- Native scoped tests passed: runtime paths2, filesystem bridge3, Portkey config2.
  Only those seven tests ran; the remainder of the native test suite was filtered.
- Native binary Cargo check passed after the updater-registration guard.
- Updater hook tests4 passed in the main rerun. Total scoped frontend checks now
  **70 passed**, with **40 backend** and **7 native** tests; not a full-suite claim.
- Intake frontend schedules no upstream update timers and blocks manual
  check/install. Native updater plugin is absent in Intake mode in current source,
  but the open window uses the previous executable. The plugin-level gate applies
  after the next rebuild/launch; current window was not interrupted to apply it.
- Native window remained responding. Seven observed app/WebView processes used
  approximately **470 MiB combined working set**. Vite/build-launch parent memory
  is additional. C:101.7 GiB and E:85.7 GiB free at this checkpoint.
- Native app PID23268 and its task-owned frontend PID23740 are deliberately left
  running for owner testing. Cargo's dev-run parent remains attached but no
  compiler is active. No corpus indexing service or local inference was launched.
- Launcher PowerShell parse check: zero errors. Future launch command is in
  DEVELOPMENT.md; close the currently running Intake window before rebuilding
  changed native source. Do not terminate other applications or mounts.
- Outstanding external prerequisites: select physical Weaviate instance for a
  separate Intake collection, then execute the bounded fictional live proof.
  Full multimodal index, graph and remote abstraction are not declared finished.
