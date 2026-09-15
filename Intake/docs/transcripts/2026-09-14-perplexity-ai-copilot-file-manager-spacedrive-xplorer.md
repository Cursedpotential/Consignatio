---
title: "Perplexity transcript — AI co-pilot file manager (Spacedrive vs Xplorer and alternatives)"
source: Perplexity (pplx export, shared by the owner 2026-09-14 22:23 EDT)
saved: 2026-09-14
original_date: unknown (export mtime 2026-09-14; conversation predates the Xplorer-first decision of 2026-09-11)
saved_by: Claude Code · Fable 5.1 (session intake-56)
tags: [transcript, perplexity, intake, xplorer, spacedrive, file-manager, research, owner-directive]
---

> _Byline: saved verbatim by Claude Code · Fable 5.1 · 2026-09-14. Owner rule (2026-09-14 22:23): transcripts from other services/models/platforms are always saved into docs so they can be found. Content below is the untouched export; treat it as research input, not as a decision record._

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I need to write an application that would allow me to navigate and make changes to my file system organize files with AI co-pilot I'd like to be able to quickly and easily grab a folder or a file or group of files and for the co-pilot to immediately be able to interact see the selection and trust discuss what to do list those files and potentially moving them and be nice with dual paint the agent needs to be able to have access

Yes — this is a very buildable product, and the right shape is a **desktop dual-pane file manager with an embedded agent sidebar**, not a chat app that merely “can browse files.” The key is to make file selection the primary context object, then let the copilot inspect, discuss, preview, and execute constrained actions like rename, move, tag, group, or organize only within approved paths.[^1_1][^1_2][^1_3]

## Product shape

- Core UI should be a dual-pane file manager, because that interaction model is already proven for browse-copy-move workflows and reduces friction when organizing files across locations.[^1_2]
- Add a persistent copilot panel on the right, so the user can select one file, a folder, or a multi-select set, and the agent immediately receives a structured snapshot of that selection: names, paths, metadata, previews, inferred types, and allowed actions.[^1_4][^1_1]
- The agent should not have blanket disk access by default; instead, it should operate on user-approved roots and explicit selections, matching the permission model used by filesystem MCP servers where reads, listings, creates, and moves are exposed through explicit tool boundaries.[^1_5][^1_3][^1_1]


## Best architecture

- Build it as a desktop app with a local shell plus web UI, most likely **Tauri + React/TypeScript** or Electron if you need faster plugin/library availability; Tauri is usually the cleaner fit for a file-heavy utility because it gives you native filesystem integration with a smaller footprint.[^1_4]
- Model the agent/file bridge after MCP-style filesystem tools: `list_directory`, `read_file`, `search_files`, `move_path`, `rename_path`, `make_directory`, and `preview_selection`, because that creates a clean permissioned boundary between UI and AI execution.[^1_3][^1_1][^1_5]
- Keep the AI orchestration local to the app process: UI emits a normalized selection payload, the agent reasons over that payload plus optional file previews, then returns either discussion text or an action plan that requires user confirmation before mutation. This mirrors current local-server patterns for granting AI controlled filesystem access while preserving approval on sensitive operations.[^1_6][^1_1]


## Interaction model

- When the user clicks or drags a selection, immediately show:
    - File list.
    - Total count and size.
    - Types detected.
    - Previewable contents for supported files.
    - Candidate actions such as “group by type,” “move screenshots,” “rename consistently,” or “archive old files.”[^1_3][^1_4]
- The agent should support three modes:
    - Discuss mode, read-only suggestions.
    - Draft mode, proposes a batch plan with diffs.
    - Apply mode, executes approved operations and shows undo.[^1_1][^1_3]
- Dual-pane behavior should stay first-class even when AI is active, because users still need direct manual control for drag/drop, compare, and target-folder selection. The AI should enhance that workflow, not replace it.[^1_2][^1_4]


## Safety model

- Scope access to approved roots only, for example `Documents`, `Downloads`, or a project workspace, instead of exposing the whole drive. MCP filesystem examples explicitly configure access by allowed directory paths, which is a good pattern to copy.[^1_6][^1_5][^1_1]
- Require confirmation for every destructive or large-batch action, especially moves, deletes

<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers

[^1_2]: https://doublecmd.sourceforge.io/

[^1_3]: https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem

[^1_4]: https://dev.to/kimlimjustin/i-put-vs-code-claude-and-a-terminal-inside-a-file-manager-i-built-using-react-and-rust-heres-k1n

[^1_5]: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

[^1_6]: https://aembit.io/blog/how-to-enable-filesystem-support-in-model-context-protocol-mcp/

[^1_7]: https://apps.microsoft.com/detail/9npk4dzd6r6s?hl=en-US\&gl=US

[^1_8]: https://www.reddit.com/r/windowsapps/comments/1ucujoq/i_built_a_fast_keyboardfirst_desktop_file_manager/

[^1_9]: https://www.reddit.com/r/pcmasterrace/comments/1q8erho/copilot_could_soon_live_inside_windows_11s_file/

[^1_10]: https://www.pcmag.com/news/copilot-creeps-into-file-explorer-and-the-taskbar-on-windows-11

[^1_11]: https://www.xda-developers.com/my-file-management-was-chaos-before-i-discovered-this-apps-dual-pane-interface/

[^1_12]: https://learn.microsoft.com/en-us/answers/questions/5941911/how-to-get-the-copilot-inside-my-ms-files

[^1_13]: https://myscale.com/blog/ai-file-explorer-windows-11-advanced-search/

[^1_14]: https://thelinuxcast.org/posts/2025/i-had-ai-make-me-a-file-manager/

[^1_15]: https://www.reddit.com/r/ClaudeAI/comments/1h4yvep/mcp_filesystem_is_magic/


---

# I don't want to start at the beginning and start fresh look for some open source libraries that couldn't or programming libraries and rust or go that would fill in a lot of the gaps and create the vast majority of what I'm looking to do

Yes — you do **not** need to start from zero. The fastest path is to assemble this from an existing open-source file manager foundation plus a filesystem tool layer for the agent, and Rust is clearly the stronger ecosystem fit than Go for the majority of what you described.[^2_1]

## Best foundations

- **Spacedrive** is the most relevant open-source base I found for your target shape: cross-platform file manager, Rust core, Tauri desktop app, React frontend, content identity, indexing, search, previewable/transactional operations, daemon model, and an extension system. That covers a very large share of the hard parts you were describing before you even add an AI copilot.[^2_1]
- Its architecture already includes a Rust core, desktop shell, CLI/daemon split, event-driven design, CQRS-style actions and queries, and preview-before-execute behavior for file operations, which is unusually aligned with “agent suggests, user approves, then mutate.”
- If your goal is “reuse the most surface area possible,” Spacedrive is the first repo I would audit deeply before building anything custom.


## Agent access layer

- For the agent/tool boundary, the open-source **Filesystem MCP Server** is an excellent reference or direct dependency if you want a permissioned file-operation surface rather than ad hoc custom tool glue. It already exposes read, write, edit, create directory, list directory, move, search, metadata lookup, and allowed-directory listing.
- Its security model is especially useful for your use case: operations are restricted to explicitly allowed directories, and the edit flow supports a dry-run preview before applying changes. That maps well to a copilot that can discuss changes, stage them, then ask for confirmation.
- If you want this layer in Rust instead of Node, the **rust-mcp-filesystem** project is a Rust rewrite specifically positioned as a filesystem MCP server for high-performance typed filesystem operations.[^2_2][^2_3]


## Rust options

- Recommended Rust stack:
    - **Spacedrive** for file-manager substrate and architectural reference or direct fork/base.
    - **rust-mcp-filesystem** or an MCP implementation approach for the agent tool surface.[^2_4][^2_2]
    - **Tauri** for desktop packaging, because Spacedrive already uses that route and it keeps you close to a practical cross-platform model.
- A second Rust reference worth inspecting is **EdenExplorer**, which is a modern open-source Windows file explorer built in Rust and focused on performance. It looks more like a traditional explorer replacement than an AI-ready platform, so I would treat it as a UI/reference candidate, not the main architecture pick.[^2_5]
- If you only need small desktop filesystem helpers in Rust rather than a full manager base, **file-handle** exists as a lighter-weight Rust crate for common desktop filesystem interactions, though it is much narrower in scope than your actual product.[^2_6]


## Go options

- Go has fewer strong matches for a rich local desktop dual-pane file manager with AI integration. The most relevant reusable piece I found is **hacdias/filemanager** (sometimes surfaced as filebrowser/filemanager), which provides a web-based file management interface with upload, delete, preview, rename, and edit operations inside a specified directory.[^2_7]
- That can help if you want a Go-based backend or embeddable file-management service, but it is much closer to a browser file admin tool than a native-feeling dual-pane desktop copilot workspace.[^2_7]
- For abstraction at the filesystem layer, **HackpadFS** gives Go filesystem interfaces and portability, but it is infrastructure plumbing rather than a near-complete product shell.[^2_8]


## What to adopt

- If you want maximum acceleration with your existing polyglot architecture, I would rank the options like this:
    - **1. Spacedrive as primary base or fork** for the desktop/file-indexing/action model.
    - **2. MCP filesystem server pattern** for agent-safe file access and approval workflows.[^2_2]
    - **3. Your own copilot/sidebar and orchestration layer** on top, using your existing React and Go-oriented system boundaries where appropriate.
