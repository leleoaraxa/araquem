#!/bin/sh
set -eu

# -------- Config --------
API_URL_RAW="${QUALITY_API_URL:-http://localhost:8000}"
# remove aspas acidentais e espaços nas pontas
API_URL="${API_URL_RAW%\"}"; API_URL="${API_URL#\"}"
API_URL="$(printf '%s' "$API_URL" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

# tempos
WAIT_MAX="${QUALITY_REPORT_WAIT_MAX:-60}"
WAIT_SLEEP="${QUALITY_REPORT_WAIT_SLEEP:-2}"
CRON_INTERVAL="${QUALITY_CRON_INTERVAL:-3600}"

# header do token (só injeta -H se houver token!)
HAS_TOKEN=0
if [ "${QUALITY_OPS_TOKEN:-}" ]; then
  HAS_TOKEN=1
  TOKEN_HDR="X-OPS-TOKEN: ${QUALITY_OPS_TOKEN}"
fi

# -------- Dep PyYAML --------
python - <<'PY'
import importlib.util, sys, subprocess
if importlib.util.find_spec('yaml') is None:
    subprocess.check_call([sys.executable,'-m','pip','install','--no-cache-dir','pyyaml'])
PY

echo "⏳ aguardando API saudável..."
if [ "$HAS_TOKEN" -eq 1 ]; then
  until curl -fsS -H "$TOKEN_HDR" "$API_URL/ops/quality/report" >/dev/null; do sleep 2; done
else
  until curl -fsS "$API_URL/ops/quality/report" >/dev/null; do sleep 2; done
fi
echo "✅ API ok, iniciando ciclo de qualidade"

# helper: POST de arquivos com quality_push.py (mantém teu fluxo)
post_quality_dir() {
  python ./scripts/quality/quality_push_cron.py || true
}

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
  post_quality_dir

  echo "⏳ aguardando consolidação das métricas..."
  waited=0
  while [ "$waited" -lt "$WAIT_MAX" ]; do
    if [ "$HAS_TOKEN" -eq 1 ]; then
      json="$(curl -fsS -H "$TOKEN_HDR" "$API_URL/ops/quality/report" || echo '{}')"
    else
      json="$(curl -fsS "$API_URL/ops/quality/report" || echo '{}')"
    fi
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
