@AGENTS.md
@AGENT_MEMORY.md

Use the root Claude guardrails inherited from `../CLAUDE.md`. Work from this
directory for frontend commands. Read `docs/DEVELOPMENT.md` before changing module
boundaries. Do not turn a frontend demo into a claim of real backend execution.

## Project Conventions (applied via /reflect 2026-09-15)
- Intake surfaces (review/metadata, search, jobs, chat) are native panels in the Xplorer client tree (`xplorer-copilot-buildkit/xplorer-copilot/apps/client/src`) reading the engine's own selection state. The docked-iframe review panel fed by `src/data/sampleReviewSet.ts` was the wrong tool for a panel that shares live selection and writes back (owner 2026-09-14 22:02-22:08; not a ban on iframes: portals may frame apps). Deployed builds never render sample data. Decision file: `Probata/probata/docs/decisions/2026-09-14-intake-native-panels-no-iframes.md`, indexed in the Propria Docstore.
- The `casebible-corpus` backend (index runs + `serve`) runs on the VPS, not on localhost:8765; the portal-served web build reaches it same-origin through a proxy under the portal (its CSP is `connect-src 'self'`). Owner 2026-09-14 23:02. Hosting of the Xplorer-era backend waits for the Spacedrive verdict.
- Owner acceptance test for the file engine (2026-09-14 22:28-23:20): every filesystem date (created/modified/accessed/added/moved), embedded EXIF/media metadata, catalog data, custom sidecar data with programmable discovery patterns, unit assignment with parent/sibling tree placement keyed by content identity, full owner CRUD (remove = retract with history), all hosted on B2. Evidence and verdicts: `docs/SPACEDRIVE-GATE-2026-09-14.md`.
- PDF readers: `projects/consignatio/repair-tool-kit/FINDINGS.md` (2026-09-11) is the seven-reader bake-off on a real evidence transcript and rules until re-tested: poppler/pypdf/pdfium decode the ZapfDingbats glyph (U+25A0, 33/33), pdfminer/pdfplumber/pdf.js return the raw byte, mutool is rejected. OpenDataLoader ran the same test on 2026-09-15 and DROPPED the glyph silently (0/33, a fourth category worse than mutool) — it is NOT a text reader for evidence; usable only as a layout/table/OCR engine, and only with the text layer taken from a passing reader. Docling remains the planned complex-PDF route (backend MASTER-TODO Phase 7). Spike: `docs/OPENDATALOADER-SPIKE-2026-09-14.md`.
