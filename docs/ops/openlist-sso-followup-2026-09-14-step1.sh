#!/bin/sh
# OpenList SSO follow-up (2026-09-14) - step 1: backup + inspect users
# Run on ovh-files (100.91.190.107) as root via:
#   ssh -i ~/.ssh/ovh root@100.91.190.107 sh < openlist-sso-followup-2026-09-14-step1.sh
set -e
CID=openlist-pn6t3nsdrhnxnueuwe7756g5-174843146837
TS=$(date +%Y%m%d-%H%M%S)
cp /data/probata/volumes/openlist/data.db /data/probata/volumes/openlist/data.db.bak-pre-rename-$TS
echo "BACKUP_OK: data.db.bak-pre-rename-$TS"
ls -la /data/probata/volumes/openlist/ | grep data.db

TOKEN=$(docker exec $CID sh -c '/opt/openlist/openlist admin token 2>&1' | tail -n1 | tr -d '\r')
echo "TOKEN_LEN: ${#TOKEN}"

docker exec $CID sh -c "wget -q -O- --header='Authorization: $TOKEN' http://127.0.0.1:5244/api/admin/user/list" > /tmp/openlist_users.json
echo "USER_LIST_BYTES: $(wc -c < /tmp/openlist_users.json)"
cat /tmp/openlist_users.json
