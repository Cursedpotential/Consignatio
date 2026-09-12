# Tier Split — casekit

## Applies?

**No — v1 is single-tier.** One Go binary invoked from the Explorer context
menu. There is no separate client process and no owned server.

The daemon/remote tier (`casekit serve --tsnet` on the OVH box) and the
spot-check review UI are **Phase 8+**, deliberately deferred under R5.

## The contract that does matter: the engine boundary

The split that governs this application is not frontend/backend — it is
**orchestrator ↔ engine**. This is what allows an engine in any language to be
built and tested independently of the Go binary, and it is defined here for
exactly the reason the split skill exists.

### Request (orchestrator → engine, stdin)

```json
{
  "v": 1,
  "op": "extract_text",
  "input": "D:\\case\\file.pdf",
  "blob_dir": "D:\\case\\_derived\\pkg-abc\\blobs",
  "args": { "pages": "1-24", "lang": "eng" }
}
```

`op` is one of: `probe`, `extract_text`, `extract_meta`, `extract_blobs`,
`extract_structure`, `render`.

### Response (engine → orchestrator, stdout)

```json
{
  "ok": true,
  "engine": { "id": "pypdf", "version": "6.17.0", "lang": "python" },
  "elements": [
    { "id": "e0041", "kind": "text_run", "page": 3,
      "offset_space": "decoded_stream",
      "offset": 4102, "length": 611, "sha256": "…",
      "container": { "object": 12, "source_offset": 31236, "source_length": 4894 },
      "value": { "text": "Nvm she pooped ■" } }
  ],
  "blobs": [ { "sha256": "a826…", "bytes": 101603, "ct": "image/png" } ],
  "commands": ["pdftotext -enc UTF-8 file.pdf -"],
  "warnings": [],
  "stats": { "duration_ms": 412 }
}
```

Failure: `{"ok": false, "error": {"code": "...", "message": "..."}}` plus a
nonzero exit. The orchestrator never parses stderr for meaning.

### Engine manifest (`engine.toml`, discovered at startup)

```toml
id           = "pypdf"
lang         = "python"
runtime      = "engines/python/.venv/Scripts/python.exe"
entry        = ["-m", "eng_pypdf"]
mode         = "worker"                       # worker | oneshot
capabilities = ["extract_text","extract_meta","extract_blobs"]
formats      = ["pdf"]
version_cmd  = ["-m","eng_pypdf","--version"]
```

Adding an engine = dropping a directory in. No orchestrator change, no
recompile, no language restriction.

### Worker mode protocol

One JSON request per line on stdin, one JSON response per line on stdout.
Process stays resident. Orchestrator holds a bounded pool per engine and kills
workers exceeding a timeout.

## Deferred tier contract (Phase 8+)

When the daemon lands, the HTTP surface is a thin wrapper over the same ops:

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/v1/profile` | `{path}` or multipart | profile JSON |
| POST | `/v1/extract` | `{path, engine?}` | extraction JSON |
| POST | `/v1/package` | `{path}` | package id + manifest |
| GET | `/v1/healthz` | — | `{ok, version, engines[]}` |

Auth is tsnet identity via `LocalClient.WhoIs`. No token layer.

## Synchronization points

1. Engine contract v1 must be frozen before more than one engine is written —
   including `offset_space` (GOTCHAS S-16). An `offset` with no declared
   coordinate space breaks R11 traceability for every PDF element.
2. Sidecar/ledger schema must be frozen before packaging (Phase 5) starts.
3. Nothing else blocks. Engines and orchestrator can proceed in parallel.
