# Byline: Claude Code · Opus 5 · 2026-09-13
# Amended: Claude Code · Opus 5 · 2026-09-13. Normalized roots; repairs rows whose first path character
# was dropped by the first zero_scan.py run on a bare drive root (os.walk("F:") yields "F:case\..." and the
# old prefix trim cut one character too many). A repair is used only when exactly one top-level entry
# matches, and repaired rows pass every safety check below.
"""Move verified all-zero files into a quarantine folder INSIDE the same root (no deletes).

Owner decision 2026-09-13: quarantine every all-zero payload. The quarantine folder stays inside
the scanned root, so Google Drive for Desktop backup roots see a move, not a deletion.

Usage:
  python local_zero_quarantine.py D:/Backup  E:/.../dbackup/D_backup_all_zero.tsv            (dry run)
  python local_zero_quarantine.py F:/        E:/.../dbackup/F_all_zero.tsv --apply

For every row of the scan TSV (path, size, mtime, attrs) it:
  1. resolves the source path; for drive-root scans only, repairs a dropped first character when exactly
     one top-level entry fits, otherwise skips the row
  2. re-stats the file: size must equal the scanned size
  3. re-reads the whole file: every byte must still be zero
  4. refuses if the quarantine target already exists (never overwrite)
  5. with --apply, os.renames() it to <root>/_quarantine_zero_filled/<relative path>
     (same volume, so this is a metadata move; mtime and attributes are preserved)
  6. confirms the target exists with the same size and the original path is gone
Every decision goes to a JSONL receipt. The script stops at the first unverified move.
"""
import argparse
import datetime as dt
import json
import os
import sys

QUARANTINE_DIR = "_quarantine_zero_filled"
CHUNK = 8 * 1024 * 1024


def all_zero(path: str) -> bool:
    with open(path, "rb") as fh:
        while True:
            block = fh.read(CHUNK)
            if not block:
                return True
            if block.count(0) != len(block):
                return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", help="scanned root, e.g. D:/Backup or F:/")
    parser.add_argument("scan_tsv", help="zero_scan.py output TSV for that root")
    parser.add_argument("--apply", action="store_true", help="perform moves (default: dry run)")
    args = parser.parse_args()

    root_arg = args.root.rstrip("/\\")
    root_fs = os.path.normpath(root_arg + os.sep)  # "F:" -> "F:\\", "D:/Backup" -> "D:\\Backup"
    drive_root = len(root_arg) == 2 and root_arg[1] == ":"
    quarantine_root = os.path.join(root_fs, QUARANTINE_DIR)
    top_entries = [n for n in os.listdir(root_fs) if n != QUARANTINE_DIR] if drive_root else []
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    label = root_arg.replace(":", "").replace("/", "_").replace("\\", "_").strip("_") or "root"
    receipt_path = os.path.join(os.path.dirname(os.path.abspath(args.scan_tsv)),
                                f"{stamp}-{label}-local-quarantine-{'APPLY' if args.apply else 'DRYRUN'}.jsonl")

    counts = {"planned": 0, "moved": 0, "would_move": 0, "repaired_truncated_path": 0,
              "skip_already_quarantined": 0, "skip_missing": 0, "skip_ambiguous_repair": 0,
              "skip_size_changed": 0, "skip_not_zero_now": 0, "skip_target_exists": 0}

    def paths_for(rel: str) -> tuple[str, str]:
        parts = [p for p in rel.replace("\\", "/").split("/") if p]
        return os.path.join(root_fs, *parts), os.path.join(quarantine_root, *parts)

    with open(args.scan_tsv, encoding="utf-8") as fh, open(receipt_path, "w", encoding="utf-8", newline="\n") as log:
        header = fh.readline()
        if not header.startswith("path\t"):
            print(f"ABORT: unexpected TSV header: {header!r}", file=sys.stderr)
            return 2

        def record(entry: dict, decision: str, **extra) -> None:
            log.write(json.dumps({**entry, "decision": decision, **extra}, ensure_ascii=False) + "\n")

        for line in fh:
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) < 4:
                continue
            scanned_rel, size = parts[0], int(parts[1])
            counts["planned"] += 1
            if scanned_rel.replace("\\", "/").split("/")[0] == QUARANTINE_DIR:
                counts["skip_already_quarantined"] += 1
                continue

            rel = scanned_rel
            src, dst = paths_for(rel)
            entry = {"time": dt.datetime.now().astimezone().isoformat(), "scanned_rel": scanned_rel, "size": size}
            repaired_from = None
            if not os.path.lexists(src) and drive_root:
                seg = scanned_rel.replace("\\", "/").split("/")[0]
                candidates = [n for n in top_entries if n[1:] == seg]
                if len(candidates) > 1:
                    counts["skip_ambiguous_repair"] += 1
                    record({**entry, "src": src}, "skip_ambiguous_repair", candidates=candidates)
                    continue
                if len(candidates) == 1:
                    repaired_from = scanned_rel
                    rel = candidates[0] + scanned_rel.replace("\\", "/")[len(seg):]
                    src, dst = paths_for(rel)
            entry.update({"rel": rel, "src": src, "dst": dst})
            if repaired_from is not None:
                entry["repaired_from"] = repaired_from

            try:
                st = os.stat(src, follow_symlinks=False)
            except FileNotFoundError:
                counts["skip_missing"] += 1
                record(entry, "skip_missing")
                continue
            if st.st_size != size:
                counts["skip_size_changed"] += 1
                record(entry, "skip_size_changed", size_now=st.st_size)
                continue
            if not all_zero(src):
                counts["skip_not_zero_now"] += 1
                record(entry, "skip_not_zero_now")
                continue
            if os.path.lexists(dst):
                counts["skip_target_exists"] += 1
                record(entry, "skip_target_exists")
                continue
            if repaired_from is not None:
                counts["repaired_truncated_path"] += 1
            if not args.apply:
                counts["would_move"] += 1
                record(entry, "would_move")
                continue
            os.renames(src, dst)
            moved_ok = os.path.exists(dst) and os.stat(dst).st_size == size and not os.path.lexists(src)
            record(entry, "moved" if moved_ok else "move_unverified")
            log.flush()
            if not moved_ok:
                print(f"STOPPED: move not verified for {src}", file=sys.stderr)
                break
            counts["moved"] += 1

    print(json.dumps({"root": root_fs, "mode": "APPLY" if args.apply else "DRY-RUN", **counts, "receipt": receipt_path}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
