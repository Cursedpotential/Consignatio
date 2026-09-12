# Selection-aware chat slice — 2026-09-11

## Implemented, not yet native-runtime verified

The independent Xplorer fork now builds metadata-only chat context from the
complete selection. Names, exact paths, directory/file/unknown type and known
byte sizes are retained. A known zero-byte file stays zero; unknown sizes stay
unknown. Cross-tab paths missing from the active directory listing carry an
explicit unknown-metadata marker instead of being asserted to be files.

Sending a discussion prompt no longer automatically reads selected text/images,
extracts documents or invokes comparison from an inferred intent. Directories
are included and the old five-file content cap no longer drops group members.
Explicit bounded content loading remains follow-up work. Existing low-level
content-reading helpers still exist for separately invoked functionality.

With `VITE_INTAKE_MODE=1`, chat also skips eager workspace content detection on
navigation and directory re-listing during prompt assembly. The manifest states
that content has not been read and that names/paths are data, not instructions.

## Remote route boundary

With native `XPLORER_INTAKE_MODE=1`, ai.rs does not probe/list local Ollama models,
fall through unknown chat model names to Ollama, run local reranking, suggest
filenames locally or auto-tag locally. Legacy provider autodetection skips
Ollama. Claude and OpenRouter request serialization now preserves the assembled
system instructions instead of recasting them as assistant history.

Existing configured `claude-...` and `openrouter:...` routes remain supported.
`VITE_INTAKE_CHAT_MODEL` can select a full prefixed frontend model name; it is
non-secret. `INTAKE_CHAT_MODEL` optionally advertises a chosen OpenRouter alias
in the native models list. The existing OpenRouter request requires native
`OPENROUTER_API_KEY`. No credential was read or printed, and no provider request
was sent. Portkey has NOT been integrated or configured in this slice; endpoint,
credential reference and model/config alias must be confirmed, not invented.

## Verification

- TypeScript `tsc --noEmit`: passed after the changes.
- Scoped `chat-selection-manifest.test.ts`: 4 tests passed, one worker.
- Covers exact mixed file/directory metadata, no IO on comparison-worded chat,
  complete 700-entry group preservation and invalid/unknown versus zero sizes.
- Scoped ESLint: passed after extracting nested conditional expressions.
- TEMP/TMP explicitly set to `E:\tmp`; existing dependencies used, no install.
- Initial test pulled unrelated extension startup through imports and stalled;
  stopped it, isolated those modules in unit mocks, reran successfully in 2s.
- Native ai.rs compilation, real provider response and desktop selection/chat
  interaction still require the lead's integrated native build/smoke test.

Transfer-engine replacement remains post-MVP; this slice does not modify copy,
move, deletion, mounts or the remote filesystem abstraction.

## Follow-up: combined search surface and configured Portkey route

The Intake-mode left search sidebar now uses the native
`filesystem_index_search` command and real `/filesystem/search` contract.
Hybrid/keyword choice, returned source IDs/paths, indexed text snippets, scores,
coverage and explicit unavailability are visible. Requests occur on submission,
not panel mount or keystrokes. Checked result paths can be added to the shared
selection for chat; local/mounted source paths can open their parent directory.
Unmapped remote URIs are not fabricated into local drive paths. No fake
FileEntry size/timestamp is manufactured for preview. Rich file preview follows
ordinary navigation and selection; the result itself shows indexed text only.

SDK transport is desktop-only and does not fall back to the unrelated default
HTTP backend. Native service endpoint and credentials stay outside the renderer.
The native bridge was implemented in the coordinated native worker lane.
Navigation hooks skip the disabled legacy index/context/whitelist/watcher
requests in Intake mode, avoiding error spam and background indexing on browse.
English keys were added to all four locale files; translation is follow-up.

Portkey source integration now exists in `ai_portkey.rs`:

- Native `INTAKE_PORTKEY_URL` is the gateway origin; `/v1/chat/completions` is
  appended. `INTAKE_PORTKEY_CONFIG_FILE` is an absolute JSON template path.
- Literal `$OLLAMA_API_KEY`-style placeholders resolve only from native env.
  Missing keys fail clearly. No config/key is logged or returned to renderer.
- `INTAKE_CHAT_MODEL=portkey:<model>` is exposed without OpenRouter rewriting;
  custom model picker accepts/persists `portkey:` and optional Vite model chooses
  the initial model. Existing model/config values are owner-selected.
- System message roles are preserved; no local-provider discovery or fallback.
- 55-second timeout, two in-flight requests, no redirects, 1-MiB response bound,
  64-KiB config checks, sensitive header marking, and empty-content rejection.
- Provider route source was the existing Probata Portkey README/chat config;
  its Ollama custom host is `https://ollama.com/v1`, not local Ollama inference.

Verification: TypeScript and scoped ESLint passed. Three frontend suites passed
12 tests total: selection manifest (4), search boundary (6), sidebar UI (2).
UI tests verify no automatic search, explicit submit, source navigation, adding
checked results to selection and disconnected-state handling. Two Rust pure
Portkey tests were added but not run by this worker; integrated native compile
belongs to the lead. No provider request was made by this worker. Live probes
performed separately by the lead must be reported from the lead's receipt.

Skills read for this integration: CocoIndex v1; Weaviate plus hybrid-search
reference. Their distinction between incremental indexing and search guided the
surface: successful search never implies complete corpus coverage.

## Follow-up: assistant-initiated combined search

