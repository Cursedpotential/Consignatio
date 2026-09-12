# Integration surface — deferred, not designed

Captured 2026-09-11 so it isn't re-derived later. **Nothing here is decided.**
This records how casekit is expected to meet the wider system, what the current
design already makes easy, and the one decision that should not be deferred.

Read `RULES.md` first — this is guidance, not a plan.

---

## 1 · The Go orchestrator engine

casekit's Go binary is the orchestrator — of **engines**, not of workflows. It
decides which engine reads a file and packages the result. It does not schedule,
retry, or know why it is running.

That boundary is deliberate and worth keeping: casekit is a **called tool, not
a caller.** Path in, one op, files out, exit status. Everything above it —
Temporal, n8n, cron, a shell loop — is somebody else's job.

Its atomic op surface is therefore already the activity boundary for anything
that drives it:

| op | input | output | side effects |
|---|---|---|---|
| `profile` | path | JSON | none — writes nothing |
| `diagnose` | path | JSON | none |
| `extract` | path | extraction JSON + blobs | scratch dir only |
| `package` | path | package dir + ledger line | additive only |
| `index` | packages dir | DuckDB db | fully rebuildable |
| `gaps` | index | JSON queue | none |

Three of six write nothing at all. That matters for anything that retries.

## 2 · Temporal.io

The natural mapping is **one op = one activity**, with packaging as the
workflow boundary. But Temporal retries activities, so each op needs to be
safe to run twice.

Current design mostly gets this free — never in-place, content-addressed
blobs, additive packages — but three things need confirming before wiring:

- **Idempotency key.** Same source hash + same engine version + same op should
  produce the same package id, or a retry creates a duplicate package. Decide
  whether package id is content-derived (deterministic) or time-derived (not).
  The current `CB-<date>-<hash>` shape is half of each.
- **Determinism.** OCR and fuzzy matching are not deterministic across
  versions. Either pin and record the version in the activity result, or treat
  those as non-retryable.
- **Ledger appends under retry.** An append-only JSONL that gets two lines for
  one logical operation is no longer a clean record. Dedupe on the idempotency
  key, or make the append itself idempotent.

Long-running work — a corpus-wide index, a 10,000-image OCR pass — is the
obvious fit for durable execution. Single-file extraction probably is not; it
finishes in under a second.

Note the two orchestration layers are separate and should stay that way. The
Go binary orchestrates **engines** within one file operation. Temporal would
orchestrate **operations** across a corpus. Collapsing them — putting retry
logic or workflow state inside casekit — would make the binary untestable in
isolation and couple it to a scheduler it does not need.

## 3 · n8n

Two surfaces, both already planned:

- **CLI** — shell node calling `casekit <op> --json`. Works today, no daemon.
- **HTTP** — the Phase 8 tsnet API. n8n on the OVH box reaches it over the
  tailnet with no exposed port and no token layer.

n8n is the right place for the "watch a folder, package what lands, notify"
loop. It is the wrong place for the extraction logic itself — that stays in
casekit so it is testable and versioned.

Open: does n8n drive Temporal, or does Temporal drive n8n? They overlap. Pick
one as the scheduler.

## 4 · Promotion into evidence

The two-zone boundary already exists in the Case Bible design: frozen evidence
vault vs agent sandbox, with a custody chain for promotion. casekit produces
**candidates**; promotion is a separate, deliberate act.

Rough shape, undecided:

```
sandbox                          promotion gate                 vault
───────                          ──────────────                 ─────
package sealed      ──►  verify SHA256SUMS independently   ──►  H1 recorded
extraction reviewed ──►  human accepts (R3: Matt decides)  ──►  H2 per message
gaps open/accepted  ──►  coverage threshold met or waived  ──►  H3 chain link
```

Open questions:

- Does promotion copy into the vault, or mark in place and move the boundary?
- What is the minimum to promote — sealed package only, or reviewed extraction?
- Can a package be promoted with `open` gaps, or must they be `resolved` or
  `accepted` first? (Probably yes with open gaps, since R2's bar is a pattern,
  not completeness — but that's a decision, not an assumption.)
- Does demotion exist? If a promoted package is superseded, what happens to
  the chain entry?

## 5 · Hash levels

Matching the existing custody scheme:

| level | over what | when computed |
|---|---|---|
| **H1** | the source file, whole | extraction — already done |
| **H2** | each individual message | **see the flag below** |
| **H3** | tamper-evident chain across entries | promotion |

---

## H2 — resolved

Two corrections, both from Matt, both right. Recorded rather than overwritten
so the reasoning survives.

**First draft said H2 must be computed at extraction.** Wrong. The package
seals the original byte-identical and hashes the whole thing at creation, so
H2 can be recomputed at any time. Timing is not the issue.

**Second, and this is the one that actually resolves it: hash the source bytes,
not the extracted fields.** Every element already carries `offset` and `length`
into the original. H2 over the message's raw byte range is stable forever —
extractor version becomes irrelevant, and no canonical serialization spec is
needed at all. Re-extract with a later casekit and H2 is identical, because
the bytes are identical.

### But H2 means two different things by source

| source | `h2_basis` | unit | version-dependent? |
|---|---|---|---|
| XML | `source_bytes` | `<sms .../>` / `<mms>…</mms>` byte range | **no** |
| JSON | `source_bytes` | message object byte range | **no** |
| PDF | `derived_content` | a construct from header lines + layout | yes |
| OCR / screenshot | `derived_content` | no per-message range exists; image is the unit | yes |

For XML and JSON the file itself defines the message boundary, so the hash is
over something the file actually contains. For PDF and OCR the boundary is the
parse, so the hash is over derived content and **does** need the extractor
version stamped on it.

State `h2_basis` on every row. Blurring the two would let a derived hash read
as though it were anchored in source bytes when it isn't.

JSON note: the mojibake fix means displayed content differs from source bytes.
That is fine — the hash is over the bytes, which is exactly why it stays stable.

### Package validation is two jobs, not one

- **Internal `SHA256SUMS`** proves the package is *self-consistent* — contents
  match the manifest. A modified package with a regenerated manifest passes
  this.
- **The ledger line** proves *identity* — that this is the package that was
  sealed. That reference has to live outside the package, and does.

Per R6 a sealed package never changes; a correction creates a successor naming
its predecessor. So a package whose hash no longer matches its ledger entry is
not a failed validation step — it is a finding.

### What's left to decide

Only where the hash gets computed, and whether promotion recomputes or trusts
the stored value. Neither blocks anything.
