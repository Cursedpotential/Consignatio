# Surreal Intake runtime progress

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 3 | Platform: Codex / win32 | Changes: link live projection and populated restore | Context: continuation supersedes earlier unverified write status -->

## Latest verification — supersedes the earlier interim limits below

Real historical metadata load and replay are now verified: 25 occurrences, one
store, no invented content identities, exact row preservation and zero writes on
replay. The SDK null-erasure issue found by live fixtures is fixed at serialization.
Populated backup restore passed record-count and logical-state-hash comparison
across all 33 tables using a dependency-ordered derived export. Original export,
synthetic fixtures and drill databases remain retained. See
[live proof and identifiers](LIVE-GRAPH-PROOF-2026-09-12.md) and
[historical manifest contract](LEGACY-CATALOG-GRAPH-MANIFEST-V1.md).

Full-corpus/live-manifest reconciliation remains open. The concurrent transfer
task owns B2 operations; the [atomic-rule handoff](ATOMIC-EOD-HANDOFF-2026-09-12.md)
records exact enrichment joins, protected units and unknown prior SQL ownership.

Migration occurrence-map adapter is implemented and live-proven against a
synthetic generation created by the migration builder itself. It preserves every
occurrence and links content only under the migration's source-bound verified
SHA-256 authority. Exact replay issued zero writes. See
[contract](R2-B2-OCCURRENCE-GRAPH-CONTRACT-V1.md). Full backend: 102 tests pass.

The database-scoped `intake_runtime` user was created with EDITOR role in
consignatio/intake. Its independently generated password is stored in Windows
Credential Manager as `INTAKE_SURREAL_PASSWORD.propria-intake-dev`, with username
`INTAKE_SURREAL_PASSWORD` and UTF-16LE credential blob. Read-back was verified;
no secret was printed. The backend get_secret path reads this credential.

The runtime agent verified real SDK readiness using this database account over
`https://surreal-intake.tilapia-skilift.ts.net`, server
`3.2.4+20260803.93ab219`. Python SDK `surrealdb==2.0.0` is pinned in pyproject and
uv.lock. The backend factory fixes the target to consignatio/intake and the
username to intake_runtime, with a bounded connection timeout.

Implemented interfaces:

- `python -m casebible_index.cli graph-status` (set INTAKE_SURREAL_URL to the HTTPS URL).
- `GET /filesystem/graph/status`.
- `GET /filesystem/graph/neighbors/{table}/{key}` with validated node IDs and bounded edges.

No password is returned by these interfaces. A live missing-occurrence probe
returned root_missing=true and zero edges. The implementation agent reported 74
full backend tests passing, then 21 focused tests passing after final timeout
hardening, with scoped Ruff clean.

Live verification corrected two mock-hidden SDK incompatibilities: SDK 2 uses
awaited query results rather than query builders, and HTTP connections require
async context lifecycle rather than connect/close. Neighborhood is one RETURN
statement because this SDK query interface exposes the first statement result.

The write adapter now also supports explicit existing-artifact inventory
projection: snapshot-scoped stores and occurrences, global raw-SHA256 content,
stored_at and occurrence_has_content links. The produced_by edge to a completed
run is written last; a snapshot alone may be partial. Exact replay and interrupted
load/resume are fixture-tested. See [input contract](INVENTORY-GRAPH-MANIFEST-V1.md).

`graph-project-inventory <manifest>` validates without credentials/network;
`--apply` explicitly enables graph writes. No corpus records were inserted by
this implementation or its connection checks. No automatic indexing hook was
added and no lake publication is claimed.

Independent final verification by the primary agent: 81 full backend tests passed
with TEMP/TMP on E:, scoped Ruff passed, and the exact CAS UPDATE and RELATE
statements passed the deployed SurrealDB 3.2.4 syntax validator. Actual graph-write
execution and data-scale reconciliation remain unproven. Two review defects were
fixed with regressions: concurrent operation-run overwrite and accepting an
immutable replay that omitted a previously recorded optional checkpoint.

Read-only authorization checks denied INFO FOR ROOT and INFO FOR NS. After an
HTTP client use() call requesting the separate restore-drill target, session::ns()
and session::db() still returned consignatio/intake. Therefore the successful
subsequent INFO FOR DB was not evidence of cross-database access. No claim of a
comprehensive authorization penetration test is made.

Registered the Tailscale named Service `svc:surreal-intake` with `tag:docker`
and tcp:443. Added the explicit autoApprovers.services rule allowing tag:docker.
The raw HuJSON update preserved existing policy text, passed API validation,
was checked against a fresh read and submitted with If-Match ETag.
The proxy was re-advertised and reported available. Certificate issuance then
completed; local Windows GET and remote HTTP HEAD health checks returned 200 at
`https://surreal-intake.tilapia-skilift.ts.net/health`.

Updated the Tailscale skill cli.md reference with the registration, Service tag,
explicit auto-approval, concurrent policy edit safeguards and verification steps.
The existing broad tagged-service rule alone did not approve this advertisement.

Backup scheduling and schema restore proof are recorded in
SURREAL-BACKUP-LIVE-PROOF-2026-09-12.md.

The timer was rechecked enabled and active after integration, with next run
reported as 2026-09-13 07:25:18 UTC; final remote HTTPS health returned 200.

## Resume next

Select existing inventory/fingerprint artifacts with a verified source identity
and explicit root. Prepare and validate an inventory-projection manifest, then
prove a bounded actual graph write and replay before scaling. Do not infer roots,
scan/hydrate a corpus incidentally, flatten atomic units or move source data.
Current artifacts do not encode a published lake manifest or enough root metadata
to silently wire an automatic publication hook. Full lake reconciliation,
atomic-unit/account/archive projection and consumer completion filtering remain
open. The [table guide](SURREAL-TABLE-GUIDE.md) explains the deployed schema.
