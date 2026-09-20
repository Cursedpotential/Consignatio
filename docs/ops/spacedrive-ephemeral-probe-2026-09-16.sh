#!/usr/bin/env bash
# Byline: Claude Code · Fable 5.1 · 2026-09-16
# Read-only: does the running spacedrive-gate build expose no-index (ephemeral) browsing of a path?
set -u
export MSYS_NO_PATHCONV=1
ssh -o ConnectTimeout=15 -i ~/.ssh/ovh root@100.91.190.107 'A=$(sed -n "s/^SD_AUTH=//p" /data/probata/secrets/spacedrive-gate/sd_auth | head -1)
L=891f127d-e9de-4330-bd3c-37f8fcc7aba4
enc() { python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1"; }
for proc in search.ephemeralPaths ephemeralFiles.list files.ephemeral; do
  arg=$(enc "{\"0\":{\"library_id\":\"$L\",\"arg\":{\"path\":\"/media/openlist/b2/salem-data\",\"withHiddenFiles\":false,\"order\":null}}}")
  code=$(curl -s -m 30 -o /tmp/ep.json -w %{http_code} -u "$A" "http://127.0.0.1:8090/rspc/$proc?batch=1&input=$arg")
  echo "$proc -> HTTP $code :: $(head -c 240 /tmp/ep.json)"
done
echo "== ephemeral symbols in served bundle:"
docker exec spacedrive-gate sh -c "grep -rhoaE \"[A-Za-z.]*[eE]phemeral[A-Za-z.]*\" / --include=*.js --include=sd-server 2>/dev/null | sort | uniq -c | sort -rn | head -10"'
