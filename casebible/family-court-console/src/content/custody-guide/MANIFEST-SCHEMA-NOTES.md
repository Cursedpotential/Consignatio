# Manifest Schema Notes

Validated against the official plugin spec at
https://code.claude.com/docs/en/plugins-reference (fetched 2026-08-11).

## Auto-discovery, not enumeration (v1.3.0)

`plugin.json` carries **identity and metadata only**: `$schema`, `name`,
`displayName`, `version`, `description`, `author`, `license`, `keywords`.

It declares **no component-path fields** (`skills`, `commands`, `agents`,
`hooks`, `mcpServers`, `lspServers`). Claude Code auto-discovers every
component from its default location:

| Component | Default location scanned | Notes |
|---|---|---|
| Skills | `skills/<name>/SKILL.md` | Finds `custody-packet/` and `toolkit/` |
| Commands | `commands/*.md` | All nine slash commands |
| Agents | `agents/*.md` | All four subagents |
| Hooks | `hooks/hooks.json` | Case-law prompt + tool hooks |
| MCP | `.mcp.json` at plugin root | `courtlistener`, credential-free HTTP |

**Why omit the arrays.** The spec says an explicit `commands`/`agents` field
*replaces* the default scan, and `skills` *adds* to it. Enumerating them means
the manifest must be maintained in lockstep with the files on disk — and it
drifted once already (a new command was missing from the list until caught).
Omitting them makes drift impossible: the folders are the source of truth.
`plugin.json` becomes minimal and matches the canonical examples in the docs.

## Namespacing

The plugin `name` (`family-court-toolkit`) namespaces every component. Users
invoke:

- Commands: `/family-court-toolkit:packet`, `/family-court-toolkit:motion`, …
- Skills: `/family-court-toolkit:custody-packet`, `/family-court-toolkit:toolkit`
- Agents: `@family-court-toolkit:case-law-researcher`, …

## The scoped MCP name is coupled to `name`

The bundled MCP server's tools are exposed as
`mcp__plugin_<name>_courtlistener__*`. That scoped string is wired into four
places, and a rename must reach all of them or the case-law integration
silently loses access:

1. `hooks/hooks.json` — the PostToolUse / PostToolUseFailure matchers
2. `hooks/case_law_tool_hook.py` — the `TOOLS` regex
3. `agents/case-law-researcher.md` — the `tools:` grant
4. `agents/michigan-source-verifier.md` — the `tools:` grant

`tests/test_claude_plugin_schema.py::test_scoped_mcp_name_tracks_plugin_name_everywhere`
enforces this across the whole plugin and fails on any stale name.

## Safety posture (unchanged)

The MCP file is the current remote HTTP shape (`type: "http"`, URL
`https://mcp.courtlistener.com/`) with no credentials. Hook commands are
root-relative `${CLAUDE_PLUGIN_ROOT}` executables that emit deterministic JSON
context only — no network activity, no tool-output mutation, no persistence.