The existing `search_files` JSON action now routes to the same combined index
adapter in Intake mode. Its optional `mode` accepts `hybrid` or `keyword`.
The legacy filesystem glob implementation remains unchanged outside Intake.
The assistant prompt explains that this route searches all indexed stores,
does not apply a path scope filter, does not scan folders, and cannot establish
absence from an empty/unknown-coverage result.

The existing action/result loop is reused, not replaced: real results flow
back to the next model iteration; failed queries flow back as failed queries.
Results preserve source/object/document/chunk identities, exact source paths,
scores and coverage. Tool context is bounded to 20 hits with 800-character
snippets and explicit truncation. Source data is marked untrusted. At most
three index searches execute in a single model response; additional searches
are marked not executed. The existing overall five-iteration cap remains.

Seven additional tests passed: actual action parsing and adapter routing,
source identity preservation, no filesystem fallback on failure, mode/path
validation, snippet/result bounds, legacy behavior outside Intake, result
feedback and per-response execution limit. TypeScript passed. ESLint's two
curly-brace warnings introduced by formatting were corrected and rechecked.
No live model-tool round trip was run by this worker.

## Read-only first-user-path audit and minimal chat-retention repair

Confirmed source wiring: top-bar Split right button calls horizontal
`splitGroup`, rendered as a row by SplitContainer. Pane file clicks update root
selectedFile/selectedFiles; Shift selects a contiguous range, Ctrl toggles items,
Ctrl+Shift adds a range. Root effects publish selected metadata to chat. The
right vertical rail's speech-bubble button titled `AI Chat` selects the standalone
chat panel and expands the sidebar. Its context chips show five names plus a
remaining count; the actual metadata manifest retains the complete selection.
Enter sends, Shift+Enter keeps a multiline draft.

Found and repaired: switching from Chat to Preview previously unmounted the
chat, losing the visible active conversation/draft and potentially cancelling
its pending autosave. Chat now mounts only after its first visit, then remains
mounted while hidden through panel toggles and sidebar collapse. Hidden chat
pauses context polling, keyboard interception, workspace detection and proactive
awareness. Reopening synchronizes the current selection immediately. Already
explicitly submitted requests may finish; hiding is not an implicit cancellation.

Verification: existing RightSidebar suite plus retention test passed (18 tests),
new visibility/context hook test passed (1 test). TypeScript and scoped ESLint
passed. The hook test proves hidden polling stops and reopened selection is fresh.
These are source/component tests, not native desktop usability proof.

Remaining actual UX gaps (not changed in this slice):

- Preview and chat still share one visible right-panel slot. State now survives
  toggling; they are not simultaneously visible yet. MainLayout has the outer
  horizontal width ResizeHandle. RightSidebar has one flex-column content area
  and Suspense; a follow-up can reuse generic vertical ResizeHandle between two
  height-constrained preview/chat slots. File-editor SplitContainer is not a
  drop-in arbitrary-panel layout.
- EditorGroupPane clears shared selection when currentPath OR isActive changes.
  Switching panes can clear a selected group. The separate cross-tab selection
  store is not aggregated into the chat snapshot. Do not claim persistent
  cross-pane grouping from the basic root selection mechanism.
- Split shortcut tooltip disagrees with the actual handler: use the visible
  `Split right` button for the first smoke test, not the keyboard shortcut.
- The top-bar `New Chat` button creates a chat file in the current directory;
  it is NOT the standalone chat panel. Use the right-rail `AI Chat` button.
- The right-rail `Content Search` panel remains the old tokenizer UI. Use the
  LEFT sidebar Search tab for the new combined-index surface.
- Preview is active by default and selecting a file can load its bytes through
  the preview handler. For a metadata-only group discussion, open AI Chat first.

Suggested bounded native smoke test: open AI Chat, use Split right, navigate to
an approved tiny local fixture, select several files in ONE active pane, verify
context names/count, enter a draft, toggle File Preview then AI Chat, verify the
draft survives, and submit a metadata-only discussion. Then test left Search
with an explicitly configured synthetic index. No corpus browsing/requests were
performed during this audit.

## Follow-up: opt-in simultaneous Preview + chat

The simultaneous-display gap above now has an Intake-only first implementation.
The Preview/AI Chat header offers a `Preview + chat` toggle. It displays selected
file preview above the retained conversation, using the existing vertical
ResizeHandle. Drag the divider or focus it and use Up/Down arrows. Preview ratio
is constrained to 20–65%, with minimum slot heights; this is sidebar-local state,
not a general docking redesign or persisted workspace-layout schema.

If measured sidebar height falls below 360 px, the UI falls back to the active
Preview or Chat tab and explains that more height is needed. The requested split
and conversation survive, so enlarging the window restores both slots. Existing
tabs and legacy Xplorer behavior remain. Selecting another file updates preview;
chat remains mounted and active while both panels are visible. The separate
visibility hook continues to supply the active selection snapshot.

Verification: RightSidebar suite 21 tests passed, including simultaneous display,
draft retention, preview selection changes, real mouse-handle and keyboard resize,
short-window fallback and legacy mode. Context hook suite 1 test passed, proving
paused hidden polling and fresh selection on reopen. TypeScript and scoped source
ESLint passed. An initial test cleanup reset the shared ResizeObserver mock;
fixed the test to restore only its own clientHeight spy, then reran successfully.
No real preview bytes, native desktop UI, provider calls or corpus data were
accessed by this worker's tests. The lead's native UI smoke test remains distinct.
