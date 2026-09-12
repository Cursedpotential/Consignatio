# casekit — Build Guide

## What it is

A local Windows CLI that takes an evidence file, works out what it is, picks
the right tool to read it, extracts everything the file contains, and seals the
original plus the extraction into a verifiable package. Originals are never
modified. Repair is optional and additive.

It exists because evidence formats lie quietly. A PDF transcript in this corpus
silently replaced every emoji with one repeated symbol, and four of the seven
most common PDF readers report that symbol as an ordinary letter.

## Shape

```
                    ┌─────────────────────────────────┐
   Explorer         │        casekit (Go binary)      │
   right-click ────►│                                 │
                    │  profile → route → extract      │
   CLI ────────────►│      ↓        ↓        ↓        │
                    │   6 signals  rules   check      │
   (later) tsnet ──►│                  ↓              │
                    │              package + seal     │
                    └──────────┬──────────────────────┘
                               │ JSON over stdin/stdout
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌───────────┐    ┌───────────┐
        │ poppler  │    │  pypdf    │    │  duckxml  │
        │ oneshot  │    │  worker   │    │  worker   │
        │   C++    │    │  Python   │    │ Py+DuckDB │
        └──────────┘    └───────────┘    └───────────┘

        any language, one contract, drop-in discovery
```

## The pipeline

```
file ─► PROFILE ─► ROUTE ─► EXTRACT ─► CHECK ─► PACKAGE
        6 cheap    rules    one         profile   original +
        signals    table    engine      predicts  extraction +
                            + raw       output    blobs + hashes
                            channel     ↓ fail
                                     escalate to next engine
```

**Profile** — size, format, images, text volume, is-it-a-conversation, who
made it. Producer string is the strongest signal; the same exporter always
produces the same shape.

**Route** — first matching rule in a hand-editable table wins. Returns a ranked
engine list.

**Extract** — one engine, plus a raw content-stream channel when the profile
flags glyph substitution.

**Check** — the profile predicts what the output must contain. If it said 33
symbol glyphs and the engine returned zero non-ASCII, the engine is wrong.
No second opinion needed. Escalate.

**Package** — original byte-identical, extraction, blobs, reports, manifest,
`SHA256SUMS`. Verifiable with stock `sha256sum` and nothing else.

## Read in this order

1. **`RULES.md`** — outranks everything else here
2. `FINDINGS.md` — what the real files actually contain
3. `STACK.md` — what to build it with
4. `GOTCHAS.md` — what will bite you, mostly things already hit
5. `SPLIT.md` — the engine contract
6. `PHASES.md` → `PROMPTS.md` — sequence and copy-paste tasks
7. `DIAGRAMS.html` — everything above, visually
