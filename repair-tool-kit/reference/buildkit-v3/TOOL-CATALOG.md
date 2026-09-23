# Tool Catalog — casekit

Everything needed to build and run. No cloud services, no API keys, no
accounts required for Phases 0–6.

## Vendored under `<INSTALL_ROOT>\engines\`  — root is **OD-1, unresolved**

| Tool | Role | Source | Pin |
|---|---|---|---|
| `pdftotext`, `pdfinfo`, `pdffonts`, `pdfimages`, `pdfdetach`, `pdftoppm` | poppler — primary PDF text + profile | poppler-windows release | record version in sidecar |
| `qpdf` | structure, `--check`, `--qdf` raw stream | qpdf releases | 11.9.x |
| `mutool` | **not shipped.** Its known-bad output is frozen as a Phase 3 test fixture (GOTCHAS S-2). Install only if you want to regenerate that fixture. | mupdf releases | not required |
| `duckdb` | XML ingest + Parquet + query | duckdb.org | 1.5.5, pin |
| `webbed` | DuckDB XML extension | `INSTALL webbed FROM community` | re-verify after upgrades |
| `tesseract` + `eng` traineddata | OCR — **Phase 6c**, screenshot pile index. Inside the usable product; A-16 makes OCR content-match the PRIMARY corroboration signal. | tessdata_best | required at 6c |

## Frozen Python venv — `<INSTALL_ROOT>\engines\python\.venv`

Managed by `uv`. Keep the path shallow (GOTCHAS B-4).

| Package | Role | Pin |
|---|---|---|
| `pypdf` | secondary PDF reader, metadata, attachments | 6.17.0 |
| `pypdfium2` | pdfium reader + rasterization | pin at install |
| `lxml` | XML slim pass — the only XML parser permitted | pin at install |
| `ftfy` | mojibake **detector** after the byte-level fix — never the primary repair | pin at install |
| `duckdb` | Python binding if needed by an engine | match CLI version |

## Go modules

| Module | Role |
|---|---|
| `tailscale.com/tsnet` | Phase 8 only — embedded tailnet node, v1.102.0, BSD-3 |
| stdlib `os/exec`, `encoding/json` | engine subprocess contract |

Nothing else. Resist adding dependencies.

## Credentials

**Phases 0–6: none.** Everything is local.

Phase 8 adds one: a Tailscale auth key (`TS_AUTHKEY` env var, or OAuth client
secret). Never committed; read from environment at runtime.

## Existing infrastructure (not built here)

| Thing | Where | Relationship |
|---|---|---|
| Case Bible vault | `V:\sorted\_raw\Case Bible\` | source corpus; casekit reads, never writes |
| Evidence dir | `…\Evidence\Phone Records\Messages with Katrina` | first target for inventory |
| Stirling-PDF | OVH box | interactive PDF work; **not** in the extraction path |
| R2 / B2 buckets | Cloudflare / Backblaze | sealed-package destination, Phase 8+ |
| OVH server | via Tailscale | daemon host, Phase 8+ |

## Reference files — commit these

Both belong in `docs/reference/`. Every phase exit criterion is stated against
them.

- `_18102689630__1___1_.pdf` — sha256 `f18e250e5aca784f…`
- `Copy_of_sms-20221104021809.xml` — sha256 `55515f2a490c9a0a…`
- `sms.xsd` and `Fields in XML backup files.md` — vendor schema, synctech.com.au
