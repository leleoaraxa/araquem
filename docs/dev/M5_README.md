
# Araquem — M5 Observabilidade & Tracing (Prometheus + Tempo + OpenTelemetry)

> Contrato permanente: **Guardrails Araquem v2.0**. Sem heurísticas. 100% YAML‑driven.
> Escopo M5 em pequenos lotes: configuração centralizada (`data/ops/observability.yaml`),
> instrumentação mínima nas quatro camadas, Collector + Tempo no compose, dashboards Grafana.

## 1. Objetivo
Elevar a maturidade de observabilidade do Araquem com **métricas padronizadas** e **tracing distribuído**,
links entre métricas (exemplares/exemplars) e traces, e governança central por YAML.

**Entregáveis**
- `data/ops/observability.yaml` como fonte de verdade (ativação, buckets, sampling, PII, sanitização SQL).
- Factories para métricas e tracing lendo o YAML (sem valores de buckets/sampling no código).
- Instrumentação mínima: **gateway**, **orchestrator/planner**, **executor (SQL)**, **cache (Redis)**.
- `otel-collector` (OTLP gRPC/HTTP) → **Tempo**; Prometheus continua raspando `/metrics` dos serviços.
- Grafana: datasources Prometheus & Tempo + dashboards provisionados (“Araquem — Observability”, “Araquem — Traces”).
- DoD: testes unit+integração garantindo emissão de métricas e spans conforme contratos, sem PII.

## 2. Arquitetura (visão lógica)
```
Client → FastAPI (gateway)
            ↘ OTel SDK (spans) ────────→ OTEL Collector → Tempo (traces)
             ↘ Prometheus client (/metrics) → Prometheus → Grafana
Gateway → Orchestrator/Planner → Executor (Postgres) → Cache (Redis)
           (propaga traceparent + baggage: request_id)
```
- YAML único em `data/ops/observability.yaml` governa **o que** e **como** medir/traçar.
- Collector aplica batch/sampling e exporta para Tempo; Grafana cria links de métricas→traces por exemplares.

## 3. Responsabilidades por camada

### 3.1 Gateway (FastAPI)
**Métricas**
- `sirios_http_requests_total{route="/ask", method, code}` — Contador por rota.
- `sirios_http_request_duration_seconds_bucket{route, method}` — Histograma (buckets do YAML).
- `sirios_ws_messages_total{direction={"in","out"}}` — Mensagens WebSocket (se aplicável).

**Tracing**
- Span raiz: `HTTP POST /ask` ou `WS /ws`.
- Atributos (sem PII): `request_id`, `client_id` (se houver), `user_kind`, `route`, `method`.
- Eventos: `payload_validated`, `ws_degraded_to_http` (quando ocorrer).

### 3.2 Orchestrator / Planner
**Métricas**
- `sirios_planner_route_decisions_total{intent, entity, outcome={"ok","fallback","blocked"}}`.
- `sirios_planner_duration_seconds_bucket{stage={"tokenize","rank","select"}}`.

**Tracing**
- Span: `planner.route` (filho do gateway).
- Atributos: `intent`, `entity`, `tokens_matched`, `confidence`, `ontology_version`.
- Evento: `anti_tokens_triggered` (quando aplicável).

### 3.3 Executor (Postgres)
**Métricas**
- `sirios_sql_query_duration_seconds_bucket{entity, db_name}`.
- `sirios_sql_rows_returned_total{entity}`.
- `sirios_sql_errors_total{entity, error_code}`.

**Tracing**
- Span: `sql.execute` (filho do planner quando for via planner; ou do gateway).
- Atributos OTel DB: `db.system="postgresql"`, `db.name`, `db.namespace` (schema), `db.sql.table` (view),
  `db.statement` **sanitizado** e **truncado** conforme YAML.
- Eventos: `retry`, `timeout` (se aplicáveis).

### 3.4 Cache (Redis)
**Métricas**
- `sirios_cache_ops_total{op={"get","set","bust"}, outcome={"hit","miss","ok","error"}}`.
- `sirios_cache_latency_seconds_bucket{op}`.
- `sirios_cache_key_ttl_seconds_bucket{entity}` (observacional).

**Tracing**
- Spans: `cache.get`, `cache.set`, `cache.bust`.
- Atributos: `cache.system="redis"`, `cache.key_hash` (hash da chave), `cache.ttl`, `cache.hit=true|false`.

## 4. Contrato YAML — `data/ops/observability.yaml`
**Princípios:**
- Nada de buckets/sampling no código — tudo vem do YAML.
- Campos `drop_attributes` e `allow_attributes` governam PII/atributos nos spans.
- `statement.sanitize=true` e `max_len` controlam o que vai para `db.statement` no trace.

