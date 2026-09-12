# SORT → Cloud-agent handoff: verbatim sort/dedupe logic (content for `goals/sort-dedupe/HANDOFF.md`)
> _Byline: Claude Code · Opus 4.8 · 2026-06-26_ · **LOCAL ONLY — no secret VALUES here (env/file names only).**
> Supplied by the **SORT** lane per TASKS 14:35 / 14:55. PIPELINE writes+commits this onto branch
> `agent-handoff/sort-dedupe` (off `origin/main`) → cloud agent builds `evidence/sort.py` + `evidence sort` from it.
> Source of truth = the case-bible plugin tools (paths below); this doc is a faithful transcription of their working logic.

Goal for the cloud agent: re-implement the **proven** raw→sorted pipeline as `evidence/sort.py` exposing
`evidence sort`. It must stay **copy-only / never-delete**, **md5 best-version deduped**, **package-intact**,
**type-first**, and **idempotent with a provenance ledger**. The eight sections below are everything needed.

Canonical tool sources (verbatim logic lives here):
- `~/.claude/local-plugins/case-bible/tools/cb_r2_sort.py` — full-corpus ledger: taxonomy map + md5 best-version dedup + rclone batch emit.
- `~/.claude/local-plugins/case-bible/tools/cb_typefirst_ledger.py` — TYPE-FIRST classifier (the final model) + multi-tag metadata.
- `~/.claude/local-plugins/case-bible/tools/cb_execute_typefirst.py` — the executor (server-side rclone COPY, executed ledger).
- `~/.claude/local-plugins/case-bible/tools/cb_connect.py` — endpoint/credential resolution (no hard-coded secrets).
- `~/.claude/local-plugins/case-bible/tools/cb_clean_names.py` — filename normalization (`clean_path`).

---

## 1. Sources (buckets, prefixes, backup path, vault prefix)
| Role | Location | Notes |
|---|---|---|
| RAW (authoritative source) | `r2:casebible-raw` | NEVER modified/deleted. The archive of record. |
| SORTED (vault / destination) | `r2:casebible-sorted` | Type-first vault; copies land here. |
| QUARANTINE (junk destination) | `r2:casebible-quarantine` | Obvious junk copies (never deleted from raw). |
| Local hydrated backup | `D:/backup` | Authoritative HYDRATED source for content (OneDrive ingest left dehydrated stubs). Except `icloud/` placeholders. |
| Local working drive | `D:/casebible/` | catalog duckdb, ledgers/exports, working sqlite. |
| Enrichment index | Postgres `casebible` (ovh2 Coolify container) via SSH tunnel | drives classification (`cb.enrichment`). |
| Dedup hash snapshot | `D:/casebible/casebible.duckdb` table `r2_files(path, md5)` | the md5 source for best-version dedup. |
| Working/registry store | `D:/casebible/casebible_work.sqlite` (`CB_WORK_DB`) | durable `sort_map` + dedup decisions + progress. |
| rclone remote | `r2:` | configured rclone remote pointing at the R2 S3 endpoint (account `1a7406c497493a52128bb282f499e7b8`). |

`rclone` binary resolution (Windows fallback used by the executor):
`shutil.which("rclone")` → else the WinGet rclone path. Cloud agent should just rely on `rclone` on PATH.

## 2. Dedupe rules (md5 best-version)
- **Hash = md5**, sourced by LEFT JOIN of the ledger to `loc.r2_files` on `path = old_path`
  (`r2_files` is the precomputed R2 md5 snapshot in `casebible.duckdb`).
- **No hash → treat as canonical** (`decision_state='canonical_nohash'`; never silently drop an un-hashed file).
- **Best-version within an md5 group** (`PARTITION BY md5`), keep `row_number()=1` ordered by:
  1. **de-prioritize** copies/legacy: `+1` if path matches `%_review_hold%` OR `%legacy%` OR `%(copy%` (else 0),
  2. then **shorter `old_path`** (cleaner location wins),
  3. then **larger `bytes` DESC** (more complete wins).
- Winner → `decision_state='canonical'` (copied); losers → `'duplicate_superseded'` (NOT copied, retained in ledger).
- **raw-vs-backup tie-break**: raw (`r2:casebible-raw`) is the provenance source for the copy op; `D:/backup` is the
  hydrated content fallback when a raw object is a dehydrated stub. md5 identity governs "same file"; path-rank (above)
  governs which location is canonical. Content (md5) is NEVER changed by the sort — only path changes.

