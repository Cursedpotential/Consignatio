# Byline: Claude Code · Opus 5 · 2026-09-18
# Write one query over timeline_build.duckdb to stdout as fully quoted CSV (bodies contain CR/LF).
import sys

import duckdb

con = duckdb.connect("/work/timeline_build.duckdb", read_only=True)
con.execute("copy (" + sys.argv[1] + ") to '/dev/stdout' (format csv, header, force_quote *)")
