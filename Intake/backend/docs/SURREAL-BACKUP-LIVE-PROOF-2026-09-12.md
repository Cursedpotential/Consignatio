# Surreal Intake backup live proof

Installed backup and restore scripts under `/opt/consignatio/surreal-intake-backup`
on ovh-files. Enabled `consignatio-surreal-intake-backup.timer`: daily at
03:15 America/New_York plus up to 45 minutes jitter. Thirty-day retention moves
exports to owner-only-deletion quarantine. Failures are recorded in the system
journal and backup events.jsonl; external notification is not configured.

The successful systemd-run export is
`/data/consignatio/backups/surreal-intake/consignatio-intake-20260912T151839Z.surql`.
It is 35,065 bytes, SHA-256
`4cfaaae54d10a4c2b437169718c4f3033a838639bf82e48336789bbdae95eba6`.

The checksum was verified and import succeeded into the separate
`restore_drill_20260912/restore_drill_20260912` database on the Intake deployment.
Post-import schema count is 33. This proves schema restore; the production graph
does not yet contain corpus records, so data-scale recovery is not claimed.
The drill database is retained for inspection.

Live fixes: SurrealDB 3.2.4 import requires a file path; '-' is not stdin.
Export to stdout requires `--log none` to prevent log lines contaminating SQL.
Systemd uses ConditionFileIsExecutable, not ConditionPathIsExecutable.

The first log-contaminated test export and checksum were preserved under
`/data/consignatio/to_be_deleted/surreal-intake-backups/log-contaminated-20260912/`.
No files were permanently deleted.
