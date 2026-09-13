# Intake SurrealDB migrations

This directory contains the schema for the dedicated Consignatio/Intake
filesystem graph. The graph is a rebuildable investigative and organizational
projection. PostgreSQL and lake manifests remain canonical; this database is
not the downstream evidence system and does not inherit evidence acceptance,
custody, legal-authority, credentials, or approval state.

## Database boundary

Apply these files only after explicitly selecting the dedicated namespace and
database (currently expected to be `consignatio` / `intake`). Do not apply them
to the Docstore graph or the downstream evidence graph. The migration does not
create a namespace, database, user, credential, or data record.

Example, with credentials supplied through `SURREAL_USER` and `SURREAL_PASS`
rather than command-line arguments:

```powershell
surreal import `
  --endpoint http://SERVER:PORT `
  --namespace consignatio `
  --database intake `
  .\0001_filesystem_graph.surql
```

Before applying, validate against the exact deployed CLI version:

```powershell
surreal version
surreal validate .\0001_filesystem_graph.surql
```

## Invariants

- PostgreSQL/lake receipts are canonical; SurrealDB can be rebuilt from a
  published manifest and projection checkpoint.
- A path-level `occurrence` is never collapsed merely because its `content`
  hash matches another occurrence.
- Atomic-unit nesting is represented by direct `contains` edges and is never
  flattened.
- Original archive parts, multipart series, export events, and account
  associations remain explicit provenance objects.
- Imported facts, machine proposals, and human decisions occupy separate
  tables or relations and carry fixed authority-layer values.
- Machine proposals never overwrite source facts. Human decisions are
  append-only overlays; corrections use `supersedes_decision`.
- Graph edges never cross into another SurrealDB database. Cross-system
  correlation uses stable external IDs and receipts at the application layer.
- This schema performs no filesystem moves, deduplication, or deletion.

## Rollback and retirement

There is intentionally no destructive down migration. Do not use `REMOVE`,
`DELETE`, or filesystem deletion as an automated rollback. If this projection
must be retired, stop writers, capture an export and schema receipt, and move
the database export or obsolete migration material into the project-controlled
`to_be_deleted` quarantine for owner review. Only the owner permanently deletes
quarantined material.

Because this graph is rebuildable, recovery is performed by creating a fresh
empty projection database and replaying a verified canonical manifest. Never
treat rebuilding the graph as authorization to alter canonical lake objects.
