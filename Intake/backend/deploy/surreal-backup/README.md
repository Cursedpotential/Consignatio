# Surreal Intake backup artifacts

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: link live installation proof | Context: distinguish artifact presence from verified activation -->

These files define, but do not install, the host-side backup schedule for the
independent `surreal-intake` Coolify service.

Deployment status (2026-09-12): these definitions were subsequently installed on
ovh-files; the timer is enabled and active, and a schema restore succeeded.
See [live proof](../../docs/SURREAL-BACKUP-LIVE-PROOF-2026-09-12.md).

- `backup.sh` creates an authenticated SurrealQL export, then an adjacent
  SHA-256 manifest. It obtains credentials only from the environment inherited
  inside the selected container.
- `restore-drill.sh` verifies a manifest and imports only into an explicitly
  named `restore_drill_* / restore_drill_*` target. It always refuses the live
  `consignatio / intake` database and any target with existing tables.
- The `.service` and `.timer` files are the deployment sources. Repository
  presence alone is not activation; the linked receipt records live verification.

Expired backups, failed partial exports, and other removal candidates are moved
under `/data/consignatio/to_be_deleted/surreal-intake-backups`. No script in
this directory permanently deletes files or databases.
