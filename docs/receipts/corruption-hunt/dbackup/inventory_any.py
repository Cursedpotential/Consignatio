# Byline: Claude Code · Opus 5 · 2026-09-13
# Metadata-only walk of D:/Backup: path, size, mtime, Windows attributes. Reads no file content.
import os, stat, collections, time
import sys
root = sys.argv[1]; out = sys.argv[2]
n = total = zero = offline = errors = 0; tops = collections.Counter(); topbytes = collections.Counter(); t0 = time.time()
with open(out, "w", encoding="utf-8") as fh:
    for dp, dns, fns in os.walk(root, onerror=lambda e: None):
        for fn in fns:
            p = os.path.join(dp, fn)
            try:
                st = os.stat(p, follow_symlinks=False)
            except OSError:
                errors += 1; continue
            attrs = getattr(st, "st_file_attributes", 0)
            off = bool(attrs & (0x1000 | 0x400000 | 0x40000))  # OFFLINE | RECALL_ON_DATA_ACCESS | RECALL_ON_OPEN
            n += 1; total += st.st_size; zero += st.st_size == 0; offline += off
            top = os.path.relpath(p, root).replace(chr(92), "/").split("/")[0]
            tops[top] += 1; topbytes[top] += st.st_size
            fh.write(f"{os.path.relpath(p, root)}\t{st.st_size}\t{int(st.st_mtime)}\t{attrs}\n")
print(f"files={n} GB={total/1e9:.1f} zero_byte={zero} cloud_or_offline_attr={offline} stat_errors={errors} secs={time.time()-t0:.0f}")
for k, v in tops.most_common(20): print(f"  {k:<50} files={v:>8} GB={topbytes[k]/1e9:.1f}")
