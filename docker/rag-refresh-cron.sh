#!/bin/sh
set -eu
echo "⏳ aguardando API saudável..."
until curl -fsS http://localhost:8000/healthz >/dev/null; do sleep 2; done
echo "✅ API ok; cron RAG iniciado"
while true; do
  now=$(date +%s)
  tgt=$(date -d '02:10' +%s 2>/dev/null || date -j -f '%H:%M' '02:10' +%s)
  [ "$tgt" -le "$now" ] && tgt=$(( tgt + 86400 ))
  sleep $(( tgt - now ))
  echo "▶️  /ops/rag/refresh"
  curl -fsS -X POST http://localhost:8000/ops/quality/push || true
  curl -fsS -X POST http://localhost:8000/ops/rag/refresh || true
  sleep 300
  curl -fsS -X POST http://localhost:8000/ops/rag/refresh || true
  sleep 82800
done
