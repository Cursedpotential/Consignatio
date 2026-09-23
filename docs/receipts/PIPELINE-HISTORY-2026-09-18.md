<!-- tags: decision, owner-directive, intake, consignatio, probata, elt, duckdb, weaviate, surrealdb, neo4j, precommit, timeline, receipt -->
# Pipeline history and current decided process — extraction → staging → stores → timelines

> _Byline: Claude Code · Opus 5 · 2026-09-18 (read-only research; nothing was changed)_
> Owner order 2026-09-18 20:16 EDT: *"Find all the discussions over the last 3 weeks . And find and read all of them before you make a fucking assumption !"* (session `claude:1955af71-51b9-42d6-b6f0-e51dba5cc68b`).

## Method and coverage

- **Claude Code logs:** every `C:/Users/matts/.claude/projects/*/*.jsonl` modified since 2026-08-28 (3,407 files, 2.3 GB) parsed with Python + DuckDB into 32,486 human/assistant turns; mid-turn queued owner messages (`queue-operation`/`enqueue`) included — that is where *"The folder names don't mean shit man"* lives. Deduped to 4,704 distinct owner turns 08-29 → 09-19; all owner turns in the keyword set read, plus every owner turn 09-13 and 09-17→09-19 read in full.
- **Codex rollouts:** `C:/Users/matts/.codex/sessions/2026/{08,09}/**` (28 files in window). Codex activity in the window is essentially **09-12 evening → 09-13** (16 files on 09-13, 5 on 09-12; scattered singles 08-29/08-30, 09-01, 09-06). The decisive pipeline thread is `rollout-2026-09-12T23-10-37-01a098be-d055-76d2-acb7-7f124c38757a`; the timeline/legal thread is `rollout-2026-09-13T04-11-44-01a099d2-7fc4-70e1-9241-e74a4423c9f2`.
- **Docs:** Probata `docs/DECISION_LOG.md` (main **and** the diverged `_worktrees/probata-integration-20260913` copy), `docs/registers/SETTLED.md`, `docs/handoffs/HANDOFF-2026-09-06-ingest-rulings-and-parser-fix.md`, `_worktrees/probata-integration-20260913/docs/reviews/2026-09-13-{proffer-precommit-review-contract,owner-source-contract-reconciliation,proffer-current-state-plan-and-gap-ledger,probata-operator-surface-repair}.md`, Consignatio `docs/URGENT-TODO.md`, `docs/decisions/2026-09-16-catalog-source-of-truth.md`, `Consignatio/Intake/backend/docs/UNIFIED-WORKBENCH-PLAN.md`, Propria root `AGENTS.md`/`AGENT_MEMORY.md`.
- **Memory:** merged auto-memory store `C:/Users/matts/.claude/projects/E--AI-Workspace-Projects-Propria/memory` (249 files) — `extraction-is-duckdb-elt`, `lifecycle-order-context-surreal-then-evidence`, `elt-hash-is-a-context-fingerprint-not-custody-h2`, `ingest-path-architecture-reconciliation`, `chat-ingest-format-learnings`, `catalog-is-source-of-truth`.
- **Docstore (SurrealDB):** `fn::docs_search` over every status (reachable); `fn::current_decisions("probata")` returns empty — decisions live in the repo files, not that table.

**Time note:** log timestamps are UTC; owner-facing times below are EDT (UTC−4) with the UTC stamp in brackets.

> **Read the Addendum at the end before implementing anything.** A code check finished after the body was written and it changes what "use the Go engine and the created templates" can mean tonight.

---

## (1) The current decided pipeline

### Stage 0 — Discovery comes from the catalog, and NOT from folder names

- Owner 2026-09-16 07:48 EDT: *"shouldn't it all be in the catalog? Like, isn't that the whole point of a lakehouse?"*; 08:32 EDT: *"enforce the catalog across all chats"* (`claude:743524f4-bffd-4c54-91e3-12fec5580661`) → `Consignatio/docs/decisions/2026-09-16-catalog-source-of-truth.md` (PG `casebible`, schema `raw_duck`, ovh-files): load listings into the catalog first, never re-scan for an answerable question.
- Owner 2026-09-18 20:02 EDT [09-19 00:02Z]: *"The one thing I did want you to do was to scan the directories and make an attempt to identifying the chat directories and index those first but whatever."*
- Owner 2026-09-18 20:03 EDT: *"Comms / Phone data / Court / Communication data / Sms folders"* (priority hint).
- Owner 2026-09-18 20:13 EDT [00:13:05Z]: **"The folder names don't mean shit man"** — this *supersedes the name-pattern ranking* built earlier the same evening, not the directory-first idea. Directory-first ordering stands; **the evidence for "this is a chat directory" must be file content/signature, not the path string.**
- The signature-based selector is not new: D-149 item 9 (2026-09-06, Probata `docs/DECISION_LOG.md`) — *"The Go router reads the file, matches its fingerprint/signature (Q18 matcher), and selects the ONE parser or extractor registered for that signature"*.
- Scope: owner 2026-09-18 12:35 EDT — *"everything should be in b2 now"* / *"thats the index taarget"*.

