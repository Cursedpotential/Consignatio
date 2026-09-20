#!/bin/sh
# Inspect x_users table schema and rows (no secrets - password fields are bcrypt hashes,
# we will not print those either, just column names + non-sensitive columns).
set -e
CID=openlist-pn6t3nsdrhnxnueuwe7756g5-174843146837
DB=/data/probata/volumes/openlist/data.db

echo "=== schema for x_users ==="
docker exec $CID sh -c "sqlite3 $DB '.schema x_users'"

echo "=== column list ==="
docker exec $CID sh -c "sqlite3 $DB 'PRAGMA table_info(x_users);'"

echo "=== rows (id, username, role, disabled, base_path) ==="
docker exec $CID sh -c "sqlite3 $DB 'SELECT id, username, role, disabled, base_path FROM x_users;'"
