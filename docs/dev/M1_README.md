# Araquem — M1 (Bootstrap Dev)

- Compose dev com API, Postgres, Redis, Prometheus, Grafana, Tempo, Ollama
- FastAPI com `/healthz` e `/metrics`
- Testes mínimos (`pytest -q`)
- Guardrails: payload imutável no `/ask`

## Como subir
```bash
cp .env.example .env
docker compose up -d
```

## Verificar
- API: http://localhost:8000/healthz
- Métricas: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (anônimo Viewer)
- Tempo: http://localhost:3200

## Testes locais
```bash
pip install -r requirements.txt
pytest -q
```


## Commit template e primeiro commit
```bash
./scripts/git_bootstrap.sh
# ou, manual:
# git init
# git config commit.template .gitmessage
# git add .
# git commit -m "chore: bootstrap Araquem (Guardrails v2.0)"
```

## Dashboard Grafana (API Overview)
- Já provisionado automaticamente em **Folder: _Araquem_** → **Araquem — API Overview**
- Painéis inclusos:
  - p95 de latência (`api_request_latency_seconds` via histogram_quantile)
  - Requests/seg por status (`api_requests_total`)
