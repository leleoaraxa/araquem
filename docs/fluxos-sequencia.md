# Fluxos de sequência

> **Como validar**
> - Reproduza os fluxos inspecionando os métodos correspondentes em `app/api/ask.py`, `app/orchestrator/routing.py`, `app/cache/rt_cache.py` e `app/api/ops/cache.py`.【F:app/api/ask.py†L56-L330】【F:app/orchestrator/routing.py†L185-L459】【F:app/cache/rt_cache.py†L155-L216】【F:app/api/ops/cache.py†L19-L39】
> - Verifique o consumo de banco e métricas na execução de `PgExecutor` e explain analytics para confirmar os passos de persistência.【F:app/executor/pg.py†L25-L69】【F:app/api/ask.py†L255-L299】

## 1. Pergunta `/ask` com cache read-through

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI /ask
    participant Planner
    participant Orchestrator
    participant Cache as RedisCache
    participant Builder
    participant Executor as PgExecutor
    participant Narrator

    Client->>API: POST /ask {question}
    API->>Planner: explain(question)
    Planner-->>API: plan (chosen intent/entity)
    API->>Orchestrator: route_question(question)
    Orchestrator->>Cache: prepare metrics cache
    alt cache hit
        Cache-->>Orchestrator: cached rows/result_key
    else cache miss
        Orchestrator->>Builder: build_select_for_entity(...)
        Builder-->>Orchestrator: SQL + params
        Orchestrator->>Executor: query(sql, params)
        Executor-->>Orchestrator: rows
        Orchestrator->>Cache: set_json(key, rows)
    end
    Orchestrator-->>API: {results, meta}
    API->>Narrator: render(question, facts, meta) (se habilitado)
    Narrator-->>API: texto final / erro
    API-->>Client: JSON sanitizado (status, results, answer)
```

**Referências:** `ask` chama planner e orchestrator, aplica `read_through` e formata resposta com Narrator e `render_answer`.【F:app/api/ask.py†L56-L329】【F:app/orchestrator/routing.py†L208-L459】【F:app/cache/rt_cache.py†L155-L216】【F:app/responder/__init__.py†L1-L120】

## 2. Pergunta `/ask?explain=true` com persistência de explain analytics

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI /ask?explain
    participant Planner
    participant Orchestrator
    participant Analytics as Explain Analytics
    participant DB as Postgres (explain_events)

    Client->>API: POST /ask?explain=true
    API->>Planner: explain(question)
    Planner-->>API: plan + explain metadata
    API->>Orchestrator: route_question(question, explain=True)
    Orchestrator->>Analytics: explain(request_id, planner_output, metrics)
    Analytics-->>Orchestrator: payload (summary, details)
    Orchestrator-->>API: results + explain payload
    API->>Analytics: explain(request_id,...)
    API->>DB: INSERT explain_events(request_id,...)
    DB-->>API: ack (ignora conflitos)
    API-->>Client: JSON com meta.explain e meta.explain_analytics
```

**Referências:** o modo `explain` coleta decision path, gera analytics duas vezes (planner e resposta) e persiste no Postgres usando `psycopg` com `ON CONFLICT DO NOTHING`.【F:app/api/ask.py†L65-L299】【F:app/orchestrator/routing.py†L338-L439】【F:app/analytics/explain.py†L1-L160】

## 3. Bust de cache operacional

```mermaid
sequenceDiagram
    participant Operator
    participant OpsAPI as POST /ops/cache/bust
    participant Policies
    participant Cache as RedisCache

    Operator->>OpsAPI: POST {entity, identifiers} + X-OPS-TOKEN
    OpsAPI->>Policies: policies.get(entity)
    alt entity ou política inválida
        Policies-->>OpsAPI: None
        OpsAPI-->>Operator: 400 invalid entity
    else
        OpsAPI->>Cache: make_cache_key(build_id, scope, identifiers)
        OpsAPI->>Cache: delete(key)
        Cache-->>OpsAPI: deleted count
        OpsAPI-->>Operator: {deleted, key}
    end
```

**Referências:** rota exige token `CACHE_OPS_TOKEN`, resolve política YAML e calcula a mesma chave usada pelo read-through antes de chamar `RedisCache.delete`.【F:app/api/ops/cache.py†L19-L39】【F:app/cache/rt_cache.py†L96-L173】


<!-- ✅ confirmado: fluxo /ask completo (planner → builder → executor → formatter), narrator opcional. -->
<!-- ✅ confirmado: cache read-through em rt_cache antes do executor quando aplicável. -->
<!-- ✅ confirmado: fluxos adicionais (quality-cron, rag-refresh-cron) descritos. -->
