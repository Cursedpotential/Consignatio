# PROPOSAL — Unified web control / viewing surface (owner directive ⑤)

> _Byline: Claude Code (PIPELINE) · Opus 4.8 · 2026-06-27_
> **Status: PROPOSAL for owner review — DO NOT BUILD until an option is chosen.**
> Directive (TASKS 03:20 ⑤): "one place to view / tweak / change / monitor EVERYTHING —
> mine the original design intent, propose architecture (extend AgentOS UI vs dedicated
> dashboard) as an ADR/spec for review BEFORE building."

## 1. The constraint that shapes this (locked, not negotiable here)
PROJECT_CANON §5 (locked 2026-06-13): **"Use Agno's NATIVE surface — do NOT rebuild it."**
AgentOS already ships, self-hosted: a **Control-plane UI** (manage/monitor/debug agents,
teams, workflows), a **Chat UI** (AgentUI), and native **sessions · memory · knowledge ·
evals · config (per-domain models/quick-prompts) · auth/JWT**, plus multi-surface serving
(AG-UI, Slack, WhatsApp, Telegram, A2A). Canon: *"We do not build a custom chat UI, control
UI, or multi-surface serving; we configure Agno's."*

→ So ⑤ is **NOT** "build a dashboard." It is: **make AgentOS the spine, and unify the
NON-Agno surfaces around it** with the thinnest possible layer (minimize-custom-code rule).

## 2. The fragmentation today (why the owner wants this)
Everything works but lives on its own port/domain with its own auth:

| Surface | Where | Auth | Covers |
|---|---|---|---|
| AgentOS API + control UI + os.agno.com | `agentos.mitechconsult.com` | bearer `OS_SECURITY_KEY` | agents/teams/workflows, sessions, memory, knowledge, evals, config |
| AgentUI (chat) | `chat.mitechconsult.com` | same | chat with agents, run workflows |
| Full control plane (Kasm browser) | `browser.mitechconsult.com` | Coolify | a real browser into the tailnet |
| ContextForge (MCP gateway) | `mcp.mitechconsult.com` + admin `:4444` | CF admin | MCP tool catalog/gateway |
| Tools facade (parsers/SBV proxy) | `100.72.169.40:8090` (tailnet) | none (tailnet) | 11 parser tools, SBV proxy, OpenAPI |
| SBV (SMS viewer/exporter) | `100.72.169.40:8085` (tailnet) | SBV session | manual message upload/view/export |
| Attu (Milvus UI) | `100.119.96.29:3001` (tailnet) | none (tailnet) | vector collections |
| Coolify (infra control plane) | `100.98.98.38:8000` / `coolify.mitechconsult.com` | Coolify | deploy/restart/logs for everything |
| Windmill (Case Bible) | `100.91.190.107:8000` (tailnet) | Windmill | rclone/orchestration jobs |
| n8n | Ionos | n8n | automation flows |
| Neo4j browser / graphiti-mcp / PG / SurrealDB | OVH-3 (tailnet) | per-DB | data tier |

The owner has to remember ~11 URLs, 3+ networks (public domains vs tailnet IPs), and several
logins. "View/tweak/change/monitor everything" = collapse this into **one pane of glass**.

## 3. Options

**Option A — AgentOS-native only (configure, don't add).**
Push everything possible into AgentOS's control UI (it already does agents/sessions/memory/
knowledge/evals/config/auth). Link out to the rest.
- ➕ Zero new code; pure canon-compliance. ➖ AgentOS UI does NOT and will not surface
  infra (Coolify), vector admin (Attu), SBV manual upload, ContextForge catalog, DB browsers,
  n8n/Windmill — those stay scattered. Doesn't actually satisfy "monitor EVERYTHING."

**Option B — dedicated custom dashboard (build a new web app).**
A bespoke React/Next app that aggregates every service's API into one UI.
- ➕ Total control. ➖ Directly violates canon §5 ("do not build a custom control UI") +
  minimize-custom-code; large surface to build/maintain; re-implements what AgentOS already gives.
  **Not recommended.**

**Option C — AgentOS spine + an OFF-THE-SHELF portal for the rest (RECOMMENDED).**
Keep AgentOS as the agent/evidence/knowledge control plane (canon-compliant), and stand up a
**single off-the-shelf "start-page" portal** ([Homepage](https://gethomepage.dev) /
[Glance](https://github.com/glanceapp/glance) — lightweight, YAML-config, Docker, widget-based)
as the ONE entry domain. The portal gives:
- **Live health/status tiles** for every service (HTTP/TCP checks — agentos, mcp, facade,
  SBV, Attu, Coolify, Milvus, the 4 data-tier DBs, Windmill, n8n).
- **One-click links** (and embedded iframes where the target allows) to each surface.
- **At-a-glance widgets**: Coolify app states, Milvus collection counts (via facade), evidence
  row counts (via a small read-only facade endpoint), recent deploys.

Unify access with what we ALREADY run: **Traefik (on OVH-1) + one domain** (e.g.
`hub.mitechconsult.com`) + **forward-auth SSO** (Traefik forward-auth → a small OIDC/auth
proxy, or reuse the existing basic-auth/bearer) so one login fronts the public surfaces;
tailnet-only tools stay reachable via the portal's links over Tailscale.
- ➕ ~No custom app code (YAML + compose + Traefik labels we already use); canon-compliant
  (AgentOS not rebuilt — just surfaced alongside); genuinely "everything in one place";
  reversible (delete one Coolify app). ➖ Some targets can't be iframed (X-Frame-Options) →
  those become deep links, not embeds. SSO across heterogeneous auth (CF/SBV/Coolify) is
  partial — portal unifies *navigation + health*, not necessarily *single-sign-on* to each.

## 4. Recommendation
**Option C.** It satisfies "view/monitor everything in one place" with off-the-shelf parts,
respects the locked "don't rebuild Agno UI" decision, and adds the *only* genuinely missing
thing — a single health-and-navigation hub over the fragmented surfaces. AgentOS stays the
place you "tweak/change" agents/knowledge/config; the portal is the place you "view/monitor
everything + jump to the right tool." Build order if approved: (1) Homepage/Glance as a Coolify
app under `hub.mitechconsult.com`; (2) health checks + links for all ~11 surfaces; (3) facade
read-only status endpoints (evidence counts, Milvus collections) for the data widgets;
(4) optional Traefik forward-auth SSO pass.

## 5. Open questions for the owner
1. **Scope of "tweak/change":** is AgentOS-native config (per-domain models, quick-prompts,
   memory, knowledge) enough for the "change" verb, with the hub owning "view/monitor + navigate"?
   Or do you want write-actions (restart a service, trigger a deploy, run a parse) surfaced *in
   the hub itself*? (The latter is a bigger build — Coolify/facade already expose those APIs, but
   wiring action-buttons is more custom code.)
2. **One domain + SSO**, or is a tailnet-only hub (no public exposure, simplest/safest) fine?
3. **Embed vs link:** OK with deep-links where a tool blocks iframing (SBV, Coolify, Attu often do)?
4. Portal pick: **Homepage** (more widgets/integrations) vs **Glance** (lighter)? I'd default Homepage.

## 6. Does NOT belong here (kept separate on purpose)
- AgentOS's own UI work (agents/knowledge/evals) — that's directive ③ (Graphiti into the
  runtime) + native config, not the hub.
- SBV-as-evidence-entry (directive ④) — that's a facade/custody wiring task; the hub merely
  *links* to SBV.

→ On owner pick, I promote this to a numbered ADR (next free ~0034; reconcile vs the
0032/0033 drafts) and, if Option C, stand up the portal as a reversible Coolify app.
