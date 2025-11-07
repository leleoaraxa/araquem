# Operações Araquem — Cheatsheet
1. `docker compose up -d redis prometheus tempo otel-collector` — inicia fundação da stack.【F:docker-compose.yml†L35-L158】
2. `docker compose up -d ollama` → aguarde `ollama ps` concluir pull do modelo.【F:docker-compose.yml†L43-L80】
3. `docker compose up -d api grafana` → cheque `curl -f localhost:8000/healthz` e `/metrics`.【F:docker-compose.yml†L1-L125】
4. `docker compose up -d quality-cron rag-refresh-cron` — ativa automações contínuas.【F:docker-compose.yml†L160-L196】
5. `python scripts/quality/quality_push_cron.py --dry-run` — valida amostras antes de enviar.【F:scripts/quality/quality_push_cron.py†L139-L181】
6. `bash scripts/quality/quality_gate_check.sh` — confirma status PASS no quality gate.【F:scripts/quality/quality_gate_check.sh†L1-L16】
7. `docker compose run --rm rag-indexer` — reconstrói embeddings e manifest.【F:docker/Dockerfile.rag-indexer†L1-L20】
8. `curl -s -X POST localhost:8000/ops/rag/refresh` — força refresh imediato.【F:docker/rag-refresh-cron.sh†L1-L20】
9. `python scripts/observability/gen_dashboards.py --config data/ops/observability.yaml --out grafana/dashboards` — atualiza painéis.【F:scripts/observability/gen_dashboards.py†L47-L98】
10. `python scripts/observability/gen_alerts.py --config data/ops/observability.yaml` — regenera rules Prometheus.【F:scripts/observability/gen_alerts.py†L50-L75】

**Checklist diário**
- API responde `200` em `/healthz` e `/metrics` não vazio.【F:docker-compose.yml†L1-L37】
- Prometheus `/-/ready` → `HTTP 200`; targets `araquem-api`, `otel-collector`, `tempo` UP.【F:prometheus/prometheus.yml†L1-L17】
- Grafana disponível em `http://localhost:3000` com dashboards atualizados.【F:docker-compose.yml†L105-L125】
- Quality gate PASS em `/ops/quality/report` e painel de quality sem alertas.【F:docker/quality-cron.sh†L15-L27】
- Métricas RAG (`rag_index_last_refresh_timestamp`) recentes após refresh noturno.【F:docker/rag-refresh-cron.sh†L1-L20】

```
API ↔ Redis ↔ Prometheus ↔ Grafana
        ↑             ↓
    QualityCron   RAGRefresh
```
