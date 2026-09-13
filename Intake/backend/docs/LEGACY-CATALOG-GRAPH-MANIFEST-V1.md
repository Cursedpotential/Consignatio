# Historical catalog projection input

This adapter imports at most 100 explicitly selected historical catalog rows.
It does not scan or open source files, create raw-content identities, move bytes,
or claim that old catalog rows are fresh filesystem observations.

```json
{
  "schema": "intake-legacy-catalog-projection-v1",
  "imported_at": "2026-09-12T20:00:00+00:00",
  "catalog_locator": "caller-supplied-database-and-table-locator",
  "source_query": "Exact query or selection description used to export these rows",
  "source_roots": {
    "bucket-name": {
      "root_locator": "caller-supplied-source-root",
      "store_kind": "historical-catalog-store",
      "label": "Human-readable source name"
    }
  },
  "rows": [
    {
      "bucket": "bucket-name",
      "path": "original/catalog/path.txt",
      "name": "path.txt",
      "ext": ".txt",
      "size": null,
      "md5": null,
      "modtime": "2020-01-02 13:14:15",
      "mimetype": null,
      "tier": null
    }
  ]
}
```

All nine original row fields are required, including fields whose values are
null. Additional row keys are retained unchanged in `metadata.catalog_row`.
Missing size stays unknown; zero stays zero. MD5 remains historical metadata and
does not establish raw SHA-256 identity. Original modification values remain
unparsed, including timezone-naive strings. No `modified_at` is emitted.

`occurrence.observed_at` is the explicit aware `imported_at`, with metadata basis
`catalog import observation, not source observation`. The imported row's path
spelling is retained in both path fields without claiming normalization.
`entry_kind` is `other` because this contract lacks verified file/directory/symlink
status. No source-relative interpretation is imposed on historical path strings.
They are stored as data and never executed or opened.

The whole JSON input is validated before graph access: at most 1 MiB, between
1 and 100 rows, explicit aware import time, locator, source query, bucket roots,
nonempty bucket/path/name, and null or nonnegative signed-64-bit size. Duplicate
bucket/path pairs fail closed. The input is reread to detect changes during
validation. The exact manifest SHA-256 defines the immutable snapshot identity.

Creates only `projection_snapshot`, `store`, `occurrence`, `stored_at`,
`operation_run` and `produced_by`. Store and occurrence identities include the
snapshot digest. Occurrence bucket/path identities use JSON tuple serialization
to avoid ambiguous separators. A `produced_by` edge to a completed operation is
written last; until it exists the snapshot may be partial. Exact replay is a
read-only operation. No content nodes or content relationships are emitted.

<!-- Updated by: Codex | Date: 2026-09-12 | Rev: 1 | Platform: Codex / win32 | Changes: document tested CLI entrypoint | Context: preserve opt-in write boundary -->

CLI validation (local, no graph credentials required):

```powershell
.venv/Scripts/python.exe -m casebible_index.cli graph-project-catalog E:/path/manifest.json
# Explicit historical metadata graph write, never an object copy:
.venv/Scripts/python.exe -m casebible_index.cli graph-project-catalog E:/path/manifest.json --apply
```

Backend invocation (explicit execution only; no automatic pipeline hook):

```python
from pathlib import Path
from casebible_index.projections.legacy_catalog import load_legacy_catalog, project_legacy_catalog
from casebible_index.projections.runtime import connect_graph

plan = load_legacy_catalog(Path("E:/path/explicit-historical-sample.json"))
async with await connect_graph() as graph:
    result = await project_legacy_catalog(graph, plan)
```

The caller owns source selection and exclusions. Store roots and catalog query
provenance are supplied explicitly; the adapter never guesses them. Secrets must
be excluded when preparing rows and query descriptions. Test fixtures prove null
preservation, unknown-versus-zero size, raw naive-time retention, occurrence
preservation without content assertions, invalid provenance rejection, duplicate
row rejection, row bounds, and immutable replay. Live sample execution belongs
to the separately recorded runtime receipt.
