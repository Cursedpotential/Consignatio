# Byline: Claude Code · Opus 5 · 2026-09-13
# Move 102 zero-filled Drive files by file ID (duplicate top-level "Takeout" folders defeat path lookup).
import datetime as dt, json, subprocess
RC = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"; CONF = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
Q = "E:/AI_Workspace/_receipts/corruption-hunt/quarantine"
rows = [l.rstrip("\n").split("\t") for l in open(f"{Q}/gdrive_moveid_102.tsv", encoding="utf-8")]
ok = fail = 0
with open(f"{Q}/gdrive_moveid_102.receipt.jsonl", "a", encoding="utf-8") as log:
    for i in range(0, len(rows), 10):
        batch = rows[i:i + 10]
        args = []
        for file_id, dest, *_ in batch:
            args += [file_id, "gd_salemnet:" + dest]
        r = subprocess.run([RC, "backend", "moveid", "gd_salemnet:", *args, "--immutable", "--config", CONF, "-v"],
                           capture_output=True, text=True, encoding="utf-8")
        status = "ok" if r.returncode == 0 else "failed"
        ok += len(batch) if r.returncode == 0 else 0
        fail += 0 if r.returncode == 0 else len(batch)
        log.write(json.dumps({"time": dt.datetime.now().astimezone().isoformat(), "batch": i // 10, "status": status,
                              "rc": r.returncode, "items": [{"id": b[0], "dest": b[1], "orig": b[2]} for b in batch],
                              "stderr_tail": r.stderr[-400:]}, ensure_ascii=False) + "\n")
        print(f"batch {i // 10}: rc={r.returncode} items={len(batch)}" + ("" if r.returncode == 0 else f" stderr={r.stderr[-200:]!r}"))
        if r.returncode != 0:
            break
print(f"moved_ok={ok} failed_batch_items={fail} of {len(rows)}")
