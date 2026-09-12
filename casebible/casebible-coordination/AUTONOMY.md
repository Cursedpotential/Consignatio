# AUTONOMY — autonomous-mode loop protocol
> _Byline: Claude Code · Opus 4.8 · 2026-06-25_ · **LOCAL ONLY.** Read this every pass.

This is the operating doc for running the 3 lanes **unattended** while the human is away, with a
**4th chat (ORCHESTRATOR)** coordinating on top. It extends `README.md` — the ownership, lock, and
append-only rules there still apply. On any conflict, `README.md` wins.

## The shape
- **3 peers** (SORT / PROCESS / PIPELINE) each run a self-paced `/loop` in their own terminal.
- **1 ORCHESTRATOR** (the 4th chat) runs its own self-paced `/loop`: it relays, sequences work into
  `TASKS.md`, triages `APPROVALS.md`, resolves lock conflicts, and rolls progress into `BOARD.md`.
- Nobody can inject into another terminal. **Coordination is 100% filesystem** — that's why every
  pass begins by re-reading the whole folder (this is what replaces the human as the relay).

## One pass (every lane, every loop iteration)
1. **Read the whole board**: `README.md`, this file, `BOARD.md`, `LOG.md` (new lines), `LOCKS.md`,
   `TASKS.md`, all `status/*`.
2. **Service inbound**: act on any `TASKS.md` directive or `LOG.md` line addressed to your lane.
3. **Advance your lane by ONE step** that is **reversible and local** (drafting, code, ledgers,
   plans, dry-runs, read-only checks).
4. **Gate the risky stuff** — see §Gating. Don't execute it; queue it to `APPROVALS.md` and do other
   safe work instead.
5. **Report**: update `status/<you>.md`; append a signed progress/handoff line to `LOG.md`.
6. **Respect `LOCKS.md`** — never act on a resource another lane holds.
7. **Decide continue vs stop** — see §The continue/stop decision.

> **Test-visibility rule (owner mandate, 2026-06-27):** any verification/test/dry-run a lane
> executes MUST be saved to a **shared, owner-visible path** (`casebible-coordination/specs/` or
> `status/`) — the harness AND the full output (counts, hashes, breakdowns, caveats) — and linked in
> `LOG.md`. NEVER leave a test only in a private session scratchpad. The owner reviews every such test.

> **Durable-write code rule (owner mandate, 2026-07-02):** any code that WRITES durable data
> (prod PG/Milvus/Neo4j, R2, ledgers the pipeline consumes) MUST be persisted to a tracked path
> (`casebible-coordination/specs/` or the repo) **BEFORE it runs**, and executed FROM that path —
> never from a session scratchpad. The code is part of the evidence's provenance. Record the
> spec/repo path (+ file sha256 or git sha) in the run's `LOG.md` line and, for DB runs, in
> `analysis.processing_run` (code_ref). Recipes/algorithms additionally get a canon entry with
> test vectors (see specs/canon-registry-0007-DRAFT.sql). Root cause: the 2026-06-26 pilot's H2
> hash recipe ran from a scratchpad and is now LOST — chain-verifiable, never again recomputable.
> Enforced client-side by the case-bible plugin hook `require_tracked_code.py` (v0.5.1).

## Gating (orchestrator-judged)
**Auto-allowed (run it):** anything reversible and local — code, docs, ADRs, ledgers, reconciliation,
plans, local tests, read-only inspections.

**GATED — do NOT run; append to `APPROVALS.md`:** any **prod/infra write** (OVH, Coolify, DBs),
any **R2 / cloud transfer** (copy/move/sync/up/download — billable Class-A ops count), any **delete**,
any **deploy**, anything with a **$ cost**. Each gated entry must include: exact command, why,
blast radius, and reversibility.

**Shared git repo guardrail (added 2026-06-25 06:53):** the working repo root is **`E:/AI_Workspace`**
(the *whole* workspace is one git repo). It currently has **110 untracked files** incl. auto-generated
`Workspace_Manifest_*.json` and an **uncommitted root `.gitignore`**. So: **NO autonomous broad git ops
in this repo** — no `git add -A` / `git add .`, no `commit` / `push` / `clean` / `reset` /
`checkout --` / `restore`. A scoped `git add <your own specific artifact>` is fine; anything broader is
gated. Cleaning the tree (commit a root `.gitignore`, decide External/Scripts/Timeline_Tools, stale per
the no-delete rule) is a separate **owner-decision** task — draft a proposal if idle, don't execute.

