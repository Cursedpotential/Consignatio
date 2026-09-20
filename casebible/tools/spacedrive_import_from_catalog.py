#!/usr/bin/env python3
"""
Byline: Claude Code - Sonnet 5 - 2026-09-16 (rev 2, parent-resolved source)

Populate Spacedrive gate's file_path/location rows for location 6 ("b2",
path /media/openlist/b2) DIRECTLY from the Propria raw_duck Postgres catalog,
instead of walking the OpenList WebDAV mount with Spacedrive's own indexer.
Owner direction 2026-09-16 08:43 EDT: "why can't Spacedrive use our
already-created catalog?"

Run ON ovh-files (needs docker exec access to the postgres container and to
the spacedrive-gate container's SQLite volume path). No B2 writes of any kind;
this only inserts/updates rows in Spacedrive's own library SQLite database.

--------------------------------------------------------------------------
SOURCE (resolved by the parent session from the dedupe lane's own log,
propria-79 / URGENT-TODO lines 161-166, terminal state as of 21:58 UTC
2026-09-16) -- rev 1 of this script used --intake-table/--vault-table flags
because the source was genuinely ambiguous at the time; that ambiguity is
now resolved and hardcoded as the DEFAULT (still overridable, never silent):
  - intake/raw-dedupe/v1/source-buckets/ = 0 objects. raw_duck.intake_objects_
    20260916_r4 = 0 rows (verified live). Intake contributes ZERO file_path rows.
  - vault/v1 = 508,152 objects / 2,170,597,644,994 bytes by a fresh `rclone size`.
    Current table: raw_duck.vault_objects_20260916_r4 (508,201 rows) MINUS the 49
    keys in raw_duck.vault_onecopy_pilot_delete_20260916 (deleted after r4 was
    loaded) = 508,152. Verified live 2026-09-16: count matches exactly (508,152)
    AND sum(size) over that same set matches the rclone byte count EXACTLY
    (2,170,597,644,994) -- both asserted below before any write.
  - Do NOT use vault_objects_20260916_post_prune (pre-move, superseded) or the
    original b2_objects/vault_objects (stale -- see rev 1 history in
    Consignatio/docs/URGENT-TODO.md for how that was discovered: a same-day
    migration by a different/concurrent session deleted 526,393 of 530,070
    b2_objects rows and pruned vault_objects from 1,677,487 down through this
    same r4/pilot_delete chain).
  - raw_duck.vault_objects_20260916_r4.key is ALREADY the full path relative to
    the salem-data bucket root (e.g. "consignatio/vault/v1/ZIP archives/org/...")
    -- verified live against the actual mount (stat matched size exactly) --
    unlike the older vault_objects table whose keys were relative to
    "consignatio/vault/v1/" instead. materialized_path is therefore built the
    same way as for intake keys: "salem-data/" + key.

--------------------------------------------------------------------------
ROW SHAPES -- copied live from the gate build's own indexer output
--------------------------------------------------------------------------
Read from `select * from file_path where location_id in (3,4) limit 5` on
the live library DB (locations 3 "exchange" and 4 "volumes", both indexed by
Spacedrive's own indexer over the same OpenList mount) on 2026-09-16:

  pub_id                16 random bytes (this script uses uuid4().bytes),
                        unique per row (file_path_pub_id_key is UNIQUE)
  is_dir                1 for directory rows, 0 for file rows
  cas_id                NULL (populated later by a file_identifier job in
                        this build; never fabricated here -- no hashing
                        over B2 despite having sha1 in the catalog, because
                        Spacedrive's cas_id is its own content-addressing
                        scheme, not a bare sha1)
  integrity_checksum    NULL (same reasoning)
  location_id           6
  materialized_path     "/" or "/a/b/" -- leading+trailing slash, relative
                        to the location root, EXCLUDING the entry's own name
  name / extension      Rust Path::file_stem()/extension() semantics: a
                        filename with no dot, or a dotfile with exactly one
                        leading dot (".spacedrive"), has NO extension (whole
                        string is `name`); otherwise split on the LAST dot
                        (observed: name="data.db" extension="bak-pre-rename-
                        20260915-015655" for a real indexed row)
  hidden                1 iff the filename starts with "."
  size_in_bytes,
  size_in_bytes_bytes   left NULL -- every sampled real row (both dirs and
                        files, locations 3 and 4) had these blank; sizing
                        appears to be populated by a later pass in this
                        build, not the indexer itself, so leaving them NULL
                        matches observed real behavior rather than guessing
                        an encoding for size_in_bytes_bytes (undocumented
                        blob format, easy to get wrong)
  inode                 NULL. SQLite's UNIQUE(location_id, inode) index
                        treats every NULL as distinct (verified: SQLite
                        unique-index NULL semantics), so many NULL inodes on
                        one location_id is legal. We have no real inode for
                        catalog-sourced rows (no filesystem walk happened)
                        and do not fabricate one.
  object_id, key_id     NULL (nullable FK; confirmed NULL on real location 4
                        rows too -- object linkage is a separate pass)
  date_created,
  date_modified         raw_duck.vault_objects_20260916_r4 carries NO
                        per-object timestamp column at all (only key, size,
                        sha1). Stat-ing 508k objects individually over WebDAV
                        to recover a real mtime is exactly the slow walk this
                        import exists to avoid, and the parent session
                        confirmed: leave dates NULL rather than fabricate.
                        Both left NULL for every imported row.
  date_indexed          wall-clock time this script runs (true and accurate)

Column types: the real rows show 13-digit integers for date_* columns
(e.g. 1789525921448), i.e. Unix epoch milliseconds, not ISO strings -- this
script writes that representation for date_indexed (the only date_* column
it actually populates).

--------------------------------------------------------------------------
Idempotency / replace semantics: the parent asked this run to REPLACE the
139,446 leftover rows a cancelled WebDAV indexer job left behind for
location 6 (two scan attempts, both cancelled -- see URGENT-TODO), not merge
with them. --apply therefore DELETEs every existing file_path row WHERE
location_id=6 (index rows only -- this never touches B2 or the mount) inside
the same transaction as the fresh insert, so a mid-run failure rolls back to
the pre-delete state rather than leaving a half-replaced index.

--------------------------------------------------------------------------
Standing risk mitigation (also parent-requested): a location's file-system
watcher in this build appears to auto-trigger a fresh WebDAV indexer scan
when its mount comes back after being unavailable (observed live 2026-09-16:
restarting the OpenList container made location 6's watcher kick off a new
`indexer scan_location` job on its own). `locations.update` accepts an
`is_archived: true` field over rspc without erroring, but a live check
showed the DB column stayed NULL after that call -- i.e. this build's
location::update handler deserializes the field but does not appear to act
on it (see Consignatio's own "config accepted != feature working" hard
rule). --apply sets is_archived=1 for location 6 via a **direct SQL UPDATE**
instead (safe here specifically because crdt_operation has 0 rows for this
library -- location/file_path are not CRDT-synced in this build, confirmed
live), then the real test is watching whether a job appears after the
container restart this script performs anyway. Report the outcome plainly
either way -- this is an experiment, not a proven fix.

--------------------------------------------------------------------------
Usage:
  python3 spacedrive_import_from_catalog.py --dry-run
      Report counts + assertion result only. Makes no DB connection writes,
      does not touch the container.

  python3 spacedrive_import_from_catalog.py --apply
      Asserts the source count/bytes match the rclone-verified totals, backs
      up the library SQLite (dated copy next to it), stops spacedrive-gate
      via `docker compose stop`, deletes existing location_id=6 file_path
      rows, writes fresh ones + sets location 6 is_archived=1, all in one
      transaction, then starts the container back up.
"""
import argparse
import csv
import shutil
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone

