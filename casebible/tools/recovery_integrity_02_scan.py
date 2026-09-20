#!/usr/bin/env python3
"""recovery_integrity_02_scan.py

Byline: Claude Code (Sonnet 5, general-purpose agent) dispatched by
Claude Code · Fable 5.1 -- 2026-09-16.

Integrity scan for the PhotoRec recovery-dump scope built by
recovery_integrity_01_scope.sql (raw_duck.recovery_dump_files_20260916).

For every row: fetch bytes from B2 (READ ONLY -- `rclone cat` to a scratch
file, deleted immediately after check), run a content-appropriate integrity
check, and write ONE result row into raw_duck.recovery_integrity_20260916.

This script never writes, moves, or deletes anything on B2. It only writes
to a scratch directory on this host and to the Postgres catalog.

Postgres access goes through `docker exec -i cd840572ae7b psql` (SQL piped
over stdin, no shell interpolation) rather than a direct TCP connection --
the only credential found on this host for a TCP route (/home/ubuntu/.pgpass,
user cb_agent, port 5434 via a tailscaled Service) targets a DIFFERENT
casebible Postgres route than the container this task named, and using it
would risk writing into the wrong instance. docker exec into the named
container is the authoritative, unambiguous path.

Resumable: on start it loads the set of keys already present in the results
table and skips them, so a killed/restarted run picks up where it left off.
Results are flushed in small batches (not on every single file) to keep the
number of docker exec calls bounded; a crash can lose at most one batch's
worth of already-computed (but unflushed) results, which will simply be
re-scanned on the next resume.

Run detached on the VPS, e.g.:
    cd /opt/casebible && nohup python3 /opt/casebible/tools/recovery_integrity_02_scan.py \
        > /opt/casebible/logs/recovery_integrity_scan.log 2>&1 < /dev/null &

Env:
    RCLONE_B2_ENV_FILE   path to the KEY=VALUE env file with RCLONE_CONFIG_B2_*
                         credentials (default: /data/consignatio/secrets/rclone-b2-intake.env)
    SCAN_WORKERS         worker thread count (default 6)
    SCAN_BUCKET          B2 bucket name (default salem-data)
    SCAN_PG_CONTAINER    docker container name/id running Postgres (default cd840572ae7b)
    SCAN_BATCH_SIZE      max results per flushed batch (default 25)
    SCAN_BATCH_SECONDS   max seconds a batch waits before flushing (default 10)
"""
from __future__ import annotations

import bz2
import gzip
import json
import os
import queue
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import threading
import time
import traceback
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None

TOOL_NAME = "recovery_integrity_02_scan.py"
# 1.2.0 (Claude Code · Opus 5 · 2026-09-17 00:20 EDT): content sniffing. PhotoRec's extension is a
# guess: 3,257 of the first 5,197 "fail" rows were zstd payloads (magic 28 B5 2F FD) named .gz and
# rejected by the gzip reader, plus JSON/text named .gz. The real format is now detected from the
# first bytes, checked with that format's decoder (zstd -t, lzma, ...), and recorded in detected_type.
# Text checks no longer pass binary content (latin-1 decodes any byte, so every .txt was "ok").
# SCAN_RECHECK=1 re-scans rows whose status is 'fail' or whose dest_type is a text type.
TOOL_VERSION = "1.2.0"
RECHECK = os.environ.get("SCAN_RECHECK", "0") == "1"
ZSTD = shutil.which("zstd")

PG_CONTAINER = os.environ.get("SCAN_PG_CONTAINER", "cd840572ae7b")
PG_USER = os.environ.get("SCAN_PG_USER", "postgres")
PG_DB = os.environ.get("SCAN_PG_DB", "casebible")

BUCKET = os.environ.get("SCAN_BUCKET", "salem-data")
ENV_FILE = os.environ.get(
    "RCLONE_B2_ENV_FILE", "/data/consignatio/secrets/rclone-b2-intake.env"
)
SCRATCH_DIR = os.environ.get(
    "SCAN_SCRATCH_DIR", "/opt/casebible/scratch/recovery-integrity"
)
WORKERS = int(os.environ.get("SCAN_WORKERS", "6"))
BATCH_SIZE = int(os.environ.get("SCAN_BATCH_SIZE", "25"))
BATCH_SECONDS = float(os.environ.get("SCAN_BATCH_SECONDS", "10"))
PROGRESS_EVERY = 500

