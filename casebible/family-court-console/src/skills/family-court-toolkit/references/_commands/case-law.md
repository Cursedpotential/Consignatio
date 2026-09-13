---
description: (family-court-toolkit) Research Michigan or family-court case law with CourtListener discovery and primary-source verification
argument-hint: '[issue, case name, citation, or jurisdiction]'
allowed-tools:
- Read
- Grep
- Glob
- Bash
disable-model-invocation: false
---
Start from the `family-court-toolkit` entry skill (safety gate first). Members live under `${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/references/`.


Use `toolkit` and the `case-law-researcher` workflow. If CourtListener MCP is connected, use it for discovery; first use opens interactive browser OAuth and must not be triggered silently. If disconnected, explain the connection option and use bundled/manual official sources.

For each candidate authority: verify exact case name, reporter/citation, court, decision date, direct opinion URL, quoted language against the opinion, published/unpublished or precedential status when available, jurisdictional weight, and negative-treatment limitation. Treat search results as leads, not holdings. Never claim Shepardization or KeyCite. Cross-check Michigan decisions against official Michigan Courts opinion material when available. Return direct URLs and an explicit verification-status table.
