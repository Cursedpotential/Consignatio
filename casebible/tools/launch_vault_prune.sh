#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-16 07:10 EDT (session propria-79)
# Vault dedupe + intake prune on B2 (run ON ovh-files). Owner 2026-09-16 07:01: "You need to dedupe this. And if it's
# into the vault [it] needs to be removed from intake, right now."
#   plan      fresh listings of vault + intake, PG keep table, delete lists + safety checks (no deletes)
#   dryrun    rclone delete --dry-run on both lists (counts only)
#   delete-intake   hard-delete intake objects already in the vault, checked folder phases (owner: intake first)
#   delete-vault    hard-delete duplicate vault copies, checked folder phases (after intake)
#   move-plan / move-copy / move-confirm / delete-moved   step 3–4: move what is left in intake, clean intake again
#   onecopy         step 5: one copy per content in the vault (B2-stored sha1 + size; name + size without sha1)
#   check     fresh listings after the deletes
set -euo pipefail
MODE="${1:?usage: launch_vault_prune.sh plan|dryrun|delete-intake|delete-vault|check}"
RUN=/data/consignatio/migrations/vault-consolidation-20260915
OUT="$RUN/prune-20260916"
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
CONF=/opt/casebible/rclone.conf
PG=fgz1n7useplhk0t91uk7k1aw
UNIT=consignatio-vault-prune-20260916
mkdir -p "$OUT"

lsjson() {  # $1 = prefix under b2:salem-data, $2 = output file
  systemd-run --unit "$UNIT-list-$(date +%s%N)" --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
    /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --fast-list --config "$CONF" "b2:salem-data/$1" > "$2"
}

rclone_delete() {  # $1 = list, extra args after
  local list="$1"; shift
  /usr/bin/rclone delete "b2:salem-data" --config "$CONF" --files-from-raw "$list" --b2-hard-delete \
    --checkers 64 --transfers 64 --fast-list --retries 3 --low-level-retries 10 --stats 60s --stats-one-line "$@"
}

