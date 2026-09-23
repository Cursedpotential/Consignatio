---
title: EvidenceVault becomes narrow — explicit promotion lifecycle and the nine domains
date_shared: 2026-09-20
shared_by: owner (pasted mid-turn into a Claude Code session, 23:59 EDT)
source_service: not stated by the owner
capture: verbatim as pasted (an excerpt; the surrounding conversation was not shared)
tags: [transcript, consignatio, evidencevault, promotion, lifecycle-state, provenance, vault-domains, advocatio-integration]
related:
  - ../../../Legal-desktop/docs/transcripts/2026-09-20-unattributed-consignatio-evidence-integration-handoff.md
---

> _Byline: Claude Code · Fable 5.1 · 2026-09-20 (saved verbatim; no facts added)_

## Transcript

EvidenceVault becomes very narrow now
And I think this is exactly what you were getting at.

```
EvidenceVault/
├── INDEX.md
├── Dashboard.md
├── _Incoming/       # promotion staging only
├── promoted/
├── exhibits/
├── manifests/
└── ...
```

Nothing gets routed directly from the B2 mess into EvidenceVault merely because it looks evidentiary.
Instead:

```
B2 mess
   ↓
Triage / domain _Incoming
   ↓
canonical context home
   ↓
processing + analysis
   ↓
EXPLICIT PROMOTION
   ↓
copy into EvidenceVault
   ↓
hash / manifest / provenance / promotion record
   ↓
IMMUTABLE
```

The original context object stays in its canonical home.
The promoted evidence object becomes a separately governed immutable artifact.
That distinction is important enough that I think the metadata should literally carry something equivalent to:

```
lifecycle_state: context
```

versus, after an explicit promotion:

```
lifecycle_state: evidence
promotion_id: ...
promoted_from: ...
promoted_at: ...
source_hash: ...
```

The promotion operation, not the folder classifier, is what creates evidence.
So I think we now have the right nine domains

```
1. Triage
2. Recovered
3. SourceCorpus
4. KnowledgeBase
5. DerivedKnowledge
6. CaseManagement
7. EvidenceVault
8. Code
9. Archive
```
