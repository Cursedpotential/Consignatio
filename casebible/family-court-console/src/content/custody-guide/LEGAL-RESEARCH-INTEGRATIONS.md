# Legal Research Integrations

## CourtListener MCP
This plugin uses the official Free Law Project CourtListener MCP endpoint: <https://mcp.courtlistener.com/>. For Claude Code, the official setup command is:

```bash
claude mcp add --transport http courtlistener https://mcp.courtlistener.com/
```

The plugin’s root `.mcp.json` declares the same remote HTTP server without tokens, headers, client secrets, API keys, user IDs, or OAuth credentials. CourtListener OAuth opens in a browser on first tool call; users need a CourtListener account. CourtListener states that all users receive standard API access automatically, while elevated access may require a Free Law Project membership/donation or commercial arrangement. Check `/mcp` in Claude Code for connection state and troubleshooting.

Official sources: <https://wiki.free.law/c/courtlistener/help/api/mcp/model-context-protocol-mcp-server-for-agentic-access> and <https://wiki.free.law/c/courtlistener/help/api/mcp/using-the-courtlistener-mcp-in-claude-chatgpt-and-other-ai-assistants>.

## Why this integration
CourtListener is the official Free Law Project MCP service. This plugin intentionally does not use CAP/deprecated paths, unofficial scraping services, paid citators, or unverified third-party MCP servers. CourtListener is a discovery aid, not a citator: it cannot justify a Shepardization/KeyCite claim or a comprehensive negative-treatment statement.

## Verification workflow and limits
Confirm case name, citation, court, date, direct opinion URL, quotation against opinion text, published/unpublished or precedential status when available, jurisdictional weight, and negative-treatment limitations. Search results are leads, not holdings. For Michigan opinions, use an official Michigan Courts opinion source as a cross-check when available. Coverage, publication status, opinion text, and treatment data can be incomplete or delayed.

## Privacy and disconnect behavior
OAuth is interactive and managed by Claude/CourtListener; the plugin stores no credential. Do not put protected case records, API tokens, or sensitive facts into a query unnecessarily. If disconnected or a call fails, do not auto-retry: use the bundled source ledger/references or manual official URLs and state the remaining limits.

## MiCOURT Case Search API — assessed, not activated

MiCOURT is an official Michigan case/docket lookup API assessment only; it is not in this plugin’s MCP configuration and no public MiCOURT MCP endpoint was established by the official pages. It may support case-number/participant searches and authorized case metadata/expansion, subject to OneCourtID/JIS permission, subscription, OAuth2 client credentials, subscription key, court key, and approval limits. It does not replace CourtListener for case-law/opinion discovery because the reviewed official docs do not establish opinion text, reporter citation, or precedential-status coverage. See `MICOURT-CASE-SEARCH-INTEGRATION.md`.
