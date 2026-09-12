# LOCKS — resource claims & freeze windows (append-only)
> Claim: `[YYYY-MM-DD HH:MM] AGENT: LOCK <resource> — <reason/until>`. Release: `... RELEASE <resource>`.
> Don't act on a resource another agent holds. Newest at the bottom.

# Example — SORT freezing the sorted vault so PROCESS can read a consistent snapshot:
#   [2026-06-25 12:00] SORT: LOCK casebible-sorted — freeze for PROCESS bulk read, ~30 min
#   [2026-06-25 12:35] SORT: RELEASE casebible-sorted

[2026-06-25 10:24] SORT: FREEZE casebible-sorted — STABLE for PROCESS bulk read. I'm holding (zero writes); the type-first restructure is human-gated and NOT imminent, so the current vault is a consistent snapshot. NOTE: this is the PRE-restructure (domain-based) layout (Evidence/ 3,646 incl. messaging, AI Chats/ 400, Legal/77, etc.). When the human approves the restructure I'll post here FIRST, then do server-side R2 moves (file content/md5 UNCHANGED, only paths change) — so any evidence PROCESS ingests by content-hash now stays valid; only provenance paths would update. Read away; I'll give notice before I touch it.
