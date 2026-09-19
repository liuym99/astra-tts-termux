#!/usr/bin/env bash
# Drop one model pair into inbox/<avatarId>/ and convert automatically.
set -u
BASE="${ASTRA_CONVERT_BASE:-$HOME/astra-convert}"
INBOX="$BASE/inbox"
SCRIPT="$BASE/convert-and-import.sh"
LOGDIR="$BASE/inbox-logs"
INTERVAL="${ASTRA_CONVERT_INTERVAL:-5}"
mkdir -p "$INBOX" "$LOGDIR"

valid_id() {
  [[ "$1" =~ ^[A-Za-z0-9_-]+$ ]]
}

while :; do
  for dir in "$INBOX"/*; do
    [ -d "$dir" ] || continue
    id="${dir##*/}"
    valid_id "$id" || { echo "[$(date '+%F %T')] skip invalid avatar id: $id" >&2; continue; }
    [ -e "$dir/.processing" ] && continue
    [ -e "$dir/.done" ] && continue
    [ -e "$dir/.error" ] && continue

    ckpt=""
    pth=""
    ckpt_count=0
    pth_count=0
    for f in "$dir"/*.ckpt; do [ -f "$f" ] && ckpt="$f" && ckpt_count=$((ckpt_count + 1)); done
    for f in "$dir"/*.pth; do [ -f "$f" ] && pth="$f" && pth_count=$((pth_count + 1)); done
    [ "$ckpt_count" -eq 1 ] || continue
    [ "$pth_count" -eq 1 ] || continue

    touch "$dir/.processing"
    log="$LOGDIR/$id-$(date +%Y%m%d-%H%M%S).log"
    {
      echo "started=$(date -Is)"
      echo "avatar=$id"
      echo "ckpt=$ckpt"
      echo "pth=$pth"
      echo "command=bash $SCRIPT $id $ckpt $pth"
      bash "$SCRIPT" "$id" "$ckpt" "$pth"
      rc=$?
      echo "exit=$rc"
      echo "finished=$(date -Is)"
      if [ "$rc" -eq 0 ]; then
        mv "$dir/.processing" "$dir/.done"
        echo "status=success"
      else
        mv "$dir/.processing" "$dir/.error"
        echo "status=error"
      fi
    } >>"$log" 2>&1
  done
  sleep "$INTERVAL"
done