IMAGE_TYPES = {
    "JPEG Images", "PNG Images", "GIF Images", "WebP Images",
    "SVG graphics", "High Efficiency Image (heic)",
    "Tagged Image Format (tiff)", "Bitmap Images (bmp)",
}
PDF_TYPES = {"PDF Documents"}
ARCHIVE_ZIP = {"ZIP archives"}
ARCHIVE_GZ = {"GZIP Archives (gz)"}
ARCHIVE_BZ2 = {"BZIP2 Archives (bz2)"}
ARCHIVE_TAR = {"TAR Archives"}
AV_TYPES = {
    "Movie Files (mp4)", "Movie Files (mov)", "Matroska Video Files (MKV)",
    "3GP Video Files", "MP3 Audio", "Ogg files", "WAV Audio", "M4A Audio",
    "AMR Audio",
}
SQLITE_TYPES = {"SQLite databases"}
TEXT_TYPES = {
    "Text Documents (txt)", "HTML Files", "XML Documents", "JSON Files",
    "CSV", "Markdown Documents (md)",
}

FFPROBE = shutil.which("ffprobe")


def load_env_file(path):
    env = {}
    with open(path, "r") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


B2_ENV = os.environ.copy()
B2_ENV.update(load_env_file(ENV_FILE))


# ---------------------------------------------------------------------
# Postgres access via `docker exec -i <container> psql` (stdin-piped SQL,
# no shell interpolation of any value).
# ---------------------------------------------------------------------

def psql_run(sql: str, timeout: int = 120) -> str:
    proc = subprocess.run(
        ["docker", "exec", "-i", PG_CONTAINER, "psql", "-U", PG_USER, "-d", PG_DB,
         "-v", "ON_ERROR_STOP=1", "-A", "-t", "-F", "\t"],
        input=sql.encode("utf-8"),
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"psql failed (rc={proc.returncode}): {proc.stderr.decode('utf-8', 'replace')[:2000]}"
        )
    return proc.stdout.decode("utf-8", "replace")


