# Consignatio — agent contract

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: record three-system boundary | Context: explicit owner clarification -->

**Owner decision — 2026-09-12:** CCC means project-local CocoIndex Code indexes only. Intake is the multifaceted CocoIndex-based filesystem workstation, using Weaviate for advanced search and SurrealDB for relationships, with multimodal tools/libraries (OCR, STT, video transcription/processing, advanced SLM extraction/classification). Docstore is CocoIndex + SurrealDB for project documentation. Keep their apps, tracking state, locks, configuration and target ownership isolated; shared technology is not a shared runtime. This defines scope, not proof every feature is implemented.

See [CCC / Intake / Docstore boundaries](../SYSTEM-BOUNDARIES.md) for indexing eligibility, duplicate provenance and the human-agent organizing workflow.

`E:\AI_Workspace\Projects\Propria\Consignatio` is an independent product repository inside the
`E:\AI_Workspace` repository router. Product code, documentation, tests, and
ordinary commits belong to this child repository, never to the parent router.

## Safety

- **Owner standing storage rule (2026-09-11): E: is the designated development
  drive.** Project files, dependency downloads, tool caches, build outputs,
  runtime data and job temporary files must use E:, not the Windows C: drive.
  Check effective paths before installations/builds, including child processes,
  TEMP/TMP, Cargo/Rustup, npm/pnpm and Python/uv caches. No silent fallback to C:.
  If a tool cannot comply or E: lacks space, stop that operation and report it.
  Do not substitute D: without owner direction. Existing shared caches require
  a verified, coordinated relocation; never move active stores blindly.
  This is a rule for agent-controlled workloads, not a claim that Windows or
  third-party applications perform zero incidental writes to C:.

- Never permanently delete files. Move material that must be removed into this
  repository's `to_be_deleted/` directory; only the owner may delete from there.
- Never reset, clean, stash, broad-stage, or overwrite concurrent work.
- Never stage evidence bytes, databases, generated indexes, exports, credentials,
  or machine-local configuration.
- Before staging or committing, run `git rev-parse --show-toplevel` from the target
  path and confirm it resolves to `E:/AI_Workspace/Projects/Propria/Consignatio`.
- Stage only explicit, reviewed paths. Never use `git add .` or `git add -A`.
- Never initiate host reboot, restart, shutdown, sleep, hibernation or logoff.
- Do not hydrate cloud placeholders, scan a corpus, start recurring workers or
  run local model inference as an incidental development step. Use small explicit
  fixtures, bounded concurrency, timeouts and per-instance state.

## Load order and execution

Read `AGENT_MEMORY.md` next; it routes to the specific application or legacy lane.
Load applicable installed skills before implementation, especially user-named
skills. If unavailable, identify that limitation rather than pretending to use them.
Use the current request as the scope: diagnosis is read-only; authorized builds
should reach a tested slice without repeatedly asking permission for ordinary edits.
Do not replace approved technologies or expand scope without owner approval.
Keep plans, implementation and verified results distinct. Record material work in
the lane's development receipt and TODO. Never label a simulated job as real work.

## Authority boundary

The live filesystem organizer is stage one. Its browsing, search, grouping and
user-directed file operations do not require evidence acceptance or candidate
review. The following evidence/review boundaries apply when working in those
downstream workflows, not as a prohibition on organizing the owner's files.
Intake's filesystem CocoIndex app and Surreal database are separate from the
downstream evidence index and evidence-analysis database.

- PostgreSQL and governed custody workflows remain canonical for Platform state.
- The Workbench is a human review and orchestration surface, not a second evidence
  store or approval authority.
- Source media in Immich or PhotoPrism remains unchanged unless a separately
  approved, receipt-producing connector action says otherwise.
- Imported source values are immutable. Human annotations and machine proposals
  live in separate, provenance-bearing overlays.

## Application

The desktop Intake application lives under `Intake/`, with its corpus backend in
`Intake/backend/`. The original deduplication, metadata and vault-structure work is
preserved under `casebible/`, alongside Intake. Read `Intake/docs/` before
changing its contracts or interface. Keep the browser UI usable independently of
the Tauri host; privileged filesystem and process operations must pass through
explicit, least-privilege native commands.

## Child repositories

`Intake/xplorer-copilot-buildkit/` holds two independent Git roots, ignored by this repository
(`.gitignore`, ignore-only, no gitlink). Commit inside the child, never here.

| Child | Path | Remote | Rule |
|---|---|---|---|
| Xplorer copilot build kit | `Intake/xplorer-copilot-buildkit/xplorer-copilot-buildkit/` | `Cursedpotential/xplorer-copilot-buildkit` (private) | own `CLAUDE.md`; push to `origin` only |
| Xplorer fork (`xplorer-copilot`) | `Intake/xplorer-copilot-buildkit/xplorer-copilot/` | `private` = `Cursedpotential/Intake-desktop`; public `origin` and `upstream` are fetch-only | push Intake work to `private` only; active branch `feat/acp-copilot` |

Private source publication is documented in `REPOSITORIES.md`. Never push all
branches or mirror this repository: local archival branches contain imported
corpus history intentionally excluded from GitHub. `repair-tool-kit-codex/` is
a linked local worktree, not an independent repository; preserve its branch.

> _Byline amendment: Claude Code · Fable 5.1 · 2026-09-09 — added Child repositories section for the Xplorer copilot kit and fork._

## Claude-Reflect Learnings

<!-- Auto-generated by claude-reflect. Do not edit this section manually. -->

### Project Conventions
- Receipts, catalog exports, hash ledgers and missing lists live in `docs/receipts/` (payloads gitignored); never a workspace-root scratch folder. (owner 2026-09-15)
- One log: `docs/URGENT-TODO.md`. Record a change there once; no README/memory/handoff fan-out of the same fact. (owner 2026-09-15)
- Fix known bugs in our own apps instead of working around them; if blocked, package the patch with proof and name the blocker. (owner 2026-09-15)

<!-- End claude-reflect section -->
