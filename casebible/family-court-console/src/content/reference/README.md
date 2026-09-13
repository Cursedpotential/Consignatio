# content/reference/ — plugin-owned reference data

> _Byline: Claude Code · Sonnet 5 · 2026-09-07 — owner orders 2026-09-07 13:09-13:16._

## What belongs here

**Reference data — the ruler, not the subject.** Behavior-detection patterns, ontology
terms, entity rules, lexicons, templates, and trusted-authority lists that the case store
loads WHOLE and uses to **customize outputs**, never to be analyzed or migrated itself
(platform convention, carried into this plugin). Every file here is loaded verbatim by
`case_reference load --from-plugin` into the case store's `reference` table
(`mcp-app/src/store.ts` — `caseReferenceLoad()`).

Put a new file here when you have a reusable pattern/definition set that should be
available to `case_reference match` (regex/alias matching with spans) or to
`case_reference list` (browsing by kind/category). Do **not** put case-specific facts,
findings, or one-off notes here — those are `memo`, `note`, or `event` records, not
reference data.

## File shape

One JSON file per logical set, either:

- a bare array of rows: `[ {...}, {...} ]`
- `{ "entries": [ {...}, ... ] }` (matches `content/tools/court-language/lexicon.json`'s
  own shape, so a file can be written the same way without inventing a second convention)
- `{ "rows": [ {...}, ... ] }`
- a single row object (rare — one-off reference item)
- JSONL (one JSON object per line) — use the `.jsonl` extension

Each row:

| field | required | note |
|---|---|---|
| `kind` | recommended | `behavior_pattern \| ontology_term \| entity_rule \| lexicon \| template \| authority` |
| `key` | recommended | stable id within its kind; used as the record id when present (else `id`, else `<kind>-<index>`) |
| `category` | optional | groups rows within a kind (e.g. `manipulation`, `court-procedure`) |
| `pattern` | optional | a JavaScript-regex source string, matched case-insensitively by `case_reference match` |
| `definition` | optional | the FULLTEXT-searchable explanation of the row (`case_search`/`case_reference list` show this) |
| `aliases` | optional | string array; each is matched literally (case-insensitive) by `case_reference match` in addition to `pattern` |
| `severity` | optional | free text (`low \| medium \| high \| stop`, or whatever the source scheme uses) |
| `factors` | optional | MCL 722.23 letters (a-l) this pattern is relevant to, if any |
| `source` | optional | provenance block ({path, url, ...}) for where the pattern definition came from |
| `version` | optional | the source scheme's own version tag |

Unrecognized extra fields are preserved on the record (the `reference` table is
SCHEMALESS) but are not indexed or matched on.

## Loading

```
case_reference({ action: "load", from_plugin: true })
```

reads every `.json`/`.jsonl` file directly in this directory, **plus** (see
`docs/2026-09-07-case-store-registers.md`) `content/tools/court-language/lexicon.json` —
an existing pattern file whose `category`/`pattern`/`severity`/`why` fields already fit this
shape once mapped (`why` -> `definition`, `kind: "lexicon"`) — ingested in code rather than
copied here, so there is exactly one copy of that lexicon.

`case_reference({ action: "load", path: "<file>" })` loads one specific file instead
(does not require `from_plugin`).

## Matching

`case_reference({ action: "match", text: "..." })` runs every loaded row's `pattern` regex
and `aliases[]` against `text` and returns each hit with its character span — this is how
another member "customizes outputs" against the loaded reference set (e.g. flagging a
DARVO/gaslighting pattern in a drafted narrative before it goes to `court_language_review`).

## What is NOT here yet

`manipulation-patterns` and `behavioral-pattern-analyzer` (`skills/family-court-toolkit/
references/{manipulation-patterns,behavioral-pattern-analyzer}/SKILL.md`) are rich prose —
not yet reduced to `{pattern, definition, aliases}` rows. Converting them into a
`behavior-patterns.json` here (see `behavior-patterns.example.json` for the target shape,
with generic examples only — no real case facts) is a deliberately deferred follow-up, not
done in this change (see `docs/2026-09-07-case-store-registers.md` §Deferred).
