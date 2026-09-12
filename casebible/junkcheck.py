import duckdb, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = "E:/AI_Workspace/casebible/junk_scrub_report.csv"
c = duckdb.connect()
SRC = "read_csv('%s', ignore_errors=true, all_varchar=true)" % P

cols = [r[0] for r in c.sql("describe select * from " + SRC).fetchall()]
n = c.sql("select count(*) from " + SRC).fetchone()[0]
print("=== junk_scrub_report.csv ===")
print("rows: %s" % format(n, ","))
print("cols: %s" % ", ".join(cols))
print()

print("=== sample ===")
for r in c.sql("select * from " + SRC + " limit 4").fetchall():
    print("  " + str(r)[:200])
print()

# find the path-ish column
pathcol = None
for cand in ("path", "file", "relpath", "src", "name", "key"):
    for col in cols:
        if cand in col.lower():
            pathcol = col
            break
    if pathcol:
        break
print("path column detected: %s" % pathcol)
print()

if pathcol:
    q = ("select * from %s where lower(\"%s\") like '%%temp%%' "
         "or lower(\"%s\") like '%%tmp%%'" % (SRC, pathcol, pathcol))
    hits = c.sql(q).fetchall()
    print("=== rows matching temp/tmp: %d ===" % len(hits))
    for h in hits[:40]:
        print("  " + str(h)[:200])
    print()
    print("=== distinct top-level folders in those hits ===")
    q2 = ("select regexp_extract(\"%s\", '^([^/\\\\\\\\]+)', 1) as root, count(*) n "
          "from %s where lower(\"%s\") like '%%temp%%' or lower(\"%s\") like '%%tmp%%' "
          "group by 1 order by n desc limit 20" % (pathcol, SRC, pathcol, pathcol))
    for r in c.sql(q2).fetchall():
        print("  %-40s %s" % (r[0], r[1]))

# also check junk4 in the duckdb
print()
print("=== junk4 (casebible.duckdb) temp/tmp rows ===")
d = duckdb.connect("E:/AI_Workspace/casebible/casebible.duckdb", read_only=True)
jc = [r[0] for r in d.sql("describe select * from junk4").fetchall()]
print("junk4 cols: %s" % ", ".join(jc))
try:
    rows = d.sql("select * from junk4 where lower(path) like '%temp%' "
                 "or lower(path) like '%tmp%' limit 40").fetchall()
    print("matching rows: %d" % len(rows))
    for r in rows[:25]:
        print("  " + str(r)[:200])
except Exception as e:
    print("ERR:", str(e)[:200])
d.close()
