# Bearing: the Propria Project Portal and its surfaces

> _Byline: Claude Code · Fable 5.1 · 2026-09-14 00:35 EDT — read-only reconnaissance for the owner's testing pass. Sources: live probes, VPS container/config inspection, Docstore (probata/workbench/infra), memsearch, project memory. Nothing was changed._

## What "the portal" is

**`https://homepage.tilapia-skilift.ts.net`** — Tailscale service `svc:homepage` on **ovh-app** (100.72.169.40).

| Piece | What it is | Where it lives |
|---|---|---|
| Portal page (`/`) | `ghcr.io/gethomepage/homepage` dashboard, titled **"Propria Project Portal"**, dark theme, five rows | container `homepage` :3010 · config `/data/dashboards/homepage/` (`services.yaml`, `settings.yaml`, `bookmarks.yaml`) — authored by Codex 2026-09-12 as the *"interim entry point for one integrated Propria product"* |
| Progress board (`/progress`) | custom Node 22 app `propria-progress-board` v0.1.0 — Surreal-`docs`-backed lanes (in flight / done / upcoming), catalog + migration reports, health probes, embedded previews | container `progress-board-…` :3020 · code `/data/dashboards/progress-board/` (`server.mjs`, `surfaces.json`, `health-endpoints.json`, `health.mjs`, `openlist-bridge.mjs`, `intake-preview/`, `family-court-preview/`) |

**Provenance gap:** neither the homepage config nor the progress-board code is in the Probata repo (`deploy/` has no definition; `grep` for `dashboards`/`progress-board` finds nothing). They exist only on the VPS filesystem. Docstore holds no ADR or handoff for the portal — only a mention in `COMPACT-SUMMARY-2026-09-08` and the 2026-09-08 TODO. Per the owner's 2026-09-12 decisions (universal Docstore; monorepo root), this needs registering.

**Lineage:** ADR-0061 *Unified operator shell with bounded capability surfaces* (Agno-MCP-Platform era) reached prototype/contract-census, was never owner-accepted past preflight, and its deploy artifacts were retired 2026-09-07. The homepage launchpad is the lightweight replacement.

## The surfaces it aggregates (live check 2026-09-14 00:20 EDT)

**Workspaces row**

| Surface | URL | Live | Notes |
|---|---|---|---|
| Probata workbench (Evidence Operations Desk) | `workbench.tilapia-skilift.ts.net` | `/` `/intake` `/evidence/preview` `/tools` `/matter` all **200** (same 921-byte SPA shell) | `GET /api/tools` → `[]`; `/api/health` and `/api/monitored-actions/capabilities` → **404**. This is the Docstore-flagged critical finding *"Probata function access is broken"* (2026-09-12): the Atomic Tools flow fails closed — no execution API, empty governed catalog, `MCP_SERVERS` defaults to `[]`. Owner's word: *utterly broken*; not a baseline. |
| Advocatio legal workbench | `legal.tilapia-skilift.ts.net` (API `legal-api.*`) | **200** | portal tile still points at the raw IP `100.72.169.40:3011`; should be the service DNS per the port/DNS standard |
| Consignatio / Case Bible Intake | `homepage…/progress/intake/` | preview | "VPS component preview · Xplorer + metadata review · shared context integration pending" |
| Michigan family court toolbox | `homepage…/progress/family-court/` | preview | "Eight-view read-only preview · no live case data or legal results" |
| Live service & storage health | `homepage…/progress/health/` | — | drives `health-endpoints.json`: platform-api, workbench `/health`, legal-api, ContextForge, n8n, OpenList API+WebDAV, Weaviate ready/meta, Surreal case/docs/intake, PostgreSQL… |

**Storage and databases row:** OpenList (`files.*` :5244), Filestash (setup, OpenList WebDAV pending), Neo4j Browser, Surrealist (*not deployed*), PostgreSQL + Weaviate read-only explorers at `workbench…/schemas`, Attu (Milvus), Databasement (setup, no jobs).
**Operations row:** Coolify (100.98.98.38:8000), Temporal, n8n, ContextForge admin, Portkey.
**Preview pipeline row:** LLM probe playground, OpenCode server, LibreChat (stopped).

**Convention drift to note:** the port/DNS standard (Docstore 2026-09-12) says humans use only Tailscale service DNS; several tiles still use raw 100.x IPs. Human portals are class 90NN (Docstore portal = 9072; Probata = product 71 → 9071 would be the standardized portal port).

## What "testing" can mean today

- **Portal itself:** loads (200, 39 KB), progress board loads (200). Reachability tiles are monitors, *not* feature proof (the yaml says so).
- **Probata:** shell routes render; the operator can browse the DEV placeholder matter and the source browser; any tool/function execution path is dead by design until `POST /api/monitored-actions` + capabilities exist and MCP servers are configured (gateway=portkey). Tests that pass today assert source strings only.
- **Advocatio:** renders; authority boundary and two-clock chronology per the surface-design contract; adoption lane UNASSIGNED.
- **Intake / Family Court:** static previews served by the progress board, no live data.

