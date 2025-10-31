Param(
  [string]$ApiUrl = "http://host.docker.internal:8000",
  [string]$Token = $env:QUALITY_OPS_TOKEN
)
if (-not $Token) {
  Write-Error "QUALITY_OPS_TOKEN não definido."; exit 1
}
$env:API_URL = $ApiUrl
$env:QUALITY_OPS_TOKEN = $Token
docker run --rm `
  -v "${PWD}:/workspace" `
  -w /workspace `
  -e API_URL=$env:API_URL `
  -e QUALITY_OPS_TOKEN=$env:QUALITY_OPS_TOKEN `
  quality-runner `
  bash -lc "python ./scripts/quality_push_cron.py && ./scripts/quality_gate_check.sh"

