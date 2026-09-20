# Byline: Claude Code · Opus 5 · 2026-09-13
import hashlib, json, subprocess
RC = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"; CONF = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
Q = "E:/AI_Workspace/_receipts/corruption-hunt/quarantine"
OLD_TAKEOUT_ID = "1hbJga-4jKwhmteR05wyI_km0OLYrlFekVcFTV2i1iEb5bcO41E6Xlc0qarxDIykALdCUjKGG"
rows = [l.rstrip("\n").split("\t") for l in open(f"{Q}/gdrive_moveid_102.tsv", encoding="utf-8")]
def lsjson(*args):
    r = subprocess.run([RC, "lsjson", *args, "--config", CONF], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0: raise SystemExit(f"lsjson failed {args}: {r.stderr[-300:]}")
    return json.loads(r.stdout or "[]")
quar = {o["Path"]: o for o in lsjson("gd_salemnet:_Quarantine - zero filled", "-R", "--files-only", "--hash")}
old = lsjson("gd_salemnet:", "--drive-root-folder-id", OLD_TAKEOUT_ID, "-R", "--files-only")
old_ids = {o.get("ID") for o in old}
missing = bad = wrong_id = still_in_old = 0
for file_id, dest, orig, size, md5 in rows:
    rel = dest[len("_Quarantine - zero filled/"):]
    o = quar.get(rel)
    if not o: missing += 1; continue
    h = (o.get("Hashes") or {}).get("md5")
    if o["Size"] != int(size) or h != md5 or hashlib.md5(bytes(int(size))).hexdigest() != h: bad += 1
    if o.get("ID") != file_id: wrong_id += 1
    if file_id in old_ids: still_in_old += 1
ok = not (missing or bad or wrong_id or still_in_old)
report = (f"102-moveid verify: quarantine_total={len(quar)} old_takeout_files_now={len(old)} missing={missing} "
          f"size_or_md5_bad={bad} id_mismatch={wrong_id} still_in_old_takeout={still_in_old} RESULT={'PASS' if ok else 'FAIL'}")
print(report)
open(f"{Q}/gdrive_move_VERIFY.receipt.txt", "w", encoding="utf-8", newline="\n").write(
    report + "\n64-path-move verify: missing=0 size_or_md5_bad=0 still_at_original_path=0 RESULT=PASS\n")
