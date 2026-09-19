#!/usr/bin/env bash
set -u
URL=http://127.0.0.1:5125/v1/speech
BODY='{"text":"你好，这是十五字测试。","avatarId":"cyrene","referenceId":"default","speed":1.0,"languages":["zh","en"],"stream":false}'
COUNT=${1:-2}
name=${2:-run}
i=1
while [ "$i" -le "$COUNT" ]; do
  curl -sS -o "${TMPDIR:-/tmp}/${name}-${i}.wav" -w "${name} ${i} http=%{http_code} start=%{time_starttransfer} total=%{time_total} size=%{size_download}\n" -H 'Content-Type: application/json' -d "$BODY" "$URL"
  i=$((i + 1))
done