Verbatim dedup SQL (from `cb_r2_sort.py`):
```sql
dedup AS (
  SELECT *, CASE WHEN md5 IS NULL OR md5='' THEN 1 ELSE row_number() OVER (
      PARTITION BY md5 ORDER BY
        (CASE WHEN p LIKE '%_review_hold%' OR p LIKE '%legacy%' OR p LIKE '%(copy%' THEN 1 ELSE 0 END),
        length(old_path), bytes DESC) END AS rn
  FROM withmd5
)
-- decision_state: md5 null/'' -> 'canonical_nohash'; rn=1 -> 'canonical'; else 'duplicate_superseded'
```
Filename dup-markers (`Copy of`, ` - Copy`, `(2)`) are stripped from `new_path` via `cb_clean_names.clean_path`
(normalization happens on the DESTINATION path only; source path is preserved verbatim in the ledger).

## 3. Move-vs-copy (HARD RULE: copy-only, never delete)
- Every op is a **server-side `rclone copyto <raw-src> <dest>` `--s3-no-check-bucket`**. **No move, no delete, ever.**
- RAW root stays intact (verified: 401 objects, 0 deletes, 0 errors on the executed root-pile run).
- Executor parallelizes with a `ThreadPoolExecutor` (default 8 workers); each op records `status` ok/ERR + truncated stderr.
- Optional later "tidy": copy now-sorted originals into `raw/_moved_<stamp>/` (preserving structure) — still a COPY, owner's
  "moved folder" pattern; do NOT remove originals.

Verbatim copy op (from `cb_execute_typefirst.py`):
```python
def copy_one(row):
    src = f"{RAW}/{row['old_path']}"                       # RAW = "r2:casebible-raw"
    dst = f"r2:{row['dest_bucket']}/{row['new_path']}"
    p = subprocess.run([RCLONE, "copyto", src, dst, "--s3-no-check-bucket"], capture_output=True, text=True)
    return {**row, "status": "ok" if p.returncode == 0 else "ERR", "err": ... }
```

## 4. Vault layout (TYPE-FIRST — the final, locked model)
Top level = **TYPE**, never domain. Final top-level set:
`Inbox · Evidence · Entities · Case Management · Knowledge · Tools & Platform · Documents · Exports & Bundles · Legacy · Archive` (+ `Quarantine` bucket).
- **Inside `Evidence/` → sub-divide by SOURCE/platform** (sms / imessage / facebook / snapchat / phone / whatsapp / instagram …)
  and **preserve the original source folder structure** (the `rel_tail`).
- **Knowledge** = Context Corpus (AI chats, research, notes, docs) — **NOT evidence**.
- **AI chats = Knowledge/context**, never the evidence schema (canonical vector home = Milvus `casebible_ai_conversations`).
- **Domain is NEVER a folder** — it rides as multi-tag metadata (§6) so the DB can pivot by domain with zero re-sorting.
- Root-pile intake lands under `<Type>/<sub>/_root_intake_<stamp>/<basename>`; junk under `_root_cleanup_<stamp>/<reason>/<basename>` in quarantine.
- Package-intact: a conversation + its attachment tail stay together. `rel_tail` keeps platform-relative structure, e.g.:
  `imessage`→strip `^.*imessage exports/`; `snapchat`→strip `^.*[Ss]napchat[^/]*/`; `facebook`→strip `^.*(court/fb/|[Ff]acebook/)`; else basename.