LIB_ID = "891f127d-e9de-4330-bd3c-37f8fcc7aba4"
LIB_DB = f"/var/lib/docker/volumes/spacedrive_gate_state/_data/libraries/{LIB_ID}.db"
LOCATION_ID = 6
LOCATION_ROOT_PREFIX = "salem-data"  # /media/openlist/b2/salem-data/...
PG_CONTAINER = "fgz1n7useplhk0t91uk7k1aw"
PG_DB = "casebible"
PG_USER = "postgres"
COMPOSE_DIR = "/data/probata/config/spacedrive-gate"

VAULT_TABLE = "vault_objects_20260916_r4"
VAULT_EXCLUDE_TABLE = "vault_onecopy_pilot_delete_20260916"
INTAKE_TABLE = "intake_objects_20260916_r4"  # 0 rows, kept for completeness/idempotent re-run

EXPECT_VAULT_COUNT = 508152
EXPECT_VAULT_BYTES = 2170597644994


def _pg_copy_csv(sql, source_table_for_errors):
    """Stream rows out of Postgres via `docker exec psql ... COPY ... CSV` and parse with
    Python's csv module (NOT naive line.split("\\t")).

    BUG FOUND AND FIXED 2026-09-17: rev 2 of this script used `line.rstrip("\\n").split("\\t")`,
    which assumes one physical line == one CSV row. That is false whenever a field contains an
    embedded newline or needs quote-escaping -- Postgres COPY CSV format quotes such fields per
    the CSV spec (wrapping in double quotes, doubling internal quotes, keeping the literal
    newline inside the quotes), spanning MULTIPLE physical lines for one logical row. This
    corpus has real filenames like AI-chat-export titles that contain embedded newlines and
    quotes (e.g. a Google AI Studio export literally named
    `**Defining the "Nuclear Option"**<newline><newline>I'm focusing intently on...`), and the
    naive splitter corrupted exactly one such row into 4 garbage file_path rows (3 spurious
    directories with a stray `"` prepended to a path segment, 1 file row with a truncated,
    newline-mangled name and extension=`"`) -- found by manually diffing an imported row against
    a real indexer-written row, column by column, per the parent session's request. `csv.reader`
    consumes additional lines from the stream itself when inside a quoted field, so it handles
    this correctly.
    """
    proc = subprocess.Popen(
        ["docker", "exec", "-i", PG_CONTAINER, "psql", "-U", PG_USER, "-d", PG_DB, "-c", sql],
        stdout=subprocess.PIPE, text=True,
    )
    reader = csv.reader(proc.stdout, delimiter="\t")
    for row in reader:
        if not row:
            continue
        key = row[0]
        size = int(row[1]) if len(row) > 1 and row[1] not in ("", "\\N") else None
        yield key, size
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"psql COPY failed for raw_duck.{source_table_for_errors} (exit {proc.returncode})")


