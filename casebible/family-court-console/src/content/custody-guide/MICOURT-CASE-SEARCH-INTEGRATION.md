# MiCOURT Case Search Integration Assessment — Documentation Only

## Status
**Not implemented, not configured, and not activated.** This plugin has no MiCOURT API/MCP connector, no MiCOURT credentials, and no MiCOURT entry in `.mcp.json`. The official pages reviewed do not establish a public MiCOURT MCP endpoint or Case Search coverage of opinion text, reporter citations, published/unpublished status, or precedential status. CourtListener remains the active case-law/opinion discovery MCP.

Official sources: <https://developer.micourt.courts.michigan.gov/docs/case-search>, <https://developer.micourt.courts.michigan.gov/get-started>, <https://developer.micourt.courts.michigan.gov/docs>, and <https://developer.micourt.courts.michigan.gov/products>.

## Appropriate potential use: case and docket lookup
The official Case Search API describes case lookup in a court/courts by case number or participant name, with filters. It documents filters such as case type/category, status, public status, judge, date fields, and other case metadata filters. When access permits, documented expansion resources include judge, referee, next hearing, and participants. These are docket/case-data functions, not a documented opinion/citation/citator product.

## Access and authentication requirements
Use requires a OneCourtID and MiCOURT Developer Portal/JIS permission. JIS provides a OneCourtID or portal permissions, confirms Starter subscription readiness, and reviews non-Starter subscription requests. Most MiCOURT REST calls require a `Jis-Api-Subscription-Key` subscription key. All endpoints require client authorization; official REST basics describe OAuth2 client-credentials bearer-token access. A `client_id` and `client_secret` are provided only after application registration and a court-data access request/approval. Many court-specific calls require a court key; the official Court API can generate it. Do not place any of those values in chat, this plugin, source control, or a prompt.

## Starter and court-data limits
The official pages state that Starter has limited daily calls/functionality. Case Search documentation says Starter returns only the first 10 search results and disallows expansion; changing limit/offset does not alter those Starter constraints. Actual court-data access may require a package upgrade and JIS approval or additional court access. Official pages do not clearly state price, a free allowance, or a public free quota; this plugin must not call MiCOURT free.

## Safety, privacy, and manual workflow
Use public/manual case lookup only for a legitimate case-management need. Do not search sealed, suppressed, adoption, nonpublic, or otherwise restricted information; do not seek `View Suppressed` or other restricted data. Minimize personal identifiers, avoid DOB/driver-license/vehicle-plate searches unless independently authorized, retain no unnecessary identifiers, and follow court/JIS authorization rules.

If a user separately configures approved MiCOURT credentials outside this plugin, the conceptual workflow is: verify permission and subscription; obtain a court key when court-specific data is needed; obtain a client-credentials bearer token through the approved process; include the subscription key; use bounded public case-number/participant lookup; and respect Starter/result/expansion restrictions. This plugin does not perform those steps, request credentials, call the API, or retain any resulting data.

## Distinguish docket metadata from case law
MiCOURT case/docket data does not establish a holding, opinion text, reporter citation, precedential status, publication status, or negative treatment. Use CourtListener discovery plus primary opinion verification for case-law research; cross-check Michigan opinions against official Michigan Courts material when available. Never turn case-search metadata into legal authority.
