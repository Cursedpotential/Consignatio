# Byline: Claude Code · Opus 5 · 2026-09-13
# Local casebible.duckdb catalog quarantine. Usage: python duckdb_catalog_quarantine.py [--commit]  (default: rollback dry run)
import duckdb, sys
COMMIT = "--commit" in sys.argv
DB = "E:/AI_Workspace/Projects/Propria/Consignatio/casebible/casebible.duckdb"
HOLD = "E:/AI_Workspace/_receipts/corruption-hunt/quarantine/r2_zero_hold_rows.csv"
con = duckdb.connect(DB)
q = lambda s: con.execute(s).fetchall()
con.execute("begin transaction")
con.execute(f"create temp table hold_r2 as select column0 as bucket, column1 as path, try_cast(column2 as bigint) as size, column3 as md5 from read_csv('{HOLD}', header=false, all_varchar=true, quote='\"')")
con.execute("create temp table zero_pairs as select distinct md5, size from hold_r2")
print("hold rows", q("select count(*) from hold_r2"))
print("BEFORE md5 not null r2/surv", q("select (select count(*) from r2_files where coalesce(md5,'') <> ''), (select count(*) from final_survivors where coalesce(md5,'') <> '')"))
con.execute("""create table if not exists integrity_hold (catalog varchar, bucket varchar, path varchar, size bigint, hash_kind varchar,
  original_hash varchar, status varchar, reason varchar, detector varchar, detected_at timestamp default current_timestamp)""")
for t in ("r2_files", "final_survivors"):
    cols = {r[0] for r in q(f"select column_name from information_schema.columns where table_name = '{t}'")}
    if "integrity_status" not in cols: con.execute(f"alter table {t} add column integrity_status varchar")
    if "integrity_reason" not in cols: con.execute(f"alter table {t} add column integrity_reason varchar")
con.execute("""insert into integrity_hold (catalog, bucket, path, size, hash_kind, original_hash, status, reason, detector)
  select 'r2_files', r.bucket, r.path, r.size, 'md5', r.md5, 'quarantined', 'all_zero_payload', 'zero-hash-by-size 2026-09-13'
    from r2_files r join hold_r2 h on h.bucket = r.bucket and h.path = r.path and h.size = r.size and h.md5 = r.md5
  union all select 'r2_files', bucket, path, size, 'md5', md5, 'quarantined', 'zero_bytes_no_content', 'zero-hash-by-size 2026-09-13' from r2_files where size = 0
  union all select 'final_survivors', f.bucket, f.path, f.size, 'md5', f.md5, 'excluded_from_migration', 'all_zero_payload', 'zero-hash-by-size 2026-09-13'
    from final_survivors f join zero_pairs z on z.md5 = f.md5 and z.size = f.size
  union all select 'final_survivors', bucket, path, size, 'md5', md5, 'excluded_from_migration', 'zero_bytes_no_content', 'zero-hash-by-size 2026-09-13' from final_survivors where size = 0""")
print("audit rows", q("select catalog, reason, count(*) from integrity_hold group by all order by 1, 2"))
con.execute("""update r2_files set md5 = null, integrity_status = 'quarantined', integrity_reason = 'all_zero_payload'
  where (bucket, path, size, md5) in (select bucket, path, size, md5 from hold_r2)""")
con.execute("update r2_files set md5 = null, integrity_status = 'quarantined', integrity_reason = 'zero_bytes_no_content' where size = 0")
con.execute("""update final_survivors set md5 = null, integrity_status = 'excluded_from_migration', integrity_reason = 'all_zero_payload'
  where (md5, size) in (select md5, size from zero_pairs)""")
con.execute("update final_survivors set md5 = null, integrity_status = 'excluded_from_migration', integrity_reason = 'zero_bytes_no_content' where size = 0")
print("AFTER flagged r2 / still hashed", q("select count(*), count(*) filter (where md5 is not null) from r2_files where integrity_status is not null"))
print("AFTER flagged surv / still hashed", q("select count(*), count(*) filter (where md5 is not null) from final_survivors where integrity_status is not null"))
print("AFTER md5 not null r2/surv", q("select (select count(*) from r2_files where coalesce(md5,'') <> ''), (select count(*) from final_survivors where coalesce(md5,'') <> '')"))
print("zero payload still matchable (must be 0)", q("select count(*) from r2_files r join zero_pairs z on z.md5 = r.md5 and z.size = r.size"))
if COMMIT:
    con.execute("commit"); print("COMMITTED")
else:
    con.execute("rollback"); print("ROLLED BACK (dry run)")