def pg_copy_vault_rows():
    """key,size for vault_objects_20260916_r4 MINUS vault_onecopy_pilot_delete_20260916.
    No timestamp column exists on this table."""
    sql = (
        f"COPY (SELECT v.key, v.size FROM raw_duck.{VAULT_TABLE} v "
        f"WHERE NOT EXISTS (SELECT 1 FROM raw_duck.{VAULT_EXCLUDE_TABLE} d WHERE d.key = v.key)) "
        f"TO STDOUT WITH (FORMAT csv, DELIMITER E'\\t')"
    )
    yield from _pg_copy_csv(sql, VAULT_TABLE)


def pg_copy_intake_rows():
    sql = f"COPY (SELECT key, size FROM raw_duck.{INTAKE_TABLE}) TO STDOUT WITH (FORMAT csv, DELIMITER E'\\t')"
    yield from _pg_copy_csv(sql, INTAKE_TABLE)


def split_name_ext(filename):
    """Rust Path::file_stem()/extension() semantics."""
    idx = filename.rfind(".")
    if idx <= 0:  # no dot, or dotfile with exactly one leading dot
        return filename, ""
    return filename[:idx], filename[idx + 1:]


def relative_parts(key):
    """catalog key -> path parts relative to the b2 LOCATION ROOT (/media/openlist/b2),
    i.e. prefixed with the bucket name since the location root is one level above it."""
    full = f"{LOCATION_ROOT_PREFIX}/{key}"
    return full.split("/")


def materialized_path_for(parent_parts):
    if not parent_parts:
        return "/"
    return "/" + "/".join(parent_parts) + "/"