### Stage 1 — Retain an immutable source package (no custody language)

- Owner 2026-09-13 00:58 EDT [04:58:51Z], Codex `01a098be`: *"Did you find the most current ELT contracts the? Doc DB prepared. **Extraction packages with metadata and attachments** and how the. Context system now works how? The hashing system and. Promotion to evidence now works how **custody is not the very first stage**… **The original will be in the package, which will be hashed, and the package will be hashed so later on we can come back and rehash the original even after it's normalized.**"*
- Owner 2026-09-13 04:56 EDT [08:56:30Z]: *"refer to nothing as custody. Until we discuss evidence, nothing you're doing right now should have the name, title or implication that it's in custody…"*
- Owner 2026-09-13 04:58 EDT [08:58:00Z]: *"messaging… there's two message bases, 2 databases. First and third party, but messaging and images could potentially be candidates. That might carry a different flag. Or we do like the uh. H1 right off the bat. But we don't have to… It's optional. It's down the road, it gets flagged. It might get an early hash."*
- Written form: **D-154 (2026-09-12, Codex GPT-5)** "Intake Source Package": byte-identical original by immutable object reference + original-byte fingerprint + fully hashed membership + deterministic manifest digest; *"Context/ELT may read the R2 object in place and must not be given custody semantics or forced through PostgreSQL first."* (`_worktrees/probata-integration-20260913/docs/DECISION_LOG.md`).
- Hash naming rule: intake-time hashes are **context fingerprints**, never H1/H2/H3 (D-152 2026-09-07; auto-memory `elt-hash-is-a-context-fingerprint-not-custody-h2`).

### Stage 2 — Extraction = DuckDB ELT templates, selected by signature; Go orchestrates; parsers are backup only

- Owner 2026-09-03 14:30 EDT [18:30:27Z] (`claude:da5b5108`): *"It needs to ELT into the raw. It needs to serve the same function as the parsers, **with the same contract and the same workflow**."*
- Owner 2026-09-04 18:14 EDT [22:14:05Z]: *"The ELT process normalizes the exact same way as if it was parsed… the exact same contract, just a different method of getting there. We had that discussion too."*
- Owner 2026-09-06 15:12 EDT [19:12:52Z] on `read_xml`/`read_html` via the community `webbed` extension: *"— do it"* → installed and proven live (`docs/reviews/2026-09-06-webbed-install.md`; HANDOFF-2026-09-06 item: `read_xml` proven with typed rows).
- D-149 item 9 registry fill rule (owner 2026-09-06 15:05–15:06 EDT): *"if DuckDB can process a signature, DuckDB IS its registered handler; a Go decoder is registered only for signatures DuckDB cannot handle"*; decoders are *"KEPT, built, and tested, but NOT in the workflow for signatures DuckDB handles"*, available for atomic calls and on **logged failure**.
- Owner 2026-09-13 00:59 EDT [04:59:14Z]: *"And **duck DB is the primary extractor, but I still want the Go engine to manage it**."*
- Owner 2026-09-13 01:37 EDT [05:37:15Z]: *"FROM THERE WE CAN CREATE THE TABLES OR **DUCKDB CAN EXTRACT AND READ IT FROM THE DATA DIRECTLY AND IT REMAINS IN PLACE**"*.
- Owner 2026-09-18 12:33–12:34 EDT: *"use the go engine"*, *"and duckdb and the created templates"*, *"look for elt extractors first"*, *"the 'parsers' are backup"*.
- Owner 2026-09-18 20:04–20:05 EDT [09-19 00:04:43Z, 00:05:14Z]: *"The sms should extract using the god damn fucking duckdb extraction process we have discussed 38 fucking times !"*, *"The fucking elt process"*, *"IT SHOULD ALL BE USING THE GOD DAMN FUCKIKG ELT DUCKDB PROCESS"*.
- ELT strictness (HANDOFF-2026-09-06 ruling 12): same four gates as parsers — template output schema, `RawRecordEnvelope`, raw-table constraints, count reconciliation + row digest; typed columns with `TRY_CAST` into reject rows.
- One unit = one Temporal Activity; hashing is its own Activity family; pass references, never payloads (Probata `AGENTS.md` ATOMICITY, D-130).

### Stage 3 — Per-attempt DuckDB proposal bundle (the staging artifact)

`_worktrees/probata-integration-20260913/docs/reviews/2026-09-13-proffer-precommit-review-contract.md` ("owner-directed implementation contract", authored the day of the 09-13 Codex session):

- Binding storage order: **source package → per-attempt DuckDB proposal bundle → human review → exact approval → Context commit → Neo4j graph → later manual SurrealDB projection.**
- Bundle layout `proposal/<operation-id>/<attempt-id>/{proposal.duckdb, manifest.json, source-package.json, tool-receipts/, derived/, warnings.json}` with relations `proposed_source_records`, `proposed_records`, `proposed_metadata`, `proposed_attachments`, `proposed_entity_mentions`, `proposed_entities`, `proposed_relationships`, `proposed_temporal_expressions`, `proposed_chunks`, `proposed_lineage`, `proposed_warnings`, `proposed_sink_operations`, `tool_receipts`.
- Two digest layers: **logical proposal digest** (row-set digests + tool/template/policy config + destination plan) inside DuckDB, then an **external bundle manifest** (byte length + SHA-256 of the checkpointed DuckDB file and every derived artifact). Approval binds both.
- An attempt is immutable: *"Rerunning a parser, changing an extraction template, refining entities, or changing a chunking policy creates a new attempt; it never overwrites a prior attempt."*

