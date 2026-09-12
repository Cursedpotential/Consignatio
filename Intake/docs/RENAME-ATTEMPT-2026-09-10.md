# Consignatio / Intake directory rename — blocked and restored

> Byline: Codex · 2026-09-10

Requested destination: `E:\AI_Workspace\Projects\Propria\Consignatio\intake\`.
Current restored location: `E:\AI_Workspace\Projects\Propria\casebible\workbench\`.

Windows denied rename/move access to the project root, the `pilot` directory and the `workbench` directory. Initial PowerShell Move-Item partially transferred contents before reporting failure. All transferred files and directories were restored using non-overwriting filesystem moves. The complete Git metadata was restored to the original project root. Subsequent atomic directory rename attempts also received access denied.

The Consignatio destination does not remain as a split project. Empty intermediate directory shells were preserved under the original project's `to_be_deleted/rename-empty-*` paths; no files were deleted. No ACLs were changed and no processes were terminated. Cause of the access denial remains unconfirmed; a process handle or filesystem permission requires diagnosis.

Verification after restoration: original Git root resolves, no unexpected missing tracked files (excluding pre-existing viz deletions and the previously completed backend move), and the Python backend imports from its original merged workbench/backend path.

Product naming remains Intake and Consignatio. Physical directory renaming is outstanding. Release any active application/terminal/editor handles using these directories before retrying; do not interpret this record as a completed rename.
