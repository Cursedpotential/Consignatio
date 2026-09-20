#!/bin/sh
# OpenList SSO follow-up (2026-09-14) - step 3
# Source analysis of OpenListTeam/OpenList server/handles/ssologin.go (OIDC branch)
# confirms OIDC login matches by db.GetUserBySSOID(userID) where userID is the VALUE
# of the claim named by sso_oidc_username_key (set to "preferred_username" =
# "msalem85"). It does NOT match by username in the OIDC path. So the real fix is
# setting sso_id, not just renaming username. We do both per the owner's request
# (rename for clarity/consistency + set sso_id for the actual binding).
set -e
CID=openlist-pn6t3nsdrhnxnueuwe7756g5-174843146837
DB=/opt/openlist/data/data.db

echo "=== before ==="
docker exec $CID sh -c "sqlite3 -header -column $DB \"SELECT id, username, role, disabled, sso_id FROM x_users;\""

docker exec $CID sh -c "sqlite3 $DB \"UPDATE x_users SET username='msalem85', sso_id='msalem85' WHERE id=3 AND username='msalem';\""
echo "UPDATE_EXIT: $?"

echo "=== after ==="
docker exec $CID sh -c "sqlite3 -header -column $DB \"SELECT id, username, role, disabled, sso_id FROM x_users;\""

echo "=== admin row unchanged check ==="
docker exec $CID sh -c "sqlite3 -header -column $DB \"SELECT id, username, role, disabled FROM x_users WHERE id=1;\""
