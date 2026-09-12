# OneDrive Case Bible — root cleanup move-map (Phase 1: corral)

> _Byline: Claude Code · Fable 5 · 2026-07-11_ · **EXECUTED 2026-07-11** — 956/956 moves OK, 0 failed.
> Ledger (undo map): `onedrive-root-cleanup-ledger.csv` (this dir). Script:
> `../scripts/onedrive-root-corral.ps1`. All moves were same-volume renames inside
> `C:\Users\matts\OneDrive\Case Bible` — server-side for OneDrive, zero re-upload, zero hydration,
> **nothing deleted**.

## What changed

Root went from **97 dirs + 873 loose files** to **15 entries**:

| Kept at root (untouched) | Why |
|---|---|
| `INBOX\` | working intake |
| `_SWEPT\` | NEW — the corral (see below) |
| `_TO_BE_DELETED\`, `_system\` | protected quarantine / state |
| `.claude .infio_json_db .memsearch .obsidian .remember .smart-env .tmp.*` | tool/OneDrive state |
| `.agentignore .obsidianignore .directory` | root config files |

| Moved (956 total) | Count | Destination |
|---|---|---|
| Content dirs (names preserved verbatim) | 71 | `_SWEPT\<name>` |
| Sync-conflict "`1`" clones, `_DUPLICATE`, `(2)` copies, empties | 15 | `_SWEPT\_sync-conflicts\<name>` |
| Loose root content files | 751 | `_SWEPT\_root-loose\` |
| Recycle-bin dump artifacts (`$I…`/`$R…`) | 119 | `_SWEPT\_root-loose\_recycle-artifacts\` |

## Notes

- Clone pairs were verified NOT to be subsets (e.g. `Takeout Data1` = 24,761 files vs primary 111)
  — nothing merged in this phase. Merge is Phase 2, gated on the owner-reviewed merge-plan table.
- Any tooling keyed to old paths (e.g. the SORT ② NEW-set list, sweep path correspondence) can be
  remapped through the ledger CSV (`old_path,new_path`).
- R2 `casebible-sorted` remains canonical; this was local hygiene only.