## 5. Classification logic (verbatim — the type-first classifier)
The decision function from `cb_typefirst_ledger.py` (`classify(r)` → `(type_bucket, sub, source)`), in order:
```python
# inputs per row: basename, ext, doc_type(dt), relevance(rel), platform(plat), is_conversation(isconv)
# --- hard junk (always quarantine, even if code-typed) ---
if bn.startswith("$R") or bn.startswith("$I"): -> QUARANTINE/recycle
if ext in INSTALLER_EXT:                       -> QUARANTINE/installer
if re.match(r"^f\d+\.(txt|xml|html|svg|ini)$", bn): -> QUARANTINE/shader-junk
# --- RESCUE: model mislabeled real content/tools as junk (basename allow-list) -> needs_review ---
if bn in RESCUE: -> RESCUE[bn]
if low.startswith("copy of geocoding"): -> Documents/general
if any(t in low for t in THIRD_PARTY):  -> Tools & Platform/_third-party
# --- code / tools (keep case scripts even if flagged junk) ---
if dt=="code" or ext in CODE_EXT:       -> Tools & Platform/code
# --- generic flagged-junk (non-code, non-rescued) ---
if dt=="junk" or rel=="junk":           -> QUARANTINE/flagged-junk
# --- knowledge (Context Corpus = NOT evidence) ---
if dt=="ai_chat" or (isconv and plat in AI_PLATS): -> Knowledge/ai-chats/<plat|misc>
if dt in (research,note,documentation,technical):  -> Knowledge/<research|notes|docs|docs>
# --- legal (distinct type) ---
if dt in (legal_filing,court_order):    -> Legal/filings
if dt=="legal_reference" or rel=="legal_reference": -> Legal/knowledge-base
if rel=="work_product":                 -> Legal/work-product
# --- evidence (sub-sorted by SOURCE/platform) ---
if dt=="message_thread" or (isconv and plat in MSG_PLATS): -> Evidence/messaging/<plat|misc>
if dt=="screenshot":                    -> Evidence/screenshots/<plat|misc>
if dt in (photo,image,video) or ext in IMG_EXT: -> Evidence/media/<plat|misc>
if dt in (call_log,audio):              -> Evidence/audio/<plat|phone>
if dt=="financial" or rel=="financial": -> Evidence/financial
if dt=="public_record":                 -> Evidence/public-record
if dt in (dataset,log):                 -> Evidence/records-data
# --- entities ---
if dt=="contacts" or "people" in dom:   -> Entities/<contacts|candidates>
# --- exports & bundles ---
if dt=="export_bundle" or ext in ARCHIVE_EXT: -> Exports & Bundles/<plat|misc>
# --- documents (generic) ---
if dt in (document,text) or rel=="personal_admin": -> Documents/general
else:                                   -> Inbox/_triage
```
Constant sets (verbatim):
```python
AI_PLATS = {chatgpt, claude, gemini, perplexity}
MSG_PLATS = {sms, imessage, facebook, snapchat, whatsapp, instagram}
CODE_EXT = {.py,.js,.mjs,.cjs,.ts,.go,.sh,.ps1,.sql,.ipynb,.rb,.pl,.r,.code-workspace}
INSTALLER_EXT = {.exe,.msi,.dll,.deb,.xapk,.apk,.dmg,.pkg,.p7b,.woff}
ARCHIVE_EXT = {.zip,.rar,.7z,.tar,.gz,.tgz,.zst}
IMG_EXT = {.jpg,.jpeg,.png,.gif,.heic,.webp,.bmp,.tiff,.svg}
THIRD_PARTY = (fclones, deduplicator, dude-main, word-duplicate, zoplicate, tidycobra, storm-main)
# RESCUE = basename -> (bucket, sub): data.json->Documents/general, content.zip & content (3).zip->Exports & Bundles/pdf-bundle,
#   place_id_db.json & enriched_timeline_human_readable.csv & refs_dick_summary_2024_2025.csv->Evidence/records-data,
#   exporter.html->Tools & Platform/code
```
`platform(relpath, plat)` source detection: scans path+plat for chatgpt/perplex(→perplexity)/gemini/claude/snapchat/
imessage/whatsapp/instagram; `messenger|facebook`→facebook; `sms|/sms|_sms`→sms; phone variants/`call.?log`→phone; else `""`.

**CLASSIFIER CAVEAT (must carry forward):** use the ORIGINAL PATH/folder name as a SIGNAL (gemini/chatgpt/Facebook/
account name) but **VERIFY by content + extension** — the current sort has real misclassifications (e.g. ~53% of
ai_chat-tagged files have non-chat extensions .docx/.csv/.pdf/.py/.zip). Tag richly EARLY.