- Given your preference for open-source and avoiding expensive proprietary dependencies, this route fits well: Spacedrive is AGPL-3.0, and the reference MCP filesystem server is MIT-licensed.
- Because your broader stack already uses a Go orchestrator with strict ownership boundaries, I would avoid forcing Go to become the desktop UI/file-manager foundation. Let Rust own the file-manager substrate, and let your existing orchestration layer remain the higher-level coordinator if needed.

Would you like me to do the next pass as a **ranked shortlist with repo-by-repo pros, cons, license, extensibility, AI fit, and “fork vs integrate vs just borrow ideas” guidance**?

<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/spacedriveapp/spacedrive

[^2_2]: https://github.com/rust-mcp-stack/rust-mcp-filesystem

[^2_3]: https://skillsllm.com/skill/rust-mcp-filesystem

[^2_4]: https://rustify.rs/articles/rust-for-mcp-model-context-protocol-servers-2026

[^2_5]: https://mtucciarone.github.io/EdenExplorer/

[^2_6]: https://lib.rs/crates/file-handle

[^2_7]: https://pkg.go.dev/github.com/hacdias/filemanager

[^2_8]: https://blog.johnstarich.com/write-once-store-anywhere-extensible-file-systems-for-go-65c7c0949e74

[^2_9]: https://www.reddit.com/r/golang/comments/y69a37/go_gui_with_access_to_filesystem_best_approach/

[^2_10]: https://github.com/systemis/file-management

[^2_11]: https://news.ycombinator.com/item?id=37841013

[^2_12]: https://www.shuttle.dev/blog/2025/09/15/mcp-servers-rust-comparison

[^2_13]: https://www.reddit.com/r/mcp/comments/1hlgf4c/mcp_filesystem_server_written_in_rust_includes_a/

[^2_14]: https://sourceforge.net/directory/file-managers/rust/

[^2_15]: https://play.google.com/store/apps/details?id=com.alphainventor.filemanager\&hl=en_US


---

# will I have file preview I need to be able to preview the files also

Yes — **file preview is absolutely possible**, but you should separate two different meanings of “preview” because they are implemented differently. Existing foundations already support both content preview and action preview, though not every stack does both equally well.[^3_1][^3_2][^3_3]

## Two preview types

- **Content preview** means seeing the selected file itself: image thumbnails, video/audio playback, text snippets, PDF rendering, metadata, or a generated lightweight proxy. Spacedrive explicitly supports previewing and organizing files, and third-party coverage notes image/video previews plus low-resolution previews for large media.[^3_4][^3_5][^3_6]
- **Action preview** means seeing what a move, rename, edit, or batch organization step would do before you commit it. Spacedrive exposes transactional operation previews, and filesystem MCP servers commonly support dry-run previews for edits and replacements.[^3_3][^3_7][^3_1]


## What existing bases give you

- **Spacedrive** is the strongest fit if preview is a first-class requirement, because it already positions itself around search, browsing, inspector metadata, and previewing operations before execution. It also appears to support lightweight previews for large media, which is useful if your AI layer needs to reason about files without fully opening or copying them.[^3_8][^3_5][^3_3]
- **filebrowser/filemanager** in Go explicitly says it can preview and edit files within a specified directory, so it is viable if your definition of preview is mainly “show the file in a web UI.” It is less compelling than Spacedrive for a local-first AI desktop experience, but preview is definitely on the table there.[^3_2][^3_9]
- **Filesystem MCP servers** are mainly for tool access, not polished visual preview panes. They help the agent read content and preview proposed changes, but they do not replace a real viewer layer for PDFs, images, audio, video, or office documents.[^3_10][^3_7][^3_1]


## Practical preview design

- Your app should have a dedicated **preview pane** or inspector that reacts to selection immediately:
    - Images: thumbnail/full preview.
    - Video/audio: lightweight playback or poster frame.
    - Text/code/Markdown/JSON: syntax-aware snippet.
    - PDF: embedded first page or scrollable renderer.
    - Office docs: extracted text plus metadata, or rendered preview if you add conversion support.
    - Unknown/binary: icon, size, hash, MIME, timestamps, and agent summary.[^3_5][^3_11][^3_8]
- For the AI copilot, the useful pattern is: user selects files, preview pane renders visual/content summary, agent receives the same normalized preview context, then suggests actions. That keeps the human and agent looking at the same thing.[^3_8][^3_1][^3_3]


## Best answer for you

- If preview matters a lot, **do not** rely on an MCP filesystem server alone; use it for controlled access and mutations, but put it behind a UI foundation that already understands previews.[^3_1][^3_10]
- The strongest reuse path remains **Spacedrive + your own AI sidebar/tool orchestration**, because it already gets you close on browsing, indexing, metadata inspection, and preview-aware operations.[^3_3][^3_5][^3_8]
- If you want, the next useful step is to break preview requirements into a matrix by file type — images, PDFs, text/code, Office docs, audio/video, archives, binaries — and identify what Spacedrive already covers versus what you would need to add.

<span style="display:none">[^3_12][^3_13][^3_14][^3_15]</span>

<div align="center">⁂</div>

[^3_1]: https://mcpservers.org/servers/gomcpgo/filesys

[^3_2]: https://pkg.go.dev/github.com/hacdias/filemanager

[^3_3]: https://github.com/spacedriveapp/spacedrive

[^3_4]: https://spacedrive.com/

[^3_5]: https://spacedrive.en.uptodown.com/windows

[^3_6]: https://www.todayonmac.com/spacedrive-the-file-explorer-you-didnt-know-you-needed/

[^3_7]: https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem

[^3_8]: https://v2.spacedrive.com/overview/get-started

[^3_9]: https://github.com/filebrowser/filebrowser

[^3_10]: https://github.com/cyanheads/filesystem-mcp-server

[^3_11]: https://www.raymondcamden.com/2026/08/11/file-preview-a-simple-web-component-for-file-previews

[^3_12]: https://hacdias.com/2020/01/23/bye-filebrowser/

[^3_13]: https://embracethered.com/blog/posts/2025/anthropic-filesystem-mcp-server-bypass/

[^3_14]: https://www.donationcoder.com/forum/index.php?topic=44064.0

[^3_15]: https://lobehub.com/mcp/marcusjellinghaus-mcp-server-filesystem


---

# do the deep dive on your first stack with space whateverand make sure that the AI is closely integrated so like I can highlight a group of folders and it will be able to see it we can preview it in a side window or something decide what it is classify it move it and and it can be able to pick up patterns and rules and detections for for what I'm doing so that it can scanning begin making recommendations before I do it manually

Answer skipped.

---

# continue

The deep dive is done. Spacedrive v2 turns out to be an unusually good fit — not for cosmetic reasons, but because its command model already works the exact way an AI copilot needs to work: every mutation runs `Preview → Commit → Verify`, so "agent proposes, you approve, system executes with an audit trail" is just how normal Spacedrive commands behave rather than something you'd have to invent.[^5_1]

A few highlights worth flagging up front:

