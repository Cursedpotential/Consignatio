# Atomic and nested organizational units

> Byline: Codex · 2026-09-10 · Planned contract extension

An atomic unit is a candidate preservation boundary, not necessarily an archive. Detect unpacked Google Takeout trees, Facebook account exports, individual service/message trees, ChatGPT export conversations, iMessage backups, and development repositories. Units may contain other units of the same or a different type.

Repository cases include ordinary `.git` directories, `.git` pointer files used by worktrees/submodules, bare repositories, nested independent repositories, monorepos with several packages and recovered partial trees. A package manifest alone is a package hint, not proof of a Git repository. Do not execute hooks, project code or Git commands from recovered content. Inspect bounded metadata and validate paths before reading a linked Git directory outside the discovered root.

Takeout/Facebook recognition uses combinations of marker files, manifests and structural patterns; a folder name alone cannot prove a complete export. Case variants, numbered folders, missing manifests, flattened paths and partial exports must produce evidence-bearing candidates rather than disappearing from inventory.

## Model

`unit_id`, `source_snapshot_id`, `root_occurrence_id`, `unit_type`, `recognizer_version`, `boundary_evidence`, `confidence`, `completeness`, `review_state` and `preservation_policy` describe a unit. Containment edges express parent/child scope; references and symlink/worktree targets are separate edges. Physical containment must be acyclic. Logical memberships can overlap and must not be mistaken for physical containment.

Every source occurrence retains its deepest matching unit plus all ancestors. Keep ambiguous overlapping candidates until review. A recognized nested repository remains visible inside a recognized Takeout or outer repository. Do not stop discovery at the first marker. Enforce bounded depth and report truncated discovery explicitly.

## Selection, dedup and copy

An outer preserve-whole policy prevents accidental partial copy of its descendants. The UI shows how many hidden descendants are included and why. Human decisions to split a boundary are recorded separately from the recognizer result. Reviewed locks and physical preservation policy are distinct from editable organizational groups.

Hash every selected member once per stable source version, then derive versioned package manifests from normalized relative member paths and compatible full-content hashes. Record missing/unreadable/unhashed members; an incomplete manifest cannot prove whole-package equality. Equal member-content sets with different structures are a separate relationship from exact package equality.

A copy planner computes the closure of selected preservation boundaries, excludes duplicate nested transfer work, validates collisions and materializes one immutable manifest. It retains unit membership, all source occurrences and corroboration even when destination content bytes are reused.

## Implementation checklist

- [ ] Extend existing `backend/src/casebible_index/atomic_units.py` through a versioned recognizer interface.
- [ ] Add unpacked Takeout and Facebook fixtures with varied names, nested services and incomplete exports.
- [ ] Add repository-in-repository, repository-in-export, worktree/submodule pointer and monorepo-package fixtures.
- [ ] Emit containment, logical references, ambiguity and completeness into lake tables and Surreal graph.
- [ ] Expose boundary explanation and ancestor expansion to search, Glide, hierarchy and copy planner.
- [ ] Verify repeated discovery is stable, cycles are rejected, source bytes stay unchanged and nested copies are not scheduled twice.
