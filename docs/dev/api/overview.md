# API Overview

As APIs públicas do Araquem permanecem estáveis e com payload imutável. Todas as rotas são servidas pelo FastAPI definido em `app/api/*`.

## Endpoints principais

| Método | Caminho | Descrição | Fonte |
| --- | --- | --- | --- |
| `POST` | `/ask` | NL→SQL, retorna `results`, `meta` e `answer` conforme roteamento do planner. | `app/api/ask.py` |
| `GET` | `/healthz` | Verifica PostgreSQL e Redis, devolvendo status agregado. | `app/api/health.py` |
| `GET` | `/metrics` | Exposição Prometheus com gauges/counters `sirios_*` e RAG. | `app/api/health.py` |
| `GET` | `/health/redis` | Sonda direta do cache Redis. | `app/api/health.py` |
| `GET` | `/debug/planner` | Executa `planner.explain` para diagnósticos. | `app/api/debug.py` |
| `GET` | `/_debug/trace` | Inicia trace manual para validar instrumentação. | `app/api/debug.py` |

## Operações (Ops)

Os endpoints de operações ficam sob `/ops/*` e requerem autenticação out-of-band (tokens/env).

| Método | Caminho | Função | Fonte |
| --- | --- | --- | --- |
| `POST` | `/ops/cache/bust` | Invalida manualmente uma chave de cache usando política declarada (`data/policies/cache.yaml`). | `app/api/ops/cache.py` |
| `GET`/`POST` | `/ops/analytics/explain` | Resumo das execuções `/ask?explain=true` filtradas por intent/entity/route. | `app/api/ops/analytics.py` |
| `GET` | `/ops/analytics/explain/events` | Lista eventos persistidos em `explain_events`. | `app/api/ops/analytics.py` |
| `GET` | `/ops/metrics/catalog` | Expõe catálogo de métricas configuradas em `app/observability/metrics.py`. | `app/api/ops/metrics.py` |
| `POST` | `/ops/metrics/rag/register` | Recalcula gauges do índice RAG. | `app/api/ops/metrics.py` |
| `POST` | `/ops/metrics/rag/eval` | Registra resultados de avaliação (`rag_eval_*`). | `app/api/ops/metrics.py` |
| `POST` | `/ops/rag/refresh` | Atualiza métricas de tamanho/densidade do índice (`data/embeddings/store/*`). | `app/api/ops/rag.py` |
| `POST` | `/ops/quality/push` | Valida projections/gates a partir de `data/ops/quality/*.json`. | `app/api/ops/quality.py` |

> Fontes: `app/api/ops/*.py` e dados declarativos referenciados em cada endpoint.【F:app/api/ops/cache.py†L1-L80】【F:app/api/ops/analytics.py†L1-L160】【F:app/api/ops/metrics.py†L1-L160】【F:app/api/ops/rag.py†L1-L80】【F:app/api/ops/quality.py†L1-L200】

## Contratos imutáveis

- Payload do `/ask` continua `{question, conversation_id, nickname, client_id}`. Campos opcionais só podem ser adicionados mediante ADR; a validação `pydantic` (`AskPayload`) garante schema fixo.【F:app/api/ask.py†L18-L57】
- O parâmetro `explain` é querystring (`/ask?explain=true`) e apenas ativa telemetria, sem alterar a estrutura do payload. Respostas mantêm `meta.result_key`, `meta.planner_*`, `meta.cache` e `meta.aggregates` conforme pipeline.【F:app/api/ask.py†L58-L220】
- Rotas `/ops/*` dependem de dados declarativos (YAML/JSON); nenhuma aceita mutação arbitrária.

Consulte [ask.md](./ask.md) para exemplos completos de request/response.
