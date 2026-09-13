# Surreal Intake backup and restore-drill runbook

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 2 | Platform: Codex / win32 | Changes: add dependency-ordered populated restore | Context: pre3.3 enforced-relation import defect -->

## Status and boundary

The scripts and systemd units are installed on ovh-files. The daily backup timer
is enabled and active. A systemd-run export and checksum-verified schema restore
succeeded on 2026-09-12. See [live proof](../SURREAL-BACKUP-LIVE-PROOF-2026-09-12.md).
External failure alerts and recurring restore drills are not configured. A later
populated restore passed all 33 table count/logical-hash comparisons; see
[live graph proof](../LIVE-GRAPH-PROOF-2026-09-12.md). This is small-dataset proof,
not data-scale recovery.

The protected source is the independent Intake graph:

- Coolify service: `surreal-intake`
- namespace/database: `consignatio / intake`
- persistent data: `/data/consignatio/volumes/surreal-intake/intake.db`
- backup directory: `/data/consignatio/backups/surreal-intake`
- quarantine: `/data/consignatio/to_be_deleted/surreal-intake-backups`

PostgreSQL/B2 lake state remains canonical. These exports preserve the current
Surreal projection and provide a direct migration path; clean reprojection from
published lake manifests remains the second recovery path.

## Safety properties

`backup.sh`:

1. Takes a non-blocking host lock so scheduled runs cannot overlap.
2. Selects exactly one running container using the stable Compose service label
   `com.docker.compose.service=surreal-intake`; it does not persist a dynamic
   Coolify container ID.
3. Verifies readiness and runs `/surreal export` inside the container.
4. Inherits `SURREAL_USER` and `SURREAL_PASS` inside the container. It never
   reads, prints, stores, or passes either credential as a command argument.
5. Streams the export to a same-filesystem partial artifact, verifies it is
   non-empty, calculates SHA-256, sets mode `0440`, and atomically renames both
   export and manifest into their final names.
6. Records completion and failure events in `events.jsonl` and the system journal.
7. Moves exports older than the configured retention period into a timestamped
   quarantine directory. It never runs `rm` or permanently deletes anything.
8. Preserves a failed partial export in quarantine for diagnosis.

`restore-drill.sh`:

1. Requires explicit namespace, database, and export arguments.
2. Requires both target identifiers to start with `restore_drill_`.
3. Always refuses the live `consignatio / intake` pair.
4. Accepts only a regular, non-symlink `.surql` file directly inside the Intake
   backup directory and verifies its adjacent SHA-256 manifest before import.
5. Refuses a target unless SurrealDB reports zero existing table definitions.
6. Derives a separate dependency-ordered SQL file with `order_restore.py`, preserving
   every original statement and schema enforcement. This is required on the pinned
   pre3.3 server to avoid ENFORCED edges preceding endpoints. Unknown formats/cycles
   are rejected. Installs must copy order_restore.py beside restore-drill.sh.
   Imports using credentials inherited inside exactly one selected container.
7. Verifies that the target has table definitions after import.
8. Leaves the drill database intact for inspection. It performs no cleanup.

## Installation and initial review

Crash-resume review on 2026-09-12: both Bash scripts passed `bash -n` on
`ovh-files`. The restore SQL-result parser passed six cases: raw zero/positive
counts, successful response envelopes, and rejection of error envelopes,
multiple results, and booleans. Python 3 and `systemd-analyze` are available on
the host. ShellCheck is not installed. These checks do not constitute a live
backup or restore drill. The subsequent live proof is linked above.

The review corrected three issues: the original CLI result regex assumed only
response envelopes; the export path check accepted nested paths; and a valid
manifest could name a different export. The restore now parses JSON, requires
the direct backup parent, and hashes exactly the selected export. Backup
failure handling also records failures after a completed export, including
retention failures, and checks both retention destination names before moving.

`restore-drill.sh` requires Python 3 in addition to the standard host commands.
Never invoke Surreal CLI help with inherited credentials: help can display
environment defaults, including passwords. Inspect help only with all credential
environment variables cleared in the inspected process.

An operator should first review the files under
`Intake/backend/deploy/surreal-backup/`. A typical host installation would copy
the scripts to `/opt/consignatio/surreal-intake-backup/` and the unit definitions
to `/etc/systemd/system/`, preserving root ownership and making only the scripts
executable. The operator would then enable the timer through the normal host
change process.

After transferring the deployment files (including order_restore.py) into a new, reviewed staging
directory such as `/data/consignatio/staging/surreal-backup-20260912`, the exact
host installation sequence is below. Inspect existing destinations first; if
they exist, preserve the old versions in a timestamped quarantine directory
before installation rather than overwriting them unseen.

