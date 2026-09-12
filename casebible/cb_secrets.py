"""cb_secrets — the ONE way scripts get credentials: ops.secret_get() on casebible-pg18.

Byline: Claude Code · Fable 5 · 2026-08-27
Bootstrap = libpq service `casebible` (+ pgpass for cb_agent). Master key = the cb_agent password
itself, read from pgpass and handed to the session; nothing else is stored anywhere.

    from cb_secrets import secret, connect
    key = secret("NVIDIA_API_KEY")
    con = connect()          # cb_agent session with cb.master_key already set
"""
import os, pathlib, psycopg

_SVC = os.environ.get("CB_PG_SERVICE", "casebible")
_HOST, _PORT, _DB, _USER = "ovh-files.tilapia-skilift.ts.net", "5434", "casebible", "cb_agent"

def _master():
    p = pathlib.Path(os.environ.get("PGPASSFILE") or (pathlib.Path.home() / "AppData/Roaming/postgresql/pgpass.conf"))
    if not p.exists(): p = pathlib.Path.home() / ".pgpass"
    for line in p.read_text(encoding="utf-8").splitlines():
        parts = line.split(":", 4)
        if len(parts) == 5 and parts[:4] in ([_HOST, _PORT, _DB, _USER], ["*", "*", "*", _USER]): return parts[4]
    raise RuntimeError("no pgpass line for cb_agent — bootstrap missing")

def connect(**kw):
    con = psycopg.connect(service=_SVC, connect_timeout=15, **kw)
    with con.cursor() as c: c.execute("select set_config('cb.master_key', %s, false)", (_master(),))
    return con

_cache = {}
def secret(name):
    if name not in _cache:
        with connect(autocommit=True) as con, con.cursor() as c:
            c.execute("select ops.secret_get(%s)", (name,)); _cache[name] = c.fetchone()[0]
    return _cache[name]

if __name__ == "__main__":
    import sys
    for n in sys.argv[1:] or ["NVIDIA_API_KEY"]: print(n, "len", len(secret(n)))