def assert_vault_source():
    """Runs the exact count+byte-sum check server-side (fast, one round trip) and aborts
    loudly if it doesn't match the rclone-verified totals the parent supplied. This must
    pass before any row is streamed for writing."""
    sql = (
        f"SELECT count(*), coalesce(sum(size),0) FROM raw_duck.{VAULT_TABLE} v "
        f"WHERE NOT EXISTS (SELECT 1 FROM raw_duck.{VAULT_EXCLUDE_TABLE} d WHERE d.key = v.key);"
    )
    out = subprocess.run(
        ["docker", "exec", PG_CONTAINER, "psql", "-U", PG_USER, "-d", PG_DB, "-Atc", sql],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    count_str, bytes_str = out.split("|")
    count, total_bytes = int(count_str), int(bytes_str)
    print(f"[assert] {VAULT_TABLE} minus {VAULT_EXCLUDE_TABLE}: count={count} bytes={total_bytes}")
    if count != EXPECT_VAULT_COUNT or total_bytes != EXPECT_VAULT_BYTES:
        raise SystemExit(
            f"[assert] MISMATCH -- expected count={EXPECT_VAULT_COUNT} bytes={EXPECT_VAULT_BYTES}, "
            f"got count={count} bytes={total_bytes}. Refusing to write. The source tables likely "
            f"changed since 21:58 UTC 2026-09-16 -- re-verify with the dedupe lane before retrying."
        )
    print("[assert] OK -- matches the rclone-verified totals exactly")


def build_rows():
    """Yields (is_dir, materialized_path, name, extension, hidden, size) for every
    directory and file implied by the vault (and, if non-empty, intake) catalog rows.
    Directories are synthesized once per unique (materialized_path, name) pair."""
    dirs_seen = {}  # (materialized_path, name) -> True
    file_count = 0
    for key, size in pg_copy_intake_rows():
        parts = relative_parts(key)
        filename = parts[-1]
        parent_parts = parts[:-1]
        for i in range(len(parent_parts)):
            dirs_seen[(materialized_path_for(parent_parts[:i]), parent_parts[i])] = True
        name, ext = split_name_ext(filename)
        hidden = 1 if filename.startswith(".") else 0
        yield (0, materialized_path_for(parent_parts), name, ext, hidden, size)
        file_count += 1
    for key, size in pg_copy_vault_rows():
        parts = relative_parts(key)
        filename = parts[-1]
        parent_parts = parts[:-1]
        for i in range(len(parent_parts)):
            dirs_seen[(materialized_path_for(parent_parts[:i]), parent_parts[i])] = True
        name, ext = split_name_ext(filename)
        hidden = 1 if filename.startswith(".") else 0
        yield (0, materialized_path_for(parent_parts), name, ext, hidden, size)
        file_count += 1
    for (d_mp, d_name) in dirs_seen:
        yield (1, d_mp, d_name, "", 1 if d_name.startswith(".") else 0, None)
    print(f"[build_rows] {file_count} file rows, {len(dirs_seen)} directory rows", file=sys.stderr)


def run_dry_run():
    assert_vault_source()
    is_dir_count = 0
    file_count = 0
    for is_dir, mp, name, ext, hidden, size in build_rows():
        if is_dir:
            is_dir_count += 1
        else:
            file_count += 1
    print(f"DRY RUN -- vault_table={VAULT_TABLE} minus {VAULT_EXCLUDE_TABLE}, intake_table={INTAKE_TABLE}")
    print(f"  would-be file rows:      {file_count}")
    print(f"  would-be directory rows: {is_dir_count}")
    print(f"  total file_path rows:    {file_count + is_dir_count}")
    print("  No database was opened; no container was touched.")


def backup_library_db():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = f"{LIB_DB}.bak-{ts}"
    shutil.copy2(LIB_DB, dest)
    print(f"[backup] {LIB_DB} -> {dest}")
    return dest


def docker_compose(*args):
    subprocess.run(["docker", "compose", *args], cwd=COMPOSE_DIR, check=True)


def apply_import():
    assert_vault_source()
    backup_library_db()
    print("[apply] stopping spacedrive-gate (SQLite is single-writer)")
    docker_compose("stop", "spacedrive-gate")

    con = sqlite3.connect(LIB_DB)
    cur = con.cursor()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    inserted = 0
    try:
        cur.execute("DELETE FROM file_path WHERE location_id=?", (LOCATION_ID,))
        deleted = cur.rowcount
        print(f"[apply] deleted {deleted} pre-existing location_id={LOCATION_ID} file_path rows "
              f"(index rows only -- no B2/mount files touched)")
        for is_dir, mp, name, ext, hidden, size in build_rows():
            cur.execute(
                "INSERT INTO file_path (pub_id, is_dir, location_id, materialized_path, "
                "name, extension, hidden, date_created, date_modified, date_indexed) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (uuid.uuid4().bytes, is_dir, LOCATION_ID, mp, name, ext, hidden,
                 None, None, now_ms),
            )
            inserted += 1
        # Standing-risk experiment: try to stop the watcher from auto-rescanning this
        # location on the restart this script is about to do. See module docstring --
        # this is unproven, report the real outcome after restart either way.
        cur.execute("UPDATE location SET is_archived=1 WHERE id=?", (LOCATION_ID,))
        con.commit()
        print(f"[apply] inserted={inserted} rows (all fresh -- location_id={LOCATION_ID} was fully cleared first)")
        print(f"[apply] set location {LOCATION_ID} is_archived=1 (direct SQL -- unverified whether it suppresses the watcher)")
    except Exception:
        con.rollback()
        print("[apply] ERROR -- rolled back, no partial write committed", file=sys.stderr)
        raise
    finally:
        con.close()

    print("[apply] starting spacedrive-gate back up")
    docker_compose("up", "-d", "spacedrive-gate")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        run_dry_run()
    else:
        apply_import()
