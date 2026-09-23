# Byline: Claude Code · Opus 5 · 2026-09-13
# Listing-only inventory of b2:salem-data for placeholder-corruption triage. Reads no object bytes.
import collections, datetime as dt, json, subprocess
rc = "C:/Users/matts/scoop/apps/rclone/current/rclone.exe"
conf = "C:/Users/matts/scoop/apps/rclone/current/rclone.conf"
out_dir = "E:/AI_Workspace/_receipts/corruption-hunt"
stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
listing = f"{out_dir}/{stamp}-b2-salem-data-listing.tsv"
cmd = [rc, "lsf", "b2:salem-data", "-R", "--files-only", "--format", "psth", "--separator", "\t",
       "--hash", "SHA1", "--config", conf, "--b2-encoding", "None", "--fast-list"]
with open(listing, "w", encoding="utf-8") as fh:
    proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE, text=True, encoding="utf-8")
print("rclone rc", proc.returncode, proc.stderr.strip()[:300])
count = total = zero = 0
by_ext = collections.Counter(); ext_bytes = collections.Counter(); top = collections.Counter()
buckets = collections.Counter(); small_office = 0; no_hash = 0
office = {".docx", ".xlsx", ".pptx", ".doc", ".xls", ".ppt", ".pdf", ".zip"}
with open(listing, encoding="utf-8") as fh:
    for line in fh:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4: continue
        path, size, _mod, sha1 = parts[0], int(parts[1] or 0), parts[2], parts[3]
        count += 1; total += size
        name = path.rsplit("/", 1)[-1]
        ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else "(none)"
        by_ext[ext] += 1; ext_bytes[ext] += size
        top["/".join(path.split("/")[:2])] += 1
        if size == 0: zero += 1
        if ext in office and 0 < size < 1024: small_office += 1
        if not sha1: no_hash += 1
        if size < 1024: buckets["<1KB"] += 1
        elif size < 1 << 20: buckets["1KB-1MB"] += 1
        elif size < 1 << 30: buckets["1MB-1GB"] += 1
        else: buckets[">=1GB"] += 1
print(f"objects={count} total={total/1e9:.2f} GB zero_byte={zero} office_like_under_1KB={small_office} missing_sha1={no_hash}")
print("size buckets", dict(buckets))
print("top-level prefixes", top.most_common(15))
print("extensions by count", by_ext.most_common(20))
print("listing file", listing)