## Related standing decisions (Docstore, critical, active)
- Docstore is the universal Propria documentation plane (2026-09-12) — the portal config/code should be registered there.
- Propria surface design contract: Carbon-Linen-Seal tokens, Evidence Operations Desk (General) / Modular Service Cockpit (Advanced, gated, no route), Legal Workdesk, Family Court Console; adoption lanes unassigned.
- Port class prefix + stable product suffix + Tailscale DNS only.
- CCC / Intake / Docstore are three isolated systems.

## OWNER DECISION 2026-09-14 07:53 EDT — the whole portal goes public

> _Byline: Claude Code · Opus 5 · 2026-09-14. Docstore: `note:propria_homepage_portal_public_20260914`._

- **Decision:** "the entire 'homepage' self host portal goes public with all the links."
- **Applied by precedent:** public hostnames use `<name>.int.mitechconsult.com`, so the portal is `homepage.int.mitechconsult.com`. It sits behind Traefik and one Authentik login. Tailscale is unchanged; Cloudflare is DNS only.
- **Order:** (1) Authentik owner identity `msalem`, as the 09-12 handoff requires before any public surface. (2) Portal public. (3) Each linked surface gets a public route, with login/deny/logout/bypass proof per surface.
- ~~**Open, owner to confirm:** the DB/admin consoles and the board's OpenList storage API widen the 09-12 "never public" list.~~ **Resolved 07:55 EDT (owner):** "all human surfaces accessible… if it's a human surface I want it… I want Attu and Surreal's surface and Filestash." Databases and APIs are **health checks only**. The agent-written 09-12 "tool gateways and storage bridges never go public" was "literally opposite of what I asked."
  - **08:19 owner — NEXT SURFACE PRIORITY:** "the Xplore CB surface is the next surface that needs to be up and working, and it's the furthest from usable." The Xplorer case-bible / Intake surface comes after the current quick fixes (Portkey + ContextForge confirmed on the public list, Filestash repair, subtle homepage tile colours).
  - **08:18 owner:** "don't forget Portkey and ContextForge" (both already on the public human-surface list); "Filestash down"; "add colors to the app buttons to make them easier to distinguish — not tacky, don't overdo it."
  - **08:07 owner (queued, not yet actioned):** "I also don't like the board as is": the progress board (`/progress`) needs a redesign or replacement. The owner's target (08:07): "more project-management app style, with widgets and tracking boards." Take it up after the Metabase deploy; don't change it now.
  - **08:06 owner:** "Metabase is a first-class Coolify app": deploy it through Coolify's one-click Metabase service (`metabase/metabase:latest` + `postgres:16-alpine` app DB), then add the DuckDB driver and verify live whether the image supports it (glibc).
  - ~~**08:02 owner:** interim data front ends are CloudBeaver, Metabase and NocoDB.~~ **08:04 owner: Metabase only** ("can it also do what noco was going to… 3 seems much"). It is the single data site: catalog browsing and filtering, SQL, dashboards, and the DuckDB driver for Parquet on B2 ("do it"). It is a human surface behind Authentik on read-only DB users until the custom Storybook/Glide/TanStack system exists. The DuckDB plugin needs a Debian-based image. No Parquet on B2 yet.
  - **07:59 owner:** "raw and unfinished is fine, I want to see progress and direct deployment." Surfaces deploy as-is; no polish gate.
  - **07:57 owner also named:** the **Legal Workdesk** (Advocatio → `legal.int.mitechconsult.com`) and the **family-law surface** (Family Court Console / `projects/family-court-workbench` → `family-court.int.mitechconsult.com`). It has no production deployment yet; only the board's read-only preview is live.
  - **Public behind Authentik:** portal and progress board, Workbench (incl. /schemas explorers), Advocatio Legal Workdesk, Family Court Console, OpenList web UI, Filestash, Surrealist (deploy), Neo4j Browser, Attu, Databasement, Coolify, Temporal UI, n8n, ContextForge admin, Portkey UI, LLM probe, OpenCode, Infisical, LibreChat (stopped).
  - **Health checks only:** platform-api, legal-api, OpenList API/WebDAV, Weaviate, Surreal ×3, PostgreSQL, Neo4j Bolt, Milvus, service /health endpoints.

## ADDENDUM 2026-09-14 03:15 EDT — what this bearing missed

> _Byline: Claude Code · Opus 5 · 2026-09-14. The owner said this bearing "doesn't even mention half the things in it." Sources: DuckDB over Claude and Codex session logs, Docstore (`sq.py` and `docstore_get`), read-only inspection of `/data/dashboards` on ovh-app, and live status probes. Nothing was changed._