case "$MODE" in
  plan)
    lsjson consignatio/vault/v1/ "$OUT/vault.before.lsjson.json"
    lsjson consignatio/intake/raw-dedupe/v1/source-buckets/ "$OUT/intake.before.lsjson.json"
    docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 < "$RUN/vault_dedupe_intake_prune.sql"
    docker cp "$PG:/tmp/vault_keep_v6.csv" "$OUT/vault_keep_v6.csv"
    docker cp "$PG:/tmp/intake_catalog_sha1.csv" "$OUT/intake_catalog_sha1.csv"
    /usr/bin/python3 "$RUN/vault_dedupe_intake_prune.py" --manifest "$RUN/vault_copy_manifest_v6.csv" \
      --keep "$OUT/vault_keep_v6.csv" --vault "$OUT/vault.before.lsjson.json" \
      --intake "$OUT/intake.before.lsjson.json" --catalog "$OUT/intake_catalog_sha1.csv" --outdir "$OUT"
    sha256sum "$OUT/vault_delete.list" "$OUT/intake_delete.list"
    ;;
  dryrun)
    for L in vault_delete intake_delete; do
      echo "== $L: $(wc -l < "$OUT/$L.list") keys"
      systemd-run --unit "$UNIT-dry-$L" --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
        bash -c "$(declare -f rclone_delete); CONF=$CONF; rclone_delete '$OUT/$L.list' --dry-run --log-level NOTICE 2>&1 | grep -c 'Skipped delete as --dry-run is set'"
    done
    ;;
  delete-intake|delete-vault)
    # owner 2026-09-16 07:11 "First, clean the intake" · 07:38 "Check. Remove next folder. Check." — checked folder
    # phases via vault_phase_runner.py (lists each folder before and after; stops on any mismatch). No bulk deletes.
    WHAT="${MODE#delete-}"
    L="$OUT/${WHAT}_delete.list"
    case "$WHAT" in
      intake) BASE=consignatio/intake/raw-dedupe/v1/source-buckets/; CAT="$OUT/intake_catalog_sha1.csv" ;;
      vault)  BASE=consignatio/vault/v1/; CAT="$OUT/vault_catalog_size.csv"
              # vault objects have no stored catalog sha1: key + size from the copy manifest (extra versions must match size)
              /usr/bin/python3 -c "import csv,sys; r=csv.DictReader(open('$RUN/vault_copy_manifest_v6.csv',newline='',encoding='utf-8')); w=csv.writer(open('$CAT','w',newline='',encoding='utf-8')); w.writerow(['key','size','sha1']); [w.writerow([x['dest_key'],x['size'],'']) for x in r]" ;;
    esac
    U="consignatio-vault-phases-$WHAT"
    test -s "$L" || { echo "ABORT: $L missing/empty"; exit 2; }
    for other in consignatio-vault-phases-intake consignatio-vault-phases-vault consignatio-vault-phases-moved; do
      if systemctl is-active --quiet "$other"; then echo "ABORT: $other is active"; exit 3; fi
    done
    systemctl reset-failed "$U" 2>/dev/null || true
    systemd-run --unit "$U" -p EnvironmentFile="$ENVF" -p MemoryMax=2G -p Nice=10 \
      /usr/bin/python3 "$RUN/vault_phase_runner.py" --list "$L" --base "$BASE" --workdir "$OUT/phases-$WHAT" --catalog "$CAT"
    sleep 5; systemctl status "$U" --no-pager -n 3 || true
    ;;
  move-plan)
    lsjson consignatio/vault/v1/ "$OUT/vault.mid.lsjson.json"
    lsjson consignatio/intake/raw-dedupe/v1/source-buckets/ "$OUT/intake.mid.lsjson.json"
    /usr/bin/python3 "$RUN/vault_move_rest.py" plan --intake "$OUT/intake.mid.lsjson.json" \
      --vault "$OUT/vault.mid.lsjson.json" --out "$OUT/move_rest_manifest.csv"
    ;;
  move-copy)
    if systemctl is-active --quiet "$UNIT-move"; then echo "ABORT: $UNIT-move already active"; exit 3; fi
    systemctl reset-failed "$UNIT-move" 2>/dev/null || true
    systemd-run --unit "$UNIT-move" --wait --pipe --quiet -p EnvironmentFile="$ENVF" -p MemoryMax=2G \
      /usr/bin/python3 "$RUN/vault_copy_driver.py" copy --manifest "$OUT/move_rest_manifest.csv" \
        --ledger "$OUT/move_rest.ledger.sqlite" --config "$CONF" --rclone-log "$OUT/move_rest.rcd.log" --workers 64
    ;;
  move-confirm)
    lsjson consignatio/vault/v1/ "$OUT/vault.moved.lsjson.json"
    lsjson consignatio/intake/raw-dedupe/v1/source-buckets/ "$OUT/intake.moved.lsjson.json"
    /usr/bin/python3 "$RUN/vault_move_rest.py" moved --intake "$OUT/intake.moved.lsjson.json" \
      --vault "$OUT/vault.moved.lsjson.json" --manifest "$OUT/move_rest_manifest.csv" --out "$OUT/intake_moved_delete.list"
    ;;
  delete-moved)
    L="$OUT/intake_moved_delete.list"; U=consignatio-vault-phases-moved
    test -s "$L" || { echo "ABORT: $L missing/empty"; exit 2; }
    for other in consignatio-vault-phases-intake consignatio-vault-phases-vault consignatio-vault-phases-moved; do
      if systemctl is-active --quiet "$other"; then echo "ABORT: $other is active"; exit 3; fi
    done
    systemctl reset-failed "$U" 2>/dev/null || true
    systemd-run --unit "$U" -p EnvironmentFile="$ENVF" -p MemoryMax=2G -p Nice=10 \
      /usr/bin/python3 "$RUN/vault_phase_runner.py" --list "$L" --base consignatio/intake/raw-dedupe/v1/source-buckets/ \
        --workdir "$OUT/phases-moved" --catalog "$OUT/intake_catalog_sha1.csv"
    sleep 5; systemctl status "$U" --no-pager -n 3 || true
    ;;
  onecopy)
    systemd-run --unit "$UNIT-list-$(date +%s%N)" --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
      /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --fast-list --hash --hash-type sha1 \
        --config "$CONF" b2:salem-data/consignatio/vault/v1/ > "$OUT/vault.final.lsjson.json"
    /usr/bin/python3 "$RUN/vault_move_rest.py" onecopy --vault "$OUT/vault.final.lsjson.json"
    ;;
  check)
    lsjson consignatio/vault/v1/ "$OUT/vault.after.lsjson.json"
    lsjson consignatio/intake/raw-dedupe/v1/source-buckets/ "$OUT/intake.after.lsjson.json"
    /usr/bin/python3 - "$OUT" <<'PY'
import json, sys
out = sys.argv[1]
for name in ("vault", "intake"):
    items = json.load(open(f"{out}/{name}.after.lsjson.json", encoding="utf-8"))
    print(f"{name}: {len(items):,} objects / {sum(i['Size'] for i in items) / 1e9:,.1f} GB")
kept = {l.split(",")[1] for l in open(f"{out}/vault_keep_v6.csv", encoding="utf-8").read().splitlines()[1:]}
vault = {"consignatio/vault/v1/" + i["Path"] for i in json.load(open(f"{out}/vault.after.lsjson.json", encoding="utf-8"))}
missing = [k for k in kept if k not in vault]
print("kept vault objects missing after delete:", len(missing))
PY
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
