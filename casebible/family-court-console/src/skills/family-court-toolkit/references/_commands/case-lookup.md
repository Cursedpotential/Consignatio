---
description: (family-court-toolkit) Guide a public/manual Michigan case lookup or assess separately configured MiCOURT Case Search API readiness
argument-hint: '[case number, court, or public lookup goal]'
allowed-tools:
- Read
- Grep
- Glob
disable-model-invocation: false
---
Start from the `family-court-toolkit` entry skill (safety gate first). Members live under `${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/references/`.


Use the `family-court-toolkit` entry skill and `content/custody-guide/MICOURT-CASE-SEARCH-INTEGRATION.md`. This plugin has **no MiCOURT connectivity** and must not make API calls or request credentials in chat. For public/manual lookup, identify the court, public case number or minimal participant information, the lawful purpose, and the official court-facing lookup route. Do not search sealed, suppressed, adoption, nonpublic, or otherwise restricted data; minimize personal identifiers and do not retain unnecessary identifiers.

If the user has separately configured, approved MiCOURT access outside this plugin, describe only the guarded workflow: OneCourtID/JIS portal permission, an approved subscription/key, client-credentials bearer-token process, and court key where required. Starter has limited calls/results and disallows expansion. Do not ask for, display, paste, store, or validate a subscription key, bearer token, client ID, or client secret.

MiCOURT case/docket metadata is not case-law authority and does not establish opinion text, reporter citation, precedential status, a holding, or negative treatment. Use `case-law` and CourtListener/primary-source verification for those questions.
