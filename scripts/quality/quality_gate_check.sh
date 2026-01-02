#!/usr/bin/env bash
set -euo pipefail

echo "🔎 [check] validating ontology manifest..."
python scripts/ontology/validate_and_hash.py --check
echo "✅ ontology manifest ok"

echo "[check] validating data contracts..."
python scripts/core/validate_data_contracts.py

QUALITY_SRC="${QUALITY_POLICY_PATH:-data/policies/quality.yaml}"
if [[ ! -f "${QUALITY_SRC}" ]]; then
  FALLBACK_SRC="${PLANNER_THRESHOLDS_PATH:-data/ops/planner_thresholds.yaml}"
  echo "[warn] quality policy not found at ${QUALITY_SRC}; falling back to ${FALLBACK_SRC}"
  QUALITY_SRC="${FALLBACK_SRC}"
fi

if command -v yq >/dev/null 2>&1; then
  MIN_TOP1=$(yq '(.targets.min_top1_accuracy // .quality_gates.thresholds.min_top1_accuracy // 0)' "${QUALITY_SRC}")
  MIN_GAP=$(yq '(.targets.min_top2_gap // .quality_gates.thresholds.min_top2_gap // 0)' "${QUALITY_SRC}")
  MIN_ROUTED=$(yq '(.targets.min_routed_rate // .quality_gates.thresholds.min_routed_rate // 0)' "${QUALITY_SRC}")
  MAX_MISSES_ABS=$(yq '(.targets.max_misses_absolute // .quality_gates.thresholds.max_misses_absolute // 0)' "${QUALITY_SRC}")
  MAX_MISSES_RATIO=$(yq '(.targets.max_misses_ratio // .quality_gates.thresholds.max_misses_ratio // 0)' "${QUALITY_SRC}")
  echo "[thresholds] top1>=${MIN_TOP1} gap>=${MIN_GAP} routed>=${MIN_ROUTED}"
  echo "[thresholds] misses_abs<=${MAX_MISSES_ABS} misses_ratio<=${MAX_MISSES_RATIO}"
else
  echo "[warn] yq not found; skipping threshold introspection"
fi

API_URL="${API_URL:-http://localhost:8000}"

report_json="$(curl -s "${API_URL}/ops/quality/report")"
status="$(printf '%s' "${report_json}" | jq -r '.status')"

echo "[report] ${report_json}"

if [[ "${status}" != "pass" ]]; then
  echo "[fail] quality gate: status=${status}"
  exit 1
fi

echo "[ok] quality gate passed"
