# Dependências

> **Como validar**
> - Confira `requirements.txt` para bibliotecas Python e confirme o uso em código nos módulos correspondentes.【F:requirements.txt†L1-L21】【F:app/executor/pg.py†L16-L69】【F:app/api/ask.py†L8-L330】
> - Revise `docker-compose.yml` e os módulos core para identificar serviços externos (Redis, Postgres, Ollama, observabilidade).【F:docker-compose.yml†L1-L197】【F:app/core/context.py†L13-L17】【F:app/rag/ollama_client.py†L18-L99】
> - Analise imports entre pacotes internos (`app.api`, `app.core`, `app.planner`, etc.) para mapear acoplamentos relevantes.【F:app/api/ask.py†L13-L171】【F:app/orchestrator/routing.py†L49-L459】

## Bibliotecas externas (Python)

| Biblioteca | Versão | Propósito no projeto | Referência |
| --- | --- | --- | --- |
| `fastapi` (via `uvicorn[standard]`) | 0.30.x | Framework HTTP da API, routers e middlewares | 【F:app/api/__init__.py†L1-L44】【F:app/api/ask.py†L8-L56】 |
| `pydantic` | 2.9.2 | Modelos de payload (AskPayload, ops payloads) | 【F:app/api/ask.py†L49-L55】【F:app/api/ops/cache.py†L14-L20】 |
| `psycopg[binary]` | 3.2.1 | Conexão Postgres para consultas e inserts de explain | 【F:app/executor/pg.py†L16-L69】【F:app/api/ask.py†L272-L299】 |
| `redis` | 5.0.7 | Cliente Redis para cache read-through | 【F:app/cache/rt_cache.py†L44-L216】 |
| `prometheus-client` | 0.20.0 | Exposição de métricas customizadas e gauges RAG | 【F:app/observability/metrics.py†L12-L157】 |
| `opentelemetry-*` | 1.27.0 / 0.48b0 | Tracing OTLP, instrumentação FastAPI/psycopg | 【F:app/observability/runtime.py†L24-L64】 |
| `Jinja2` | 3.1.4 | Renderização de templates legado (`render_rows_template`) | 【F:app/formatter/rows.py†L1-L160】 |
| `PyYAML` | 6.0.3 | Leitura de ontologia, entidades, políticas e configs | 【F:app/utils/filecache.py†L34-L115】【F:app/builder/sql_builder.py†L18-L115】 |
| `httpx` | 0.27.2 | Scripts e possivelmente Narrator (quando stream) | 【F:scripts/quality/quality_push.py†L14-L52】 |
| `requests` | 2.32.3 | Fallbacks/integrações (ex: scripts de observabilidade) | 【F:scripts/observability/obs_audit.py†L1-L120】 |

## Serviços e recursos externos

| Serviço | Uso | Consumidor | Fonte |
| --- | --- | --- | --- |
| PostgreSQL (externo) ⚠️ | Views SQL consultadas pelas entidades e tabela `explain_events` | `PgExecutor`, health check | 【F:.env.example†L1-L3】【F:app/executor/pg.py†L21-L69】【F:app/api/ask.py†L272-L299】 |
| Redis | Cache de métricas e bust via `/ops/cache` | `RedisCache`, health, orchestrator | 【F:docker-compose.yml†L39-L45】【F:app/cache/rt_cache.py†L44-L216】 |
| Ollama API | Embeddings RAG e geração do Narrator | `app/rag/ollama_client`, planner, narrador | 【F:docker-compose.yml†L47-L74】【F:app/planner/planner.py†L187-L236】【F:app/narrator/narrator.py†L71-L120】 |
| Prometheus | Coleta métricas expostas pela API e jobs | Observabilidade stack, scripts quality | 【F:docker-compose.yml†L92-L104】【F:app/observability/runtime.py†L69-L96】 |
| Grafana | Visualização de métricas | Operações/observabilidade | 【F:docker-compose.yml†L105-L122】 |
| Tempo | Backend de tracing distribuído | OTEL collector, API | 【F:docker-compose.yml†L123-L148】【F:app/observability/runtime.py†L24-L64】 |
| OTEL Collector | Ponte OTLP -> Tempo | API (tracing) | 【F:docker-compose.yml†L137-L148】 |
| Quality cron & RAG cron | Jobs internos (qualidade e refresh) que consomem API | `scripts/quality/*`, `/ops/rag/refresh` | 【F:docker-compose.yml†L149-L185】【F:app/api/ops/rag.py†L12-L33】 |

⚠️ Indica serviços que requerem credenciais ou dados sensíveis não inclusos no repositório.

## Dependências internas (pacotes)

| Origem | Depende de | Finalidade | Evidência |
| --- | --- | --- | --- |
| `app.api.ask` | `planner`, `orchestrator`, `cache`, `policies`, `Narrator`, `render_answer` | Processar `/ask` e montar resposta final | 【F:app/api/ask.py†L13-L329】 |
| `app.orchestrator.routing` | `Planner`, `PgExecutor`, `CachePolicies`, `RedisCache`, `build_select_for_entity`, `infer_params` | Determinar rota, montar SQL e aplicar cache | 【F:app/orchestrator/routing.py†L49-L459】 |
| `app.planner.planner` | `load_ontology`, `cached_embedding_store`, `OllamaClient`, `entity_hints_from_rag` | Scoring NL→intent/entity com fusão RAG | 【F:app/planner/planner.py†L9-L345】 |
| `app.core.context` | `RedisCache`, `CachePolicies`, `Planner`, `PgExecutor`, `Orchestrator` | Wiring central inicializado no import | 【F:app/core/context.py†L3-L33】 |
| `app.cache.rt_cache` | `redis`, `yaml`, `metrics instrumentation` | Cache TTL e métricas de hit/miss | 【F:app/cache/rt_cache.py†L1-L216】 |
| `app.analytics.explain` | `app.observability.instrumentation` | Gerar payload de explain/telemetria | 【F:app/analytics/explain.py†L1-L160】 |
| `app.observability.metrics` | `prometheus_client`, `instrumentation` | Wrapper para métricas estruturadas | 【F:app/observability/metrics.py†L12-L157】 |
| `app.api.ops.quality` | `planner`, `orchestrator`, `prom_query_instant` | Qualidade de roteamento e thresholds RAG | 【F:app/api/ops/quality.py†L12-L200】 |

## Observações

- O Planner e o Orchestrator compartilham a mesma ontologia e thresholds; qualquer mudança nos YAMLs requer reinicialização ou hot-reload manual (não implementado).【F:app/planner/planner.py†L90-L115】【F:app/orchestrator/routing.py†L208-L299】
- Scripts de qualidade, dashboards e crons reutilizam o token `QUALITY_OPS_TOKEN`; planejar rotação coordenada para evitar interrupções simultâneas.【F:docker-compose.yml†L149-L185】【F:scripts/quality/quality_push.py†L21-L67】
- Dependências de Postgres (views) e explicação de schema não estão versionadas; manter documentação externa alinhada às entidades YAML para evitar divergências.
