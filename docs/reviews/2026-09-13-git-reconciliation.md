# Consignatio Git reconciliation — 2026-09-13

This receipt records preservation of the dirty canonical checkout at
`E:/AI_Workspace/Projects/Propria/Consignatio`. The work began from local `main`
at `fa4f249a5c9d69bb7964ea851e71e8cecbab08a9`, two commits behind
`origin/main` at `1db6e9dd07a1044db3204d9efa92d3fcedf28331`.

The 52 reported dirty paths were preserved on
`codex/consignatio-preserve-20260913` and classified before staging:

| Group | Paths | Treatment |
|---|---|---|
| Repository and Intake routing | root and Intake `AGENTS.md` / `AGENT_MEMORY.md`, current architecture and plan documents | Review and commit as one documentation group |
| Intake Surreal graph/runtime | backend source, migrations, deployment definitions, runbooks, tests, dependency metadata, and verification receipts | Scan, test, and commit as one implementation group |
| Case Bible atomic grouping | schema, staged-path SQL, detection SQL, and the associated handoff | Review and commit as one SQL/documentation group |
| Repair-tool-kit session output | `repair-tool-kit/COMPACT-SUMMARY-2026-09-12.md` | Keep local and exclude from Git; this is generated PostCompact hook payload rather than product documentation |
| Local runtime artifact | root `version` file | Keep local and exclude from Git; binary inspection identifies a DuckDB database, not source |

Safety boundaries used throughout:

- No reset, clean, stash, broad stage, deletion, or source overwrite.
- No corpus/evidence bytes, credentials, generated databases, indexes, caches, or
  `to_be_deleted` contents may enter a commit.
- Each commit stages an explicit path list after a sensitive-content and diff check.
- Reconciliation with `origin/main` occurs only after the local groups are committed.
- The existing `codex/r2-b2-migration-reconcile-20260913` linked worktree and its
  branch are preserved; this lane does not move or rewrite that worktree.

## Validation record

- `17b578f` preserves the repository and Intake routing/documentation group.
- `89ccb2b` preserves the Intake Surreal graph/runtime group. The backend suite passed
  all 107 tests after formatting the changed Python files; Ruff checks passed for
  every changed Python source and test in that group.
- `cce9e52` preserves the Case Bible atomic grouping schema, staged-path SQL,
  detection SQL, and handoff. Static review found no credential pattern. The SQL
  `DROP` uses are limited to replacing two constraints and dropping temporary
  tables on transaction completion; the scripts contain no persistent-data deletion.
- A high-confidence credential scan across all publishable changed files found no
  private key, common provider token, or credential-bearing URL pattern.
- `repair-tool-kit/COMPACT-SUMMARY-2026-09-12.md` and root `version` remain present
  locally and are ignored. The latter is a 12,288-byte DuckDB runtime database.

Upstream reconciliation and push proof remain pending.
