# Synthetic live proof

**2026-09-11 execution update:** the backend proof now passes against the settled
8082 instance. See `LIVE-PROOF-2026-09-11.md` for results and the lifecycle bug
found/fixed. The original proposed commands below are retained as historical
context; physical target selection is no longer pending.

Repeatable runner (creates a fresh synthetic collection and makes real NIM calls):

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend" && & { $env:PYTHONDONTWRITEBYTECODE='1'; $env:TEMP='E:\AI_Workspace\.intake-dev\temp'; $env:TMP=$env:TEMP; $env:INTAKE_WEAVIATE_URL='http://100.91.190.107:8082'; .\.venv\Scripts\python.exe scripts/synthetic_live_proof.py }
```

The runner accepts no corpus source path; it only indexes the committed fictional
note. Each index subprocess times out after 150 seconds. It starts its own
loopback API for HTTP checks and terminates only that process on completion.
Limits are file/chunk/concurrency/time bounds, **not an OS memory ceiling**.

## Original pre-execution plan

Physical Weaviate instance selection is pending owner direction. No collection,
schema, service, corpus index or provider request was created by this document.
These are future operator commands after prerequisites below are satisfied.

## Readiness

1. Main agent confirms physical Weaviate service and a dedicated **synthetic**
   collection. Provision the schema from `FILESYSTEM-SEARCH-2026-09-11.md` under
   that chosen test name. Do not reuse an evidence collection.
2. Backend environment contains `INTAKE_WEAVIATE_URL`, collection name, text
   named vector, and service-scoped API key. Keys never appear in command text.
3. `NVIDIA_API_KEY` resolves through existing secret lookup. NIM embed/summary
   models and access are verified; `INTAKE_WEAVIATE_EMBED_MODEL` must match the
   chosen `NIM_EMBED_MODEL` and `NIM_EMBED_DIMENSIONS`.
4. Existing E: `.venv` dependencies are ready. Commands below do not run uv,
   install packages, scan mounts, or download models.

Actual pipeline startup acquires source lock, records run start, checks NIM key,
then fetches the chosen Weaviate schema and validates required properties and
`none` named-vector configuration **before source enumeration**. This does not
prove NIM model access until its first remote call, nor infer collection model
identity from dimensions. An operator must verify matching model settings.

The single committed input is `sample_docs/correspondence/example.txt`, a fictional
meeting note (no personal data). It is the **only source directory** in this proof.
Use a new output directory; do not overwrite earlier proof receipts.

## First bounded index run

After prerequisites, run in PowerShell 7. This command sets process-local limits,
retains all output on E:, and refuses an already-used proof output directory.
It makes real NIM requests and writes derived objects to the chosen Weaviate test
collection; it must not be run before physical target selection is settled.

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend" && & { if (Test-Path -LiteralPath '.\output\synthetic-live-proof-20260911') { throw 'Choose a new proof output directory; retain the previous receipt.' }; foreach ($name in @('INTAKE_WEAVIATE_URL','INTAKE_WEAVIATE_COLLECTION','INTAKE_WEAVIATE_TEXT_VECTOR','INTAKE_WEAVIATE_EMBED_MODEL')) { if (-not [Environment]::GetEnvironmentVariable($name)) { throw "Missing $name" } }; $env:PYTHONDONTWRITEBYTECODE='1'; $env:TEMP=(Get-Location).Path; $env:TMP=$env:TEMP; $env:INTAKE_MAX_FILE_BYTES='4096'; $env:INTAKE_MAX_EXTRACTED_CHARS='4096'; $env:INTAKE_MAX_CHUNKS_PER_FILE='8'; $env:INTAKE_MAX_INFLIGHT_FILES='1'; $env:NIM_MAX_CONCURRENCY='1'; $env:NIM_MAX_RETRIES='1'; $env:NIM_TIMEOUT_SECONDS='30'; $env:INTAKE_WEAVIATE_INDEX_ENABLED='1'; & .\.venv\Scripts\python.exe -m casebible_index.cli index --source '.\sample_docs\correspondence' --source-id 'intake-live-proof-20260911' --output '.\output\synthetic-live-proof-20260911' }
```

Expected: one observed supported file, one transformed file, no failure events,
one small active-document snapshot and a receipt. A zero-error run receipt alone
is **not** proof that query search retrieves it: perform the next step.

## Serve and query

Main agent first verifies a free bindable loopback port and substitutes it if
18765 is unavailable. This is the backend API only, not another desktop host.
In a terminal with the same selected provider settings:

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend" && & { $env:PYTHONDONTWRITEBYTECODE='1'; $env:TEMP=(Get-Location).Path; $env:TMP=$env:TEMP; & .\.venv\Scripts\python.exe -m casebible_index.cli serve --host 127.0.0.1 --port 18765 --output '.\output\synthetic-live-proof-20260911' }
```

From a second PowerShell terminal:

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend" && Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:18765/filesystem/search' -ContentType 'application/json' -Body '{"query":"Synthetic scheduling note","mode":"keyword","limit":5}'
```

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend" && Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:18765/filesystem/search' -ContentType 'application/json' -Body '{"query":"When is the fictional review meeting scheduled?","mode":"hybrid","limit":5}'
```

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\Intake\backend" && Invoke-RestMethod -Uri 'http://127.0.0.1:18765/filesystem/status'
```

Verify actual hit source ID `intake-live-proof-20260911`, absolute local source
path, deterministic document/chunk IDs, excerpt and finite score. Unknown coverage
is expected and honest. Verify both keyword and hybrid return the synthetic note.
Record provider latency, observed memory, result identity and errors in a new
receipt. Do not proceed automatically to mounts or real corpus input.

Only after first-run success, repeat the same `index` invocation (without the
fresh-directory guard) to check unchanged-state behavior. Source test modifications
and retirement tests require a new disposable fixture, not altering the committed
sample or removing original files. Any generated bytes/rows are retained; cleanup
does not issue DELETE. Stop the explicit API process when the proof is finished;
no scheduled or recurring worker is introduced.

## API-only verification completed

`tests/test_filesystem_api.py`: 14 ASGI contract cases cover real routing and
request validation, success serialization and source paths, hybrid vector handoff,
keyword execution without initializing NIM, limit/query/mode rejection before
secret/provider setup, missing service, model mismatch, missing NIM key, sanitized
provider errors, and last-run status success/failure.

A failing test exposed whitespace-only queries reaching provider setup. The
request model now rejects them with HTTP 422 before secret lookup or embedding.

Together with adapter/runtime suites: **36 tests passed in 1.75 seconds**. These
tests use in-process ASGI, fake provider transports/clients, and synthetic runtime
state. They are not live provider/service proof.
