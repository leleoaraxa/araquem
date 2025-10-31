#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"

report_json="$(curl -s "${API_URL}/ops/quality/report")"
status="$(printf '%s' "${report_json}" | jq -r '.status')"

echo "[report] ${report_json}"

if [[ "${status}" != "pass" ]]; then
  echo "[fail] quality gate: status=${status}"
  exit 1
fi

echo "[ok] quality gate passed"
