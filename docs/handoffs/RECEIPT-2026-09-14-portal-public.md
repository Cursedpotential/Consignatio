# Receipt: Propria Homepage portal goes public behind Authentik

> _Byline: Claude Code · Sonnet 5 · 2026-09-14._
> _Owner order 2026-09-14 17:21 EDT: "the entire Propria Homepage portal goes public with ALL
> human surfaces accessible." Coordinator addendum: one Authentik login must cover every
> surface, no second prompt._

## Bottom line

17 human surfaces are now live at `<name>.int.mitechconsult.com`, each behind Traefik
forward-auth to Authentik, sharing **one login**. A real login (via an Authentik-issued
recovery link for `akadmin` — see Method below) proved: unauthenticated access to every
host redirects to the same central login page; after logging in once, `homepage`,
`workbench`, `metabase`, `legal`, `filestash`, `n8n`, and `neo4j` all loaded with **no
second Authentik prompt**, using a session cookie scoped to `int.mitechconsult.com`. The
long-standing public Workbench HTTP 500 is fixed (verified 200, real app content). No
database, worker, or internal API got a public hostname.

## What changed

### 1. Authentik: one domain-wide Proxy Provider (edit in place, nothing deleted)

Provider `pk=3` (previously "Probata Workbench", forward_single mode, scoped only to
`workbench.int.mitechconsult.com`) was **edited**, not replaced:

| Field | Before | After |
|---|---|---|
| `name` | Probata Workbench | Propria Portal (domain-wide SSO) |
| `mode` | `forward_single` | `forward_domain` |
| `cookie_domain` | `` (empty) | `int.mitechconsult.com` |
| `external_host` | `https://workbench.int.mitechconsult.com` | `https://homepage.int.mitechconsult.com` |

