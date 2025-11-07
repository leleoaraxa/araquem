#!/bin/sh
set -eu

API_URL="${QUALITY_API_URL:-http://localhost:8000}"
: "${QUALITY_OPS_TOKEN:?QUALITY_OPS_TOKEN is required}"

echo "🔧 QUALITY_API_URL: ${API_URL}"
echo "🔧 QUALITY_OPS_TOKEN: **** (redacted)"

echo "⏳ aguardando API saudável..."
until curl -fsS -H "X-OPS-TOKEN: ${QUALITY_OPS_TOKEN}" "${API_URL}/ops/quality/report" >/dev/null; do
  sleep 2
done
echo "✅ API ok, iniciando ciclo de qualidade"

while true; do
  python ./scripts/quality/quality_push_cron.py || true
  echo "⏳ aguardando consolidação das métricas..."
  WAIT_MAX=${QUALITY_REPORT_WAIT_MAX:-60}
  WAIT_SLEEP=${QUALITY_REPORT_WAIT_SLEEP:-2}
  waited=0
  while [ $waited -lt $WAIT_MAX ]; do
    json=$(curl -fsS -H "X-OPS-TOKEN: ${QUALITY_OPS_TOKEN}" "${API_URL}/ops/quality/report" || echo '{}')
    echo "$json" | jq -e '(.metrics.routed_rate // 0) > 0 and (.metrics.top1_accuracy // 0) > 0' >/dev/null && break
    sleep $WAIT_SLEEP
    waited=$(( waited + WAIT_SLEEP ))
  done
  ./scripts/quality/quality_gate_check.sh || true
  sleep 3600
done
