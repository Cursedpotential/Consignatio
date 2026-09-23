import hashlib, json, subprocess
rc = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"; conf = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
SRC = "b2:salem-data/consignatio/intake/raw-dedupe/v1/"; DST = "b2:salem-data/consignatio/intake/_quarantine/zero-filled/v1/"
def stat(path):
    r = subprocess.run([rc, "lsjson", "--stat", "--hash", path, "--config", conf, "--b2-encoding", "None"], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0: return None
    o = json.loads(r.stdout)
    return None if (o.get("IsDir") or not o.get("Name") or o.get("Size", -1) < 0) else o
for rel in open("E:/AI_Workspace/_receipts/corruption-hunt/quarantine/b2_move_sample3.txt", encoding="utf-8").read().splitlines():
    d = stat(DST + rel); s = stat(SRC + rel)
    if d:
        sha = (d.get("Hashes") or {}).get("sha1", "")
        zero = hashlib.sha1(bytes(d["Size"])).hexdigest() == sha
        print(f"QUARANTINE present size={d['Size']} sha1_all_zero={zero} | SOURCE present={bool(s)} :: {rel}")
    else:
        print(f"QUARANTINE MISSING | SOURCE present={bool(s)} :: {rel}")
