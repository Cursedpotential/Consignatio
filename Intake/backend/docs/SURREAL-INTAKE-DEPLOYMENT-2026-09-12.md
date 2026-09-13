# Surreal Intake deployment receipt — 2026-09-12

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 2 | Platform: Codex / win32 | Changes: record bounded live data and restore | Context: completed subsequent live proof -->

## Outcome

Consignatio Intake now has a third, physically independent SurrealDB deployment.
It does not share a SurrealDB process, RocksDB store, root identity, Coolify
resource, or lifecycle with either the downstream evidence graph or Docstore.

| Item | Value |
|---|---|
| Coolify project | `consignatio` |
| Coolify project UUID | `wwa0zxg6ckg9ufsjv3slrd8f` |
| Coolify service | `surreal-intake` |
| Coolify service UUID | `av9iykza3zdq7s9uwa3cmoss` |
| Server | `ovh-files` (`cn89l8801u8gsginw1rxq5qt`) |
| Image | `surrealdb/surrealdb:v3.2.4` |
| Storage engine | `rocksdb:/data/intake.db` |
| Host storage | `/data/consignatio/volumes/surreal-intake` |
| Host endpoint | `100.91.190.107:8473` (Tailnet interface only) |
| Namespace / database | `consignatio / intake` |
| Root identity | `intake_root`; password stored only in the Coolify service |

The compose source of truth is
`Intake/backend/deploy/surreal-intake.compose.yml`. The database schema source of
truth is `Intake/backend/migrations/surreal/0001_filesystem_graph.surql`.

## Boundary

PostgreSQL and the published B2/lake manifests remain canonical. This SurrealDB
database is a rebuildable filesystem, provenance, temporal, atomic-unit, and
review graph. It is not the downstream evidence database and it is not the
Docstore database.

The deployment is also network-isolated from the shared `probata` Docker network.
It is exposed only on the `ovh-files` Tailnet address, not on `0.0.0.0`.

## Applied schema

Migration `0001_filesystem_graph.surql` was validated and imported into
`consignatio/intake` using SurrealDB 3.2.4. Live `INFO FOR DB` verification found:

- 33 schema-full tables.
- 19 typed, enforced relation tables.
- Separate imported-fact, machine-proposal, and human-decision layers.
- No evidence/source data inserted by the migration.

The schema preserves duplicate occurrences and nested atomic units. A duplicate
proposal or possible extraction is an edge/proposal; it does not delete, collapse,
or silently rewrite an occurrence.

Migration SHA-256 after adding the SurrealDB 3 import preamble:

`3deaf3ef13184c68118d584b1cf13252b2188d3cbc8187bc073d7007cbc1a9f2`

## Verification

- Coolify-managed container reached Docker health state `healthy`.
- `GET http://100.91.190.107:8473/health` returned HTTP `200` from the local
  Tailnet client.
- Host socket inspection showed only `100.91.190.107:8473`, not a wildcard bind.
- Root authentication succeeded after a Coolify-managed restart.
- `INFO FOR ROOT` showed the `consignatio` namespace and `intake_root` identity.
- `INFO FOR DB` showed all 33 intended tables and no query errors.
- An authenticated export completed successfully.

First export receipt:

| Item | Value |
|---|---|
| Artifact | `/data/consignatio/backups/surreal-intake/consignatio-intake-20260912T140622Z.surql` |
| Size | 35,065 bytes |
| SHA-256 | `4cfaaae54d10a4c2b437169718c4f3033a838639bf82e48336789bbdae95eba6` |
| Mode | `0440` |

This proves the database can be exported for migration. A future destination can
import the SurrealQL export into a selected namespace/database, or Intake can
rebuild the projection from canonical lake manifests using stable IDs and
checkpoints.

## Corrected bootstrap and quarantine

The first API-created service boot left its Coolify magic variables empty, so
SurrealDB initialized an empty-name root user. No Intake schema or source data had
been written. The service was stopped through Coolify, the empty RocksDB store was
moved intact to:

`/data/consignatio/to_be_deleted/surreal-intake-empty-bootstrap-20260912T135620Z/intake.db`

Nothing was permanently deleted. The owner is the only person who may delete the
quarantined copy.

The administrative password was rotated again after a CLI help invocation exposed
the then-current value in local command output. The exposed value is no longer
valid. The replacement value was generated in memory, written to Coolify without
being printed, applied to the root user, and verified after restart.

The pre-`OPTION IMPORT` copy of the migration was also preserved at:

`/data/consignatio/to_be_deleted/surreal-intake-migration-pre-import-option-20260912T140300Z/0001_filesystem_graph.surql`

## Post-crash integration verified

- Database-scoped `intake_runtime` credentials are provisioned through Windows
  Credential Manager; the renderer never receives the database password.
- The Python SDK 2.0.0 backend factory, readiness CLI and bounded read-only graph
  API are implemented. Authenticated HTTPS readiness passed against all 33 tables.
- `https://surreal-intake.tilapia-skilift.ts.net` is reachable privately. The named
  Service is registered with `tag:docker` and an explicit matching auto-approval
  rule; local Windows and remote health checks returned HTTP 200.
- The daily export timer is enabled and active. Thirty-day retention quarantines
  old exports; failures are journaled. A checksum-verified schema restore into a
  separate drill database succeeded. External alerts and recurring restore drills
  are not configured.

See [runtime proof](SURREAL-RUNTIME-PROGRESS-2026-09-12.md) and
[backup/restore proof](SURREAL-BACKUP-LIVE-PROOF-2026-09-12.md).

## Deliberately pending

The graph now contains 25 real historical catalog occurrences plus explicitly
synthetic integration fixtures. Exact replay and a small populated restore are
verified; see [live proof](LIVE-GRAPH-PROOF-2026-09-12.md). End-to-end live/lake
manifest reconciliation, full graph UI wiring, full-corpus loading and data-scale
restore verification remain separate unfinished work.