### Stage 4 — Preview = precommit proposal, and it is the review surface

- Owner 2026-09-13 05:33 EDT [09:33:00Z], Codex `01a098be`, quoting the agent and correcting it: *"**Preview means precommit proposal.** The review surface shows proposed source records, chunks, entities, relationships, metadata, attachments, hashes, warnings, and full source → package → attempt → record → chunk/entity lineage before any PostgreSQL, Weaviate, SurrealDB, or index commit. — **Don't forget Neo 4J.**"*
- Owner 2026-09-13 01:28 EDT [05:28:08Z]: *"but i GET COMPLETE VISABLITY AND OCNTROL REGARDLESS! IF I WNAT TO OVER RIDE I DO! IF I WNAT A DIFFERANT PARSER OR EXTRACT TEMPL;ATE I CAN IF I WANT TO RERUN IT WITH A TEMPLATE TWEAK I FUCKING CAN!"* and *"AND THEN PREVIEW THE CHUNKS@!"*
- Owner 2026-09-13 04:04 EDT [08:04:51Z]: *"the idea would be that I can immediately see the chunks. **Before the chunks are actually created.** … And then I can view the chunks and then once it does get. Injected into the databases, I can then still view all of the chunks. And I can view the entity table… that's supposed to be the fucking surface."*
- Owner 2026-09-13 05:36 EDT [09:36:29Z]: *"the next tab, the one that's currently listed, preview. It should just be a review or a viewer. It should be where I can view the graphs, view the relationships, view the chunks."* and *"it definitely should not be asking me for some kind of fucking context ID or some stupid fucking bullshit. It should just show me a list of fucking resources I can look at."*
- Contract text: *"No proposed source record, normalized record, chunk, entity, relationship, or index entry may be written to PostgreSQL, Weaviate, Neo4j, SurrealDB, or a searchable index before exact proposal approval."* Read-only destination queries during preparation are allowed; PostgreSQL may hold control coordinates only.

### Stage 5 — Entities and timeline are built early, previewable and re-runnable

- Owner 2026-09-13 04:55 EDT [08:55:53Z]: *"what are we using for entity extraction? **It needs to happen at the beginning.** I want to preview these entities. Need to tell it whether or not it needs to go look again. Refine the entities… Maybe I need to add an alias or a name or link to something else… that whole entity thing needs to be a space in its own. And it needs to be **refinable and rerun able** and it needs to happen relatively early."*
- Owner 2026-09-13 05:17 EDT [09:17:35Z] (Codex `01a099d2`): *"Then we need our overall timeline. Be it relationship timeline. Claim timeline, court timeline, visitation timeline. Katrina being a horror timeline… need to be a viewable timeline."*
- Owner 2026-09-13 05:19 EDT [09:19:05Z]: *"within that timeline, it's going to be important to show whether or not we have linked evidence for it… evidence linking to claims, that's critical. And reports to show claims without evidence."*
- Owner 2026-09-18 12:33 EDT: *"minimunm needed to discover and parse chats into events events and tinelines"*; 12:34 *"forcus on json md for chats plus zips exports and html and json chats with katrina"*; 12:36 *"and my dauigthter and events around gher"*.

### Stage 6 — Destinations, and the order they receive data

**Newest statement (governs now).** Owner 2026-09-18 20:06–20:07 EDT [09-19 00:06:25Z, 00:06:49Z, 00:07:01Z, 00:07:07Z]:
> *"IT ALL NEEDS TO BE LOADED TO FUCKING WEIVIATE EXTRACTED THO DUCKDB AND THE TIMELINES ENTITIES AND GRAPHS IN SURREAL WHAT THE FUCKING FUCK MAN"* · *"FUCK PG"* · *"IT ALL GOES TO WEIVIATE FIRST"* · *"THATS THE FUCIING PROCMESS"*

and 2026-09-18 12:35 EDT: *"surreral backend for simplicity/weiviate for now for simplicity"*.

