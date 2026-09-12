# Stack Decision — casekit

Research date: 2026-09-11. Versions below were either searched this session or
verified by execution in a sandbox this session (marked **[verified]**).

## Application type

A **local-first CLI tool with a daemon mode** for Windows, plus a Linux build
for a remote box. Not a website. It is invoked from the Windows Explorer
context menu, orchestrates external processes, and writes files to disk.

## Chosen stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Orchestrator | **Go** | 1.26.x (1.26.0 rel. 2026-02-10; 1.26.4 rel. 2026-06-02) | Single static binary, trivial Windows+Linux cross-compile, goroutine model fits subprocess pools |
| Remote transport | **tsnet** (`tailscale.com/tsnet`) | v1.102.0, BSD-3-Clause | Embeds a full Tailscale node *in-process* — no `tailscaled`, no open ports, identity + ACLs for free |
| Query / analytics | **DuckDB** | 1.5.5 **[verified]** | Already installed globally on Matt's machine; reads Parquet/JSON natively |
| XML ingestion | **DuckDB `webbed` extension** | community **[verified]** | `INSTALL webbed FROM community` → `read_xml()` parsed the real 231-message export correctly |
| PDF text (primary) | **poppler** `pdftotext` | **[verified]** | Correctly decoded all 33 ZapfDingbats glyphs; CLI-only, no runtime |
| PDF text (secondary) | **pypdf** | 6.17.0 (2026-09-04) | Same correct result, pure Python, no native deps; also reads metadata/attachments |
| PDF render/raster | **pdfium** via `pypdfium2` | **[verified]** | Correct glyphs; needed for screenshot-class PDFs and OCR input |
| PDF structure | **qpdf** | 11.9.0 **[verified]** | `--check`, `--qdf`, object graph, xref, encryption |
| XML pre-pass | **lxml** | **[verified]** | Streaming blob strip; handles base64 that regex corrupts |
| Python runtime | **uv**-managed frozen venv | — | Vendored under install root; no ambient interpreter dependency |
| Install root | `D:\case_apps` | — | Matt's decision |

## Rejected alternatives

- **Rust orchestrator** — the only clear advantage was `IExplorerCommand` COM
  for the Win11 top-level menu. v1 uses a registry cascade, which just execs a
  command line, so that advantage does not apply. Go wins on tsnet (Go-native,
  no Rust equivalent) and on dual-platform builds.
- **mutool / MuPDF** — **actively rejected for text extraction.** On the real
  transcript it mapped ZapfDingbats `0x6E` to `I`, a letter that corresponds to
  nothing and cannot be reversed. Worst of seven readers tested. Still usable
  for raster/structure work; never for glyph-accurate text.
- **pdfminer.six / pdfplumber / pdf.js** — all return the raw byte `n` instead
  of decoding. Not wrong exactly, but not glyph-accurate. Retained as
  *raw-byte reporters* for triangulation, not as primary readers.
- **Consensus-on-every-file** — rejected as over-engineering (R2, R5). Running
  seven readers per file does not pay for itself.
- **Calibration framework with fidelity vectors** — rejected. Matt inspects
  output directly; a hand-edited routing table is sufficient.
- **Per-file RFC 3161 timestamps** — deferred. Out of scope for R2's bar.
- **Stirling-PDF as an engine** — it will run on OVH for interactive work, but
  it is not in the extraction path. Note: the sample transcript in evidence was
  *produced* by Stirling-PDF v1.1.1, which is where the emoji loss originated.

## Integration mechanism

**Subprocess + JSON over stdin/stdout.** The orchestrator never links an
engine library (except where a pure-Go one exists). Every engine — Python, JS,
C, Go, anything — is a process that reads a JSON request on stdin and writes a
JSON response on stdout. See `SPLIT.md` for the contract.

Two invocation modes:
- `oneshot` — process per call. For fast CLI binaries (poppler, qpdf).
- `worker` — resident process, NDJSON loop. For interpreted runtimes where
  startup cost (~50–200ms) would dominate across thousands of files.

Remote mode adds an HTTP API bound to a `tsnet` listener; caller identity comes
from `LocalClient.WhoIs`, so there is no bearer-token layer to build.

## Time-sensitive flags

- **`webbed` is a DuckDB community extension**, not core. It can lag DuckDB
  releases. Pin the DuckDB version and re-verify `read_xml` after any upgrade.
- **DuckDB `read_xml` schema inference is sample-based** and silently drops
  sparse attributes — see `GOTCHAS.md` S-1. This is current behaviour as of
  1.5.5 and may change.
- **pypdf ships frequently** (6.11 → 6.17 between May and September 2026). Pin
  the version and record it in every sidecar.
- Go 1.28 will require a Go 1.26 minor release for bootstrap — irrelevant now,
  relevant if the toolchain is left untouched for a year.

## Research limitations

Version numbers for Go, tsnet, and pypdf come from live search this session.
DuckDB, `webbed`, poppler, qpdf, mutool, pdfium and lxml versions and
behaviours were verified by **executing them against Matt's actual evidence
files** in this session — stronger evidence than documentation.

## Sources

- Go release history — go.dev/doc/devel/release
- tsnet — tailscale.com/docs/features/tsnet, pkg.go.dev/tailscale.com/tsnet
- pypdf changelog — pypdf.readthedocs.io/en/latest/meta/CHANGELOG.html
- All other versions/behaviours — direct execution, 2026-09-11
