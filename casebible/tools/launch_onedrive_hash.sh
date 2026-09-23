#!/usr/bin/env bash
# Byline: Claude Code · Fable 5.1 · 2026-09-14
# Server-side content hash (md5) of the OneDrive size-collision set. Runs ON the VPS (ovh-files).
#
# Why: OneDrive exposes only quickxor; the catalog match key is (md5,size). 319k of 323k OneDrive
# files collide by size with raw_duck.r2_files (the R2 quarantine/onedrive tree is an earlier copy),
# so bytes must be hashed before anything is copied — owner rule "hash before transfer". This is a
# READ: rclone streams each file from the Graph API into the hasher (no spool, no local OneDrive
# client involved, nothing hydrates on the laptop). Output feeds the copy plan; nothing is copied here.
#
# Usage: launch_onedrive_hash.sh            (one transient systemd unit; scopes run sequentially,
#                                            small ones first as a sanity check, Case Bible last)
# Resume: rerun; paths already present in hashes/<scope>.md5 are skipped.
set -euo pipefail
RUN=/data/consignatio/migrations/onedrive-copy-20260914
CONF=/opt/casebible/rclone.conf
UNIT=consignatio-onedrive-hash-20260914
if systemctl is-active --quiet "$UNIT"; then echo "already running: $UNIT"; exit 0; fi
mkdir -p "$RUN/hashes" "$RUN/logs"
cat > "$RUN/run-onedrive-hash.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
RUN=/data/consignatio/migrations/onedrive-copy-20260914
CONF=/opt/casebible/rclone.conf
declare -A ROOT=( [AI_Space]="AI Space" [Documents_CSV]="Documents/CSV" [Documents_Disk_Drill]="Documents/Disk Drill" [Case_Bible]="Case Bible" )
rc_all=0
for scope in AI_Space Documents_CSV Documents_Disk_Drill Case_Bible; do
  # lists/<scope>.hash.list (written by onedrive_hash_join.py) = residual still needing a real md5 after the
  # name+size+mtime proxy match against the R2 backups; falls back to the full size-collision list
  LIST="$RUN/lists/$scope.hash.list"; [ -s "$LIST" ] || LIST="$RUN/lists/$scope.collide.list"
  OUT="$RUN/hashes/$scope.md5"; TODO="$RUN/lists/$scope.collide.todo"
  [ -s "$LIST" ] || { echo "$scope: nothing to hash"; continue; }
  # a previous run killed before its merge leaves a .part — keep those hashes
  if [ -s "$OUT.part" ]; then cat "$OUT.part" >> "$OUT"; rm -f "$OUT.part"; fi
  # resume: drop paths already hashed (hashsum lines are "<md5>  <path>")
  if [ -s "$OUT" ]; then
    python3 - "$LIST" "$OUT" "$TODO" <<'PY'
import sys
done={l.rstrip("\n")[34:] for l in open(sys.argv[2],encoding="utf-8") if len(l)>34}
todo=[l for l in open(sys.argv[1],encoding="utf-8") if l.rstrip("\n") not in done]
open(sys.argv[3],"w",encoding="utf-8").writelines(todo)
print(f"resume: {len(done)} done, {len(todo)} to go")
PY
  else
    cp "$LIST" "$TODO"
  fi
  [ -s "$TODO" ] || { echo "$scope: all hashed"; continue; }
  echo "$scope: hashing $(wc -l < "$TODO") files from od:${ROOT[$scope]}"
  # OD_NOTRAVERSE=1 (default since 2026-09-14 09:15 UTC): skip the 9,142-folder walk — every throttle so far
  # landed during/after a walk; per-file lookup+download is steadier and a restart costs no walk.
  NT=(); [ "${OD_NOTRAVERSE:-1}" = "1" ] && NT=(--no-traverse)
  rclone --config "$CONF" hashsum md5 "od:${ROOT[$scope]}" --download "${NT[@]}" \
    --files-from-raw "$TODO" --output-file "$OUT.part" \
    --transfers "${OD_TRANSFERS:-4}" --checkers "${OD_CHECKERS:-4}" --tpslimit "${OD_TPS:-8}" --bwlimit "${OD_BWLIMIT:-50M}" \
    --retries 5 --low-level-retries 20 \
    --stats 60s --stats-one-line --log-level "${OD_LOGLEVEL:-INFO}" --log-file "$RUN/logs/$scope.log"
  rc=$?
  cat "$OUT.part" >> "$OUT" && rm -f "$OUT.part"
  echo "$scope: rclone exit=$rc hashed_total=$(wc -l < "$OUT")"
  [ $rc -ne 0 ] && rc_all=$rc
done
echo "ALL-SCOPES-DONE rc=$rc_all"
exit $rc_all
EOF
chmod +x "$RUN/run-onedrive-hash.sh"
# Throttling (2026-09-14, three runs): OneDrive returned "Too many requests" after ~100 GiB in ~10 min at
# 65, 97 and 250 MiB/s alike — a BYTE quota per window, not a request rate — with 14–21 min Retry-After,
# after which rclone's pacer decays only 25 %/success (~1 h crawl). Sustained moderate bandwidth stays under
# it: OD_BWLIMIT defaults to 50M (~30 GiB/10 min). Override per launch with OD_TRANSFERS, OD_CHECKERS,
# OD_TPS, OD_BWLIMIT, OD_LOGLEVEL (DEBUG shows pacer/429 lines) — passed through to the unit.
# No --collect: a killed unit must stay visible (an OOM-killed tranche unit was erased by --collect on 2026-09-14
# and every status query then reported "success"). Progress is judged by hashed counts, never by Result.
systemctl reset-failed "$UNIT" 2>/dev/null || true
systemd-run --unit "$UNIT" -p MemoryMax=2G --working-directory "$RUN" \
  --setenv=OD_TRANSFERS="${OD_TRANSFERS:-4}" --setenv=OD_CHECKERS="${OD_CHECKERS:-4}" \
  --setenv=OD_TPS="${OD_TPS:-8}" --setenv=OD_LOGLEVEL="${OD_LOGLEVEL:-INFO}" --setenv=OD_BWLIMIT="${OD_BWLIMIT:-50M}" \
  --setenv=OD_NOTRAVERSE="${OD_NOTRAVERSE:-1}" \
  /bin/bash "$RUN/run-onedrive-hash.sh"
echo "launched $UNIT — log: journalctl -u $UNIT ; per-scope rclone logs in $RUN/logs/"
