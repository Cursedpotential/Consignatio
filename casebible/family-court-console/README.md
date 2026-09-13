# family-court-console — Docker build source

> _Byline: Claude Code · Sonnet 5 · 2026-09-07_

This directory holds the build source for the `family-court-console` Coolify app
(`deploy/family-court-console.yaml`) — the family-court-toolkit MCP console
served over MCP Streamable HTTP and federated through ContextForge (owner
rulings 2026-09-07 16:16-17:12: the console runs in the cloud as its own
Coolify app; no client downloads anything).

## Why this directory exists

The family-court-toolkit plugin — including this MCP server's TypeScript
source, its `content/` (~55 MB of curated legal-reference material), and its
`skills/` — lives **outside** this repo, on the desktop at
`~/.claude/local-plugins/plugins/family-court-toolkit/`. It is a Claude Code
local plugin checkout, not a probata module, and Coolify's git-based
"Docker Compose" build can only see files committed to this repository.

`src/` in this directory is a **synced copy of the plugin's runtime subset**,
committed here so Coolify has something to build from:

```
deploy/docker/family-court-console/
  README.md          <- this file
  src/               <- COMMITTED sync target (small: dist ~5 MB + content ~55 MB)
    Dockerfile.cloud
    .dockerignore
    mcp-app/
      dist/           <- pre-built esbuild output (node build.mjs run in the plugin)
      package.json
      package-lock.json
    content/          <- curated legal-reference material the server reads at runtime
    skills/           <- skill markdown the server's tools reference (e.g. court-language)
```

`deploy/family-court-console.yaml` builds from `./docker/family-court-console/src`
with `dockerfile: Dockerfile.cloud`.

## Keeping it in sync

Whenever the plugin's `mcp-app/src/*.ts`, `content/`, or `skills/` change:

1. In the plugin checkout, rebuild: `cd ~/.claude/local-plugins/plugins/family-court-toolkit/mcp-app && node build.mjs`
2. From this repo, re-sync: `bash scripts/sync_family_court_console.sh`
   (accepts an optional `PLUGIN_ROOT` argument; defaults to
   `$HOME/.claude/local-plugins/plugins/family-court-toolkit`)
3. Review the diff under `deploy/docker/family-court-console/src/` and commit it
   in the same change as anything that depended on the update.

The sync script never deletes: it quarantines any existing `src/` under
`_stale/` (this repo's standard quarantine pattern — see `AGENTS.md`) before
copying a fresh one in. Only the owner clears `_stale/`.

## Why `dist/` is committed, not built by Coolify

This image never runs `esbuild` or `tsc` itself — `Dockerfile.cloud` only runs
`npm ci --omit=dev` (for `surrealdb` + `@surrealdb/node`, both esbuild
externals per `mcp-app/build.mjs` — `@surrealdb/node` ships native `.node`
binaries that cannot be bundled) and then copies the already-built
`mcp-app/dist/`. Building on the desktop, where the full toolchain, tests, and
the SurrealDB dev store already exist, and shipping only the build artifact
keeps the Coolify build fast and keeps this repo from needing a Node/esbuild
toolchain of its own for a service it does not otherwise own.

## Directory-shape dependency (do not flatten this)

The server resolves `content/` and `skills/` at runtime via
`pluginRootPath()` (see the plugin's `mcp-app/src/core.ts`,
`court-language.ts`, `survival-guide.ts`): two directories up from
`dist/server.js`, i.e. `dirname(dist/server.js) + "/../.."`. That is why
`Dockerfile.cloud` places `content/` and `skills/` directly under `/app`,
sibling to `mcp-app/`, reproducing the desktop plugin's own directory shape
exactly. Do not reorganize this layout without updating
`pluginRootPath()` in the plugin source first.

## Runtime configuration

See `deploy/family-court-console.yaml` for the full compose definition. In
summary, the container:

- Serves MCP Streamable HTTP (`MCP_TRANSPORT=http`) on `0.0.0.0:8765`, path
  `/mcp`, with a required bearer token (`MCP_BEARER_TOKEN`) and
  unauthenticated `/healthz` + `/version`.
- Connects to the shared case store at `CUSTODY_CASE_DB=ws://surreal-case:8000`
  (the `surreal-case` Coolify app on the same `probata` Docker network — see
  `deploy/surreal-case.yaml`), signing in with `CUSTODY_CASE_DB_USER` /
  `CUSTODY_CASE_DB_PASS`. Those two values must match the credentials
  configured as `SURREAL_USER` / `SURREAL_PASS` on the `surreal-case` app —
  they are the same root credential, held under different env-var names on
  each side because `surreal-case.yaml` names the server's own credential and
  `family-court-console.yaml` names the client's.
- Is stateless: no volume. All case data lives in `surreal-case`, not here.

## ContextForge registration

See
`plugins/family-court-toolkit/docs/2026-09-07-case-store-registers.md`
(this repo does not carry that file — it lives in the plugin checkout,
alongside the rest of `docs/` there) for the exact `POST /gateways` body and
client-side `.mcp.json` / config snippets for pointing Claude Code, Codex,
OpenCode, and Gemini at this console through ContextForge.