def sql_quote(value) -> str:
    """Return a safe SQL literal for value (string/int/float/bool/None)."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return repr(value)
    s = str(value).replace("'", "''")
    return f"'{s}'"


def ensure_results_table():
    psql_run(
        """
        CREATE TABLE IF NOT EXISTS raw_duck.recovery_integrity_20260916 (
            key TEXT PRIMARY KEY,
            size BIGINT,
            sha1 TEXT,
            dest_type TEXT,
            status TEXT,
            reason TEXT,
            width INTEGER,
            height INTEGER,
            has_exif BOOLEAN,
            pages INTEGER,
            duration_s DOUBLE PRECISION,
            tool TEXT,
            tool_version TEXT,
            checked_at TIMESTAMPTZ DEFAULT now()
        );
        """
    )


def ensure_detected_type_column():
    psql_run("ALTER TABLE raw_duck.recovery_integrity_20260916 ADD COLUMN IF NOT EXISTS detected_type TEXT;")


def load_done_keys() -> set:
    if RECHECK:
        # keys that are done AND trustworthy: everything except fails and text-type rows
        types = ", ".join(sql_quote(t) for t in sorted(TEXT_TYPES))
        out = psql_run(
            "SELECT key FROM raw_duck.recovery_integrity_20260916 "
            f"WHERE status <> 'fail' AND dest_type NOT IN ({types});"
        )
    else:
        out = psql_run("SELECT key FROM raw_duck.recovery_integrity_20260916;")
    return {line for line in out.splitlines() if line}


def load_scope() -> list:
    out = psql_run(
        "SELECT key, size, sha1, dest_type FROM raw_duck.recovery_dump_files_20260916 ORDER BY key;",
        timeout=300,
    )
    rows = []
    for line in out.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 4:
            continue
        key, size, sha1, dest_type = parts
        rows.append({
            "key": key,
            "size": int(size) if size else 0,
            "sha1": sha1 if sha1 else None,
            "dest_type": dest_type if dest_type else None,
        })
    return rows


def flush_batch(batch: list):
    if not batch:
        return
    values = []
    for r in batch:
        values.append(
            "(" + ", ".join([
                sql_quote(r["key"]), sql_quote(r["size"]), sql_quote(r["sha1"]),
                sql_quote(r["dest_type"]), sql_quote(r["status"]), sql_quote(r["reason"]),
                sql_quote(r["width"]), sql_quote(r["height"]), sql_quote(r["has_exif"]),
                sql_quote(r["pages"]), sql_quote(r["duration_s"]), sql_quote(r["tool"]),
                sql_quote(r["tool_version"]), sql_quote(r.get("detected_type")),
            ]) + ")"
        )
    # Each `v` is "(key_lit, size_lit, ..., tool_version_lit)"; strip the
    # trailing ")" and append ", now())" for the checked_at column.
    rows_sql = ",\n".join(v[:-1] + ", now())" for v in values)
    sql = (
        "INSERT INTO raw_duck.recovery_integrity_20260916 "
        "(key, size, sha1, dest_type, status, reason, width, height, has_exif, "
        "pages, duration_s, tool, tool_version, detected_type, checked_at) VALUES\n"
        + rows_sql
        + "\nON CONFLICT (key) DO UPDATE SET "
        "status = EXCLUDED.status, reason = EXCLUDED.reason, width = EXCLUDED.width, "
        "detected_type = EXCLUDED.detected_type, "
        "height = EXCLUDED.height, has_exif = EXCLUDED.has_exif, pages = EXCLUDED.pages, "
        "duration_s = EXCLUDED.duration_s, tool = EXCLUDED.tool, "
        "tool_version = EXCLUDED.tool_version, checked_at = now();"
    )
    psql_run(sql, timeout=120)


# ---------------------------------------------------------------------
# Content checks
# ---------------------------------------------------------------------

def is_zero_filled(data: bytes, full_size: int) -> bool:
    if not data:
        return full_size == 0
    if full_size <= 4 * 1024 * 1024:
        return all(b == 0 for b in data)
    head = data[:65536]
    tail = data[-65536:]
    return all(b == 0 for b in head) and all(b == 0 for b in tail)


def fetch_bytes(key: str, scratch_path: str, timeout: int) -> tuple[bool, str]:
    remote = f"b2:{BUCKET}/{key}"
    try:
        with open(scratch_path, "wb") as out:
            proc = subprocess.run(
                ["rclone", "cat", remote],
                env=B2_ENV,
                stdout=out,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
        if proc.returncode != 0:
            return False, proc.stderr.decode("utf-8", "replace")[:300]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "rclone cat timed out"
    except Exception as e:  # noqa: BLE001
        return False, f"fetch exception: {e}"


def check_image(path, full_size):
    if Image is None:
        return "unsupported", "Pillow not available", None, None, None
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
            width, height = im.size
            has_exif = False
            try:
                exif = im.getexif()
                has_exif = bool(exif) and len(exif) > 0
            except Exception:  # noqa: BLE001
                has_exif = False
        with open(path, "rb") as f:
            data = f.read()
        if is_zero_filled(data, full_size):
            return "zero_filled", "all-zero payload", width, height, has_exif
        return "ok", "", width, height, has_exif
    except Exception as e:  # noqa: BLE001
        try:
            with open(path, "rb") as f:
                data = f.read()
            if is_zero_filled(data, full_size):
                return "zero_filled", "all-zero payload", None, None, None
        except Exception:  # noqa: BLE001
            pass
        return "fail", str(e)[:300], None, None, None


def check_pdf(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload", None
    if pypdf is None:
        return "unsupported", "pypdf not available", None
    try:
        reader = pypdf.PdfReader(path)
        pages = len(reader.pages)
        return "ok", "", pages
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300], None


def check_zip(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload"
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad is not None:
                return "fail", f"corrupt member: {bad}"[:300]
        return "ok", ""
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300]


def check_gz(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload"
    # Decompress the FIRST gzip member only. PhotoRec cannot tell where a gzip ends, so carved files
    # often carry the next file's bytes after a complete member; gzip.open() treats those as a second
    # member and raises "Not a gzipped file (b'(\xb5')" on a file whose compressed data is intact.
    import zlib
    try:
        d = zlib.decompressobj(wbits=31)
        fed = 0
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                fed += len(chunk)
                d.decompress(chunk)
                if d.eof:
                    break
        if not d.eof:
            return "fail", "truncated gzip stream (no end-of-stream marker)"
        consumed = fed - len(d.unused_data)
        trailing = full_size - consumed
        if trailing > 0:
            return "ok", f"valid gzip member; {trailing} trailing bytes after it (carving overrun)"
        return "ok", ""
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300]


def check_bz2(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload"
    try:
        with bz2.open(path, "rb") as bz:
            while bz.read(1024 * 1024):
                pass
        return "ok", ""
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300]


def check_tar(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload"
    try:
        with tarfile.open(path) as tf:
            tf.getmembers()
        return "ok", ""
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300]


def check_sqlite(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload"
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        result = cur.fetchone()
        conn.close()
        if result and result[0] == "ok":
            return "ok", ""
        return "fail", str(result)[:300]
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300]


def check_av(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload", None
    if not FFPROBE:
        magic_ok = len(data) > 12 and any([
            data[4:8] == b"ftyp",
            data[0:4] == b"\x1a\x45\xdf\xa3",
            data[0:3] == b"ID3" or data[0:2] == b"\xff\xfb",
            data[0:4] == b"OggS",
            data[0:4] == b"RIFF",
            data[0:6] == b"#!AMR\n",
        ])
        if magic_ok:
            return "ok", "header-magic check only (no ffprobe)", None
        return "fail", "no recognizable container header", None
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type", "-of", "json", path],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            return "fail", proc.stderr.strip()[:300], None
        info = json.loads(proc.stdout or "{}")
        fmt = info.get("format", {})
        duration = fmt.get("duration")
        duration = float(duration) if duration else None
        streams = info.get("streams", [])
        if not streams:
            return "fail", "no streams found by ffprobe", duration
        return "ok", "", duration
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300], None


def check_text(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload"
    if len(data) == 0:
        return "fail", "empty file"
    # latin-1 decodes every byte, so decodability alone proves nothing; reject binary payloads.
    sample = data[:1024 * 1024]
    nul = sample.count(0)
    if nul > max(4, len(sample) // 200):
        return "fail", f"binary content, not text ({nul} NUL bytes in first {len(sample)})"
    ctrl = sum(1 for b in sample if b < 32 and b not in (9, 10, 12, 13))
    if ctrl > len(sample) // 20:
        return "fail", f"binary content, not text ({ctrl} control bytes in first {len(sample)})"
    try:
        data.decode("utf-8")
        return "ok", ""
    except UnicodeDecodeError:
        return "ok", "not utf-8; latin-1/cp1252 text"


def check_zstd(path, full_size):
    with open(path, "rb") as f:
        head = f.read(65536)
    if is_zero_filled(head, min(full_size, 65536)):
        return "zero_filled", "all-zero payload"
    if not ZSTD:
        return "unsupported", "zstd CLI not available"
    try:
        proc = subprocess.run([ZSTD, "-t", "-q", path], capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            return "ok", ""
        return "fail", (proc.stderr.strip() or f"zstd -t rc={proc.returncode}")[:300]
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300]


def check_xz(path, full_size):
    import lzma
    try:
        with lzma.open(path, "rb") as xz:
            while xz.read(1024 * 1024):
                pass
        return "ok", ""
    except Exception as e:  # noqa: BLE001
        return "fail", str(e)[:300]


def sniff(path):
    """Real format from the first bytes; None when no known signature."""
    with open(path, "rb") as f:
        h = f.read(512)
    if h[:2] == b"\x1f\x8b": return "gzip"
    if h[:4] == b"\x28\xb5\x2f\xfd": return "zstd"
    if h[:3] == b"BZh": return "bz2"
    if h[:6] == b"\xfd7zXZ\x00": return "xz"
    if h[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"): return "zip"
    if len(h) >= 262 and h[257:262] == b"ustar": return "tar"
    if h[:8] == b"\x89PNG\r\n\x1a\n": return "image"
    if h[:3] == b"\xff\xd8\xff": return "image"
    if h[:6] in (b"GIF87a", b"GIF89a"): return "image"
    if h[:4] == b"RIFF" and h[8:12] == b"WEBP": return "image"
    if h[:2] in (b"II", b"MM") and h[2:4] in (b"*\x00", b"\x00*"): return "image"
    if h[:5] == b"%PDF-": return "pdf"
    if h[:16] == b"SQLite format 3\x00": return "sqlite"
    if h[4:8] == b"ftyp" or h[:4] in (b"\x1a\x45\xdf\xa3", b"OggS") or h[:3] == b"ID3": return "av"
    s = h.lstrip(b"\xef\xbb\xbf \t\r\n")
    if s[:1] in (b"{", b"[", b"<") and 0 not in h: return "text"
    return None


FAMILY_OF_DEST = {}
for _t in IMAGE_TYPES: FAMILY_OF_DEST[_t] = "image"
for _t in PDF_TYPES: FAMILY_OF_DEST[_t] = "pdf"
for _t in ARCHIVE_ZIP: FAMILY_OF_DEST[_t] = "zip"
for _t in ARCHIVE_GZ: FAMILY_OF_DEST[_t] = "gzip"
for _t in ARCHIVE_BZ2: FAMILY_OF_DEST[_t] = "bz2"
for _t in ARCHIVE_TAR: FAMILY_OF_DEST[_t] = "tar"
for _t in AV_TYPES: FAMILY_OF_DEST[_t] = "av"
for _t in SQLITE_TYPES: FAMILY_OF_DEST[_t] = "sqlite"
for _t in TEXT_TYPES: FAMILY_OF_DEST[_t] = "text"


def check_generic(path, full_size):
    with open(path, "rb") as f:
        data = f.read()
    if is_zero_filled(data, full_size):
        return "zero_filled", "all-zero payload"
    return "unsupported", "no content-specific check for this dest_type"


def scan_one(row):
    key = row["key"]
    size = row["size"] or 0
    sha1 = row["sha1"]
    dest_type = row["dest_type"]

    fd, scratch_path = tempfile.mkstemp(dir=SCRATCH_DIR, prefix="ri_")
    os.close(fd)

    result = {
        "key": key, "size": size, "sha1": sha1, "dest_type": dest_type,
        "status": "fail", "reason": "", "width": None, "height": None,
        "has_exif": None, "pages": None, "duration_s": None,
        "tool": TOOL_NAME, "tool_version": TOOL_VERSION, "detected_type": None,
    }

    try:
        timeout = max(60, min(600, size // (512 * 1024) + 30))
        ok, err = fetch_bytes(key, scratch_path, timeout=timeout)
        if not ok:
            result["status"] = "fail"
            result["reason"] = f"fetch failed: {err}"
            return result

        actual_size = os.path.getsize(scratch_path)

        claimed = FAMILY_OF_DEST.get(dest_type)
        detected = sniff(scratch_path)
        family = detected or claimed
        result["detected_type"] = detected
        note = ""
        if detected and claimed and detected != claimed:
            note = f"content is {detected}, extension says {claimed}"
        elif detected and not claimed:
            note = f"content is {detected}"

        if family == "image":
            status, reason, w, h, exif = check_image(scratch_path, actual_size)
            result.update(status=status, reason=reason, width=w, height=h, has_exif=exif)
        elif family == "pdf":
            status, reason, pages = check_pdf(scratch_path, actual_size)
            result.update(status=status, reason=reason, pages=pages)
        elif family == "zip":
            status, reason = check_zip(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        elif family == "gzip":
            status, reason = check_gz(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        elif family == "zstd":
            status, reason = check_zstd(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        elif family == "xz":
            status, reason = check_xz(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        elif family == "bz2":
            status, reason = check_bz2(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        elif family == "tar":
            status, reason = check_tar(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        elif family == "av":
            status, reason, duration = check_av(scratch_path, actual_size)
            result.update(status=status, reason=reason, duration_s=duration)
        elif family == "sqlite":
            status, reason = check_sqlite(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        elif family == "text":
            status, reason = check_text(scratch_path, actual_size)
            result.update(status=status, reason=reason)
        else:
            status, reason = check_generic(scratch_path, actual_size)
            result.update(status=status, reason=reason)

        if note:
            result["reason"] = (note + ("; " + result["reason"] if result["reason"] else ""))[:300]
        return result
    except Exception as e:  # noqa: BLE001
        result["status"] = "fail"
        result["reason"] = f"unhandled exception: {e}\n{traceback.format_exc()[-200:]}"
        return result
    finally:
        try:
            if os.path.exists(scratch_path):
                os.remove(scratch_path)
        except Exception:  # noqa: BLE001
            pass


def writer_loop(out_q: "queue.Queue", stop_event: threading.Event, counters: dict, lock: threading.Lock):
    batch = []
    last_flush = time.time()
    while True:
        try:
            item = out_q.get(timeout=1)
            batch.append(item)
        except queue.Empty:
            pass

        should_flush = (
            len(batch) >= BATCH_SIZE
            or (batch and time.time() - last_flush >= BATCH_SECONDS)
            or (stop_event.is_set() and out_q.empty() and batch)
        )
        if should_flush:
            try:
                flush_batch(batch)
            except Exception as e:  # noqa: BLE001
                print(f"[writer ERROR] failed to flush batch of {len(batch)}: {e}", flush=True)
            with lock:
                for item in batch:
                    counters["done"] += 1
                    counters[item["status"]] = counters.get(item["status"], 0) + 1
                if counters["done"] // PROGRESS_EVERY != (counters["done"] - len(batch)) // PROGRESS_EVERY:
                    print(
                        f"[progress] done={counters['done']} "
                        f"ok={counters.get('ok',0)} fail={counters.get('fail',0)} "
                        f"zero_filled={counters.get('zero_filled',0)} "
                        f"unsupported={counters.get('unsupported',0)} "
                        f"elapsed={time.time()-counters['start']:.0f}s",
                        flush=True,
                    )
            batch = []
            last_flush = time.time()

        if stop_event.is_set() and out_q.empty() and not batch:
            break


def main():
    print(f"[start] {TOOL_NAME} v{TOOL_VERSION} at {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    os.makedirs(SCRATCH_DIR, exist_ok=True)

    ensure_results_table()
    ensure_detected_type_column()
    print(f"[mode] recheck={RECHECK} zstd={ZSTD}", flush=True)
    done_keys = load_done_keys()
    scope = load_scope()
    print(f"[scope] total={len(scope)} already_done={len(done_keys)}", flush=True)

    todo = [row for row in scope if row["key"] not in done_keys]
    total_bytes = sum((r["size"] or 0) for r in todo)
    est_egress_usd = total_bytes / (1024 ** 3) * 0.01
    print(
        f"[budget] remaining_files={len(todo)} remaining_bytes={total_bytes} "
        f"(~{total_bytes/1024/1024/1024:.2f} GiB) est_b2_egress=${est_egress_usd:.2f} "
        f"workers={WORKERS}",
        flush=True,
    )

    if not todo:
        print("[done] nothing left to scan", flush=True)
        return

    out_q: "queue.Queue" = queue.Queue()
    stop_event = threading.Event()
    counters = {"done": 0, "start": time.time()}
    lock = threading.Lock()

    writer_thread = threading.Thread(
        target=writer_loop, args=(out_q, stop_event, counters, lock), daemon=True
    )
    writer_thread.start()

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(scan_one, row): row["key"] for row in todo}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                result = fut.result()
            except Exception as e:  # noqa: BLE001
                result = {
                    "key": key, "size": None, "sha1": None, "dest_type": None,
                    "status": "fail", "reason": f"worker crash: {e}",
                    "width": None, "height": None, "has_exif": None,
                    "pages": None, "duration_s": None,
                    "tool": TOOL_NAME, "tool_version": TOOL_VERSION,
                }
            out_q.put(result)

    stop_event.set()
    writer_thread.join(timeout=60)

    elapsed = time.time() - counters["start"]
    print(
        f"[finished] done={counters['done']} elapsed={elapsed:.0f}s "
        f"ok={counters.get('ok',0)} fail={counters.get('fail',0)} "
        f"zero_filled={counters.get('zero_filled',0)} "
        f"unsupported={counters.get('unsupported',0)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
