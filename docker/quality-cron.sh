#!/bin/sh
set -eu

# -------- Config --------
API_URL="${QUALITY_API_URL:-http://localhost:8000}"
API_URL="${API_URL%\"}"; API_URL="${API_URL#\"}"
API_URL="$(printf '%s' "$API_URL" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
: "${QUALITY_OPS_TOKEN:?QUALITY_OPS_TOKEN is required}"

WAIT_MAX="${QUALITY_REPORT_WAIT_MAX:-60}"
WAIT_SLEEP="${QUALITY_REPORT_WAIT_SLEEP:-2}"
CRON_INTERVAL="${QUALITY_CRON_INTERVAL:-3600}"
PUSH_RETRY_SLEEP="${QUALITY_PUSH_RETRY_SLEEP:-10}"

TOKEN_HEADER="X-OPS-TOKEN: ${QUALITY_OPS_TOKEN}"

# -------- Dep PyYAML --------
python - <<'PY'
import importlib.util, sys, subprocess
if importlib.util.find_spec('yaml') is None:
    subprocess.check_call([sys.executable,'-m','pip','install','--no-cache-dir','pyyaml'])
PY

echo "🔧 QUALITY_API_URL: ${API_URL}"
echo "🔧 QUALITY_OPS_TOKEN: **** (redacted)"

echo "⏳ aguardando API saudável..."
until curl -fsS -H "$TOKEN_HEADER" "$API_URL/ops/quality/report" >/dev/null; do
  sleep 2
done
echo "✅ API ok, iniciando ciclo de qualidade"

echo "🔎 validando imports de qualidade..."
python -c "import app; import app.api.ops.quality_contracts; print('imports ok')"
echo "✅ imports prontos"

# fallback sem jq (mantém o teu teste de routed_rate/top1_accuracy)
ready_json() {
  python - "$1" >/dev/null 2>&1 <<'PY'
import sys, json
try:
    d=json.loads(sys.argv[1]); m=d.get("metrics") or {}
    rr=float(m.get("routed_rate") or 0); t1=float(m.get("top1_accuracy") or 0)
    sys.exit(0 if (rr>0 and t1>0) else 1)
except Exception:
    sys.exit(1)
PY
}

while true; do
  if ! python ./scripts/quality/quality_push_cron.py; then
    echo "❌ quality_push_cron falhou; pulando consolidação e quality_gate_check (retry em ${PUSH_RETRY_SLEEP}s)"
    sleep "$PUSH_RETRY_SLEEP"
    continue
  fi

  echo "⏳ aguardando consolidação das métricas..."
  waited=0
  while [ "$waited" -lt "$WAIT_MAX" ]; do
    json="$(curl -fsS -H "$TOKEN_HEADER" "$API_URL/ops/quality/report" || echo '{}')"
    if command -v jq >/dev/null 2>&1; then
      echo "$json" | jq -e '(.metrics.routed_rate // 0) > 0 and (.metrics.top1_accuracy // 0) > 0' >/dev/null 2>&1 && break
    else
      ready_json "$json" && break || true
    fi
    sleep "$WAIT_SLEEP"
    waited=$(( waited + WAIT_SLEEP ))
  done

  ./scripts/quality/quality_gate_check.sh || true
  sleep "$CRON_INTERVAL"
done
