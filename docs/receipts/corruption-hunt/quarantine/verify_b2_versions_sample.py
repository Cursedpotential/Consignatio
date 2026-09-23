import json, random, subprocess
RC = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"; CONF = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
Q = "E:/AI_Workspace/_receipts/corruption-hunt/quarantine"
rels = [l.rstrip("\n") for l in open(f"{Q}/b2_move_files_from_raw.txt", encoding="utf-8") if l.strip()]
random.seed(20260913); sample = random.sample(rels, 8)
SRC = "b2:salem-data/consignatio/intake/raw-dedupe/v1/"
kept = 0
for rel in sample:
    folder, name = rel.rsplit("/", 1)
    r = subprocess.run([RC, "lsjson", SRC + folder, "--b2-versions", "--files-only", "--b2-encoding", "None", "--config", CONF],
                       capture_output=True, text=True, encoding="utf-8")
    versions = [o for o in json.loads(r.stdout or "[]") if o["Name"].startswith(name.rsplit(".", 1)[0]) and o["Name"] != name]
    exact_live = [o for o in json.loads(r.stdout or "[]") if o["Name"] == name]
    ok = bool(versions)
    kept += ok
    print(f"{'VERSION KEPT' if ok else 'NO OLD VERSION'} live_at_source={bool(exact_live)} versions={[v['Name'][-40:] for v in versions][:2]} :: {rel[-70:]}")
print(f"sample={len(sample)} hidden_prior_versions_present={kept}")
