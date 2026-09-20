# Byline: Claude Code · Opus 5 · 2026-09-13
# Read-only local scan: stat every file; if its first 4 KiB are all zero, read it fully to confirm
# an all-zero payload. Records Windows attributes (sparse 0x200, offline 0x1000, recall 0x400000/0x40000).
# Amended 2026-09-13 (Claude Code · Opus 5): normalize the root. A bare drive root "F:" made os.walk yield
# "F:case\..." with no separator, and the old trim `p[len(root) + 1:]` dropped the first path character.
import os, sys, time, collections
root = os.path.normpath(sys.argv[1].rstrip("/\\") + os.sep); out = sys.argv[2]  # "F:" -> "F:\\"
n = total = zero_files = zero_bytes = zero_len0 = errors = 0
by_top = collections.Counter(); attr_mix = collections.Counter(); t0 = time.time()
with open(out, "w", encoding="utf-8") as fh:
    fh.write("path\tsize\tmtime\tattrs\n")
    for dp, dns, fns in os.walk(root, onerror=lambda e: None):
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = p[prefix_len:].replace(chr(92), "/")
            try:
                st = os.stat(p, follow_symlinks=False)
            except OSError:
                errors += 1; continue
            n += 1; total += st.st_size
            if st.st_size == 0:
                zero_len0 += 1; continue
            try:
                with open(p, "rb") as f:
                    head = f.read(4096)
                    if head.count(0) != len(head):
                        continue
                    allzero = True
                    while True:
                        blk = f.read(8 * 1024 * 1024)
                        if not blk: break
                        if blk.count(0) != len(blk):
                            allzero = False; break
            except OSError:
                errors += 1; continue
            if allzero:
                attrs = getattr(st, "st_file_attributes", 0)
                zero_files += 1; zero_bytes += st.st_size
                by_top[rel.split("/")[0]] += 1
                attr_mix[("sparse" if attrs & 0x200 else "") + ("|offline" if attrs & 0x1000 else "") + ("|recall" if attrs & 0x440000 else "") or "plain"] += 1
                fh.write(f"{rel}\t{st.st_size}\t{int(st.st_mtime)}\t{attrs}\n")
print(f"root={root} files={n} GB={total/1e9:.1f} zero_length_files={zero_len0} ALL_ZERO_PAYLOAD_FILES={zero_files} zero_GB={zero_bytes/1e9:.2f} errors={errors} secs={time.time()-t0:.0f}")
print("all-zero by attribute:", dict(attr_mix))
print("all-zero by top folder:", by_top.most_common(25))
