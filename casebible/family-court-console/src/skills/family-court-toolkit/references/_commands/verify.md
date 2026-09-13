---
description: (family-court-toolkit) Verify that the most recent legal work is complete, accurate, and free of hallucinations.
metadata:
  author: Lawvable
  license: AGPL-3.0
  version: 2026.01.07
---
Start from the `family-court-toolkit` entry skill (safety gate first). Members live under `${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/references/`.


## Context

You have just completed a legal task. Before finalizing, you must self-review to ensure quality and reliability.

## Your Task

Review your most recent work and verify:

1. **Completeness** — Does it fully address what was originally asked?
2. **Accuracy** — Are all facts, references, and citations correct?
3. **Consistency** — Is the reasoning coherent and free of contradictions?

If you find issues, fix them. If everything checks out, confirm briefly.

## Rules

- Re-read source documents before confirming extracted information
- Do not invent or assume references — if uncertain, say so
- Flag any assumptions or ambiguities that could affect the conclusion