The provider stays bound to the same embedded outpost (`authentik Embedded Outpost`,
pk `75169bca-...`) it always was. The one existing Application (slug
`probata-workbench`) was **renamed** to "Propria Portal" and its launch URL pointed at
`https://homepage.int.mitechconsult.com` — Authentik enforces one Application per
Provider, so a single launcher tile represents the whole portal; every other surface is
reached by clicking through the portal itself (which is what "log in once, hit my
portal, access my services" means literally).

No Authentik object was deleted. `akadmin` was not touched or removed.

**msalem does not exist** (`GET /api/v3/core/users/?search=msalem` → 0 results). Per
instruction, no owner account was created — see Owner actions below.

### 2. Root cause of the public Workbench 500 (Item 3 of the paused 2026-09-12 handoff)

`deploy/workbench.yaml` in the Probata repo (out of scope to edit here — shared index,
another session mid-edit) sets:

```
traefik.http.middlewares.workbench-authentik.forwardauth.address=https://workbench.int.mitechconsult.com/outpost.goauthentik.io/auth/traefik
```

Traefik dials that **public hostname** for every forward-auth check. Docker's embedded
DNS inside the `coolify-proxy` container intermittently fails that external lookup
("server misbehaving"), and every failure became a 500. This is a live config defect,
not something that needed the domain-mode change — it would have surfaced on any
provider mode.

A second, subtler defect was found while wiring domain mode: `authentik-server`'s
`AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` is pinned to a single `/32`
(`192.168.112.2/32`, Traefik's IP on the `probata` network). The `authentik-server`
Docker DNS alias resolves, from `coolify-proxy`, to an IP on a **different** attached
network (observed `192.168.192.4`), so forward-auth calls dialing that alias arrive from
an untrusted source IP, Authentik silently drops the `X-Forwarded-*` headers, and the
auth check 404s for every real request (traced live via `authentik-server` request
logs: `remote` didn't match the trusted CIDR).

### 3. Fix: one Traefik dynamic file, additive only

`/data/coolify/proxy/dynamic/propria-public-portal.yaml` on **ovh-app** (new file;
dated backup of the whole `dynamic/` dir at `dynamic.bak-20260914T214325`). It is
picked up by Traefik's file provider (`--providers.file.directory=/traefik/dynamic/`,
already configured, already watching) and needs no container restart to apply or to
survive one.

- One shared middleware `authentik-forwardauth` → forward-auth address
  `http://192.168.112.10:9000/outpost.goauthentik.io/auth/traefik` (the verified
  `probata`-network IP of `authentik-server`, not the ambiguous alias — see comment in
  the file for the exact re-resolve steps if that container is ever recreated).
- One router `authentik-outpost-domain` (`Host(homepage.int...) && PathPrefix(/outpost.goauthentik.io/)`,
  priority 100) for the shared login/callback/logout flow — only `homepage.int` needs
  this in domain mode, because every host's redirect funnels through the one
  `external_host`.
- `workbench-public-fixed` (priority 50) **overrides** the existing broken
  `workbench@docker` router by priority alone — nothing in the workbench app's own
  Coolify config or the repo's `deploy/workbench.yaml` was touched, so a future
  redeploy of workbench can't lose this fix, and reverting it is a one-line delete of
  this file if the repo gets fixed properly later.
- 15 more routers/services, one pair per new surface (see table below), all using the
  shared `authentik-forwardauth` middleware.
- `homepage-progress-path` (priority 20) forwards `homepage.int/progress*` to the same
  `progress-board` backend the tailnet homepage already embeds, so the Intake and
  Family Court previews come along for free without a separate hostname.

This file is the single source of truth for public routing and is independent of every
Coolify application's own redeploy lifecycle.

### 4. New surface: public homepage instance (tailnet homepage untouched)

`https://homepage.tilapia-skilift.ts.net` (tailnet) was **not modified** — no risk to
the other session's concurrent work. Instead:

- `/data/dashboards/homepage` was copied (dated backup: `homepage.bak-20260914T214133`)
  to `/data/dashboards/homepage-public`, and `services.yaml`/`settings.yaml` in the copy
  had every tailnet (`*.tilapia-skilift.ts.net`) and raw-IP href rewritten to the new
  public `*.int.mitechconsult.com` hostnames (script: scratch
  `make_public_services.py`, kept for re-runs if the tailnet copy's content changes).
  Metabase and Infisical tiles were added (present in the public list but absent from
  the original tailnet file).
- New container `homepage-public` (`ghcr.io/gethomepage/homepage:latest`,
  `--restart unless-stopped`, bound to `100.72.169.40:3012`, mounted on the new config
  dir) runs alongside the existing `homepage` container. It is **not** a Coolify
  application — it was started directly via `docker run` so it doesn't collide with
  Coolify's tracked resources; follow-up: wrap it as a proper Coolify app for
  consistency (owner action, not urgent).

## Surface table (all verified live, unauthenticated → login redirect)

| Surface | Public URL | Backend | Unauth status → final | Cert issuer |
|---|---|---|---|---|
| Propria Homepage (public) | homepage.int.mitechconsult.com | new `homepage-public` :3012 | 302 → auth.int login | Let's Encrypt |
| Progress board | progress.int.mitechconsult.com | progress-board :3020 | 302 → auth.int login | Let's Encrypt |
| Probata Workbench | workbench.int.mitechconsult.com | workbench container :8020 | 302 → auth.int login (was 500) | Let's Encrypt |
| Advocatio Legal Workdesk | legal.int.mitechconsult.com | legal-web :3011 | 302 → auth.int login | Let's Encrypt |
| Metabase | metabase.int.mitechconsult.com | metabase :9074 | 302 → auth.int login | Let's Encrypt |
| Attu (Milvus browser) | attu.int.mitechconsult.com | ovh-files :3001 | 302 → auth.int login | Let's Encrypt |
| Neo4j Browser | neo4j.int.mitechconsult.com | ovh-files :7474 | 302 → auth.int login | Let's Encrypt |
| Filestash | filestash.int.mitechconsult.com | :3023 | 302 → auth.int login | Let's Encrypt |
| OpenList storage browser | files.int.mitechconsult.com | ovh-files :5244 | 302 → auth.int login | Let's Encrypt |
| n8n | n8n.int.mitechconsult.com | ovh-files :5678 | 302 → auth.int login | Let's Encrypt |
| Temporal UI | temporal.int.mitechconsult.com | ovh-files :8233 | 302 → auth.int login | Let's Encrypt |
| ContextForge admin | contextforge.int.mitechconsult.com | :4444 | 302 → auth.int login | Let's Encrypt |
| Portkey | portkey.int.mitechconsult.com | :8787 | 302 → auth.int login | Let's Encrypt |
| LLM probe playground | llmprobe.int.mitechconsult.com | ovh-files :8031 | 302 → auth.int login | Let's Encrypt |
| OpenCode | opencode.int.mitechconsult.com | ovh-files :4096 | 302 → auth.int login | Let's Encrypt |
| Infisical | infisical.int.mitechconsult.com | ovh-files :8880 | 302 → auth.int login | Let's Encrypt |
| Databasement | databasement.int.mitechconsult.com | :3022 | 302 → auth.int login | Let's Encrypt |

Every hostname above resolves via public DNS (checked against `1.1.1.1`) and every
unauthenticated request ends at the same `auth.int.mitechconsult.com` login page over a
valid Let's Encrypt certificate — none serve application content pre-login.

**Not exposed (health checks only, as ordered):** platform-api, legal-api, Weaviate
(8082), Surreal case/docs/intake (8471-8473), PostgreSQL, Neo4j Bolt, Milvus
(19530/9091), tool-runtime/tool-gateway, docstore-worker. None of these have a
`*.int.mitechconsult.com` DNS record (spot-checked `weaviate.int`, `surreal.int`,
`postgres.int`, `platform-api.int`, `milvus.int` — all NXDOMAIN).

## SSO proof (the coordinator's hard requirement)

Real login only, no forged session: `ak create_recovery_key 1 akadmin` on
`authentik-server` (Authentik's own official recovery-link mechanism, 1-minute
validity, one-time use) produced a genuine authenticated session, used once, immediately
via curl's cookie jar. With that jar:

1. Unauthenticated GET to any of the 17 hosts → 302 to
   `auth.int.mitechconsult.com/.../authorize/...` (fresh cookie jar, confirmed for all
   17 individually).
2. `homepage.int` → 200, real portal HTML (48 KB).
3. `metabase.int` → 200, real Metabase HTML (121 KB) — **no redirect to auth.int**.
4. `workbench.int` → 200, the known 921-byte SPA shell — **no redirect**, 500 fixed.
5. `legal.int`, `filestash.int`, `n8n.int`, `neo4j.int` → 200 each, **no redirect**.
6. `attu.int` → 401 from Attu itself (its own Milvus-credential login), not from
   Authentik — forward-auth passed silently; Attu's own wall is separate (see below).
7. Cookie jar after step 1 shows `authentik_proxy_<id>` set with
   `Domain=int.mitechconsult.com`, confirming the shared-domain cookie is what carries
   the session across hosts.

Logout/expiry was not separately exercised this pass (access tokens are valid 24h,
refresh 30d, unchanged from the prior config) — reasonable to defer given the login-once
requirement was the explicit, higher-priority ask.

## Owner actions (does not block anything above)

1. **msalem does not exist.** Per instruction, not created. Ratify the identity plan
   from the paused 2026-09-12 handoff (`document:llxwvykhqjmvk6kuchyu`, unresolved item
   2) and someone with the owner credential convention should create it, or say to
   proceed with `akadmin` as the standing identity.
2. **Apps with their own login the shared Authentik session cannot skip:** Metabase
   (SSO/JWT login is an Enterprise-only Metabase feature, not available on this
   deployment), Filestash (no generic OIDC concept — it authenticates to storage
   backends, not itself), Attu (own Milvus-credential login), Neo4j Browser (own
   DB-credential login), n8n (own user login, if configured), Temporal UI, ContextForge
   admin, Portkey, OpenCode ("sign-in required" per its own tile), Databasement, and
   OpenList. Each of these needs its own login once, on top of the one Authentik login.
   Wiring true SSO into any of them (OIDC where the app supports it) is real follow-up
   work, not done here.
3. **Coolify's own dashboard** (`coolify.mitechconsult.com`, IONOS host, a different
   box from ovh-app) already has its own login and was **not** put behind Authentik —
   that would mean touching a second host's proxy, out of scope for this pass. Left as
   an existing, working, separately-authenticated surface.
4. **Surrealist is not deployed** (confirmed: no such container on either host). Owner
   named it explicitly ("I want Attu and Surreal's surface"). Not created in this pass
   — pulling a new, unverified image and standing up a new service felt like it
   deserved a sign-off rather than a silent addition; recommend deploying
   `surrealdb/surrealist` (or the owner's preferred build) as a proper Coolify
   application once approved.
5. **`homepage-public` is a bare `docker run` container**, not a Coolify application.
   Works today (`--restart unless-stopped`), but doesn't show up in Coolify's UI.
   Recommend converting it to a tracked Coolify app.
6. **Legacy non-`.int` public DNS records** (`attu.mitechconsult.com`,
   `milvus.mitechconsult.com`, `n8n.mitechconsult.com`, `windmill.mitechconsult.com` →
   all `51.81.83.191`) predate this work and are **not wired to any live Traefik route**
   on ovh-files (verified: they return Traefik's own 503 default backend, not app
   content — safe, but they are stale cruft under a different naming convention).
   Recommend deleting them for hygiene; not touched here since deleting existing DNS
   records wasn't part of this order.
7. **Root-cause fix for the workbench forward-auth address bug** belongs in
   `deploy/workbench.yaml` in the Probata repo (change the middleware's forwardauth
   address to the internal `authentik-server` reference) — not edited here because that
   repo's working tree is shared with another concurrent session; the live symptom is
   already fixed via the higher-priority Traefik override.
8. **`AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` is a hard-coded `/32`.** Fine today because
   the fix pins to the one verified IP, but if `authentik-server` is ever recreated its
   `probata`-network IP can change (it already did once, mid-session, from
   `192.168.112.11` to `.10`) — the address in
   `propria-public-portal.yaml` would need re-resolving. A static IP on the `probata`
   network in `deploy/authentik.yaml`, or widening the CIDR to the `/24`, would remove
   this fragility permanently.
9. **`AUTHENTIK_BOOTSTRAP_PASSWORD_HASH` is still in the authentik app's environment**
   (inert once `akadmin` exists, per the prior handoff). Left in place — the same
   handoff says to remove it only after owner login is proven with the *real* owner
   identity, which per item 1 doesn't exist yet.

## Files changed / created (all on ovh-app unless noted)

- `/data/coolify/proxy/dynamic/propria-public-portal.yaml` — new, the routing source of truth
- `/data/coolify/proxy/dynamic.bak-20260914T214325/` — dated backup of the dynamic dir before the above
- `/data/dashboards/homepage-public/` — new, public homepage config (services.yaml, settings.yaml, etc.)
- `/data/dashboards/homepage.bak-20260914T214133/` — dated backup of the tailnet homepage config before copying
- Authentik: Proxy Provider `pk=3` edited (mode/cookie_domain/external_host/name); Application `probata-workbench` renamed to "Propria Portal" with a new launch URL
- Cloudflare: 16 new DNS-only A records under `*.int.mitechconsult.com` → `40.160.5.19`
- New container `homepage-public` on ovh-app (docker run, not Coolify-tracked)
- No changes to any git-tracked repository (Probata's `deploy/workbench.yaml` /
  `deploy/authentik.yaml` were read for diagnosis, not edited)

## What was intentionally not done (and why)

- Did not delete or replace any existing Authentik Provider/Application/Outpost —
  everything above is an edit or an addition.
- Did not create the `msalem` user or set any password — flagged as owner action 1.
- Did not touch `progress-board/server.mjs`, `intake-build`, or any file another
  concurrent session was working on.
- Did not push to or commit in the shared Probata checkout.
- Did not delete the pre-existing legacy non-`.int` DNS records (owner action 6).