Ver arquivo modelo em `data/ops/observability.yaml` (incluído neste pacote).

## 5. Configuração (env/compose)
Variáveis padrão (por serviço):
- `OBSERVABILITY_CONFIG=data/ops/observability.yaml`
- `OTEL_SERVICE_NAME=gateway|orchestrator|executor|cache`
- `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`
- `PROMETHEUS_MULTIPROC_DIR=/tmp/prom` (se multiprocess)

Compose (novos serviços, sugestão):
- **otel-collector**: receivers `otlp`, processors `batch,attributes,sampling`, exporters `tempo,logging`.
- **tempo**: armazenamento local para dev; retention configurável.
- **grafana**: provisioning para datasources (Prometheus/Tempo) e dashboards.

## 6. Padrões de instrumentação (código)
- **Metrics factory**: cria `Counter/Histogram` com rótulos fixos e curtos (`route`, `entity`, `method`, `code`, `outcome`, `db_name`). Lê `enabled` e `buckets` do YAML.
- **Tracer factory**: inicializa OTel com recurso padrão (`service.name`) e aplica sampling do YAML:
  - `root_ratio` (probabilístico) e `slow_threshold_ms` (força amostragem quando excedido).
- **Contexto**: propagar `request_id` como baggage; respeitar `traceparent`.
- **Sanitização de SQL**: elisão de literais (substitui por `?`) + truncamento em `max_len`.
- **Cache keys**: sempre `hash_sha256` — nunca a chave em claro em métricas ou spans.

## 7. Dashboards Grafana
**Araquem — Observability (Prometheus)**
- Gateway: QPS `/ask`, latência p50/p95/p99, error-rate (4xx/5xx).
- Planner: decisões por `intent/entity`, p95 por estágio, fallbacks vs ok.
- Executor: p95 por `entity`, top N lentas, erros por `error_code`.
- Cache: hit-rate, p95 `cache.get`, TTL observado.
- Infra: Postgres (TPS, conexões, locks), Redis (ops, mem).
- **Exemplars**: habilitar em latências; link direto para traces no Tempo.

**Araquem — Traces (Tempo)**
- Filtros: `service IN (gateway, orchestrator, executor, cache)` + `route="/ask"`.
- Waterfall e heatmap de spans lentos.
- Drill por `intent/entity` + exemplos de “slow traces” (> `slow_threshold_ms`).

## 8. Privacidade e PII
- Nunca tracear/logar `question` em claro; usar apenas hash quando necessário.
- `cache.key` sempre como hash (exposto como `cache.key_hash`).
- Enforcar `drop_attributes`/`allow_attributes` do YAML.
- `db.statement` sanitizado e truncado.

## 9. Testes (DoD M5)
**Unit**
- Parser/validador do YAML (schema + defaults).
- Factories criam métricas/summaries/histograms somente quando `enabled`.
- Sanitização SQL (regex + truncamento) e hashing da cache key.

**Integração**
- `/ask` emite `sirios_http_requests_total` e `sirios_http_request_duration_seconds`.
- `planner.route` gera span com `intent/entity` visíveis no Tempo.
- Cache hit/miss reflete em `sirios_cache_ops_total` e span `cache.get` com `cache.hit`.
- Trace e2e com `request_id` propagado (gateway→planner→executor→cache).

**Observabilidade**
- Grafana com datasources Prometheus/Tempo provisionados.
- Dashboard “Araquem — Observability” renderiza sem erros e com exemplars.

**Segurança**
- Ausência de `question_raw` em métricas, logs e spans (checagem automatizada).

## 10. Runbooks (operação)
- **Latência alta**: comparar p95 gateway vs planner vs sql/cache; abrir exemplar → Tempo; verificar spans longos.
- **Hit rate caiu**: revisar TTL, chaves, cardinalidade; checar `cache.miss` e SQL subjacente.
- **Erros SQL**: observar `sql_errors_total{error_code}`; abrir traces e inspecionar `db.statement` sanitizado.
- **Ruído de cardinalidade**: rever rótulos; reduzir `allow_attributes` no YAML.

## 11. Próximos passos (lotes recomendados)
1) Commit do YAML + factories mínimas (gateway).  
2) Adicionar Collector/Tempo no compose + datasources Grafana.  
3) Instrumentar planner/executor/cache.  
4) Provisionar dashboards (JSON).  
5) Testes M5 (unit/integration) e checklist DoD.
