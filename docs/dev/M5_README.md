# M5 — Observabilidade & Tracing (Prometheus + Grafana + Tempo + OTel Collector)

## Objetivo
Prover métricas de gateway, planner, executor e cache, além de tracing distribuído end-to-end, tudo **YAML-driven** via `data/ops/observability.yaml`, sem heurísticas nem hardcodes.

## Componentes
- **Prometheus**: scrape `api:8000/metrics`, `otel-collector:8888`, `tempo:3200`.
- **Grafana**: datasources provisionados (`Prometheus`, `Tempo`) + dashboards provisionados.
- **Tempo**: armazena traces OTLP (`4317` gRPC, `4318` HTTP internos).
- **OTel Collector**: recebe spans do API e exporta para Tempo (schema novo com `service.telemetry.metrics.readers`).

## Métricas (nomes canônicos)
- **Gateway**: `sirios_http_request_duration_seconds` (histogram), `sirios_http_requests_total` (counter).
- **Planner**: `sirios_planner_duration_seconds` (histogram por stage), `sirios_planner_route_decisions_total`.
- **Executor (SQL)**: `sirios_sql_query_duration_seconds` (histogram por entidade/db), `sirios_sql_rows_returned_total`, `sirios_sql_errors_total`.
- **Cache**: `sirios_cache_ops_total`, `sirios_cache_latency_seconds`, `sirios_cache_key_ttl_seconds` (opcional).

## Spans (principais)
- `planner.route` — atributos: `planner.intent`, `planner.entity`, `planner.score`.
- `sql.execute` — atributos: `db.system=postgresql`, `db.name`, `db.sql.table`, `db.statement` (sanitizado).
- (opcional) `cache.get`, `cache.set` — atributos: `cache.key_hash`, `cache.ttl`.

## Dashboards provisionados
- `grafana/dashboards/api_overview.json` — p95/p99, RPS, planner, SQL e cache.
- `grafana/provisioning/dashboards/araquem_traces.json` — busca TraceQL pronta (Tempo).

## Operação
1. `docker compose up -d --build`
2. Gere tráfego: `/healthz`, `/_debug/trace`, `/ask`.
3. Grafana → **Dashboards**:
   - **Araquem — API Overview**
   - **Araquem — Traces**

## Troubleshooting
- **Dashboard vazio**:
  - Confirme `curl http://api:8000/metrics` (deve listar `sirios_*`).
  - Dentro do Prometheus: `wget -qO- http://api:8000/metrics | head` (via `docker compose exec prometheus`).
  - Verifique nomes no JSON do painel (usar `sirios_*`).
- **Collector erro `invalid keys: address`**:
  - Atualize para `service.telemetry.metrics.readers.pull.exporter.prometheus`.
- **Collector `connection refused tempo:4317`**:
  - Verifique `tempo/tempo.yaml` com `receivers.otlp.protocols.grpc.endpoint: 0.0.0.0:4317` e `depends_on: [tempo]`.
- **Traces não aparecem no Tempo**:
  - Confirme variáveis do API: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`.
  - Gere `/ _debug/trace`.

## Segurança (ops)
- `/ops/cache/bust` protegido por `X-OPS-TOKEN` (env: `CACHE_OPS_TOKEN`).
  - Exemplo:
    ```bash
    curl -s -X POST http://localhost:8000/ops/cache/bust \
      -H 'Content-Type: application/json' \
      -H 'X-OPS-TOKEN: secret' \
      -d '{"entity":"fiis_cadastro","identifiers":{"ticker":"HGLG11"}}'
    ```
