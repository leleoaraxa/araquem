# C4 – Componentes

> **Como validar**
> - Analise a composição da aplicação em `app/api/__init__.py`, `app/core/context.py` e módulos referenciados para confirmar os componentes descritos.【F:app/api/__init__.py†L1-L44】【F:app/core/context.py†L3-L33】
> - Verifique o fluxo de dados no orchestrator, planner, executor e cache para garantir que as dependências internas estejam corretas.【F:app/orchestrator/routing.py†L49-L459】【F:app/planner/planner.py†L1-L345】【F:app/executor/pg.py†L16-L71】【F:app/cache/rt_cache.py†L15-L216】
> - Confirme a integração opcional do Narrator e do cliente RAG ao revisar `app/narrator/narrator.py` e `app/rag/ollama_client.py`.【F:app/narrator/narrator.py†L1-L120】【F:app/rag/ollama_client.py†L10-L106】

## Componentes do serviço `api`

```mermaid
flowchart TD
    subgraph FastAPI App
        API[Router /ask]
        OPS[Rotas /ops/*]
        HEALTH[Healthz & Metrics]
    end

    CONTEXT[Core Context
Planner/Executor/Cache] --> API
    CONTEXT --> OPS
    CONTEXT --> HEALTH

    API --> ORCH[Orchestrator
`route_question`]
    ORCH --> PLANNER[Planner
Ontologia + RAG]
    ORCH --> BUILDER[SQL Builder
entity.yaml]
    ORCH --> EXEC[PgExecutor]
    ORCH --> CACHE[RedisCache + Policies]
    API --> NARR[Narrator (opcional)]
    OPS --> OBS[Observability Metrics]
```

### Routers e camada HTTP
- **`app.api.ask`**: expõe `/ask`, gera `request_id`, aciona `planner.explain`, trata cache read-through, formata resposta e opcionalmente chama o Narrator antes de retornar JSON sanitizado.【F:app/api/ask.py†L56-L330】
- **`app.api.health`**: fornece `/healthz`, `/metrics` e `/health/redis`, validando Redis e Postgres com `psycopg`.【F:app/api/health.py†L11-L40】
- **`app.api.ops.*`**: coleção de rotas autenticadas para bust de cache, auditoria de planner, métricas de RAG e explicabilidade; usam tokens de ambiente para autorização.【F:app/api/ops/cache.py†L19-L39】【F:app/api/ops/quality.py†L29-L200】【F:app/api/ops/metrics.py†L15-L38】

### Core & domínio
- **`app.core.context`**: inicializa Planner (ontologia YAML), PgExecutor (Postgres via `DATABASE_URL`), RedisCache e políticas declaradas, expondo instâncias singletons para as rotas.【F:app/core/context.py†L9-L33】
- **`app.planner.planner`**: normaliza texto com ontologia, calcula scores por intent, integra hints RAG e thresholds YAML para selecionar entidade e gerar metadados de explain.【F:app/planner/planner.py†L90-L345】
- **`app.orchestrator.routing`**: aplica gates de thresholds, infere parâmetros declarativos, tenta cache de métricas, constrói SQL com `build_select_for_entity` e formata linhas; também gera explain analytics e controla métricas de planner/cache.【F:app/orchestrator/routing.py†L208-L459】
- **`app.builder.sql_builder`**: traduz contratos YAML das entidades em SELECT parametrizado, respeitando agregações, ordering whitelists e limites inferidos.【F:app/builder/sql_builder.py†L1-L160】
- **`app.executor.pg`**: executa SQL usando `psycopg` com tracing e métricas, sanitizando statement antes de enviar ao span.【F:app/executor/pg.py†L16-L69】
- **`app.cache.rt_cache`**: implementa políticas TTL por entidade, key hashing, métricas de hit/miss e bloqueia cache para payloads vazios, além de utilitário `read_through`.【F:app/cache/rt_cache.py†L15-L216】

### Observabilidade e narrativas
- **`app.observability.runtime`**: carrega `data/ops/observability.yaml`, registra métricas canônicas e habilita tracing OTLP, usado no bootstrap da aplicação.【F:app/observability/runtime.py†L17-L96】【F:app/api/__init__.py†L24-L31】
- **`app.observability.metrics`**: catálogo de métricas com validação de labels, gauges e registradores específicos para RAG, quality e Narrator.【F:app/observability/metrics.py†L24-L157】
- **`app.narrator.narrator`**: cliente opcional que monta prompt via `app.narrator.prompts`, chama Ollama e retorna texto + metadados para a resposta final; fallback determinístico mantém compatibilidade.【F:app/narrator/narrator.py†L27-L120】【F:app/api/ask.py†L179-L329】
- **`app.analytics.explain`**: produz payload estruturado para explain analytics e logging com spans específicos, usado tanto em `/ask` quanto no orchestrator para correlacionar métricas.【F:app/analytics/explain.py†L1-L160】【F:app/api/ask.py†L85-L270】

### Crons e jobs auxiliares
- **Quality cron**: scripts `scripts/quality/*.py` consomem `/ops/quality/push` e métricas Prometheus para avaliar precisão do planner.【F:scripts/quality/quality_push_cron.py†L21-L226】
- **RAG indexer & refresh**: `scripts/embeddings/embeddings_build.py` gera embeddings JSONL e `rag-refresh-cron` dispara refresh via API, mantendo `data/embeddings/store`.【F:scripts/embeddings/embeddings_build.py†L1-L160】【F:docker-compose.yml†L172-L185】

## Dependências cruzadas relevantes
- `app/api/ask` importa diretamente `planner`, `orchestrator`, `cache` e `policies` do contexto, reforçando o acoplamento entre camada HTTP e core; alterações no core exigem atenção à inicialização única (Singleton).【F:app/api/ask.py†L13-L171】【F:app/core/context.py†L13-L33】
- O orchestrator depende de `read_through` (cache) e `build_select_for_entity` (builder), que por sua vez leem os YAMLs. Falhas nesses arquivos propagam como `ValueError` no builder; monitorar logs ao atualizar contratos.【F:app/orchestrator/routing.py†L286-L459】【F:app/builder/sql_builder.py†L18-L115】
- O Planner usa `cached_embedding_store` e `OllamaClient`; se o índice RAG estiver ausente ou corrompido, ele captura exceções e continua com scores base, mas registra contadores de erro.【F:app/planner/planner.py†L187-L345】【F:app/utils/filecache.py†L34-L115】
