# Backend job contract

> _Byline: Codex · GPT-5 · 2026-08-30._

The Workbench invokes governed backend work; it does not execute arbitrary server
commands and does not become the workflow authority. Every request names a registered
job kind and an exact set of stable review-record IDs.

## Start a job

`POST {VITE_WORKBENCH_API_URL}/jobs`

Headers:

```text
Content-Type: application/json
Idempotency-Key: <same value as body.idempotencyKey>
```

Body:

```json
{
  "kind": "prepare-intake",
  "reviewSetId": "album-snapshot-001",
  "recordIds": ["asset-001", "asset-002"],
  "idempotencyKey": "album-snapshot-001:asset-001,asset-002:2026-08-30T12:00:00.000Z",
  "requestedAt": "2026-08-30T12:00:00.000Z"
}
```

The backend authenticates the reviewer, authorizes the job kind and record scope,
persists the idempotency key, and returns one durable `JobRun`. Repeating the same
request must return the same run rather than enqueueing duplicate work.

## Observe a job

`GET {VITE_WORKBENCH_API_URL}/jobs/{runId}` returns:

```json
{
  "id": "RUN-000001",
  "kind": "prepare-intake",
  "status": "running",
  "createdAt": "2026-08-30T12:00:00.000Z",
  "updatedAt": "2026-08-30T12:00:02.000Z",
  "progress": {
    "completed": 1,
    "total": 2,
    "message": "Preparing governed intake request"
  }
}
```

Valid states are `queued`, `running`, `succeeded`, `failed`, and `cancelled`.
Terminal success includes a durable receipt and an opaque result reference; it does
not return evidence bytes in the job-status payload.

## Cancel a job

`POST {VITE_WORKBENCH_API_URL}/jobs/{runId}/cancel`

Cancellation is a governed request, not a process kill. The backend returns the
updated run and records who requested cancellation. Completed runs remain immutable.

## Security boundary

- The browser sends authenticated requests with credentials included.
- The backend must enforce CSRF protection when cookie authentication is used.
- Imported fields can populate typed job arguments but cannot choose executables,
  working directories, URLs, or raw command text.
- Secrets, native paths, and workflow-provider credentials never enter the browser.
- Temporal, n8n, MCP, or registered scripts sit behind the Platform implementation;
  their internal identifiers may be linked from the durable receipt.
