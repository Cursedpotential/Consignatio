# Catalog reconciliation

Byline: Codex | 2026-09-20

This additive layer retains the existing catalog, captures B2 metadata, and exposes
source occurrences and object versions as queryable data. No source content is read
or changed. An occurrence is identified by source, scope, path and provider ID;
it is never collapsed into a content hash.

Run from the Consignatio repository, with Python's existing `pyarrow` and `duckdb`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='E:\AI_Workspace\.tmp'
$env:TMP=$env:TEMP
python -B casebible/catalog_reconcile/run.py capture --generation docs/receipts/catalog-reconciliation-2026-09-20/generation-NEW
python -B casebible/catalog_reconcile/run.py build --generation docs/receipts/catalog-reconciliation-2026-09-20/generation-NEW
python -B casebible/catalog_reconcile/lakehouse.py --generation docs/receipts/catalog-reconciliation-2026-09-20/generation-NEW
python -B casebible/catalog_reconcile/publish.py --generation docs/receipts/catalog-reconciliation-2026-09-20/generation-NEW
```

The last command only describes publication. `--apply` explicitly publishes the
validated generation to new dated `raw_duck.reconcile_*_20260920` tables and the
`catalog_reconcile` SQL views. Publication is one transaction. Historical corpus
tables are not updated. The schema contract is checked before reuse.

Each generation is append-only. A failed generation is preserved and cannot be
published. Do not rerun a phase over its partial outputs: use a new generation.
Capture uses compressed SSH streaming with read-only database sessions. B2 permits
only account authorization and metadata listing APIs. Credentials stay in memory.

Parquet stores complete source records as lossless JSON strings. Typed PostgreSQL
and DuckDB views provide SQL access while preserving uncommon provider fields.
This is a functional metadata lakehouse slice; it is not an Iceberg/Delta catalog
or a claim that every source item has passed forensic validation.

`validated_metadata_reconciliation` means fingerprint and row-conservation checks
passed. Sequential PostgreSQL captures and paginated B2 lists are observation
windows, not a cross-provider atomic snapshot. SHA-1/size and inherited MD5 bridges
are recorded matching evidence; they do not grant retention or deletion authority.

Every occurrence starts with `bas_status=not_assessed` and
`retirement_status=not_cleared`. Office/PDF export availability does not prove
preservation of an editable Google native source. Historical versions are linked
explicitly. Atomic package roots and membership remain separate records.

`probe_google.py` optionally checks a bounded set of mapped Google file IDs using
metadata-only requests. It refreshes credentials in memory and never rewrites the
rclone config. `--oldest` selects the oldest mapped items instead of the first
items. Include each probe output with `run.py build --probe <probe-directory>`.
Live native observations can support provisional BAS #1 candidates in a separate
view; they do not change the occurrence's unassessed content-quality status.

The live `casebible` database has **pg_duckdb 1.1.0**, with embedded **DuckDB 1.4.3**,
verified by an actual `DuckDBScan`. Use `python -B casebible/catalog_reconcile/analytics.py availability`
for the named read-only analytics path. `native_candidates` and `duplicate_totals`
are also supported; `--explain` shows actual execution. The tool opts into DuckDB
only within its transaction and disables external access and extension installation.
Ordinary PostgreSQL views remain usable without changing global engine settings.
Some PostgreSQL-specific JSON functions are not supported in the DuckDB path;
the named reports use compatible expressions directly over the dated facts.

Direct server-side Parquet/B2 access is a separate connection/capability check.
This run proves DuckDB execution over PostgreSQL facts, not end-to-end B2 Parquet
access. No extension installation, global setting change or database restart was needed.

After publication, `verify_live.py --generation <directory>` checks the live views;
`summarize.py` and `report.py` produce the inventory and verified human receipt.
The receipt generator describes the dated first slice and requires successful
live read-back. `query_examples.sql` provides bounded PostgreSQL queries.

Run safety tests with `python -B -m unittest discover -s casebible/catalog_reconcile -p test_*.py`.
See the dated specification and receipt under `docs/receipts/catalog-reconciliation-2026-09-20/`.
