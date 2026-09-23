#!/bin/sh
# Diagnose admin token output shape without printing secret value
set -e
CID=openlist-pn6t3nsdrhnxnueuwe7756g5-174843146837
docker exec $CID sh -c '/opt/openlist/openlist admin token 2>&1' > /tmp/openlist_token_raw.txt
echo "LINE_COUNT: $(wc -l < /tmp/openlist_token_raw.txt)"
awk '{ if ($0 ~ /INFO|WARN|ERRO|DEBU/) k="LOG"; else k="DATA"; print NR": len="length($0)" kind="k }' /tmp/openlist_token_raw.txt
