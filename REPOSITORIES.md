# Consignatio — private repository map

Owner-authorized source backup, 2026-09-11. This is a Git checkpoint, not a claim
that the application MVP or live combined-index proof is complete.

| Source | Private repository | Branch / checkpoint |
|---|---|---|
| Vault plans, Intake UI/backend, original development tools | https://github.com/Cursedpotential/Consignatio | `main`; source-only root `aa3b9bc7` plus publication documentation |
| Native Intake desktop (Xplorer fork) | https://github.com/Cursedpotential/Intake-desktop | `feat/acp-copilot`, `6990b7ed` |
| Existing Xplorer build kit | https://github.com/Cursedpotential/xplorer-copilot-buildkit | `main`, `d0954e37` |
| Repair toolkit source | https://github.com/Cursedpotential/Consignatio | `main`, under `repair-tool-kit/`; source-only integration from local `cfe951a` and its preserved working changes |

## Recreate the application checkout

Use an empty destination on E:. These child repositories are intentionally
independent and ignored by the parent; cloning the parent alone does not obtain
the native desktop. Do not run these commands over existing working directories.

```powershell
cd "E:\AI_Workspace\Projects\Propria" && gh repo clone Cursedpotential/Consignatio Consignatio
cd "E:\AI_Workspace\Projects\Propria\Consignatio" && gh repo clone Cursedpotential/Intake-desktop Intake/xplorer-copilot-buildkit/xplorer-copilot -- --branch feat/acp-copilot
cd "E:\AI_Workspace\Projects\Propria\Consignatio" && gh repo clone Cursedpotential/xplorer-copilot-buildkit Intake/xplorer-copilot-buildkit/xplorer-copilot-buildkit
```

Existing desktop checkout uses remote `private` for pushes and branch tracking.
Its public `origin` and upstream remain available for fetching only. A fresh clone
from Intake-desktop naturally uses the private repository as `origin` instead.

## Local history is preserved, not published

The original parent root commit `161d3c4` contained 879 imported conversation/corpus
files. It was explicitly local-only. The new `main` starts from a source-only root;
the original commit and relocation staging are preserved locally under
`local-archive/pre-private-publication-20260911` at `01ac582e`.
No working files were removed or restored over user edits.

The linked worktree `repair-tool-kit-codex/` stays on local `codex/casekit-ab` at
`cfe951a`, preserving its inherited history. Its 36 new source files were committed
locally and exported as a separate source-only root on `repair-toolkit-snapshot`.
The snapshot branch remains a historical backup. On 2026-09-20 the module source
was copied into main under `repair-tool-kit/`, including its tested engine additions,
without merging the archival ancestry. Existing planning files remain, with the
original plan README in `repair-tool-kit/BUILD-KIT-README.md`. Do not push or merge
`codex/casekit-ab` or the archival branch.

**Never use `git push --all` or `git push --mirror` here.** Push named source branches
only. The old corpus history is not part of the private source backup.

## Excluded from publication

Imported corpus, evidence bytes, ledger caches, databases, generated indexes,
copy-operation reports, local agent memories, runtime/build/dependency directories,
environment credentials and quarantine directories stay on disk and are ignored.
Original development scripts, schema/design documents and plans remain included.
Private source backup is not a backup of the owner's evidence corpus or credentials.

## Verification receipt

- Gitleaks 8.30.1 official Windows release, archive SHA-256 matched release checksum.
- Source-only parent root: 1 commit / approximately 3.46 MB scanned; no findings.
- Desktop inherited history: 1,172 commits / approximately 30.09 MB; no findings.
- Desktop staged implementation: approximately 116.59 KB; no findings.
- Repair toolkit staged source: approximately 177.07 KB; no findings.
- Reports are redacted and stay locally under
  `E:\AI_Workspace\.intake-dev\repo-audit`; credentials were not rotated or printed.
- Secret scanning is a bounded check, not proof that arbitrary content cannot
  contain sensitive information. Corpus directories were excluded independently.
- No application build, service restart, corpus scan or model workload was started
  as part of Git publication. Prior scoped test results remain in the Intake handoff.

Continue application work from
`Intake/docs/HANDOFF-2026-09-11-INTAKE-NATIVE-AND-INDEX.md`.