Consistent earlier owner statements:
- 2026-09-13 01:30 EDT [05:30:16Z]: *"AND NONE MESSAGING DATA I DO BELIVE GOES STRAIGHT TO WEIVIATE NOW??"*; 01:35 EDT [05:35:53Z]: *"AND IM 99% SURE THAT NONMESSAGING ALWAYS GONNA BE CONTEXT GOES STRAIJT TO WEIVIATE AND **PG ONLY HOLDING METADATA**"*.
- D-158 (2026-09-13, Codex GPT-6, `_worktrees/probata-integration-20260913/docs/DECISION_LOG.md`): storage splits by source type — **messaging** keeps canonical text in PostgreSQL with `working.content_chunk_message`; **non-messaging context** may be extracted and queried by DuckDB in place, PG holding only package/source identity, provenance, locators, fingerprints, template/attempt references, workflow state, decisions, projection coordinates and receipts; after approval the searchable chunk goes to Weaviate.
- 2026-09-06 (D-149 item 8): Weaviate holds the searchable chunk object (vector + PG coordinates + member ids), no text.
- SurrealDB: owner 2026-09-06 17:51 EDT [21:51:09Z] *"SURREAL IS ANALYTICAL SDURFACE"*; 2026-09-06 10:34–11:49 EDT (D-145) the lifecycle *ingest → context → owner reads → **send to Surreal** (owner click) → analysis → **promote to evidence** (second owner click)*; owner: *"Did you realize that… analyzing the data and deciding what goes to Surreal and then working in surreal. That's the whole point of the fucking goddamn platform."*
- Neo4j: owner 2026-09-13 05:33 EDT *"Don't forget Neo 4J"* and 05:36 EDT [09:36:28Z] *"**That's where the graph is gonna live. Before surreal. Surreal will be a separate manual projection.** That'll be once I decide that is relevant… for me to actually consolidate everything and look at it as a whole and decide what is evidence."* — the precommit contract encodes this as: Neo4j = first durable graph destination after approval; SurrealDB receives nothing automatically.
- Graphiti: retired (D-070); not in the pipeline. Milvus: memsearch only (owner ruling 2026-09-03 — *"milvus = memsearch only / weiviate = project vector store projections"*, `claude:972e1d98`). Lance + Parquet: lake representations for later processing/reproducibility in the Intake plan (`UNIFIED-WORKBENCH-PLAN.md`), not a live pipeline stage — today's Parquet copies on B2 are consistent with that role.

### Stage 7 — Nothing is evidence yet; promotion is a later, separate, owner-clicked action

- Owner 2026-09-13 04:55 EDT [08:55:53Z]: *"the custom path is the context only path, semantic is the other path. **Evidence is down the fucking road. Evidence happens later. Completely later. We're not even there. Don't even think about it. There is no evidence.**"*
- Owner 2026-09-13 01:33 EDT [05:33:30Z]: *"WE HAVENT TAKLED PROMOTION TO EVIDENCE YET"* / *"WE CANT GET PAST INTAKE AND CONTEXT"*.
- Owner 2026-09-13 04:05 EDT [08:05:15Z]: *"Flag it for potential promotion."*
- D-145/D-146 + `2026-09-13-owner-source-contract-reconciliation.md`: *"`EvidenceChunkV1`, `EvidenceChunkV2`, H1/H2/H3 evidence receipts, and evidence publication are therefore not acceptance criteria for this intake/context repair."*

### Stage 8 — Where CocoIndex (Intake) and the Go engine (Probata) sit

- **Three indexes, never merged** (Propria `AGENTS.md`, owner decision 2026-09-12): **CCC** = project-local CocoIndex *code* indexes; **Intake** = the multifaceted CocoIndex-based filesystem workstation using **Weaviate for advanced search and SurrealDB for relationships** plus multimodal tooling (OCR, STT, video, SLM extraction/classification); **Docstore** = CocoIndex + SurrealDB for project documentation. *"Keep their apps, tracking state, locks, configuration and target ownership isolated; shared technology is not a shared runtime."*
- Owner 2026-09-14 09:19–09:20 EDT (`claude:17f83d73`): *"it's supposed too and it's backed by cocoindex . that's the path / a custom cocoindex app"*; *"docs to cocoindeax indexer to surreal. that's how I expected it that's what I fought to make happen"* (Docstore lane).
- Owner 2026-09-14 17:25 EDT: *"you need to find the conversation about the **cocoa index case Bible super index multimodal app**… it is a completely separate cocoa index index… it is next it needs to be integrated with the fucking intake"*; 2026-09-13 01:30 EDT [05:30:16Z]: *"N8N SHOULD LIKLY GET MORE USE WHEN IT COMES TO IMAGAGES AND PDF… ITS THE PURPOSE BEHIND THE CASEWIDE COCOSUPER APP"*.
- Owner 2026-09-14 20:41 EDT: *"The search surface in intake needs full cocoindex , weoviate , surreal and duck DB tools . With a rich and intuitive UI that exposes at the different search methods… Including also basics like rg ."*
- Owner 2026-09-18 12:32–12:33 EDT: *"we need the ccc based super app we were creating to start indexing the directies most likely to have chats… get the minimum needed to get coco index and duckdb working… and get the mvp for coco up"*.
- **Go engine / Probata:** `modules/engine` owns orchestration (`ProfferWorkflow`, stage graph, signature registry, `activities/elt_structured.go`); Temporal owns durability, retries, waits, approval, commit order and read-back; n8n owns visible composition (arrival, media/PDF flows) invoked at an Activity boundary (`2026-09-13-owner-source-contract-reconciliation.md`; HANDOFF-2026-09-06 ruling 10: *"Go orchestrates everything including DuckDB"*).

### Stage 9 — Two applications, one boundary (repeated many times)

