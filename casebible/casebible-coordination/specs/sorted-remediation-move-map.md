# Sorted-bucket remediation move-map (4 mis-structured top-levels)

> _Byline: Claude Code · Opus 4.8 · 2026-06-29_ · **✅ EXECUTED 2026-06-29 (owner-approved: server-side
> moveto + quarantine).** Result: `casebible-sorted` 15,036→14,458 obj. AI Chats & Quarantine top-levels
> GONE; Legal content → Case Management + Knowledge/legal-reference; 484 junk/retired → quarantine bucket;
> ~94 same-name collisions overwritten on consolidation (raw intact = re-derivable). REMAINING: Legal/ +
> Platform/ shells hold only `_root_intake` (62+12) → RECLASSIFY pass clears them. Wiki tension still open.
> Target = the **TYPE-FIRST locked model** (`domain_governance_rules.md`, reconciled 2026-06-29).
> Bucket: `r2:casebible-sorted`. Only the 4 non-conforming top-levels are touched; the 10 locked
> top-levels (Evidence, Knowledge, Tools & Platform, Documents, Exports & Bundles, Inbox, Case
> Management, Entities, Archive, Legacy) are correct and untouched.

## Summary
~**1,010 objects** across 4 folders: ~**933 clean moves**, ~**74 reclassify** (raw intake dumps),
~**8 retire** (dropped-domain governance files). All copy/move stays **within sorted** except
Quarantine → the quarantine bucket. md5 dedup applies on landing (AI Chats likely overlaps existing
`Knowledge/ai-chats`).

## 1. `Quarantine/` (476) → `r2:casebible-quarantine` BUCKET  [clean move]
Quarantine is a bucket, not a sorted top-level.
| From | To | n |
|---|---|---|
| `Quarantine/flagged-junk/**` | `r2:casebible-quarantine/flagged-junk/**` | 457 |
| `Quarantine/shader-junk/**` | `r2:casebible-quarantine/shader-junk/**` | 19 |

## 2. `AI Chats/` (400) → `Knowledge/ai-chats/<platform>/`  [move + platform-detect + dedup]
Stray duplicate of the locked `Knowledge/ai-chats`.
| From | To | n |
|---|---|---|
| `AI Chats/Gemini/**` | `Knowledge/ai-chats/gemini/**` | 128 |
| `AI Chats/Claude-Export-2025-12-08/**` | `Knowledge/ai-chats/claude/**` | 4 |
| `AI Chats/ChatGPT/**` | `Knowledge/ai-chats/chatgpt/**` | 2 |
| `AI Chats/Perplex/**` | `Knowledge/ai-chats/perplexity/**` | 2 |
| `AI Chats/{mattsalem85,salenma}/**` (account dirs) | `Knowledge/ai-chats/<detect|misc>/**` | 33 |
| `AI Chats/<loose files>` (ChatGPT-*.md→chatgpt, *Gemini*→gemini, …) | `Knowledge/ai-chats/<detect|misc>/` | ~231 |
| ⚠ non-chat extensions among the above (.docx/.csv/.pptx) | **FLAG → review** (may be Documents/Knowledge, not chats) | — |
> Note: filenames carry stray `␍` (CR) chars → normalize via `cb_clean_names.clean_path` on the dest.

## 3. `Legal/` (118) → Legal DROPPED, folds out  [mixed]
| From | To | n | action |
|---|---|---|---|
| `Legal/work-product/**` + `Legal/Work Product/**` | `Case Management/work-product/**` | 25 | move |
| `Legal/filings/**` | `Case Management/filings/**` | 8 | move |
| `Legal/knowledge-base/**` + `Legal/Knowledge Base/**` | `Knowledge/legal-reference/**` | 19 | move |
| `Legal/_root_intake_2026-06-22/**` | **re-run type-first classifier** | 62 | reclassify |
| `Legal/{AGENTS,INDEX,Dashboard}.md`, `MANIFEST.json` | retire (dropped-domain governance) → `.to_be_deleted/` | 4 | retire |

## 4. `Platform/` (16) → `Tools & Platform/`  [mixed]
| From | To | n | action |
|---|---|---|---|
| `Platform/_root_intake_2026-06-22/**` (zips, docx specs, html, pptx) | **re-run classifier** (→ Tools & Platform / Documents / Exports & Bundles) | 12 | reclassify |
| `Platform/{AGENTS,INDEX,Dashboard}.md`, `MANIFEST.json` | retire (superseded by Tools & Platform) → `.to_be_deleted/` | 4 | retire |

## Execution notes (gated)
- Within-sorted reorg = server-side `rclone moveto` (copy+delete same bucket) **or** copy-then-quarantine
  the old path — **owner picks** (the no-delete rule is about RAW; sorted reorg moving a misplaced copy
  to its right home is the intent). Quarantine relocation = `rclone copyto` to the quarantine bucket.
- Every op recorded old→new in a ledger (provenance). md5 best-version dedup on landing.
- The ~74 `_root_intake` files do **not** get hand-mapped — they go back through
  `cb_typefirst_ledger.py` so they're classified correctly (avoids re-creating mis-sorts).
- Cost: ~1,010 R2 ops (Class-A) ≈ negligible (<$0.05). No deletes from raw.

## Decisions needed before execution
1. **Reorg mechanic:** server-side `moveto` (cleaner, removes the stale sorted copy) vs copy-then-quarantine?
2. **Retire mechanic** for the 8 dropped governance files: quarantine vs delete-list?
3. **Wiki tension** (separate, flagged in domain_governance_rules.md + AGENT_CONTEXT_MERGE_PLAN.md):
   `Knowledge/wiki` (as sorted) vs the app/platform wiki home — resolve before any wiki move.
