# Case Bible — Multi-Agent Coordination Board
> _Byline: Claude Code · Opus 4.8 · 2026-06-25_ · **LOCAL ONLY — do not sync to cloud, no secrets here (secrets live in `~/.secrets`).**

A shared filesystem "war room" for the **3 Case Bible agents** on this dev box. The agents run as
separate chats and **cannot message each other** — they cooperate by reading/writing this folder.
The human relays when needed. Everything here is plain markdown (minimize-custom-code).

## The three agents (lanes)
> **PATHS (2026-07-01):** ALL lanes **open in `E:\AI_Workspace\Projects\the-platform-workspace`** (project memory/logs/history key off it). The **board is `D:\casebible\casebible-coordination`**. `C:\Users\matts\OneDrive\Case Bible` stays a **canonical working source** (read/write), just not the opening dir. Nothing under `C:\Users\matts\…` is used for coordination or memory. The old `C:\Users\matts\casebible-coordination` is retired.

| Chat | opens in | working areas | Mandate |
|---|---|---|---|
| 🟦 **SORT** | `E:\…\the-platform-workspace` | OneDrive Case Bible (source) · R2 `casebible-raw/-sorted/-quarantine` · `D:\casebible` catalog | Raw → clean, deduped, **type-organized** `casebible-sorted` vault (+ ovh2 enrichment, ledger, quarantine). |
| 🟩 **PROCESS** | `E:\…\the-platform-workspace` | `casebible-sorted` (read-only) · live PG/Neo4j/Milvus | Read `casebible-sorted` → run the evidence pipeline → populate + **verify** evidence/knowledge/graph. |
| 🟥 **PIPELINE** | `E:\…\the-platform-workspace` | Agno-MCP-Platform repo · OVH infra · Coolify | Build & operate the **agno platform machinery** (infra, parsers, custody/HITL, graph wiring). Owns the platform repo + ADRs. |

## Ownership (who writes what)
| Resource | Sole writer | Readers |
|---|---|---|
| `casebible-sorted` (R2) + sort ledger + `casebible-raw/-quarantine` | **SORT** | PROCESS (read-only) |
| ovh2 enrichment PG | **SORT** | — |
| Milvus `casebible_ai_conversations` | **SORT** | — |
| Milvus `casebible_evidence`, Neo4j `group_id="casebible"`, `casebible-evidence` bucket | **PROCESS** | — |
| agno PG/SurrealDB/Milvus/Neo4j **infra**, Coolify, OVH-1/3, `Agno-MCP-Platform` repo+ADRs, `evidence/*` code | **PIPELINE** | PROCESS (runs it, doesn't edit) |

## The one rule that prevents most collisions
`casebible-sorted` has **exactly one writer (SORT)** and **one reader (PROCESS, read-only)**. PROCESS
only **bulk-reads inside a SORT-announced freeze window** (claimed in `LOCKS.md`).

## Protocol
1. **Before touching any shared resource, read this whole folder** (`BOARD.md`, `LOCKS.md`, others' `status/*`).
2. Write **only your own** `status/<you>.md` — update it whenever your state changes.
3. To claim/freeze a shared resource, **append** a signed line to `LOCKS.md`; release it by appending a `RELEASE`. Don't act on a resource someone else holds.
4. Cross-agent messages / handoffs / "done, your turn" → **append** to `LOG.md`. This is the shared chat.
5. `LOCKS.md` and `LOG.md` are **append-only** — never rewrite another agent's lines.
6. Sign every appended line: `[YYYY-MM-DD HH:MM] AGENT: message`.

## Files
- `BOARD.md` — at-a-glance current state (phase, top blocker).
- `LOG.md` — append-only cross-agent messages (the shared chat).
- `LOCKS.md` — append-only resource claims / freeze windows.
- `status/{sort,process,pipeline,orchestrator}.md` — each agent owns one; reads all.
- `AUTONOMY.md` — autonomous-mode loop protocol (read every pass when looping).
- `TASKS.md` — directives from ORCHESTRATOR to the lanes (append-only).
- `APPROVALS.md` — gated actions waiting on the human (append-only).

## Autonomous mode (human away)
When the human leaves, the 3 lanes run a self-paced `/loop` and a **4th chat (ORCHESTRATOR)**
coordinates on top. Full protocol — one-pass steps, gating rules, the ~5-min continue/stop/back-off
decision, and the paste-in loop prompts — lives in **`AUTONOMY.md`**. Key invariants: coordination
stays filesystem-only (each pass re-reads the folder = the relay); only reversible/local work runs
unattended; prod / cloud-transfer / delete / $ actions are queued to `APPROVALS.md` for the human;
a lane that's merely *waiting* keeps looping (it can't be woken if it stops).
