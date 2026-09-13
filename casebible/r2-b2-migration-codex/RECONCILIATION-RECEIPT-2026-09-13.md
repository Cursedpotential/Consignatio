# R2/B2 migration Git reconciliation receipt — 2026-09-13

## Ownership and repository boundary

- Owning repository: `E:/AI_Workspace/Projects/Propria/Consignatio`
- Remote: `https://github.com/Cursedpotential/Consignatio.git`
- Canonical tracked path: `casebible/r2-b2-migration-codex/`
- Reconciliation branch: `codex/r2-b2-migration-reconcile-20260913`
- Linked checkout:
  `E:/AI_Workspace/Projects/Propria/_worktrees/consignatio-r2-b2-reconcile`
- Git common directory:
  `E:/AI_Workspace/Projects/Propria/Consignatio/.git`
- Starting commit: `fa4f249a5c9d69bb7964ea851e71e8cecbab08a9`

The Propria `_worktrees` path is only a linked checkout. It is not a new
repository and does not change ownership. Consignatio remains the repository
that owns this source and its history.

The archived lane began as an untracked directory in the dirty Consignatio main
checkout. That checkout also contains unrelated Intake and Casekit work. The
reconciliation copied only this lane's source, tests, and documentation into the
linked checkout and never staged the dirty main checkout.

## Preserved local-only material

The original lane contained 102 files totaling 96,686,343 bytes. The following
material remains preserved locally but is excluded by this lane's `.gitignore`:

- `.tmp/` and Python bytecode;
- `.venv/` and `runtime/` state;
- `operator-controls/`, including the dated enable-control file;
- `pg18-survivor-copy-*/`, including approximately 95 MB of generated manifests,
  occurrence lists, hashes, and receipts;
- `to_be_deleted/`, including prior safe-operation backups.

These exclusions keep generated data, machine controls, and backups out of Git
without deleting them. After the branch was committed and its exact remote SHA
was verified, the complete 102-file loose directory was moved intact to:

```text
E:/AI_Workspace/Projects/Propria/Consignatio/to_be_deleted/r2-b2-migration-codex-loose-lane-20260913
```

The quarantined directory still contains 96,686,343 bytes. The owner is the only
person who may delete it. The former loose path under `casebible/` is absent in
the main checkout, so it no longer pollutes that checkout's untracked status.

## Reconciled destination contract

Current executable code and operating instructions use:

```text
b2:salem-data/consignatio/intake/raw-dedupe/v1/
```

This is an Intake raw physical-deduplication namespace. Source bucket and object
path are provenance. Neither the destination nor historical names such as
`casebible-sorted` confer sorting, review, acceptance, evidence, or Vault status.

The change covers:

- manifest-builder and CLI defaults;
- manifest finalization;
- payload-runner destination construction;
- conservative transfer-runner prefix guards;
- generation publication path;
- operator examples and runtime documentation;
- positive and negative destination regression tests.

Historical references to `consignatio/vault/v1/` remain only where they document
the superseded incident or prove that the obsolete prefix is rejected.

## Validation

Run with `PYTHONPATH=src`, the shared E: uv cache, and temporary state under the
linked checkout:

```text
python -m unittest discover -s tests -v
12 tests passed

python -m unittest discover -s remote-runtime -p test_*.py -v
25 tests passed

python -m compileall -q src remote-runtime
passed

bash -n remote-runtime/export_live_inventory_after_sha.sh \
  remote-runtime/export_sha256_partitions.sh \
  remote-runtime/finalize_manifest_after_export.sh \
  remote-runtime/launch_transfer_after_review.sh
passed
```

The runtime suite includes a regression that accepts only the Intake raw-dedupe
prefix and rejects the superseded Vault prefix.

## Live boundary at 2026-09-13 03:55 UTC

Read-only `systemctl` proof on `ovh-files` found the transient unit
`consignatio-pg18-r2-to-b2-raw-dedupe-20260912-v2.service` active/running. Its
actual command targets
`b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/$bucket`, uses
immutable rclone copy, and was processing `casebible-raw`. The transfer log had
61,040 `Copied (new)` entries and zero `ERROR` entries at the checkpoint. Current
memory was 350,756,864 bytes and peak memory was 464,908,288 bytes under the
unit's 1 GiB limit.

The source reconciled here has not been deployed. The active copy is a separate
transient unit created from the corrected live command. This Git operation did
not change the unit, its key, B2, R2, an operator gate, or any remote file.

Remaining live work is to let the transfer reach a terminal state, independently
verify destination counts and sampled content identities, freeze the exhaustive
occurrence-to-content map, and publish the governed catalog artifacts. Atomic
unit detection, semantic classification, evidence acceptance, and source
deletion remain outside this physical-copy stage.