- The extension docs explicitly describe extensions that "create AI agents with unlimited memory," "generate derivative sidecars," and "propose file operations with user approval" — your exact use case is a stated design target, though the SDK is still pre-stable.[^5_2][^5_1]
- Content identity via BLAKE3 means classifications, embeddings, and learned rules key to file *content*, not path — so nothing is lost when the copilot moves a file.[^5_1]
- The daemon architecture gives you the persistent background process that proactive scanning requires; a UI-hosted agent would lose all learned state on window close.[^5_1]
- Two real constraints: v2 is alpha with Windows landing in alpha.2 (you're on Michigan/Windows), and the core is AGPL-3.0, which for a distributed desktop app behaves like GPL.[^5_3][^5_1]
- Worth a serious look as an alternative: **Xplorer** — Tauri 2 + Rust + React, already ships AI chat, split panes, and video preview, and is Apache-2.0 instead of AGPL.[^5_4][^5_5][^5_6]

The report covers the full stack recommendation (`rmcp` for the tool boundary, `rig` + `fastembed` + `sqlite-vec` for the agent and local classification, `organize`-style YAML for synthesized rules, `trash` for reversible deletion), the preview crate matrix by file type, a four-layer design for pattern learning and proactive recommendations, and a 10-phase build sequence starting with a Windows feasibility gate.

<span style="display:none">[^5_10][^5_100][^5_101][^5_102][^5_103][^5_104][^5_105][^5_106][^5_107][^5_108][^5_109][^5_11][^5_110][^5_111][^5_112][^5_113][^5_114][^5_115][^5_116][^5_117][^5_118][^5_119][^5_12][^5_120][^5_121][^5_122][^5_123][^5_124][^5_125][^5_126][^5_127][^5_128][^5_129][^5_13][^5_130][^5_131][^5_132][^5_133][^5_134][^5_135][^5_136][^5_137][^5_138][^5_139][^5_14][^5_140][^5_141][^5_142][^5_143][^5_144][^5_15][^5_16][^5_17][^5_18][^5_19][^5_20][^5_21][^5_22][^5_23][^5_24][^5_25][^5_26][^5_27][^5_28][^5_29][^5_30][^5_31][^5_32][^5_33][^5_34][^5_35][^5_36][^5_37][^5_38][^5_39][^5_40][^5_41][^5_42][^5_43][^5_44][^5_45][^5_46][^5_47][^5_48][^5_49][^5_50][^5_51][^5_52][^5_53][^5_54][^5_55][^5_56][^5_57][^5_58][^5_59][^5_60][^5_61][^5_62][^5_63][^5_64][^5_65][^5_66][^5_67][^5_68][^5_69][^5_7][^5_70][^5_71][^5_72][^5_73][^5_74][^5_75][^5_76][^5_77][^5_78][^5_79][^5_8][^5_80][^5_81][^5_82][^5_83][^5_84][^5_85][^5_86][^5_87][^5_88][^5_89][^5_9][^5_90][^5_91][^5_92][^5_93][^5_94][^5_95][^5_96][^5_97][^5_98][^5_99]</span>

<div align="center">⁂</div>

[^5_1]: https://v2.spacedrive.com/extensions/introduction

[^5_2]: https://github.com/spacedriveapp/spacedrive

[^5_3]: https://spacedrive.com/

[^5_4]: https://opensource.stackexchange.com/questions/6879/may-i-use-agpl-license-in-a-desktop-application-without-providing-the-source-cod

[^5_5]: https://fossa.com/blog/open-source-software-licenses-101-agpl-license/

[^5_6]: https://github.com/spacedriveapp/spacedrive/blob/main/AGENTS.md

[^5_7]: https://v2.spacedrive.com/overview/get-started

[^5_8]: https://spacedrive.en.uptodown.com/windows

[^5_9]: https://github.com/bojand/infer

[^5_10]: https://www.reddit.com/r/rust/comments/1txqa5d/how_do_i_check_the_file_type_in_rust/

[^5_11]: https://github.com/ajrcarey/pdfium-render

[^5_12]: https://lib.rs/crates/pdfium-render

[^5_13]: https://github.com/anvie/dotext

[^5_14]: https://docs.rs/docx-lite

[^5_15]: https://docs.rs/image/latest/image/imageops/fn.resize.html

[^5_16]: https://github.com/cykooz/fast_image_resize

[^5_17]: https://www.reddit.com/r/rust/comments/1on2xhr/resizing_images_in_rust_now_with_exif_orientation/

[^5_18]: https://crates.io/crates/ffmpeg-next

[^5_19]: https://docs.rs/ffmpeg-next

[^5_20]: https://github.com/tfeldmann/organize

[^5_21]: https://guissmo.com/blog/automated-file-organization-using-organize/

[^5_22]: https://mcpservers.org/servers/gomcpgo/filesys

[^5_23]: https://lobehub.com/mcp/marcusjellinghaus-mcp-server-filesystem

[^5_24]: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

[^5_25]: https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem

[^5_26]: https://github.com/modelcontextprotocol/rust-sdk

[^5_27]: https://docs.rs/rmcp

[^5_28]: https://hackmd.io/@Hamze/S1tlKZP0kx

[^5_29]: https://crates.io/crates/rust-mcp-sdk

[^5_30]: https://github.com/rust-mcp-stack/rust-mcp-filesystem

[^5_31]: https://skillsllm.com/skill/rust-mcp-filesystem

[^5_32]: https://embracethered.com/blog/posts/2025/anthropic-filesystem-mcp-server-bypass/

[^5_33]: https://rustify.rs/articles/rust-ai-agents-from-scratch-2026

[^5_34]: https://rig.rs/

[^5_35]: https://github.com/0xplaygrounds/rig

[^5_36]: https://docs.rs/rig-core

[^5_37]: https://www.reddit.com/r/rust/comments/1rchad0/neuron_composable_building_blocks_for_ai_agents/

[^5_38]: https://github.com/anush008/fastembed-rs

[^5_39]: https://docs.rs/fastembed

[^5_40]: https://dev.to/joshmo_dev/local-embeddings-with-fastembed-rig-rust-3581

[^5_41]: https://github.com/asg017/sqlite-vec

[^5_42]: https://news.ycombinator.com/item?id=40243168

[^5_43]: https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html

[^5_44]: https://openapps.pro/packages/sqlite-vec

[^5_45]: https://github.com/sqliteai/sqlite-memory

[^5_46]: https://docs.rs/notify/

[^5_47]: https://www.reddit.com/r/rust/comments/q6nyc6/async_file_watcher_like_notifyrs/

[^5_48]: https://github.com/notify-rs/notify

[^5_49]: https://v2.spacedrive.com/core/locations

[^5_50]: https://filearbor.com/blog/best-automatic-file-organizers-windows-mac

[^5_51]: https://docs.rs/trash

[^5_52]: https://crates.io/crates/trash

[^5_53]: https://lib.rs/crates/ai-trash

[^5_54]: https://crates.io/crates/trash/1.3.0

[^5_55]: https://v2.tauri.app/plugin/file-system/

[^5_56]: https://v2.tauri.app/security/permissions/

[^5_57]: https://github.com/orgs/tauri-apps/discussions/11792

[^5_58]: https://v2.tauri.app/reference/javascript/fs/

[^5_59]: https://aembit.io/blog/how-to-enable-filesystem-support-in-model-context-protocol-mcp/

[^5_60]: https://docs.rs/ignore

[^5_61]: https://crates.io/crates/ignore

[^5_62]: https://john-cd.com/rust_howto/categories/filesystem/directory_traversal.html

[^5_63]: https://www.reddit.com/r/rust/comments/1rdsc6u/parawalk_a_minimal_parallel_directory_walker_no/

[^5_64]: https://snyk.io/articles/agpl-license/

[^5_65]: https://github.com/kimlimjustin/xplorer

[^5_66]: https://xplorer.space/

[^5_67]: https://dev.to/kimlimjustin/xplorer-a-modern-file-explorer-that-was-written-using-typescript-has-its-performance-improved-on-the-recent-release-4f99

[^5_68]: https://sourceforge.net/projects/xplorer.mirror/

[^5_69]: https://dev.to/kimlimjustin/i-put-vs-code-claude-and-a-terminal-inside-a-file-manager-i-built-using-react-and-rust-heres-k1n

[^5_70]: https://github.com/sxyazi/yazi

[^5_71]: https://yazi-rs.github.io/docs/plugins/overview/

[^5_72]: https://www.reddit.com/r/rust/comments/16fxr58/meet_yazi_blazing_fast_terminal_file_manager/

[^5_73]: https://yazi-rs.github.io/docs/resources/

[^5_74]: https://pkg.go.dev/github.com/hacdias/filemanager

[^5_75]: https://blog.johnstarich.com/write-once-store-anywhere-extensible-file-systems-for-go-65c7c0949e74

[^5_76]: https://github.com/filebrowser/filebrowser

[^5_77]: https://v2.spacedrive.com/extensions/getting-started

[^5_78]: https://www.reddit.com/r/rust/comments/1jglry7/introducing_rmcp_maybe_the_best_rust_mcp_sdk/

[^5_79]: https://docs.cloud.google.com/sdk/gcloud/reference/alpha/service-extensions/wasm-plugins/create

[^5_80]: https://www.reddit.com/r/rust/comments/17dniwx/fastembedrs_rust_library_to_generate_sentence/

[^5_81]: https://v2.spacedrive.com/overview/introduction

[^5_82]: https://crates.io/crates/fastembed/5.3.1

[^5_83]: https://crates.io/keywords/filetype

[^5_84]: https://www.reddit.com/r/rust/comments/jhrmol/send_files_to_trash/

[^5_85]: https://docs.rs/philiprehberger-mime-detect

[^5_86]: https://docs.rs/notify/latest/notify/trait.Watcher.html

[^5_87]: https://users.rust-lang.org/t/read-metadata-from-a-binary-file/52393

[^5_88]: https://dev.to/sendotltd/the-notify-crate-is-surprisingly-pleasant-i-built-a-cross-platform-file-watcher-in-four-7md

[^5_89]: https://crates.io/keywords/text-extraction

[^5_90]: https://www.reddit.com/r/rust/comments/1pwryik/pdfiumbind_easiest_way_to_add_pdf_rendering_in/

[^5_91]: https://lib.rs/crates/docxide-pdf

[^5_92]: https://docs.rs/crate/pdfium-render/0.5.0

[^5_93]: https://crates.io/crates/kreuzberg-pdfium-render

[^5_94]: https://stackoverflow.com/questions/79262872/tauri-v2-trouble-with-the-file-system-s-mkdir

[^5_95]: https://users.rust-lang.org/t/reading-ms-word-file/21397

[^5_96]: https://www.reddit.com/r/LocalLLaMA/comments/1ehlazq/introducing_sqlitevec_v010_a_vector_search_sqlite/

[^5_97]: https://www.reddit.com/r/selfhosted/comments/12sv535/organize_file_management_automation_tool/

[^5_98]: https://www.simular.ai/use-cases/file-organizer

[^5_99]: https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html

[^5_100]: https://ai-sdk.dev/docs/agents/memory

[^5_101]: https://spacedrive.com/blog/alpha-zero-two-release

[^5_102]: https://www.meetapro.com/blog/designing-a-semantic-search-system-for-internal-documents-78

[^5_103]: https://www.reddit.com/r/AgentsOfAI/comments/1ptwmc1/how_do_you_store_longterm_memory_for_ai_agents/

[^5_104]: https://docs.opensearch.org/latest/vector-search/ai-search/semantic-search/

[^5_105]: https://agent-memory.dev/

[^5_106]: https://www.elastic.co/docs/solutions/search/semantic-search

[^5_107]: https://community.openai.com/t/add-longterm-memory-per-user-using-openai-agents-sdk/1324654

[^5_108]: https://www.reddit.com/r/rust/comments/1vwz76e/video_thumbnail_extraction/

[^5_109]: https://users.rust-lang.org/t/image-crate-resize/97978

[^5_110]: https://www.reddit.com/r/rust/comments/irgb4u/imagers_and_images_with_hugeish_dimensions/

[^5_111]: https://users.rust-lang.org/t/walkdir-performance-a-small-experiment/24112

[^5_112]: https://users.rust-lang.org/t/how-to-put-data-into-a-frame-in-ffmpeg/49199

[^5_113]: https://lib.rs/multimedia/video

[^5_114]: https://yazi-rs.github.io/docs/installation

[^5_115]: https://www.reddit.com/r/rust/comments/wzqrez/can_i_use_an_agpl_licensed_crate_in_my_closed/

[^5_116]: https://discuss.logseq.com/t/on-the-agpl-license-and-the-idea-to-move-away-from-it/14716?page=3

[^5_117]: https://www.reddit.com/r/tauri/comments/1m2tv5i/building_a_fast_file_manager_how_hard_can_it_be/

[^5_118]: https://apps.microsoft.com/detail/9npk4dzd6r6s?hl=en-US\&gl=US

[^5_119]: https://www.reddit.com/r/windowsapps/comments/1ucujoq/i_built_a_fast_keyboardfirst_desktop_file_manager/

[^5_120]: https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers

[^5_121]: https://www.reddit.com/r/pcmasterrace/comments/1q8erho/copilot_could_soon_live_inside_windows_11s_file/

[^5_122]: https://doublecmd.sourceforge.io/

[^5_123]: https://www.pcmag.com/news/copilot-creeps-into-file-explorer-and-the-taskbar-on-windows-11

[^5_124]: https://www.xda-developers.com/my-file-management-was-chaos-before-i-discovered-this-apps-dual-pane-interface/

[^5_125]: https://learn.microsoft.com/en-us/answers/questions/5941911/how-to-get-the-copilot-inside-my-ms-files

[^5_126]: https://myscale.com/blog/ai-file-explorer-windows-11-advanced-search/

[^5_127]: https://thelinuxcast.org/posts/2025/i-had-ai-make-me-a-file-manager/

[^5_128]: https://www.reddit.com/r/ClaudeAI/comments/1h4yvep/mcp_filesystem_is_magic/

[^5_129]: https://www.reddit.com/r/golang/comments/y69a37/go_gui_with_access_to_filesystem_best_approach/

[^5_130]: https://github.com/systemis/file-management

[^5_131]: https://news.ycombinator.com/item?id=37841013

[^5_132]: https://www.shuttle.dev/blog/2025/09/15/mcp-servers-rust-comparison

[^5_133]: https://mtucciarone.github.io/EdenExplorer/

[^5_134]: https://www.reddit.com/r/mcp/comments/1hlgf4c/mcp_filesystem_server_written_in_rust_includes_a/

[^5_135]: https://sourceforge.net/directory/file-managers/rust/

[^5_136]: https://rustify.rs/articles/rust-for-mcp-model-context-protocol-servers-2026

[^5_137]: https://lib.rs/crates/file-handle

[^5_138]: https://play.google.com/store/apps/details?id=com.alphainventor.filemanager\&hl=en_US

[^5_139]: https://hacdias.com/2020/01/23/bye-filebrowser/

[^5_140]: https://github.com/cyanheads/filesystem-mcp-server

[^5_141]: https://www.donationcoder.com/forum/index.php?topic=44064.0

[^5_142]: https://www.todayonmac.com/spacedrive-the-file-explorer-you-didnt-know-you-needed/

[^5_143]: https://www.raymondcamden.com/2026/08/11/file-preview-a-simple-web-component-for-file-previews

[^5_144]: https://v2.spacedrive.com/core/architecture


---

# Licensing doesn't really matter to me. Because it's a personal tool. Do a deep dive then on. The second option there the explore option. How that would work?

Here's the deep dive on the Xplorer path. One important correction to my earlier summary first: **Xplorer is AGPL-3.0, not Apache-2.0** — the LICENSE file on the `next` branch reads "GNU AFFERO GENERAL PUBLIC LICENSE Version 3" with copyright Justin Maximillian Kimlim, 2026. You said licensing doesn't matter for a personal tool, so this is moot for you, but it means both of your candidate bases are AGPL and neither has a licensing edge.

## What Xplorer actually is

- A Tauri v2 desktop file explorer: Rust backend, React 18 + TypeScript frontend, Vite 5, Tailwind with a glassmorphic theme, TanStack Query for state, and a pnpm monorepo.[^6_1]
- Repo is `kimlimjustin/xplorer` — 5,666 stars, created April 2021, default branch `next`, last push June 2026, with the modern rewrite tagged `v1.0.0-alpha.1` in April 2026. The 2022-era `v0.3.1` releases are the old codebase; everything relevant lives on `next`.
- Monorepo layout is `apps/client` (React SPA), `apps/src-tauri` (Rust), `apps/web` (Next.js docs + marketplace), and `packages/{sdk, extension-sdk, create-extension, extensions, cli}`.
- Windows is a first-class target, not an afterthought — the getting-started prerequisites list Visual Studio Build Tools with the C++ workload and WebView2, and there's a dedicated `windows_recycle_bin.rs` (15KB) plus Windows registry shell-integration commands (`set_default_folder_handler`, `add_context_menu_entry`). This is the single biggest practical advantage over the Spacedrive path for you.


## The critical discovery: it already has both halves you need

This is what makes Xplorer a genuinely different proposition from "a file manager you'd bolt an agent onto."

**It already ships an MCP server.** `apps/src-tauri/src/mcp_server.rs` is a JSON-RPC 2.0 over stdio server, activated by launching the binary with `--mcp-server`. The header comment literally documents the intended invocation as `claude --mcp-server "xplorer --mcp-server"`. It implements `initialize`, `tools/list`, and `tools/call` against MCP protocol version `2024-11-05`, routing calls to handlers in `mcp_host.rs`.

The exposed tool set is currently narrow — six tools: `read_file`, `write_file`, `list_directory`, `search_files`, `run_command`, `get_git_status`. That's your extension point, and it's a small, obvious file to extend.

**It also already ships its own agent.** `apps/src-tauri/src/agent/` is roughly 165KB of Rust across seven files: `mod.rs`, `tools.rs`, `tool_executor.rs`, `planner.rs`, `streaming.rs`, `memory.rs`, and `security.rs`. The internal agent tool vocabulary is much richer than the MCP surface — `read_file`, `write_file`, `copy_file`, `move_file`, `rename`, `delete`, `create_directory`, `list_directory`, `search_files`, `search_content`, `search_indexed`, `extract_document_text`, `execute_command`, `get_system_info`, plus `create_plan` / `execute_plan` / `remember` / `recall`.

That last group matters. `create_plan`, `execute_plan`, and `agent_approve_plan` mean the propose-then-approve loop you want is already modeled in the backend, not something you'd have to invent.

## The security model is the part worth stealing

`agent/security.rs` is 33KB and is the most reassuring file in the repo:

- `normalize_path` resolves `.` and `..` without requiring the path to exist on disk, falling back when `canonicalize` fails — this is the correct way to prevent traversal on not-yet-created destinations, which is exactly what a "move these files there" operation needs.
- `validate_agent_path` rejects known sensitive system locations.
- `is_blocked_command` maintains a hard blocklist of commands the agent may never execute.
- `is_network_command` supports an "internet sandbox" mode that blocks a broader set of network-reaching and diagnostic/transfer tools beyond the default blocklist (which already covers curl, wget, ssh, nc).
- `is_custom_blocked_command` and `validate_agent_path_with_permissions` layer user config on top: system blocklist first, then custom blocked paths, then an allow-list where a non-empty list means the path must be inside one of them.

That allow-list-plus-blocklist-plus-custom design is precisely the permission model I described in the first answer, already implemented. There are matching Tauri commands — `get_agent_permissions` and `update_agent_permissions` — so it's user-configurable at runtime rather than compile-time.

## Backend surface you'd be building on

`main.rs` registers roughly 300 Tauri commands. The ones that matter for your product:


| Capability | Commands available |
| :-- | :-- |
| Core mutation | `copy`, `copy_with_progress`, `move_file`, `move_with_progress`, `rename`, `bulk_rename`, `remove_file`, `remove_dir`, `cancel_file_operation` |
| Reversibility | `move_to_trash`, `get_trash_items`, `restore_trash_item`, `undo_operation`, `redo_operation`, `get_undo_history` |
| Versioning | `enable_versioning`, `create_version`, `list_versions`, `restore_version`, `get_version_count` |
| Audit | `get_audit_log`, `clear_audit_log`, `export_audit_log` |
| Organization | `analyze_directory`, `preview_organization`, `execute_organization` (from `file_organizer.rs`, 37KB) |
| Semantic retrieval | `semantic_search`, `hybrid_search`, `find_similar_files`, `trigger_ai_indexing`, `get_ai_index_status`, `natural_language_search`, `get_file_recommendations` |
| Metadata | tags (incl. `batch_add_tags` / `batch_remove_tags`), notes, annotations, tag categories, custom metadata, bookmarks, recents |
| Conflict handling | `check_conflicts`, `get_rename_destination` |
| Terminal | `pty_spawn`, `pty_write`, `pty_resize`, `pty_kill`, `pty_kill_all` |
| Extraction | `extract_document_text` (PDF/DOCX/XLSX/PPTX, 17KB module) |

The `file_organizer` trio — `analyze_directory` → `preview_organization` → `execute_organization` — is the same Preview/Commit shape I praised in Spacedrive, and `analyze_storage`, `find_duplicates`, and `compute_file_hash` cover the analysis side.

The search module is unexpectedly serious for a file manager: BM25F scoring, an FST index, inverted index with segmentation, stemming, synonym expansion, fuzzy matching, bitmap filters, a context ranker, a reranker, an Ollama embedding client, and a filesystem watcher for incremental index updates. You would not need to build the retrieval layer.

## How you'd wire in opencode and Claude

Three viable paths. The third is what exists today; the first is what you should build.

**Path A — ACP client (recommended).** Make Xplorer an Agent Client Protocol *Client* and run opencode or Claude as an agent subprocess. ACP standardizes editor-to-agent communication over JSON-RPC 2.0 on stdio and is explicitly designed as "the LSP for AI agents". The flow is `initialize` → optional `authenticate` → `session/new` (or `session/load`) → `session/prompt`, with the agent streaming `session/update` notifications back and the turn ending with a `stopReason`.[^6_2][^6_3][^6_4]

The reason this fits your requirements almost eerily well:

- `session/request_permission` is a **baseline Client method** — the agent asks *you* for authorization before each tool call, and the spec has the client mark pending tool calls and respond with `cancelled` on interruption. Your dual-pane UI becomes the approval surface for free.
- Tool calls arrive as `session/update` notifications with `toolCallId`, `title`, `kind`, and a status lifecycle of `pending` → `in_progress` → `completed`, so you can render live per-operation progress in the pane.
- The `plan` update type carries entries with `content`, `priority`, and `status` — that's your batch-plan diff view, protocol-native.
- `session/prompt` accepts a `ContentBlock[]` including `resource` blocks with `uri`, `mimeType`, and inline `text`. **Your file selection maps directly onto this.** Multi-select a group of files, and each becomes a resource block. This is the "copilot immediately sees the selection" requirement, satisfied by the protocol rather than by string-concatenating paths into a prompt.
- `session/cancel` gives you a real stop button, and `usage_update` reports tokens used, context size, and cumulative cost in ISO 4217 currency — useful given your habit of tracking model spend.
- All protocol file paths MUST be absolute, and line numbers are 1-based.
- Extensibility is built in: `_meta` fields, custom methods prefixed with `_`, and custom capabilities advertised at initialization. You'd use this for file-manager-specific concepts the spec doesn't model, like "current pane target directory."
- `session/set_mode` maps cleanly onto the Discuss / Draft / Apply modes from the first answer.

On the agent side, both of your preferred backends are already ACP agents:

- **opencode** supports ACP natively — you run `opencode acp` and it speaks JSON-RPC over stdio as a subprocess. All features work identically to the terminal: built-in tools, custom tools and slash commands, configured MCP servers, `AGENTS.md` project rules, custom formatters/linters, and the agents-and-permissions system.[^6_5][^6_6]
- **Claude** has an official adapter. Zed ships `@zed-industries/claude-code-acp`, installable globally via npm, and there's now `@agentclientprotocol/claude-agent-acp` — an ACP agent built on the official Claude Agent SDK. The adapter is a translator: it receives ACP from the client and converts to Claude Agent SDK calls.[^6_3][^6_7]

Because both speak the same protocol, **you write one integration and get a backend switcher.** That's a strictly better outcome than the current situation where the Xplorer agent module is Claude-specific Rust.

There's also a well-trodden pattern worth copying from `josephschmitt/opencode-acp`: on session start it launches a per-session MCP HTTP server proxying file and terminal actions back to ACP, starts `opencode serve` in the session cwd, and **injects config to disable opencode's built-in destructive tools** — `read`, `write`, `edit`, `multiedit`, `bash`, `patch` — then registers the MCP bridge so opencode uses ACP-backed tools instead. That inversion is the key safety move: the agent loses its own unmediated filesystem access and can only act through *your* permissioned tools. opencode supports exactly this via the `permission` field in `opencode.json`, which allows, denies, or requires approval per tool with wildcard support (e.g. requiring approval for all tools from a given MCP server).[^6_8][^6_9][^6_10]

**Path B — Xplorer as MCP server.** Leave the agent outside entirely; extend `mcp_host.rs` from six tools to the full vocabulary (`move_file`, `bulk_rename`, `move_to_trash`, `batch_add_tags`, `preview_organization`, `execute_organization`, `semantic_search`, `find_similar_files`, `check_conflicts`, `undo_operation`) and connect Claude Code or opencode as an MCP client. Cheapest path to something working, and it makes your file manager useful to *any* MCP client. Weakness: MCP has no equivalent of ACP's `session/request_permission` round-trip or plan updates, so the approval UI and streaming plan view are on you.

**Path C — Extension SDK panel (what ships today).** The `packages/extensions/claude-code` extension is instructive mainly as a cautionary tale. Its manifest declares `permissions: ["file:read","file:write","ui:panels","system:exec","ai:chat","ai:read"]`, `activationEvents: ["onStartup"]`, a `ctrl+shift+c` command, and registers a right-located sidebar panel. But the implementation `pty_spawn`s a terminal, writes the literal string `claude\n` to start interactive Claude, then **scrapes the PTY output** — stripping ANSI escapes with three chained regexes — and decides the response is finished via a 2-second polling interval that checks whether the message length stopped changing. It also flattens newlines out of your prompt before sending. It's a clever hack, not a foundation, and it's precisely the problem ACP was invented to solve.

Its one genuinely good idea, worth keeping: the panel reads `useCurrentPath()` and `useSelectedFiles()`, renders the selection as removable file chips above the input, and prepends structured context as `[Working directory: ...] [Selected files: path1, path2] <prompt>`. Replace the string-prepending with ACP `resource` content blocks and the chip UI carries over unchanged.

## The extension sandbox — and why it forces a fork

The Extension SDK is nicer than expected. High-level registration APIs cover `Theme`, `Sidebar`, `SidebarTab`, `BottomTab`, `Preview`, `Editor`, `Command`, and `ContextMenu`. `ContextMenu.register` takes a `when` clause of `'always' | 'singleFileSelected' | 'multipleFilesSelected' | 'directorySelected'` and an `action(files, api)` — a natural home for "Ask copilot about these." Reactive hooks (`useCurrentPath`, `useSelectedFiles`, `navigateTo`) and themed UI primitives (`Button`, `Input`, `Select`, `Toggle`, `Spinner`, `Panel`, `Card`) are provided. `XplorerAPI` exposes `files` (incl. `watch`), `ui` (`showMessage`, `showProgress`, `showInputBox`, `showQuickPick`), `navigation` (incl. `openInEditor`), `settings`, `commands`, `shortcuts`, plus `database`, `images`, `backup`, and `docker` namespaces. Extension context has VS Code-style `globalState` / `workspaceState` / `subscriptions` / `asAbsolutePath`, and there's hot-reload via `extension_watcher.rs` and signing via `extensions/signing.rs`.

**But the sandbox blocks exactly what you need.** Extensions run with `fetch`, `XMLHttpRequest`, `WebSocket`, `localStorage`, `sessionStorage`, `indexedDB`, `eval`, and — critically — `__TAURI__`, `__TAURI_INTERNALS__`, and `__TAURI_IPC__` all blocked. Extensions must go through the injected `XplorerAPI`.

`XplorerAPI` has **no process-spawning namespace**. There's no way to launch `opencode acp` as a subprocess from a sandboxed extension. Note that the shipped `claude-code` extension bypasses this by doing `await import('@tauri-apps/api/core')` and calling `invoke('pty_spawn', ...)` directly — meaning either the sandbox isn't uniformly enforced for bundled extensions or the docs and runtime disagree. Either way, that's not a boundary to build a serious tool on top of.

**Conclusion: fork, don't extend.** Add ACP support to `apps/src-tauri` as a first-class Rust module alongside `agent/` and `mcp_host.rs`, and expose it to the frontend through new Tauri commands rather than through the extension sandbox. For a personal tool with AGPL irrelevant to you, forking is the right call.

## Concrete build sequence

1. **Windows gate.** Clone the `next` branch, install Node 18+/pnpm/Rust/Tauri CLI/VS Build Tools + WebView2, run `pnpm dev` (Vite on 5174 + Tauri window), then `pnpm check`, `pnpm test`, `pnpm test:tauri`. Confirm `v1.0.0-alpha.1`-era code actually builds and that trash/recycle-bin ops work on your machine. Nothing else matters if this fails.
2. **Verify the MCP server.** Launch with `--mcp-server`, hand-drive `initialize` and `tools/list` over stdio, confirm the six tools respond. This validates the JSON-RPC plumbing before you write any ACP code.
3. **Build `acp_client.rs`.** Spawn agent subprocess, JSON-RPC over stdio, implement `initialize` with capability negotiation, `session/new`, `session/prompt`, and handle inbound `session/request_permission`, `fs/read_text_file`, `fs/write_text_file`, and the terminal methods. Reuse `pty.rs` for `terminal/*`. Advertise `fs.readTextFile` / `fs.writeTextFile` / `terminal` capabilities. Test against `opencode acp` first — it's a single command with no npm adapter layer.[^6_5]
4. **Route every agent action through `security.rs`.** Before honoring any `fs/write_text_file` or terminal request, run `validate_agent_path_with_permissions` and `is_blocked_command`. Configure the allow-list to your actual working roots. Turn on internet-sandbox mode for organization tasks — a file-organizing agent has no business making network calls.
5. **Neuter the agent's native tools.** Generate an `opencode.json` per session disabling `read`/`write`/`edit`/`multiedit`/`bash`/`patch` and pointing at your MCP bridge, following the `opencode-acp` pattern. For Claude, restrict tools through the Agent SDK adapter's config.[^6_9][^6_8]
6. **Selection → resource blocks.** On multi-select, build a `ContentBlock[]`: one `text` block with the instruction, one `resource` block per selected file with absolute `uri`, `mimeType`, and inline `text` for previewable types. Use `extract_document_text` to populate PDF/DOCX/XLSX/PPTX contents. Keep the file-chip UI from the existing extension.
7. **Plan → approval UI.** Render `plan` updates as an ordered checklist in the inactive pane, with per-entry priority and live status. Render `tool_call` / `tool_call_update` as rows transitioning pending → in_progress → completed. Wire `session/request_permission` to an inline approve/deny/approve-all control, and the stop button to `session/cancel`.
8. **Reversibility everywhere.** Force all agent deletions through `move_to_trash`. Bind Ctrl+Z to `undo_operation`. Enable `create_version` on directories the agent touches. Surface `get_audit_log` as a panel — you get a full history of what the copilot did, which is exactly what makes a mutating agent trustworthy.
9. **Add file-manager tools to `mcp_host.rs`.** Extend past the six defaults with `move_file`, `bulk_rename`, `check_conflicts`, `batch_add_tags`, `preview_organization`, `execute_organization`, `find_duplicates`, `semantic_search`, `find_similar_files`, `move_to_trash`, `undo_operation`. Register this as an MCP server in the ACP agent's config — opencode picks up configured MCP servers when running under ACP. Now the agent has organization-native verbs instead of only generic file I/O.[^6_5]
10. **Model routing.** Expose a backend picker in the panel: opencode (which brings its own multi-provider routing and an inline OpenRouter model picker per recent commits) vs. Claude via the Agent SDK adapter. Since both are ACP, this is a subprocess-command swap. Display `usage_update` tokens and cost in the panel footer.[^6_7]

## Xplorer vs. Spacedrive, revised

| Dimension | Xplorer | Spacedrive v2 |
| :-- | :-- | :-- |
| Windows readiness | Explicit VS Build Tools/WebView2 setup, dedicated recycle-bin module, registry shell integration | Windows arriving in alpha.2 |
| Agent already present | ~165KB Rust agent with planner, memory, tool executor, security | Command model is agent-friendly but no agent shipped |
| MCP | Server already implemented, 6 tools, extend from there | Would need building |
| Dual-pane | `use-split-layout` hook, split-pane layout present | Would need building |
| Retrieval | BM25F + FST + embeddings + watcher, built in | Content-addressed via BLAKE3 |
| Content identity | Hash via `compute_file_hash`, but path-keyed metadata | BLAKE3 content identity is architecturally central |
| Reversibility | Trash, undo/redo, file versions, audit log | Preview/Commit/Verify on every command |
| Extension model | Sandbox blocks subprocess spawning → fork required | Extension API pre-stable |
| Maturity signal | Last push June 2026, alpha.1 Apr 2026, agentic AI commits Apr 2026 | Alpha |
| License | AGPL-3.0 | AGPL-3.0 |

The honest tradeoff: **Spacedrive has the better foundational model** — content-addressed identity means learned classifications survive every move, which is architecturally cleaner than Xplorer's path-keyed tag/note storage. **Xplorer has far more of the actual product already built**, runs on Windows today, and already contains an agent security layer you'd otherwise spend weeks getting right.

Given you're building a personal tool on Windows and want opencode/Claude rather than a bespoke agent, Xplorer is the pragmatic choice — but fork it, add ACP as native Rust, and treat the existing `agent/` module as a source of security logic and tool vocabulary rather than as the agent you'll actually ship. If you later want content-addressed identity, adding a BLAKE3 column and re-keying the tags/notes/metadata tables to content hash is a contained change, since `compute_file_hash` already exists.

<span style="display:none">[^6_100][^6_101][^6_102][^6_103][^6_104][^6_105][^6_106][^6_107][^6_108][^6_109][^6_11][^6_110][^6_111][^6_112][^6_113][^6_114][^6_115][^6_116][^6_117][^6_118][^6_119][^6_12][^6_120][^6_121][^6_122][^6_123][^6_124][^6_125][^6_126][^6_127][^6_128][^6_129][^6_13][^6_130][^6_131][^6_132][^6_133][^6_134][^6_135][^6_136][^6_137][^6_138][^6_139][^6_14][^6_140][^6_141][^6_142][^6_143][^6_144][^6_145][^6_146][^6_147][^6_148][^6_149][^6_15][^6_150][^6_151][^6_152][^6_153][^6_154][^6_155][^6_156][^6_157][^6_158][^6_159][^6_16][^6_17][^6_18][^6_19][^6_20][^6_21][^6_22][^6_23][^6_24][^6_25][^6_26][^6_27][^6_28][^6_29][^6_30][^6_31][^6_32][^6_33][^6_34][^6_35][^6_36][^6_37][^6_38][^6_39][^6_40][^6_41][^6_42][^6_43][^6_44][^6_45][^6_46][^6_47][^6_48][^6_49][^6_50][^6_51][^6_52][^6_53][^6_54][^6_55][^6_56][^6_57][^6_58][^6_59][^6_60][^6_61][^6_62][^6_63][^6_64][^6_65][^6_66][^6_67][^6_68][^6_69][^6_70][^6_71][^6_72][^6_73][^6_74][^6_75][^6_76][^6_77][^6_78][^6_79][^6_80][^6_81][^6_82][^6_83][^6_84][^6_85][^6_86][^6_87][^6_88][^6_89][^6_90][^6_91][^6_92][^6_93][^6_94][^6_95][^6_96][^6_97][^6_98][^6_99]</span>

<div align="center">⁂</div>

[^6_1]: https://xplorer.space/donate

[^6_2]: https://agentclientprotocol.com/get-started/introduction

[^6_3]: https://github.com/anthropics/claude-code/issues/6686

[^6_4]: https://github.com/agentclientprotocol/agent-client-protocol

[^6_5]: https://opencode.ai/docs/acp/

[^6_6]: https://zed.dev/acp/agent/opencode

[^6_7]: https://www.npmjs.com/package/@agentclientprotocol/claude-agent-acp

[^6_8]: https://github.com/josephschmitt/opencode-acp

[^6_9]: https://opencode.ai/docs/tools/

[^6_10]: https://computingforgeeks.com/opencode-cli-cheat-sheet/

[^6_11]: https://xplorer.space/docs/extensions/getting-started

[^6_12]: https://marketplace.looker.com/marketplace/detail/extension-api-explorer

[^6_13]: https://www.reddit.com/r/selfhosted/comments/1v4fpsn/impersonator_copied_my_agpl_v3_open_source/

[^6_14]: https://xplorer.space/docs

[^6_15]: https://docs.cloud.google.com/looker/docs/api-explorer

[^6_16]: https://www.ultralytics.com/legal/agpl-3-0-software-license

[^6_17]: https://xplorer.space/

[^6_18]: https://developers.google.com/apis-explorer

[^6_19]: https://github.com/kimlimjustin/xplorer/releases?ref=news.itsfoss.com

[^6_20]: https://robertsspaceindustries.com/community-hub/post/star-citizen-hangar-extension-xplor-and-bulk-ZZ549naBoAOgU

[^6_21]: https://code.visualstudio.com/api/references/vscode-api

[^6_22]: https://rockxy.io/license

[^6_23]: https://addons.mozilla.org/en-US/firefox/addon/star-citizen-hangar-xplorer/

[^6_24]: https://stackoverflow.com/questions/73637194/can-i-automate-downloading-of-visual-studio-code-extensions-to-a-private-marketp

[^6_25]: https://ospo.cc.gatech.edu/releasing-open-source/

[^6_26]: https://xplorer.space/docs/intro

[^6_27]: https://docs.cloud.google.com/looker/docs/intro-to-extension-framework

[^6_28]: https://docs.spectrocloud.com/architecture/architecture-overview/

[^6_29]: https://www.xplorer.space/docs/api/tauri-commands

[^6_30]: https://xplorer.space/docs/Extensions/create/

[^6_31]: https://ntrs.nasa.gov/citations/20140017423

[^6_32]: https://v2.tauri.app/reference/javascript/api/

[^6_33]: https://xplorer.space/docs/getting-started

[^6_34]: https://ieeexplore.ieee.org/document/10715720

[^6_35]: https://v2.tauri.app/reference/config/

[^6_36]: https://code.visualstudio.com/api/references/commands

[^6_37]: https://nss.org/nasa-s-exploration-systems-architecture-study/

[^6_38]: https://docs.rs/tauri

[^6_39]: https://marketplace.visualstudio.com/items?itemName=DaoVietCuong.solution-explorer

[^6_40]: https://opencode.ai/docs/sdk/

[^6_41]: https://github.com/anthropics/claude-agent-sdk-typescript

[^6_42]: https://opencode.ai/v2/docs/api/

[^6_43]: https://opencode.ai/docs/server/

[^6_44]: https://hidekazu-konishi.com/entry/claude_agent_sdk_complete_guide.html

[^6_45]: https://opencode.ai/docs/web/

[^6_46]: https://opencode.ai/

[^6_47]: https://langfuse.com/integrations/frameworks/claude-agent-sdk-js

[^6_48]: https://www.reddit.com/r/opencodeCLI/comments/1rj61qn/does_anyone_use_opencode_server/

[^6_49]: https://www.reddit.com/r/ClaudeAI/comments/1psuktn/agent_sdk_vs_headless_claude_code/

[^6_50]: https://team400.ai/blog/2026-04-claude-agent-sdk-typescript-building-production-agents

[^6_51]: https://anomalyco-opencode.mintlify.app/share

[^6_52]: https://opencode.ai/docs/cli/

[^6_53]: https://www.aiagentshub.net/blog/claude-agent-sdk-guide

[^6_54]: https://github.com/anomalyco/opencode/issues/5256

[^6_55]: https://opencode.ai/docs/plugins/

[^6_56]: https://opencode.ai/docs/permissions/

[^6_57]: https://github.com/joelhooks/opencode-config

[^6_58]: https://opencode.ai/docs/custom-tools/

[^6_59]: https://open-code.ai/en/docs/permissions

[^6_60]: https://opencode.ai/v2/docs/agents/

[^6_61]: https://gist.github.com/rstacruz/946d02757525c9a0f49b25e316fbe715

[^6_62]: https://opencode.school/lessons/permissions/

[^6_63]: https://opencode.ai/docs/commands/

[^6_64]: https://opencode.ai/v2/docs/permissions/

[^6_65]: https://opencode.ai/docs/rules/

[^6_66]: https://opencode.ai/docs/config/

[^6_67]: https://opencode.ai/docs/agents/

[^6_68]: https://www.reddit.com/r/opencodeCLI/comments/1qssabi/the_definitive_guide_to_opencode_from_first/

[^6_69]: https://stackoverflow.com/questions/2614511/can-open-source-code-hosted-at-github-be-closed-source

[^6_70]: https://xplorer.space/pricing

[^6_71]: https://github.com/orgs/community/discussions/19990

[^6_72]: https://xplorer.space/extensions

[^6_73]: https://github.com/microsoft/vscode/issues/119276

[^6_74]: https://softwareengineering.stackexchange.com/questions/86754/is-it-possible-to-rewrite-every-line-of-an-open-source-project-in-a-slightly-dif

[^6_75]: https://news.ycombinator.com/item?id=24549491

[^6_76]: https://www.reddit.com/r/programming/comments/og8gxv/github_support_just_straight_up_confirmed_in_an/

[^6_77]: https://marketplace.visualstudio.com/

[^6_78]: https://code.visualstudio.com/blogs/2021/06/10/remote-repositories

[^6_79]: https://stackoverflow.com/questions/57247646/i-am-unable-to-connect-to-the-extension-marketplace-of-visual-studio-code

[^6_80]: https://github.com/kimlimjustin/xplorer/blob/master/LICENSE

[^6_81]: https://devblogs.microsoft.com/bharry/paid-extension-in-the-visual-studio-marketplace/

[^6_82]: http://github.com/austral-electronics/Xplorer/pulls

[^6_83]: https://v2.tauri.app/learn/sidecar-nodejs/

[^6_84]: https://github.com/orgs/tauri-apps/discussions/8641

[^6_85]: https://v2.tauri.app/develop/sidecar/

[^6_86]: https://v2.tauri.app/plugin/shell/

[^6_87]: https://tauri.app/v1/guides/building/sidecar/

[^6_88]: https://tauri.app/v1/guides/building/sidecar

[^6_89]: https://mclare.blog/posts/writing-a-pandas-sidecar-for-tauri/

[^6_90]: https://tauri.app/v1/api/js/shell

[^6_91]: https://www.reddit.com/r/rust/comments/1lkux0e/tauri_things_to_watch_out_for_using_nodejs_in/

[^6_92]: https://www.reddit.com/r/rust/comments/19458hw/troubles_using_sidecar_in_tauri/

[^6_93]: https://github.com/orgs/tauri-apps/discussions/5206

[^6_94]: https://github.com/tauri-apps/plugins-workspace/issues/3090

[^6_95]: https://jonaskruckenberg.github.io/tauri-docs-wip/examples/sidecar.html

[^6_96]: https://v2.tauri.app/plugin/process/

[^6_97]: https://dev.to/zaid_sunasra/adding-nodejs-server-to-tauri-app-as-a-sidecar-509j

[^6_98]: https://github.com/emanuelef/daily-stars-explorer

[^6_99]: https://www.sitepoint.com/x-plore-dual-pane-file-manager-for-google-android/

[^6_100]: https://github.com/oprogramador/github-star-history

[^6_101]: https://www.lonelycatgames.com/apps/xplore

[^6_102]: https://github.com/kimlimjustin/xplorer

[^6_103]: https://github.com/orgs/community/discussions/13356

[^6_104]: https://www.reddit.com/r/Android/comments/186sz9c/whats_your_favorite_file_manager_for_android/

[^6_105]: https://sourceforge.net/software/product/X-plore-File-Manager/

[^6_106]: https://stackoverflow.com/questions/77062721/tauri-how-to-open-a-new-file-from-the-native-file-explorer

[^6_107]: https://www.gharchive.org/

[^6_108]: https://x-plore-file-manager.updatestar.com/

[^6_109]: https://developer.chrome.com/docs/extensions/reference/api/sidePanel

[^6_110]: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/sidebarAction

[^6_111]: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/devtools/panels/ExtensionSidebarPane

[^6_112]: https://developer.chrome.com/docs/extensions/reference/api

[^6_113]: https://developer.chrome.com/docs/extensions/reference/api/devtools/panels

[^6_114]: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/devtools/panels/ElementsPanel/createSidebarPane

[^6_115]: https://docs.readme.com/main/docs/openapi-extensions

[^6_116]: https://developer.chrome.com/docs/extensions/develop/ui/create-a-side-panel

[^6_117]: https://docs.rws.com/en-US/tridion-sites-10-1-main-documentation-1174622/gui-extensions-for-experience-space-1068407

[^6_118]: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/extension

[^6_119]: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/user_interface/Sidebars

[^6_120]: https://v2.tauri.app/distribute/pipelines/github/

[^6_121]: https://github.com/tauri-apps/awesome-tauri

[^6_122]: https://play.google.com/store/apps/details?id=gov.nasa.jsc.igoal.ISSResearchExplorer\&hl=en_US

[^6_123]: https://v2.tauri.app/develop/configuration-files/

[^6_124]: https://www.reddit.com/r/tauri/comments/1cjutti/tauri_beta_android_how_to_import_tauris_apilooing/

[^6_125]: https://chromewebstore.google.com/detail/nasa-space-explorer-disco/kdbblbiggblcikgldcfcpoaalaalppnm?hl=en

[^6_126]: https://v2.tauri.app/blog/tauri-20/

[^6_127]: https://sourceforge.net/projects/tauri.mirror/files/

[^6_128]: https://zed.dev/acp

[^6_129]: https://tessl.io/blog/zed-debuts-agent-client-protocol-to-connect-ai-coding-agents-to-any-editor

[^6_130]: https://ai-sdk.dev/providers/community-providers/acp

[^6_131]: https://open-code.ai/en/docs/acp

[^6_132]: https://www.reddit.com/r/Jetbrains/comments/1pewvju/bring_your_own_ai_agent_using_agent_client/

[^6_133]: https://forum.sublimetext.com/t/acp-agent-client-protocol/77027

[^6_134]: https://www.jetbrains.com/acp/

[^6_135]: https://www.reddit.com/r/emacs/comments/1ncrpgv/experimenting_with_acp_agent_client_protocol/

[^6_136]: https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-notes

[^6_137]: https://github.com/anomalyco/opencode/issues/19572

[^6_138]: https://stackoverflow.com/questions/79812685/all-files-from-a-forked-github-repo-are-locked-blue-padlock-in-vs2022

[^6_139]: https://www.reddit.com/r/opencodeCLI/comments/1qs52vd/i_find_it_annoying_that_there_is_not_a_menu_for/

[^6_140]: https://github.com/karatelabs/xplorer/releases

[^6_141]: https://www.reddit.com/r/LegionGo/comments/1duyw4a/legion_space_1029/

[^6_142]: https://www.reddit.com/r/LocalLLaMA/comments/1u8uf75/new_ollama_model_file_editor_beta_looking_for/

[^6_143]: https://play.google.com/store/apps/details?id=com.lonelycatgames.Xplore\&hl=en_US

[^6_144]: https://developers.openai.com/plugins/build/plugins

[^6_145]: https://www.morphllm.com/best-ollama-models

[^6_146]: https://developers.archilogic.com/extension-sdk/guide

[^6_147]: https://testerstories.com/2026/01/ai-and-testing-ollama-and-models/

[^6_148]: https://www.rudderstack.com/docs/sources/event-streams/sdks/client-side-features/plugin-architecture/create-custom-plugin/

[^6_149]: https://xsoar.pan.dev/docs/reference/integrations/ollama

[^6_150]: https://www.sidetool.co/post/building-custom-plugins-for-replit-agents-extend-your-coding-assistant-s-power/

[^6_151]: https://localaimaster.com/blog/best-ollama-models

[^6_152]: https://docs.openclaw.ai/plugins/building-plugins

[^6_153]: https://v2.tauri.app/concept/architecture/

[^6_154]: https://v2.tauri.app/develop/calling-rust/

[^6_155]: https://play.google.com/store/apps/details?id=gov.nasa.jsc.igoal.ISSResearchExplorer\&hl=en

[^6_156]: https://github.com/pythoninthegrasses/mt/blob/main/docs/tauri-architecture.md

[^6_157]: https://developer.android.com/guide/sdk-extensions

[^6_158]: https://v2.tauri.app/start/project-structure/

[^6_159]: https://developer.chrome.com/docs/extensions


---

# OK well, the agents are going to be doing all of this work anyways. So I need you to compile this into a build guide. And scaffold with all the gotchas to dos. The All the things to watch out for. And instructions. Targeted for Claude.

The build kit is packaged. Twelve documents plus Rust/TypeScript scaffolding, all written as instructions *to Claude* rather than as prose for you to translate.

## What the agents get

**`CLAUDE.md`** — drop-in operating rules. Seven absolute constraints (never bypass `agent::security`, never hard-delete, no `invoke()` in components, never scrape a PTY, don't build it as a sandboxed extension, preview-then-commit, absolute paths only), the verification loop, and a where-code-goes table.[^7_1][^7_2]

**`docs/06-PROMPTS.md`** — eleven copy-paste task prompts, one per phase, each naming the specific gotcha IDs that apply so Claude reads the relevant warnings before writing code rather than after.

**`docs/04-GOTCHAS.md`** — the centerpiece, 40 traps ranked S/A/B by damage. The severity-S ones are genuinely load-bearing:

- `canonicalize` fails on paths that don't exist yet, and a move destination never exists yet — so you need lexical-first, then canonicalize the existing prefix, or Windows junctions inside an allowed root defeat validation entirely.[^7_3]
- `session/request_permission` is a *blocking* JSON-RPC request. Panel closed = agent hangs forever holding a turn open. Timeout must resolve to rejection.[^7_4]
- `session/cancel` is not a hard stop — the spec says keep accepting `tool_call` updates after cancelling, and you still owe an outstanding permission request a `cancelled` outcome.[^7_5][^7_4]
- `allow_always` scoped by tool name alone becomes a lifetime license to move anything anywhere.

**Two findings worth your attention that the earlier research didn't surface:**

- **A-13 / the inversion.** opencode enables *all* tools with *no* permission required by default. Without denying `read`/`write`/`edit`/`multiedit`/`bash`/`patch`, the agent bypasses every guard you write and edits disk directly. The shipped `opencode.json` does this, routing everything through Xplorer's MCP verbs instead.[^7_6][^7_7]
- **B-16 / metadata orphaning.** Xplorer keys tags, notes, and custom metadata by *path* — and this copilot's entire purpose is moving files. Every unintercepted agent move silently destroys user metadata while "organizing." Phase 8 requires re-keying inside the same transaction, with a `fixture/tagged/` test that proves it.


## Structural notes

`docs/02-ACP-REFERENCE.md` condenses the live spec — every method, every enum, capability defaults, and the fact that `loadSession` sits at the top level of `agentCapabilities` rather than inside `sessionCapabilities` (the spec flags its own inconsistency there).[^7_8][^7_4][^7_5]

Phase 0 is a hard gate: build on Windows, prove the existing `--mcp-server` responds to `tools/list`, and record both agents' capability objects verbatim — because omitted means unsupported, and Claude and opencode advertise different sets.[^7_8]

Phase 1 also builds a **fake agent** harness that advertises zero capabilities, dies mid-turn, hangs on permission requests, and emits updates after cancel. Reproducing those failure modes against real Claude is expensive; scripting them is not.

<div align="center">⁂</div>

[^7_1]: https://github.com/spacedriveapp/spacedrive

[^7_2]: https://pkg.go.dev/github.com/hacdias/filemanager

[^7_3]: https://www.shuttle.dev/blog/2025/09/15/mcp-servers-rust-comparison

[^7_4]: https://dev.to/kimlimjustin/i-put-vs-code-claude-and-a-terminal-inside-a-file-manager-i-built-using-react-and-rust-heres-k1n

[^7_5]: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

[^7_6]: https://github.com/tfeldmann/organize

[^7_7]: https://filearbor.com/blog/best-automatic-file-organizers-windows-mac

[^7_8]: https://www.xda-developers.com/my-file-management-was-chaos-before-i-discovered-this-apps-dual-pane-interface/


---

# So the recommended route is explore and not. Spaceship.

Yes — **Xplorer**, not Spacedrive, is the recommended route, despite Spacedrive's architecture being conceptually the better fit.

## Why the recommendation flipped

Licensing was the deciding factor in the original comparison, and you said it doesn't matter for a personal tool — so on pure fit, Spacedrive's content-addressed (BLAKE3), daemon-based, preview-then-commit architecture would still be the more elegant foundation. But once licensing is off the table, three practical issues still favor Xplorer:

- Spacedrive v2 is genuinely alpha — Windows support only landed in alpha.2, and you're on Windows in Burton, Michigan, so you'd be debugging the platform itself before writing any copilot code.
- Xplorer already ships the things this build needs as day-one primitives: Tauri 2 + Rust + React, a working MCP server with real tools (`read_file`, `write_file`, `list_directory`, `search_files`, `run_command`, `get_git_status`), dual-pane support, an agent module with security guards, trash-based deletion, undo/redo, and file versioning — all discoverable and verified in the actual repo.
- The build guide I just produced is written against Xplorer's real file layout, its actual `CLAUDE.md` conventions, and its existing `agent/security.rs` — none of that groundwork transfers if you pivot back to Spacedrive.


## Where "spaceship" was right

Spacedrive's daemon-first model and content-identity-over-path design are the more forward-looking approach for this problem — proactive background scanning, classification surviving arbitrary moves, and extensions explicitly designed for "AI agents with unlimited memory" are things Xplorer doesn't have natively. If Xplorer's copilot build later feels architecturally constrained — especially the path-keyed metadata problem (moving a file orphans its tags/notes unless you intercept every move, which the build guide flags as the single highest-value bug to fix) — that's the moment revisiting Spacedrive makes sense, once it's out of alpha on Windows.

For now, Xplorer is the pragmatic starting point; the build kit already accounts for hardening it toward Spacedrive-like guarantees (content hashing via `compute_file_hash`, transaction-safe metadata re-keying, audit logging) without waiting on someone else's alpha software.

---

# What skill did you use? When creating this development plan with this build kit.

I used the **website-building** skill for the first response (the file-manager copilot concept), then switched to **research** and **research-report** for the deep dive comparisons, and for the actual build kit and scaffold I used **research** combined with direct code-generation tools (`bash`, `execute_code`, `get_url_content`) to produce the markdown docs and Rust/TypeScript stub files — no `xlsx`, `slides`, or `website-building` skill was involved in that last deliverable since the output was a documentation/scaffold bundle, not a live app or site.

---

# Can you create a skill or? Rather a plug in package. For Claude, that gets me that same fucking output when I ask him to create a plan for an application and give me a handoff. Include resources, tools and not necessarily. Just don't. He's kind of dumb sometimes, so don't restrict it to just websites, applications in general. And if it's going to have a front and a back end, maybe just a split, tell it to split those.

This is a full Claude Code skill bundle — one orchestrator skill plus five independently-usable sub-skills, not a single monolithic prompt.

## Structure

- **`app-planning-handoff`** (orchestrator) — triggers on "plan out," "build guide," "handoff," "development plan," etc. and runs the pipeline below in order.
- **`app-research-stack`** — forces real web research on current library versions, breaking changes, and licensing instead of guessing from memory. Includes a classification guide so Claude asks "web app vs. CLI vs. mobile vs. service vs. game" before defaulting to "website."
- **`app-frontend-backend-split`** — the piece you specifically asked for. It has an explicit decision tree for *when* to split (persistent backend + a client tier = split; static site or backend-only = don't), and forces a concrete contract (API schema, event catalog, or IPC surface) to be defined before the two workstreams are separated.
- **`app-gotcha-audit`** — produces S/A/B-ranked traps, with a "quality bar" reference file containing bad-vs-good examples so Claude can't get away with "write tests" as a gotcha.
- **`app-phase-planning`** — numbered phases with hard, checkable exit criteria plus copy-paste task prompts per phase, with an exit-criteria checklist to stop vague phases before they happen.
- **`app-scaffold-generator`** — real stub file trees matching actual ecosystem conventions (Next.js App Router vs. Tauri vs. Flutter vs. Go, etc.), plus a `CLAUDE.md` generator, with a branch for existing codebases so it audits instead of overwriting.

Each sub-skill ships its own `templates/` (fill-in-the-blank output files) and `reference/` (decision guides, quality checklists) — so they're not just instructions, they're self-contained with the scaffolding Claude needs to produce consistent output every time, and each one works standalone if you only want one piece (e.g., "what stack should I use for X").

Install with `./install.sh --global` for all projects or `--project <path>` for one repo; Claude Code auto-discovers `.claude/skills/`.

