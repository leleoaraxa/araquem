#!/bin/sh
set -eu

API_URL="${QUALITY_API_URL:-http://localhost:8000}"
WAIT_MAX="${QUALITY_REPORT_WAIT_MAX:-60}"
WAIT_SLEEP="${QUALITY_REPORT_WAIT_SLEEP:-2}"
CRON_INTERVAL="${QUALITY_CRON_INTERVAL:-3600}"

# Header do token sempre entre aspas (evita quebra de argumentos)
CURL_TOKEN_ARG=""
if [ "${QUALITY_OPS_TOKEN:-}" ]; then
  CURL_TOKEN_ARG="-H"
  CURL_TOKEN_VAL="X-OPS-TOKEN: ${QUALITY_OPS_TOKEN}"
fi

# Garantir PyYAML sem usar pkgutil (deprecation-safe)
python - <<'PY'
import importlib.util, sys, subprocess
if importlib.util.find_spec('yaml') is None:
    subprocess.check_call([sys.executable,'-m','pip','install','--no-cache-dir','pyyaml'])
PY

echo "⏳ aguardando API saudável..."
until sh -c "curl -fsS ${CURL_TOKEN_ARG:+$CURL_TOKEN_ARG} ${CURL_TOKEN_VAL:+\"$CURL_TOKEN_VAL\"} ${API_URL}/ops/quality/report >/dev/null"; do
  sleep 2
done
echo "✅ API ok, iniciando ciclo de qualidade"

has_jq() { command -v jq >/dev/null 2>&1; }

while true; do
  # roda o ciclo de posts; não derruba se algum arquivo falhar
  python ./scripts/quality/quality_push_cron.py || true

  echo "⏳ aguardando consolidação das métricas..."
  waited=0
  while [ "$waited" -lt "$WAIT_MAX" ]; do
    json="$(curl -fsS ${CURL_TOKEN_ARG:+$CURL_TOKEN_ARG} ${CURL_TOKEN_VAL:+\"$CURL_TOKEN_VAL\"} ${API_URL}/ops/quality/report || echo '{}')"

    if has_jq; then
      if echo "$json" | jq -e '(.metrics.routed_rate // 0) > 0 and (.metrics.top1_accuracy // 0) > 0' >/dev/null 2>&1; then
        break
      fi
    else
      python - "$json" >/dev/null 2>&1 <<'PY'
import sys, json
try:
    data=json.loads(sys.argv[1])
    m=data.get("metrics") or {}
    rr=float(m.get("routed_rate") or 0.0)
    t1=float(m.get("top1_accuracy") or 0.0)
    sys.exit(0 if (rr>0 and t1>0) else 1)
except Exception:
    sys.exit(1)
PY
      if [ $? -eq 0 ]; then
        break
      fi
    fi
    sleep "$WAIT_SLEEP"
    waited=$(( waited + WAIT_SLEEP ))
  done

  ./scripts/quality/quality_gate_check.sh || true
  sleep "$CRON_INTERVAL"
done