`2026-09-13-owner-source-contract-reconciliation.md`: (1) **Probata/Proffer** = intake, extraction, repair, context preview, override, Temporal, n8n; (2) **Xplorer + Case Bible + Consignatio(Intake)** = one combined application (ACP copilot, permissioned file ops, agent HITL, vault organization/dedupe, review workflows). Owner 2026-09-13 02:07 EDT [06:07:38Z]: *"said this 100 timews"*; 02:08 EDT [06:08:53Z]: *"THIS IS A SIGLE FUCKING TOOL!@! THO"*.

---

## (2) Superseded versions, in date order

| Superseded statement | Where it came from | What superseded it |
|---|---|---|
| "All canonical searchable text lives in PostgreSQL" (generalized from messaging) | D-149 items 7–8 wording, 2026-09-06 | **D-158, 2026-09-13** — storage splits by source type; the universal wording came from a doc marked `PROPOSED — owner has not ruled`. Reconciliation doc §"Source-type storage split". |
| "The ELT process… goes into fucking PG as a raw table and then it gets normalized" (owner, 2026-09-04 18:14 EDT) | `claude:da5b5108` | Narrowed by **D-158** to messaging; for the current chat/timeline work superseded outright by owner **2026-09-18 20:06 EDT "FUCK PG" / "IT ALL GOES TO WEIVIATE FIRST"**. The *contract equality* ("same contract, same workflow as a parser") is NOT superseded. |
| "DuckDB ELT is PRIMARY / decoders are the fallback ladder" | D-149 item 9 first draft, 2026-09-06 | **Corrected the same day 15:04–15:06 EDT**: not a priority ladder — a **signature registry**; DuckDB owns every signature it can process, Go decoders registered only where it cannot, kept callable as backup on logged failure. |
| "Go-primary parsing by coverage" (ADR-0052 Q3, older) | 2026-08 | **2026-09-06 routing correction** (registry by signature) — recorded by the Codex agent on 09-13 05:18Z and accepted by the owner. |
| "Custody/H2 hashing belongs in the ELT lane" (crew CR-3/GAP-3) | probata_build_crew run-08, 2026-09-06 | **D-152, 2026-09-07** — intake hashes are *context fingerprints*; custody H1/H2/H3 only at promotion. Owner 2026-09-07 02:31 EDT: *"What about the fucking ELT hash? What the fuck about it?"* |
| "Evidence/custody is the first stage" | earlier ingest design | **Owner 2026-09-13 00:58 / 04:56 EDT** — *"custody is not the very first stage"*, *"refer to nothing as custody"*; D-154/D-158. |
| "SurrealDB is retired" | stale 2026-08 docs | **D-073/D-080/D-145/D-151** — only the legacy Agno operational adapter is retired; Surreal is the analytical/graph surface. |
| "Graphiti holds the belief graph / Graphiti in the pipeline" | ADR-0045-era text | **D-070** — Graphiti retired; Neo4j (09-13) then Surreal. |
| "Milvus is down / Milvus is the platform vector store" | pre-09-03 docs | Owner 2026-09-03: **Milvus = memsearch only; Weaviate = project vector store projection.** |
| "Preview = a late PostgreSQL-backed read of already-committed rows" | current Proffer implementation | **2026-09-13 precommit contract**: *"any view backed by already committed PostgreSQL rows must say **Committed read-back**"*; only a frozen per-attempt artifact may say *Precommit proposal*. |
| "Surreal is where the graph lives first" | pre-09-13 assumption | **Owner 2026-09-13 05:36 EDT** — Neo4j first, *"Surreal will be a separate manual projection"*… **but see the open point below: on 2026-09-18 20:06 EDT the owner said timelines/entities/graphs go to SurrealDB and did not mention Neo4j.** |
| Folder-name ranking of chat directories | built 2026-09-18 20:06–20:13 EDT | **Owner 2026-09-18 20:13 EDT: "The folder names don't mean shit man."** |
| "Surreal paused; catalog PG is the timeline store" (evening workaround) | 2026-09-18 13:40 EDT | **Owner 2026-09-18 20:14 and 20:16 EDT** — all events → Weaviate; timelines/entities/graphs → Surreal; PG is not the store. |
| Numbering: two live `D-154…D-158` sequences | Probata main vs `_worktrees/probata-integration-20260913` | **Unresolved collision.** Main has D-154 (agent memory) … D-160 (intake is consignatio's product); the integration worktree has a different D-154 (Intake Source Package) … D-158 (storage split). Both are owner rulings; the ID reuse is a bookkeeping defect that must be reconciled before anyone cites "D-158" without a path. |

---

## (3) Open / undecided points

1. **Neo4j vs SurrealDB for the graph, right now.** 09-13: graph lives in Neo4j, Surreal is a later *manual* projection. 09-18: *"the timelines entities and graphs in surreal"* with no mention of Neo4j. Newest wins for tonight's chat-timeline work (Surreal), but the Proffer commit contract still names Neo4j as the first durable graph destination. **Needs one sentence from the owner.**
2. **Precommit proposal vs "get me timelines tonight".** The 09-13 contract forbids any store write before exact approval. The 09-18 direction is a speed run. Nothing in the 09-18 messages revokes the preview rule; it was simply not applied. **Which gate applies to the Consignatio/Intake chat-timeline lane is undecided.**
3. **Whether the Intake chat-timeline lane is inside the Proffer contract at all.** The precommit contract is written for Probata/Proffer; the chat timeline is being built in Consignatio/Intake. The two-application boundary says they are different products with shared interaction principles.
4. **SMS/MMS XML through `read_xml`.** The template does not work yet on the real 1.3 GB file (DuckDB "invalid XML"; one bare `&`, ~95 MB base64 lines). The owner's rule is *stop and report*, not fall back. **The DuckDB-only repair path is undecided.**
5. **n8n's role per flow** — *"Whether n8n drives Temporal or Temporal invokes a bounded n8n activity was explicitly open in the original repair kit; it must be decided per flow"* (reconciliation doc).
6. **Early H1 for messaging/images** — optional flag, *"down the road"* (owner 09-13 04:58 EDT). Not decided.
7. **Entity workspace** — owner wants aliases/merge/split/refine "a space in its own"; nothing built.
8. **Identity confirmations still owed by the owner** (from today's run): FB "Katrina Kinzel", phones 810-295-9303 / 810-353-3592 merged; 810-268-9630 / 810-853-2989 and the two emails "possible"; Catrina-the-landlord 130 ambiguous events.
9. **Metabase** has no `casebible` connection yet, so the owner cannot browse the views there.
10. **Gemini free-tier throttling** for the Intake chat model (a/b/c options pending).

---

## (4) How today's work (Consignatio `docs/URGENT-TODO.md`, 2026-09-18 sections) deviates from the decided process

| # | What was done today | Decided process | Verdict |
|---|---|---|---|
| 1 | Chat candidates discovered by **guessing format from the B2 key name** (`raw_duck.chat_candidates_20260918`, 6,431 objects), then directories ranked by **folder-name patterns** (`chat_directories_20260918`, 25,596 dirs; `chat_dir_files_20260918`, 893,619 files). | Signature/fingerprint matching decides the handler (D-149 item 9); owner 20:13 EDT *"folder names don't mean shit"*. | **Deviation.** Ranking is invalid by the owner's own statement; the tables are a usable file inventory but not a valid priority. |
| 2 | SMS/calls XML, iMessage TXT and FB Messenger HTML extracted with the **Probata Go/Python parsers**; FB/IG JSON, WhatsApp txt, Google Chat, AI `conversations.json` via DuckDB templates. | *"the 'parsers' are backup"* (12:34 EDT); *"IT SHOULD ALL BE USING THE GOD DAMN FUCKIKG ELT DUCKDB PROCESS"* (20:05 EDT); D-149 registry rule. | **Deviation** for every parser-extracted format — this is exactly what the owner objected to at 20:04. |
| 3 | 551,877 deduped events + 1,080,505 provenance rows landed in **PostgreSQL** (`raw_duck.chat_events_20260918`, views `timeline_*`), because Surreal was unreliable. | PG holds control coordinates/metadata only (D-158, owner 09-13 01:35 EDT); owner 20:06 EDT *"FUCK PG"* / *"IT ALL GOES TO WEIVIATE FIRST"*. | **Deviation** (it predates the 20:06 statement, so it was defensible when done; it is not the target state). |
| 4 | Weaviate `ChatEvents20260918` (106,496 objects so far) embedded **after/alongside** PG, not first. | Weaviate first, from the ELT output. | **Deviation in order**, right destination. |
| 5 | Surreal loaded directly from the loader into `tl_*_20260918` tables with a FULLTEXT index; hung 3 times. | Surreal receives timelines/entities/graphs **built from Weaviate** (20:06 EDT); Surreal is the analytical/manual-projection surface (D-145, 09-13 05:36 EDT). | **Deviation** in source and in "automatic vs manual". |
| 6 | **No per-attempt DuckDB proposal bundle, no manifest.json, no logical/bundle digest, no attempt identity.** Scratch DuckDB files described as "small and rebuildable". | Stage 3 contract: `proposal.duckdb` + external manifest + two digest layers; a rerun creates a new immutable attempt. | **Deviation** — the staging layer the contract is built around does not exist in this lane. |
| 7 | **No precommit review.** Events went to PG → Weaviate → Surreal with no owner-visible proposal, no chunk/entity preview, no approval step. | *"Preview means precommit proposal… before any PostgreSQL, Weaviate, SurrealDB, or index commit"* (09-13 05:33 EDT); *"I can immediately see the chunks. Before the chunks are actually created"* (09-13 04:04 EDT). | **Deviation — the biggest one.** |
| 8 | Entity/person tagging by a regex terms file (`/data/probata/config/timeline-mvp/terms.json`), strong/medium/weak; identity list returned in chat for confirmation. | Entity extraction early, **previewable, refinable, re-runnable, alias-editable, its own space** (09-13 04:55 EDT). | **Partial** — confidence + provenance kept and the owner was asked; no preview/refine surface, no rerun-as-new-attempt. |
| 9 | Hashing: source-object sha1 from the catalog, extractor version, dedup key, `event_provenance` per source row. | Package + original hashed at intake as *context fingerprints*; package manifest digest; rehash of the original at promotion (09-13 00:58 EDT; D-154). | **Partial** — no package manifest digest, no per-attempt digest; naming correctly avoids H1/H2/H3 and custody. |
| 10 | No custody/evidence language anywhere; timelines flagged only. | 09-13 04:56 EDT *"refer to nothing as custody"*; evidence later. | **Compliant.** |
| 11 | Go engine not used; the MVP is a standalone Python/DuckDB runner image on ovh-files. | *"duck DB is the primary extractor, but I still want the Go engine to manage it"* (09-13 00:59 EDT); *"use the go engine"* (09-18 12:32 EDT); one unit = one Temporal Activity. | **Deviation** — no Temporal, no Activity boundary, no receipts. |
| 12 | Catalog used as the file-discovery source; new facts written as dated `raw_duck` tables with tracked SQL under `casebible/tools/`. | `2026-09-16-catalog-source-of-truth.md`. | **Compliant.** |
| 13 | A `docker restart` on surreal-intake before the supervisor's answer; later restarts via Coolify API. A throwaway-container diagnosis plan was briefed, then corrected. | LIVE ONLY, no parallel stacks; restarts via Coolify. | **Deviation, self-reported and corrected.** |
| 14 | Surreal hang root cause diagnosed read-only (RocksDB WriteBufferManager stall, `allow_stall=true`, 144 MiB effective limit under the 2 GiB cgroup); proposed fix = raise block cache. | Owner 20:20 EDT: raising the cap alone is rejected — *memory must also clear during a load*. | **Open**, correctly on hold. |
| 15 | CocoIndex was not used at all in the chat lane. | Owner 12:33 EDT *"and get the mvp for coco up"*; Intake = the CocoIndex workstation (09-12 decision). | **Deviation / not done** (the indexing side of the ask). |

---

## (5) Minimum correct path to Katrina + daughter timelines tonight, inside the decided process

Everything below is doable with what already exists; each step names the rule it satisfies.

1. **Signature pass instead of folder names** (Stage 0, D-149 item 9). One DuckDB job over the catalog's B2 keys: read the first N KB of each candidate object through `/srv/openlist/b2` and classify by **content** (XML root element `<smses>`/`<calls>`, FB `messages_*.json` shape, Google Voice/Chat HTML markers, iMessage bracket-TXT, mbox `From ` lines, ZIP central directory with member names). Write `raw_duck.chat_signatures_20260919` (dated, tracked SQL under `casebible/tools/`). Rank by **signature + owner's folder hints as a tiebreak only**. This replaces the invalidated name ranking without re-scanning anything the catalog already holds.
2. **One named ELT template per signature** (Stage 2). `elt_<format>_v1` as tracked SQL, run in the **DuckDB engine** (not pg_duckdb — owner 20:07 EDT), `webbed` for `read_xml`/`read_html`, `read_json_auto`/`read_csv_auto` otherwise, `zipfs` for ZIP members. Keep the four gates (typed columns, `TRY_CAST` reject rows, count reconciliation, row digest).
   - **SMS/calls XML blocker:** fix it inside DuckDB — stream the file with `read_text`/`read_blob`, `regexp_replace` the bare `&` into `&amp;` (and any other XML-illegal byte) into a sanitized temp file under `/data/probata/volumes/timeline-mvp/`, then `read_xml`; validate **11,676 records on the 1.3 GB file** against the known-good decoder count before accepting. If it still fails, **stop and report** (owner's rule) — do not silently re-run the parser.
   - Formats already extracted by DuckDB templates today (FB/IG JSON, WhatsApp txt, Google Chat, AI conversations) can be re-used as-is; only the parser-derived rows must be re-extracted.
3. **Per-attempt bundle, cheap version** (Stage 3). For each `(signature, run)` write `proposal/<op>/<attempt>/proposal.duckdb` holding at minimum `proposed_source_records`, `proposed_records`, `proposed_entity_mentions`, `proposed_warnings`, `proposed_lineage`, plus `manifest.json` with per-relation row counts + row-set digests and, after checkpoint, the file's byte length + SHA-256. This is an hour of work and it makes every later step reproducible and approvable.
4. **One preview the owner actually looks at** (Stage 4) — the smallest thing that honors *"Preview means precommit proposal"*: a DuckDB-backed table/page listing, per attempt: format, source object, event counts, date span, top threads/participants, sample events, entity candidates (Katrina/daughter strong/medium/weak), warnings, and the proposal digest. Owner says go → commit. Nothing reaches a store before that click. If the owner waives it tonight, record the waiver in `URGENT-TODO.md` as an explicit exception rather than silently skipping it.
5. **Weaviate first** (Stage 6). Publish approved events to `ChatEvents20260918` with deterministic UUIDs from the dedup key and full provenance (source object sha1, template id + version, attempt id, dedup key). Priority order: Katrina set → daughter set → everything else. Keep the existing embed job pattern (NIM), paced.
6. **SurrealDB from Weaviate** (Stage 6). Build `conversation` / `participant` / `event` / relation records and the `fn::timeline_*` functions **from the Weaviate-published set**, not from PG. Load memory-efficiently per the owner's 20:20 EDT correction: small batches under the RocksDB flush threshold, a pause between batches, no FULLTEXT index on the load table (search stays in Weaviate), no concurrent counts, stop-for-good on a timeout. Re-verify health between phases.
7. **Timelines and reports** (Stage 5): `timeline_katrina`, `timeline_daughter`, plus day-count rollups; keep the strong/medium/weak confidence field and the "possible identity" sets separate, since the owner still has to confirm the two unconfirmed phone numbers and the two emails. Surface "claims without linked evidence" later — it is the owner's stated timeline requirement but not needed tonight.
8. **Treat the existing PG tables as disposable staging, not canon.** They stay readable while the ELT re-run proceeds (they are the only readable timeline right now), and they are dropped once the ELT-derived set is in Weaviate + Surreal. This follows the standing rule that test/staging data never becomes canonical.
9. **Say nothing about custody or evidence.** Flag-for-promotion only.

**If only one thing can be done tonight:** step 2's SMS/calls `read_xml` template (45,689 of the 115,511 Katrina events came from SMS XML through the *wrong* path) + step 5 publication of the Katrina set to Weaviate. That converts the largest non-compliant slice into a compliant one and leaves the timeline readable the whole time.

---

## Addendum — what the Go engine actually contains (code-verified 2026-09-18, after the body above)

A grep I had backgrounded over `Probata/probata/{docs,modules}` returned **zero** hits for "extraction package", "extract contract", "precommit proposal" or "signature registry" inside `modules/` — so I read the code. Four findings, each from the file named:

1. **The ruled signature registry does not exist in code.** `modules/engine/parser/registry.go` is a *parser-adapter* registry: `Registry.Select(format FormatID)` picks among registered Go adapters by declared format coverage and quality tier (*"input size is deliberately absent from Select"*). It contains **no ELT or DuckDB entry of any kind**. D-149 item 9's rule — *"if DuckDB can process a signature, DuckDB IS its registered handler"* — is therefore **ruled but unimplemented**: there is no code path that can select a DuckDB template over a Go parser.
2. **The one ELT Activity that exists handles only CSV and NDJSON.** `modules/engine/activities/elt_structured.go`: *"Only the two formats named by the BUILD LANE E1 deliverable are supported; any other value is a hard validation error, never a silent no-op"* (`StructuredELTFormatCSV`, `StructuredELTFormatNDJSON`). There is **no `read_xml` / `read_html` / `read_json_auto` template lane in the Go engine** — the "created templates" of the 09-18 12:33 EDT instruction are the D-149 design plus `scripts/pgduckdb_webbed_smoke.sql`, not implemented engine templates.
3. **That Activity has never run.** `activities/register.go:222-227`: *"RegisterStructuredELTActivities registers ExecuteStructuredELT… **It is not yet called from** profferworker.Run/buildRegistrations — that workflow-layer wiring… is the exact remaining step the BUILD LANE E1 handoff reports as outstanding."* And `elt_structured.go`'s own header: *"deliberately NOT yet registered as a stagegraph.StageID member."* This confirms the 09-06 change-map note ("ELT activity registered on no worker") is still true on 09-18.
4. **The existing ELT body is pg_duckdb-bound, which the newest ruling rejects.** `elt_structured.go`: *"SourceURL must be reachable from INSIDE the PostgreSQL server process itself (pg_duckdb's httpfs/R2 secret) — the DuckDB read happens in the database, never in this Go worker."* That is exactly the shape the owner struck on 2026-09-18 20:07 EDT (*"FUCK PG"*, standalone DuckDB templates). The existing implementation **cannot** satisfy both "use the go engine" (12:33 EDT) and "FUCK PG" (20:07 EDT) without changing its execution engine.

**Consequences for section (5):** step 2 stands as written — **standalone DuckDB templates** are both the newest ruling and the only thing that can work tonight. Do **not** route tonight's work into `ExecuteStructuredELT`: it is unregistered, csv/ndjson-only, and runs inside Postgres. The Go engine's ruled role (orchestrate, select by signature, own the Activity boundary) is a follow-up build, not tonight's tool — and it needs three things landed in order: an ELT adapter registered in `parser/registry.go` against `FormatID`, template families beyond csv/ndjson, and the `profferworker` wiring the code comment describes.

**Consequence for deviation #11:** today's agent building a standalone Python/DuckDB runner instead of using the Go engine was, on the engine's actual state, the only executable choice. The deviation is real against the *ruling* but it is not the agent inventing a shortcut — the ruled lane was never built. Record it as an implementation gap, not an agent error.

**One terminology trap for anyone grepping this repo:** `D-090` (2026-08-26) uses "**extraction packages**" to mean *substitutable third-party extraction capability packages* (Tika, EXIF, Tesseract, n8n community nodes). That is **not** what the owner means on 2026-09-13 by *"Extraction packages with metadata and attachments"* — he means the per-source **Intake Source Package** of D-154. Two different concepts, one phrase; an agent that greps the term will land on D-090 and build the wrong thing.
