# Byline: Claude Code · Opus 5 · 2026-09-13
"""Verify the B2 zero-filled quarantine move end to end (read-only).

Checks, from one fresh listing of each prefix:
  - every planned key is present under _quarantine/zero-filled/v1/
  - every quarantined object's size matches the plan and its SHA-1 is the all-zero hash for that size
  - no planned key remains under raw-dedupe/v1/
Writes a receipt next to this script.
"""
import csv
import datetime as dt
import hashlib
import subprocess

RC = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"
CONF = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
Q = "E:/AI_Workspace/_receipts/corruption-hunt/quarantine"
SRC = "b2:salem-data/consignatio/intake/raw-dedupe/v1"
DST = "b2:salem-data/consignatio/intake/_quarantine/zero-filled/v1"


def listing(root: str) -> dict[str, tuple[int, str]]:
    cmd = [RC, "lsf", root, "-R", "--files-only", "--format", "psh", "--separator", "\t",
           "--hash", "SHA1", "--b2-encoding", "None", "--fast-list", "--config", CONF]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise SystemExit(f"listing failed for {root}: {out.stderr.strip()[:300]}")
    rows = {}
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[1].isdigit():
            rows[parts[0]] = (int(parts[1]), parts[2].lower())
    return rows


def main() -> None:
    plan = {}
    with open(f"{Q}/b2_move_files_from_raw.txt", encoding="utf-8") as fh:
        for rel in fh.read().splitlines():
            plan[rel] = None
    with open(f"{Q}/b2_move_plan.tsv", encoding="utf-8") as fh:
        prefix = "consignatio/intake/raw-dedupe/v1/"
        for line in fh:
            src, _dst, size = line.rstrip("\r\n").split("\t")
            plan[src[len(prefix):]] = int(size)

    dst = listing(DST)
    src = listing(SRC)
    missing, bad_size, not_zero, still_at_source = [], [], [], []
    for rel, size in plan.items():
        got = dst.get(rel)
        if got is None:
            missing.append(rel)
        else:
            if got[0] != size:
                bad_size.append((rel, size, got[0]))
            if hashlib.sha1(bytes(got[0])).hexdigest() != got[1]:
                not_zero.append((rel, got[1]))
        if rel in src:
            still_at_source.append(rel)

    ok = not (missing or bad_size or not_zero or still_at_source)
    lines = [
        f"verified_at={dt.datetime.now().astimezone().isoformat()}",
        f"planned={len(plan)} quarantine_objects_total={len(dst)} source_objects_total={len(src)}",
        f"missing_in_quarantine={len(missing)} size_mismatch={len(bad_size)} sha1_not_all_zero={len(not_zero)} still_at_source={len(still_at_source)}",
        f"RESULT={'PASS' if ok else 'FAIL'}",
    ]
    for label, items in (("missing", missing), ("size_mismatch", bad_size), ("not_zero", not_zero), ("still_at_source", still_at_source)):
        for item in items[:10]:
            lines.append(f"  {label}: {item}")
    report = "\n".join(lines)
    print(report)
    with open(f"{Q}/b2_move_VERIFY.receipt.txt", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(report + "\n")
    with open(f"{Q}/b2_move_VERIFY.detail.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["relpath", "planned_size", "quarantine_size", "quarantine_sha1", "at_source"])
        for rel, size in plan.items():
            got = dst.get(rel, (None, None))
            writer.writerow([rel, size, got[0], got[1], rel in src])


if __name__ == "__main__":
    main()
