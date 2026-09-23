# Open decisions

**Unresolved. Resolve in-session with Claude Code or Codex, then update the
files listed and delete the entry from here.**

Everything else in this kit is internally consistent as of 2026-09-11. These
are the points where the kit either contradicts itself, contradicts another
governing document, or was never decided.

---

## OD-1 · Install root — D: or E:

**Conflict.** `STACK.md` and `TOOL-CATALOG.md` say `D:\case_apps`, attributed
to Matt, 2026-09-11. The Consignatio `AGENTS.md` storage rule of the same date
designates **E:** as the development drive and says not to substitute D:
without owner direction.

Scope is larger than an install path — it governs the whole vendored
toolchain: poppler, qpdf, duckdb, the frozen `uv` venv, optional tesseract.
Order 1–2 GB. Also sets the package output root and the venv depth (B-4).

Free space: D: 192 GB · E: 85 GB.

**Files to update once decided:** `STACK.md`, `TOOL-CATALOG.md`, `KICKOFF.md`,
`PROMPTS.md` (Phase 0), `scaffold/internal/config/config.go`, `CLAUDE.md`.

## OD-2 · Go module root

casekit is a module inside Consignatio's Case Bible lane, not a standalone
product. `CLAUDE.md` assumes the repo root is the module root. Where does
`go.mod` actually live?

**Files to update:** `CLAUDE.md`, `PROMPTS.md` (Phase 0), `scaffold/go.mod`.

## OD-3 · Derivation-block granularity — R11 vs R2

`RULES.md` R11 mandates a six-field `derivation` block plus `remediation` and
`status` on every derived value. `RULES.md` R2 says don't gold-plate.

Two sub-questions, both Matt's to answer:

1. Does a `text_run` read straight out of `pdftotext` need a derivation block?
   (Plain reading of R11: no — it was *read*, not *derived*.)
2. Is the unit per-element or per-run?

Answer changes Phase 4 output size by roughly an order of magnitude.

**Files to update:** `scaffold/docs/DERIVATION.md`, `PROMPTS.md` (Phase 4),
`PHASES.md` (Phase 4).

## OD-4 · Reference file locations

Four files carry every exit criterion in Phases 2–5 and are not in the kit:

- `_18102689630__1___1_.pdf` — 36,025 B, sha256 `f18e250e5aca784f…`
- `Copy_of_sms-20221104021809.xml` — 3,852,198 B, sha256 `55515f2a490c9a0a…`
- `sms.xsd` — synctech vendor schema
- `Fields in XML backup files.md` — synctech vendor field docs

All four to `docs/reference/`. Without them nothing validates.

## OD-5 · Install permission

Phase 0 needs: DuckDB `webbed` community extension (writes to
`~/.duckdb`), a full poppler distribution (the only `pdftotext` on the machine
is an incidental Git-for-Windows v4.00 with no `pdfimages`/`pdfdetach`), and
qpdf 11.9.x. All vendored under the OD-1 root.

## OD-6 · Governance precedence

The global `CLAUDE.md` carries rules that collide with this kit — a mandatory
`docs/planning/<date>-TODO.md` updated every turn, and mandatory skill
invocation per turn. Kit `RULES.md` R0/R4 say no file creation without approval
and no process accretion.

Which governs inside this project? Neither agent should guess.

## OD-7 · Corpus scale gate

`FINDINGS.md` is written against a 3.85 MB XML. The real exports in
`…\Messages with Katrina` are **832 MB** — 216× larger — plus 2.77 GB and
1.52 GB zips, ~6.8 GiB total. `xml_extract_attributes` already OOM'd at
3.1 GiB on the *small* one (S-3).

Phase 5's exit criterion is a valid unit test and is **not** representative of
the target. A scale gate belongs somewhere in Phases 5/5b. Also: `V:` is a
network/cloud mount — listing is free, reading 6.8 GB is not.

Two files, `sms-11-08-2022 14-44-57.xml` and `sms-11-08-2022 14-46-06.xml`, are
byte-size-identical and 90 seconds apart. Likely the first real duplicate-source
case.

---

# Fixed in this revision — do not re-raise

| Was | Now |
|---|---|
| STACK rejected mutool; Phase 3 required running it | mutool is a **frozen test fixture**, not a shipped engine. Phase 3 escalation is proven against its recorded known-bad output. Not required to be installed. |
| Phase 0 exit criterion required a shell verb (Phase 7) | Phase 0 tests console flash via `.lnk` and `cmd /c start`. No registry verb in Phase 0. |
| A-6 covered only the parent process | A-6 now covers child processes — every `exec.Cmd` needs `SysProcAttr{HideWindow:true}`. Stdlib, no new dependency. |
| `offset` had no coordinate space; broke R11 traceability for PDF | New **S-16**. Contract carries `offset_space` (`source_file` \| `decoded_stream`) plus a `container` block. Named as SPLIT sync point #1. |
| ZIP sequenced after JSON, contradicting PHASES' own reasoning | Reordered: 5 → **5b ZIP** → **5c JSON** → 5d HTML/text. Both `PHASES.md` and `PROMPTS.md` physically reordered. |
| TOOL-CATALOG said tesseract was Phase 10 | Corrected to **Phase 6c**, inside the usable product. |
| poppler bake-off presented as settled | Marked **[sandbox-verified]** in `STACK.md` and `FINDINGS.md`. Phase 0 re-runs it against the pinned Windows binary and records version + path. |
