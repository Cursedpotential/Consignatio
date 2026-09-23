#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-14
# Purpose: Authentik OAuth2 providers created tonight with an EMPTY grant_types list reject every
# authorize request with "invalid_request: The request is otherwise malformed" (root cause of the
# Temporal UI OIDC failure; diffed against the working ContextForge provider). This sets
# grant_types=[authorization_code, refresh_token] on any OAuth2 provider whose list is empty,
# then re-tests the authorize endpoint for Temporal UI and OpenList. Idempotent. Prints no secrets
# (client_id is public; client_secret is never read).
# Run from the desktop (Git-Bash): bash docs/ops/authentik-oauth-grant-types-fix-2026-09-14.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1
APP=root@100.72.169.40
KEY="$HOME/.ssh/ovh"

out=$(ssh -o ConnectTimeout=15 -i "$KEY" "$APP" 'c=$(docker ps --format "{{.Names}}" | grep -E "^authentik-server" | head -1); docker exec "$c" ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider as P
for p in P.objects.all():
    before=list(p.grant_types or [])
    if not before:
        p.grant_types=[\"authorization_code\",\"refresh_token\"]; p.save()
    print(\"GT|\"+p.name+\"|\"+str(before)+\"|\"+str(p.grant_types)+\"|\"+p.client_id+\"|\"+(p.redirect_uris[0].url if p.redirect_uris else \"\"))
" 2>&1 | grep "^GT|"')

echo "$out" | awk -F'|' '{printf "%-36s grant_types before=%s after=%s cid=%s…\n", $2, $3, $4, substr($5,1,8)}'

echo "$out" | awk -F'|' '$2=="Temporal UI" || $2=="OpenList" {print $2"|"$5"|"$6}' | while IFS='|' read -r name cid redir; do
  enc=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$redir")
  # Capture first, then truncate: piping curl straight into `cut` makes curl exit 23 under pipefail.
  res=$(curl -sS -m 20 -o /dev/null -w "%{http_code} -> %{redirect_url}" \
    "https://auth.int.mitechconsult.com/application/o/authorize/?client_id=$cid&redirect_uri=$enc&response_type=code&scope=openid+profile+email&state=grantfixcheck")
  echo "$name authorize: ${res:0:140}"
done
# Verified 2026-09-14 22:45 EDT: Temporal UI grant_types [] -> [authorization_code, refresh_token];
# Temporal and OpenList authorize now 302 to default-authentication-flow (was invalid_request).
