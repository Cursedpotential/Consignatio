# casekit — build kit

Planning output for a local evidence extraction and packaging tool.
Generated 2026-09-11. Greenfield, single workstream.

## Read in this order

| # | File | What it is |
|---|---|---|
| 1 | **`RULES.md`** | **Operating agreement. Outranks everything else here.** |
| 2 | `BUILD_GUIDE.md` | One-page orientation and architecture sketch |
| 3 | `FINDINGS.md` | What the real evidence files actually contain, with reproduction commands |
| 4 | `STACK.md` | Chosen stack, versions, rejected alternatives |
| 5 | `GOTCHAS.md` | Ranked failure modes — most were hit during planning |
| 6 | `SPLIT.md` | The engine contract (the boundary that matters) |
| 7 | `PHASES.md` | Build sequence with hard exit criteria |
| 8 | `PROMPTS.md` | Copy-paste task prompts, one per phase |
| 9 | `TOOL-CATALOG.md` | Everything needed to build and run |
| 10 | `DIAGRAMS.html` | All of the above, visually — open in a browser |

## Scaffold

`scaffold/` is the stub tree. Every file carries a `TODO(claude)` naming what
goes there and which phase implements it. Copy it to the repo root to start.

## Start here

```
cd <repo>
# paste PROMPTS.md → Phase 0 into Claude Code
```

Phases 0–6 are the usable product. 7–10 are deferred deliberately — do not
start them until 0–6 are running on real files.

## Known open questions

Six, listed in `DIAGRAMS.html` §12. **None of them block Phases 0–5.**

## One thing worth knowing before you start

The reference PDF in this corpus silently replaced every emoji with a single
repeated symbol, and four of the seven most widely used PDF readers report that
symbol as an ordinary letter. That is why this tool exists, why there is no
default engine, and why every extraction is graded against a prediction derived
from the file itself.