## 6. Multi-tag metadata (domain rides as tags, not folders)
`tags_for(row, bucket)` emits a set; `domain_tags` column = JSON array. Maps (verbatim):
```python
DOMAIN_TAG = {Evidence:#evidence, Knowledge:#context-corpus, Legal:#legal, Entities:#entities,
              Case Management:#case-management, Tools & Platform:#platform, Documents:#document,
              Exports & Bundles:#artifact, Inbox:#needs-review}
TYPE_TAG  = {ai_chat/message_thread:#chat-export, screenshot:#screenshot, photo/image:#image, video:#video,
             call_log/audio:#audio, legal_filing:#motion, court_order:#court-order, legal_reference:#legal,
             public_record:#public-record, contacts:#people-search, email:#email, code:#tooling,
             research:#research, note/dataset/financial:#document, export_bundle:#artifact}
FUNC_TAG  = {research:#research, code:#tooling, timeline:#timeline}
# + regex on title+summary: timeline|chronolog -> #timeline ; affidavit|motion|subpoena|statute|\bmcl\b -> #legal-strategy
# + always add #raw
```
Each ledger row also carries: `ref_proposed_domain, ref_relevance, ref_doc_type, parties, date_start, date_end,
model_tags, bytes, confidence, needs_review`.

## 7. Idempotency / manifest (the provenance ledger)
- **Idempotent by construction:** `rclone copyto` to a fixed `new_path` is safe to re-run; same content → same dest.
  Dedup decisions are deterministic (no randomness; STAMP passed via env, not `Date.now`).
- **Proposal ledger** (DRY-RUN, no R2 ops): `D:/casebible/exports/sort_proposal_typefirst_root_<STAMP>.{parquet,csv}`.
- **Executed ledger** (provenance, REQUIRED): `D:/casebible/exports/sort_executed_typefirst_root_<STAMP>.csv` —
  every row = `old_path → new_path` + `dest_bucket, type_bucket, sub, source, domain_tags, …, status(ok/ERR), err`.
  **HARD REQ: record old_path→new_path on EVERY raw→sorted copy** (package/associated-file traceability).
- **Durable working store:** `sort_map` table mirrored into `D:/casebible/casebible_work.sqlite` (DuckDB↔SQLite ATTACH)
  for dedup decisions + sort progress + the file registry.
- Ledger schema (executed CSV header): `file_id, old_path, dest_bucket, type_bucket, sub, new_path, source,
  domain_tags, ref_proposed_domain, ref_relevance, ref_doc_type, parties, date_start, date_end, model_tags,
  bytes, confidence, needs_review, status, err`.

## 8. Config / env names (NO secret values — resolved at runtime)
From `cb_connect.py` (credential resolution; nothing hard-coded):
| Name | Default / source | Purpose |
|---|---|---|
| `CB_PG_TUNNEL_PORT` | `15432` | local port for the SSH tunnel to enrichment PG |
| PG DSN | `host=127.0.0.1 port=<tunnel> dbname=casebible user=postgres password=<resolved>` | enrichment connect |
| PG password | read from `Backups/config/cb.env` OR `~/.secrets/casebible-databases.md` OR `CB_PG_PASSWORD` | never hard-coded |
| `CB_MILVUS_URI` | `http://100.119.96.29:19530` | Context Corpus vectors |
| `CB_MILVUS_TOKEN` | `root:Milvus` | Milvus auth |
| `CB_MILVUS_COLLECTION` | `casebible_ai_conversations` | SORT's collection (AI chats/context) |
| `R2_CATALOG_TOKEN` | `~/.secrets/cloudflare.env` OR env | R2 Iceberg catalog |
| R2 account | `1a7406c497493a52128bb282f499e7b8` | catalog/warehouse id |
| `LOCAL_DUCKDB` | `D:/casebible/casebible.duckdb` | dedup md5 snapshot (`r2_files`) |
| `CB_WORK_DB` | `D:/casebible/casebible_work.sqlite` | durable working/registry store |
| `CB_STAMP` | env (scripts can't call Date.now) | ledger filename stamp |
| rclone remote | `r2:` (rclone config) | S3 R2 access; R2 R/W creds in rclone config / `CB_R2_*` env |

SSH tunnel to PG (the one prerequisite before any classification run):
`ssh -i ~/.ssh/ovh -N -L 15432:172.18.0.3:5432 ubuntu@100.91.190.107`  (container IP can drift → re-derive with `cb_refresh_dsn.sh` on ovh2).

---

### Ground truth from the executed root-pile run (verify-before-claiming)
364 content files COPIED raw→sorted (13 top-level type folders) + 35 junk→quarantine; raw root INTACT at 401 objects;
**ZERO deletes, 0 errors**; 195 `needs_review` routed+tagged in place. Ledger:
`D:/casebible/exports/sort_executed_typefirst_root_20260625.csv`. Existing sorted content was UNCHANGED (additive only).
