---
title: Coco super index — deployed on ovh-files, first catalog-sourced run over B2
date: 2026-09-22
status: RECEIPT (live)
domains: [consignatio, intake, superindex, search]
tags: [receipt, deployment, coolify, catalog, b2, weaviate, surreal, cocoindex, streaming]
---

# Coco super index — first catalog run, live

> _Byline: Claude Code · Opus 5 · 2026-09-22. Branch `feat/superindex-service`, worktree
> `_worktrees/consignatio-superindex-service`, based on `cfdeec8` (contains the other
> session's image-lane `fb9a3e0`; nothing reverted)._

Closes Audit 1 items I-2, I-3 (text formats), I-5, I-6, I-8 and I-9 of
`2026-09-22-intake-index-expectations-vs-built.md`. I-1 (whole corpus) and I-4
(archive members) are **not** closed; see "Not proven".

## The service

| Fact | Value |
|---|---|
| Coolify application | `superindex`, uuid **`f12skzwshwp85b1k4lbgm0pp`** |
| Project / environment | `consignatio` (`wwa0zxg6ckg9ufsjv3slrd8f`) / `production` |
| Server / destination | ovh-files `cn89l8801u8gsginw1rxq5qt` / `zmw9iqejjdeswxxrgg3dngyy` |
| Git source | GitHub app `r4mhpblr8cnxk3481r07xxz0`, `Cursedpotential/Consignatio`, branch `feat/superindex-service` |
| Build | `dockercompose`, base dir `/Intake/backend`, compose `/deploy/superindex.compose.yml` |
| Container | `superindex-f12skzwshwp85b1k4lbgm0pp-*`, healthy |
| Address | `http://100.91.190.107:8765` — **tailnet only**, no public port, no Traefik route |
| Watch paths | `Intake/backend/**` |

No Tailscale service (`svc:superindex`) was registered: the three-step recipe exists, but
no receipt in this repository shows it already applied to a Consignatio service, so the
service stays on the tailnet IP. Registering it is a one-line follow-up if the owner wants
`https://superindex.tilapia-skilift.ts.net`.

### Live proof

```
GET  /health              200  {"status":"ok","snapshot":".../20260922T150716...parquet"}
GET  /filesystem/status   200  {"state":"finished","files_observed":200,"files_transformed":200,
                                "files_without_usable_text":15,"failure_events":0}
GET  /filesystem/graph/status 200  {"status":"ready","version":"surrealdb-3.2.4+20260803.93ab219"}
GET  /documents?limit=2   200  rows keyed by the vault key
POST /search              200  hits carry vault_key + resolution
POST /filesystem/search   200  Weaviate hybrid, hits carry vault_key + resolution
```

## The run

`casebible-corpus index --limit 200 --path-prefix "consignatio/vault/v1/HTML Files/"`,
inside the container, catalog mode.

| | |
|---|---|
| Catalog table | `raw_duck.vault_index_source_20260918` (508,152 objects / 2,170,597,644,994 bytes) |
| Catalog role | `metabase_ro` (read-only; `advocatio_desk` has no USAGE on `raw_duck`) |
| Objects indexed | **200** observed, **200** transformed, **0** failures, 15 with no usable text |
| Duration | 139 s first run (14:52:21 → 14:54:40 UTC) |
| Bucket reads | **200 requests, 8,657,842 bytes, 200 distinct objects** — one streamed GET each |
| Parquet | 200 document rows, 185 chunk shards |
| Weaviate | `IntakeCorpus` on `http://100.91.190.107:8082`, **2,375 objects**, named vector `text_vector`, 2048 dims, vectorizer `none` |
| Surreal | `index-run:consignatio-vault-v1:71f8732248088bf7`, **200 occurrence nodes** + store + `stored_at` edges |
| Receipt | `/var/lib/superindex/output/receipts/20260922T150721.256076Z-index-c08ed7f1.json` |

Sample hit (`POST /search`, "prompt engineering"):

```
vault_key  consignatio/vault/v1/HTML Files/Het Prompting Boek (00159888).html
resolution content_on_b2
```

## Embeddings: NIM credits are NOT out

Live probe 13:38 EDT before any code ran: `POST https://integrate.api.nvidia.com/v1/embeddings`,
`nvidia/nemotron-3-embed-1b`, **HTTP 200**, 1 vector, 2048 dims. Audit item I-5's "credits out
→ 503" no longer holds for embeddings; the run above embedded 2,375 chunks on NIM.

`INTAKE_EMBED_MODE=deferred` remains as the fallback: it extracts, chunks, writes Parquet and
Surreal with `embedding_status=pending` and zero vectors, and skips the Weaviate write for
those rows. Summaries are **off** (`INTAKE_SUMMARY_MODE=off`) — the owner's 09-18 ruling puts
summaries on Gemini as a separate pass, and nothing in this build wires Gemini.

## Moving a file does not re-index it

Owner ruling 2026-09-22 10:48 (sorting and indexing happen at the same time):

- `document_id = uuid5(source_id, catalog content hash)`. `version_id` and `chunk_id` were
  already content-addressed. A move therefore changes **only** the `vault_key` property.
- Nothing re-extracts, nothing re-embeds, the Weaviate object id is unchanged, and the
  Surreal occurrence node is keyed by `document_id`, so it follows the file.
- **What still re-indexes:** an object the catalog has no SHA-1 for — a B2 large file
  uploaded in parts — falls back to a key+size identity that a move does change. Those
  objects re-extract and re-embed after a move.
- To apply a move today the catalog row's `key` is updated and the object is re-run; the
  cheap path (patch `vault_key` in place, in Parquet + Weaviate + Surreal, without a
  re-run) is **not built** and is the obvious next slice.

## Large objects, live

| Object | Size | Result |
|---|---|---|
| `moved/data-2025-12-08-01-38-39-batch-0000/conversations.json` | 61,724,767 B | **0 failures.** 1 bucket request, 61,724,767 B. 35,483 chunks in 70 shards, all embedded on NIM and written to Weaviate. 1,498 s (15:47:14 → 16:12:12 UTC). |
| `xml/f146876416.xml` (SMS backup) | 505,511,165 B | **0 failures.** 1 bucket request, 505,511,165 B, **38 s** with `INTAKE_EMBED_MODE=deferred` and Weaviate off. The file is **truncated** — it ends mid-element at line 19156 — and the run indexes the 2,007 records it did read and records a note, instead of losing the file. |

Both large-object runs used their own `CASEBIBLE_SOURCE_ID` and a **container-local**
`CASEBIBLE_OUTPUT_DIR` (`/var/lib/superindex/output-big`, `-xml2`), so their Parquet was
replaced with the container on the next deploy. What survives is each run's printed receipt
(quoted above) and, for the JSON, its **Weaviate objects — the collection holds 37,857
objects**, the 2,375 from the HTML slice plus the 35,483 from `conversations.json`. If those
Parquet artifacts are wanted, re-run with `CASEBIBLE_OUTPUT_DIR` under the bind mount.

Container memory during those runs (`docker stats --no-stream`, 10 s samples):

- 505 MB XML: 1.03 GiB at the download burst, then 246–406 MiB. Extraction measured
  separately on the same object: **peak RSS 288 MiB for a 505 MB file**.
- 61 MB JSON with embeddings and Weaviate ON: 350–780 MiB rising, **3.16 GiB at its peak**.

**That 3.16 GiB is a real limit and it is not the extractor.** Extraction, chunking and
Parquet are bounded (288 MiB on a 505 MB object). The growth is CocoIndex holding one
declared Weaviate target state per chunk for the whole component: 35,483 chunks × a
2048-float vector. It is bounded by the largest single object's chunk count, not by the
corpus, but a multi-gigabyte SMS XML with embeddings on would exceed the box. Until that
is changed, very large objects should run with `INTAKE_WEAVIATE_INDEX_ENABLED=0` (Parquet
+ DuckDB search still work) or the Weaviate write needs to move out of the coco target
into a direct per-shard write.

## Archive members

`casebible-corpus archive-members "<key>" --size <bytes> --limit N` lists a ZIP's members
**without downloading it**, using the same signed `ObjectStore` with ranged GETs.

Live, on a Takeout part:

```
archive_key    consignatio/vault/v1/Archive/Takeout Data/Google Takeout/Takeout (1)/
               takeout-20231119T033545Z-003.zip
archive_bytes  10,739,336,802          (10.7 GB)
members_listed 8 (limit)
b2_requests    4        b2_bytes_read  1,919,623        real 4.3 s
```

Four ranged reads and 1.9 MB to open a 10.7 GB archive. `read_member` streams one member's
decompressed bytes in 1 MiB windows through the same reader.

**Not done:** those members are not yet fed through the extractors into the index, so there
are no `member_path` rows. The column, the reader and the CLI exist; wiring
`archive-members` into `process_file` as catalog-linked rows is the remaining step.
tar/tar.gz are deliberately not handled — no central directory, no seekable gzip — and need
a front-to-back streamed path.

## Caps: gone

`INTAKE_MAX_FILE_BYTES` (8 MiB reject), `INTAKE_MAX_EXTRACTED_CHARS` (1 M) and
`INTAKE_MAX_CHUNKS_PER_FILE` (512) are deleted from the code, not raised. In their place:

- objects stream in 1–4 MiB windows;
- text is decoded incrementally, split on line boundaries;
- `.xml` SMS backups are split on `<sms>`/`<mms>`/`<call>` record boundaries with
  `iterparse` + `clear()`, the boundaries SBV uses;
- `.json` arrays and NDJSON are split per record by a bracket-depth scanner;
- chunks flush to their own Parquet shard every `INTAKE_CHUNK_FLUSH_SIZE` (512) chunks, so
  no full chunk list is ever held;
- PDF/DOCX/RTF/EML, which need random access, go through a **disk spool** under
  `/var/lib/superindex/spool` — bounded memory, not a byte cap. `.xml` also spools so
  `iterparse` can read it front to back.

## Bugs found and fixed while proving this

1. **Catalog mode could not read a byte.** It listed catalog keys and then opened them as
   local paths under `CASEBIBLE_SOURCE_DIR`; no deployment mounts the bucket. Objects are now
   read over the S3 API (`object_store.py`, SigV4, ranged and streamed GETs, per-run counters).
2. **Catalog runs produced an empty snapshot.** `build_active_snapshot` decided a row was
   current by stat-ing `source_dir/<relative_path>`. Every catalog row failed that test, so
   `/health` stayed `not_indexed`, `/search` and `/documents` returned nothing and the graph
   projection wrote 0 rows. Catalog mode now validates the key instead.
3. **A second run over the same slice failed 200/200.** The immutable writer refused the
   existing shard because `indexed_at` differed — a fact about the run, not the artifact. An
   existing file at an artifact-fingerprinted path is now accepted. Nothing is overwritten.
4. **The graph projection needed `pytz`,** which the image does not carry; DuckDB raised
   `InvalidInputException` converting a tz-aware timestamp. The timestamp is selected as text.
5. **`/filesystem/search` 503'd** whenever `INTAKE_WEAVIATE_EMBED_MODEL` was unset; it now
   defaults to the configured NIM model and still refuses an explicit mismatch.
6. **Bind-mounted volumes were root-owned** and the container runs as uid 10001. Fixed on the
   host once: `chown -R 10001:10001 /data/consignatio/volumes/superindex`. A fresh deploy on a
   new host needs that same chown.
7. **Every chunk row was collected in memory before any shard was written,** because the
   artifact id was a rolling digest over all chunks. For the 61 MB conversations.json that is
   30,136 rows of 2048 floats held live — the exact unbounded behaviour this work removes.
   The streaming artifact id now pins the derivation (version + chunking + models), is known
   before the first chunk, and each shard is written and declared as it is produced.
8. **A 341,373-character chunk.** Minified JSON records have no separator, so the recursive
   splitter returned one enormous part and NIM answered 400, failing the object. Oversized
   splits are hard-wrapped on size with the same overlap.
9. **A chunk the embedder rejects no longer fails the object.** Chunks are bounded in
   characters, NIM in tokens; minified CSS inside a chat export tokenizes far denser than
   prose. The batch is bisected and a single failing text is halved to a 256-char floor. The
   full text is still stored and lexically searchable; the row records
   `embedding_status` = `ok` / `truncated` / `failed` / `pending`.
10. **The bucket response was held open for the whole embed loop** and died mid-object after
    208 s. Every object is spooled once and read back from disk, as the PDF path already did.
11. **A truncated XML lost the whole file.** `iterparse` raised at line 19156 after 2,007
    records. The parse now stops at the damage, keeps what it read and notes it.
12. **A failed component said nothing.** "Index run did not finish cleanly" with no reason
    cost several blind rounds; the failure type and a bounded message now go to stderr.

## Shared toolkit, separate data

Per the owner's 10:48 ruling that engines and tooling are shared across surfaces and only
databases may be isolated: `object_store.py`, `vault_source.py`, `streaming.py`,
`stream_extract.py`, `catalog_source.py` and `projections/index_run.py` are shared modules,
not text-app-private. The image lane keeps its own app name, state directory, lock and
Weaviate collection (`IntakeImageV1`); `exiftool` and `tesseract` are installed in this
image so it can run from here.

## One-app-per-slice: a different `--path-prefix` retires the last run

A bounded run with a new `--path-prefix` under the **same** `CASEBIBLE_SOURCE_ID` makes
CocoIndex reconcile the previous slice out of existence — observed live: "200 deleted". That
is correct reconcile behaviour (the objects are no longer in the source list), but it means
**each slice needs its own `CASEBIBLE_SOURCE_ID` and `CASEBIBLE_OUTPUT_DIR`**, which is the
owner's isolation rule applied to runs. The large-object runs above used
`vault-bigfile-json` and `vault-bigfile-xml2` for exactly this reason.

## Not proven

- **The whole corpus (I-1).** 200 of 508,152 objects. No full run was started.
- **Archive members are listed, not indexed (I-4).** See "Archive members" above.
- **The image lane on catalog/B2.** It still reads a local directory. The shared reader it
  needs now exists; it has not been pointed at it.
- **Video, audio, scanned PDF, entities to Surreal (I-7).** Untouched.
- **`tests/test_migration_partition.py`** was already failing before this branch
  (`ModuleNotFoundError: scripts`) and is untouched. Everything else: 109 passed, ruff clean.