The **ORCHESTRATOR** triages `APPROVALS.md`: items that are genuinely reversible-and-local (a peer
over-escalated) get greenlit by moving them to `TASKS.md`; genuine prod / cloud-transfer / delete / $
items **stay in `APPROVALS.md` for the human** — the orchestrator does **not** approve those on the
human's behalf. (Mirrors the human's hard rules: verify before claiming; dry-run + sign-off before
any transfer; confirm before destructive/prod actions.)

## The continue/stop decision (end of every pass)
Pick exactly one and act on it:

- **CONTINUE (~5 min):** you did actionable work this pass, OR there's actionable work queued for you
  now → schedule the next check in ~5 minutes (use ~270s to keep cache warm/cheaper). Reset your
  idle counter.
- **CONTINUE while waiting (~5 min):** you're holding/blocked but **waiting on another lane, a freeze
  window, an `APPROVALS.md` decision, or the human** → keep looping (nobody can restart you if you
  stop). Increment your idle counter.
- **BACK OFF (~20 min):** idle counter ≥ 3 (≈15 min, nothing changed for you) → widen checks to
  ~20 min to save tokens; note "low-frequency holding" in your `status`. Drop back to ~5 min the
  moment anything actionable appears.
- **STOP:** your lane is **fully complete** — no next step, no open dependency, and nothing depends on
  you waking → append `LANE complete — loop stopped` to `LOG.md` and end the loop. The human
  re-pastes the prompt to restart you if needed.

> Rule of thumb: **stop only when truly finished; otherwise keep looping (or back off).** A lane that
> is merely *waiting* must NOT stop — it has no way to be woken.

## Loop prompts (paste one per terminal) — updated 2026-07-01
Self-paced (no fixed interval) so the continue/stop decision above governs cadence.
**OPEN each chat in the E: Agno-MVP workspace** `E:\AI_Workspace\Projects\the-platform-workspace` (project memory / logs / conversation history key off it). The **board is `D:\casebible\casebible-coordination`**. `C:\Users\matts\OneDrive\Case Bible` stays a **canonical working source** (read/write), just not the opening dir. Never put coordination or memory under `C:\Users\matts\…`.

**🟦 SORT**
```
/loop You are the SORT lane. Opened in the E: Agno-MVP workspace (project memory/logs/history live here; OneDrive Case Bible is a canonical working source). Read the war-room board D:\casebible\casebible-coordination IN FULL every pass — especially BOARD.md's 2026-07-01 RESUME block — and follow AUTONOMY.md exactly. Do one pass, then make the continue/stop decision.
```
**🟩 PROCESS**
```
/loop You are the PROCESS lane. Opened in the E: Agno-MVP workspace (project memory/logs/history live here; OneDrive Case Bible is a canonical working source). Read the war-room board D:\casebible\casebible-coordination IN FULL every pass — especially BOARD.md's 2026-07-01 RESUME block — and follow AUTONOMY.md exactly. Do one pass, then make the continue/stop decision.
```
**🟥 PIPELINE**
```
/loop You are the PIPELINE lane. Opened in the E: Agno-MVP workspace (you own the Agno-MCP-Platform repo + the forensic-DB build). Read the war-room board D:\casebible\casebible-coordination IN FULL every pass — especially BOARD.md's 2026-07-01 RESUME block — and follow AUTONOMY.md exactly. Do one pass, then make the continue/stop decision.
```
**🟪 ORCHESTRATOR**
```
/loop You are the ORCHESTRATOR lane. Opened in the E: Agno-MVP workspace. Read the war-room board D:\casebible\casebible-coordination IN FULL every pass — especially BOARD.md's 2026-07-01 RESUME block — and follow AUTONOMY.md exactly (relay, sequence TASKS.md, triage APPROVALS.md, resolve LOCKS.md, roll BOARD.md; greenlight reversible/local, escalate prod/$/delete/cloud-transfer to the owner, never execute prod). Do one pass, then make the continue/stop decision.
```

## Handing control back
Stop each loop (interrupt the `/loop` in each terminal), then read **`APPROVALS.md`** top-to-bottom —
that's the queue of everything that waited on you. `BOARD.md` shows where each lane landed.