**1. The portal is meant to become the *authenticated owner portal*, not only a tailnet launchpad.**
- **Owner decision** `docs/decisions/2026-09-12-authentik-owner-correction.md` sets **two access lanes**.
  - **Trusted owner lane:** the existing Tailscale routes, untouched and unfettered.
  - **Public browser lane:** Internet → public HTTPS on the existing Coolify **Traefik** → **Authentik** login, session and **launcher** → only explicitly approved human-facing surfaces.
  - Cloudflare is DNS only: no Tunnel, Access or Workers.
  - OIDC authorization-code flow where supported. Otherwise an Authentik proxy provider, trusting identity headers only from the exact Traefik peer.
  - Never public: DBs, workers, internal APIs, tool runtime or gateway, storage bridges, native/Tauri command surfaces.
  - Each surface needs proof of: DNS/TLS, unauthenticated deny, login, session-bound use, direct-origin bypass resistance, logout/expiry, and unchanged Tailscale.
- **Docstore handoff** `document:llxwvykhqjmvk6kuchyu`, "Probata recovery accountability and authenticated owner portal – 2026-09-12". It is STATUS PARTIAL / PAUSED FOR OWNER REVIEW. Its unresolved list:
  1. Owner portal hostname and the full surface/route/role matrix (not ratified).
  2. Authentik bootstrap created **`akadmin`**; the owner identity must be **`msalem`**.
  3. **Public Workbench HTTP 500** (layer undiagnosed).
  4. Remove the inert `AUTHENTIK_BOOTSTRAP_PASSWORD_HASH` after owner login is proven.
  5. Reconcile the uncommitted Intake/Proffer operator-workflow work (the separate Proffer New Run task `01a050b5…` owns the Go start cutover).
  6. Durable operator controls.
  7. Image/OCR/vision routing.
  8. n8n production binding (unassigned).
  9. Context-package vs evidence-admission routing.
  10. Stale imported active handoffs.
- It also records six root-agent errors, including an auto-deploy after saying deploys were held.

**2. Live state re-probed 2026-09-14 ~03:10 EDT.**

| Endpoint | Result |
|---|---|
| `auth.int.mitechconsult.com` | 302 → Authentik default authentication flow |
| `workbench.int.mitechconsult.com` | **500** (still broken) |
| `coolify.mitechconsult.com` | 302 → /login. **This is the correct Coolify browser URL**; the portal tile's `100.98.98.38:8000` is the API/tailnet endpoint |
| homepage `/`, `/progress/`, `/progress/health/`, `/progress/intake/`, `/progress/family-court/` | 200 |
| `legal.*`, `files.*`, `infisical.*`, `workbench.*` | 200 |
| `workbench…/api/tools` | still `[]` |

Authentik containers (server, worker, postgres) run on ovh-app, healthy, up about 21 hours.

**3. Progress board internals** (`/data/dashboards/progress-board/server.mjs`, Codex 09-12, a read-only projection).
- Reads Surreal `probata/docs` tables **`todo`** (≤500) and **`portal_observation`** (≤300) via `/api/board`.
- `/api/health-report` is driven by `health-endpoints.json`, which includes Probata Platform, Workbench, Advocatio API, ContextForge, n8n, OpenList API+WebDAV, Weaviate 8082, Surreal case 8471 / docs 8472 / intake 8473, PG, Neo4j Bolt and Milvus. Disconnected/undeployed notes cover the Intake Xplorer and metadata backends, the Family Court MCP runtime and Filestash.
- **Intake preview** serves versioned builds from `intake-build/releases/<release>` via `current.json`: release `2026-09-12T16-01-25-624Z`, 617 source files, fingerprinted.
- **`/intake/storage/api/<command>` and `/intake/storage/api/asset`** proxy to OpenList through `openlist-bridge.mjs` (`OPENLIST_TOKEN`). This is a storage bridge on the portal host, which the public-lane rule says must never be exposed.
- Supporting files: `diagnose.mjs`, `validate-homepage.cjs`, `outputs/live-service-storage-health.html`.
- `surfaces.json` lists **Infisical** (`infisical.tilapia-skilift.ts.net`), which the homepage does not.
- Compose is Homepage only, tailnet-bound `100.72.169.40:3010`, with `HOMEPAGE_ALLOWED_HOSTS` set. Dashy was retired 2026-07-19.
- `portal_observation` lanes: Project portal (1 done, 2 in progress), **Identity and access (in progress)**, Storage and Infrastructure (**blocked** rows), Consignatio Intake ("schema ready; population not started", "awaiting current ledger", one interrupted). **The newest observation is 2026-09-13 02:48 UTC.** The Codex automation `refresh-propria-portal-reports` has not refreshed it since.

**4. No collision found:** today's other Authentik-mentioning sessions (subagents 06:42–07:04 UTC) are a read-only Weaviate-ownership investigation, not portal work.

## Open items surfaced by this pass
1. Register `/data/dashboards/{homepage,progress-board}` as tracked source (Probata `deploy/` + Docstore) — today they are VPS-only.
2. Replace raw-IP tiles with service DNS (`legal.*`, `files.*`, `neo4j.*`, `n8n.*`, `temporal.*`, `contextforge.*`, `portkey.*` all exist).
3. Probata execution path (monitored-actions API + MCP catalog) is the blocker for any functional test beyond browsing.
4. Surrealist viewer not deployed; the progress board reads Surreal `docs` directly (env `SURREAL_DOCS_*`).