```bash
install -d -m 0750 /opt/consignatio/surreal-intake-backup
install -d -m 0750 /data/consignatio/backups/surreal-intake
install -d -m 0750 /data/consignatio/to_be_deleted/surreal-intake-backups
install -m 0750 /data/consignatio/staging/surreal-backup-20260912/backup.sh /opt/consignatio/surreal-intake-backup/backup.sh
install -m 0750 /data/consignatio/staging/surreal-backup-20260912/restore-drill.sh /opt/consignatio/surreal-intake-backup/restore-drill.sh
install -m 0750 /data/consignatio/staging/surreal-backup-20260912/order_restore.py /opt/consignatio/surreal-intake-backup/order_restore.py
install -m 0644 /data/consignatio/staging/surreal-backup-20260912/consignatio-surreal-intake-backup.service /etc/systemd/system/consignatio-surreal-intake-backup.service
install -m 0644 /data/consignatio/staging/surreal-backup-20260912/consignatio-surreal-intake-backup.timer /etc/systemd/system/consignatio-surreal-intake-backup.timer
systemd-analyze verify /etc/systemd/system/consignatio-surreal-intake-backup.service /etc/systemd/system/consignatio-surreal-intake-backup.timer
systemctl daemon-reload
systemctl start consignatio-surreal-intake-backup.service
systemctl status consignatio-surreal-intake-backup.service --no-pager
```

Verify the new checksum and run the explicit restore drill below before enabling
the timer with `systemctl enable --now consignatio-surreal-intake-backup.timer`.
Confirm the schedule with `systemctl list-timers consignatio-surreal-intake-backup.timer --all`.
This reloads systemd unit definitions; it does not reboot or restart the host.
Scheduling activation was subsequently performed and verified; these commands
remain installation/recovery instructions, not a request to rerun them blindly.

The installed schedule is daily at 03:15 America/New_York with up to 45 minutes
of randomized delay and persistent catch-up after downtime. Default retention
is 30 days. “Retention” means quarantine, not deletion.

Before activation, verify on `ovh-files`:

```bash
docker ps --filter label=com.docker.compose.service=surreal-intake \
  --filter status=running --format '{{.ID}} {{.Names}}'

systemd-analyze verify \
  /etc/systemd/system/consignatio-surreal-intake-backup.service \
  /etc/systemd/system/consignatio-surreal-intake-backup.timer
```

Do not place a password in an `Environment=` line, environment file, script,
shell history, or command argument. The export deliberately executes within the
database container so the existing Coolify-managed credentials are inherited
without being copied to the host process.

## Manual backup verification

Run the installed backup script and inspect its result:

```bash
/opt/consignatio/surreal-intake-backup/backup.sh

cd /data/consignatio/backups/surreal-intake
sha256sum --check --strict consignatio-intake-YYYYMMDDTHHMMSSZ.sha256

journalctl -t surreal-intake-backup --since today
```

The event log should contain `backup_completed` with the artifact name, byte
count, and digest. A failed run should contain `backup_failed`, and any partial
artifact should be under the quarantine root rather than silently discarded.

## Restore drill

Choose new identifiers for every drill. Never reuse a previous target. The
script refuses a target that has existing table definitions.

```bash
/opt/consignatio/surreal-intake-backup/restore-drill.sh \
  --namespace restore_drill_20260912 \
  --database restore_drill_intake_20260912 \
  --export /data/consignatio/backups/surreal-intake/consignatio-intake-YYYYMMDDTHHMMSSZ.surql
```

Success means the manifest verified, the import returned successfully, and the
target reported one or more table definitions. It does not prove application
queries, record counts, or semantic parity. Add those checks when real graph
data exists and the projection reconciliation contract is implemented.

The drill target is retained for explicit human inspection. If it later needs
removal, follow the owner-controlled quarantine process; do not add automated
drop/delete behavior to this script.

## Recovery or migration

For direct recovery into a new physical SurrealDB deployment:

1. Provision a fresh, isolated deployment and pin a compatible SurrealDB version.
2. Transfer the `.surql` export and `.sha256` manifest together over an approved
   authenticated channel.
3. Verify the manifest before import.
4. Import into an explicitly selected namespace/database using credentials
   supplied by that destination's secret manager.
5. Verify schema, record counts, representative traversals, and projection
   checkpoint reconciliation before changing any client endpoint.
6. Preserve the former deployment until the owner approves its quarantine.

The same export can therefore be moved to another server or imported into a new
logical namespace/database. No direct cross-database graph edge is required.
