import hashlib, json, subprocess
RC = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"; CONF = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
Q = "E:/AI_Workspace/_receipts/corruption-hunt/quarantine"
plan = {l.rstrip("\n").split("\t")[0]: (int(l.split("\t")[2]), l.rstrip("\n").split("\t")[3]) for l in open(f"{Q}/gdrive_move_plan.tsv", encoding="utf-8")}
moved = [l.rstrip("\n") for l in open(f"{Q}/gdrive_move_64_files_from_raw.txt", encoding="utf-8") if l.strip()]
r = subprocess.run([RC, "lsjson", "gd_salemnet:_Quarantine - zero filled", "-R", "--files-only", "--hash", "--config", CONF],
                   capture_output=True, text=True, encoding="utf-8")
dst = {o["Path"]: o for o in json.loads(r.stdout or "[]")}
missing = bad = 0
for p in moved:
    o = dst.get(p); size, md5 = plan[p]
    if not o: missing += 1; continue
    h = (o.get("Hashes") or {}).get("md5")
    if o["Size"] != size or h != md5 or hashlib.md5(bytes(size)).hexdigest() != h: bad += 1
src_left = 0
for p in moved:
    s = subprocess.run([RC, "lsjson", "--stat", "gd_salemnet:" + p, "--config", CONF], capture_output=True, text=True, encoding="utf-8")
    if s.returncode == 0:
        o = json.loads(s.stdout)
        if o.get("Name") and not o.get("IsDir") and o.get("Size", -1) >= 0: src_left += 1
print(f"64-move verify: quarantine_listing_total={len(dst)} missing={missing} size_or_md5_bad={bad} still_at_original_path={src_left} RESULT={'PASS' if not (missing or bad or src_left) else 'FAIL'}")
