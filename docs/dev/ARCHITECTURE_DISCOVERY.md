# Araquem — Descoberta Arquitetural

## 1. Estrutura de diretórios (profundidade até 4)

```
./
    .dockerignore
    .env.example
    .gitattributes
    .gitignore
    .gitmessage
    LICENSE
    docker-compose.yml
    pytest.ini
    requirements.txt
.git/
    FETCH_HEAD
    HEAD
    config
    description
    index
    packed-refs
    info/
        exclude
    objects/
        info/
        pack/
            pack-643853819b364ea73cd7394b049dda8056652843.idx
            pack-643853819b364ea73cd7394b049dda8056652843.pack
            pack-643853819b364ea73cd7394b049dda8056652843.rev
    logs/
        HEAD
        refs/
            remotes/
            heads/
                work
    branches/
    hooks/
        applypatch-msg.sample
        commit-msg.sample
        fsmonitor-watchman.sample
        post-update.sample
        pre-applypatch.sample
        pre-commit.sample
        pre-merge-commit.sample
        pre-push.sample
        pre-rebase.sample
        pre-receive.sample
        prepare-commit-msg.sample
        push-to-checkout.sample
        sendemail-validate.sample
        update.sample
    refs/
        tags/
        remotes/
        heads/
            work
data/
    ontology/
        .hash
        entity.yaml
    ops/
        observability.yaml
        param_inference.yaml
        planner_thresholds.yaml
        quality_experimental/
            negatives_m65.json
            param_inference_samples.json
            planner_rag_integration.json
            rag_eval_last.json
            rag_eval_set.json
            rag_search_basics.json
            routing_misses_via_ask.json
        quality/
            README.md
            projection_client_fiis_positions.json
            projection_fiis_cadastro.json
            projection_fiis_dividendos.json
            projection_fiis_financials_revenue_schedule.json
            projection_fiis_financials_risk.json
            projection_fiis_financials_snapshot.json
            projection_fiis_imoveis.json
            projection_fiis_noticias.json
            projection_fiis_precos.json
            projection_fiis_processos.json
            projection_fiis_rankings.json
            projection_history_b3_indexes.json
            projection_history_currency_rates.json
            projection_history_market_indicators.json
            routing_samples.json
    entities/
        fiis_precos/
            fiis_precos.yaml
            templates.md
            responses/
                table.md.j2
        fiis_cadastro/
            fiis_cadastro.yaml
            templates.md
            responses/
                list.md.j2
        history_currency_rates/
            history_currency_rates.yaml
            templates.md
            responses/
                list.md.j2
        fiis_financials_risk/
            fiis_financials_risk.yaml
            hints.md
            templates.md
            responses/
                summary.md.j2
        fiis_financials_snapshot/
            fiis_financials_snapshot.yaml
            templates.md
            responses/
                summary.md.j2
        fiis_noticias/
            fiis_noticias.yaml
            templates.md
            responses/
                list.md.j2
        fiis_imoveis/
            fiis_imoveis.yaml
            templates.md
            responses/
                list.md.j2
        history_market_indicators/
            history_market_indicators.yaml
            templates.md
            responses/
                list.md.j2
        client_fiis_positions/
            client_fiis_positions.yaml
            templates.md
            responses/
                table.md.j2
        fiis_rankings/
            fiis_rankings.yaml
            templates.md
            responses/
                table.md.j2
        fiis_processos/
            fiis_processos.yaml
            templates.md
            responses/
                list.md.j2
        fiis_dividendos/
            fiis_dividendos.yaml
            templates.md
            responses/
                table.md.j2
        history_b3_indexes/
            history_b3_indexes.yaml
            templates.md
            responses/
                list.md.j2
        fiis_financials_revenue_schedule/
            fiis_financials_revenue_schedule.yaml
            hints.md
            templates.md
            responses/
                table.md.j2
    contracts/
        entities/
            client_fiis_positions.schema.yaml
            fiis_cadastro.schema.yaml
            fiis_dividendos.schema.yaml
            fiis_financials_revenue_schedule.schema.yaml
            fiis_financials_risk.schema.yaml
            fiis_financials_snapshot.schema.yaml
            fiis_imoveis.schema.yaml
            fiis_noticias.schema.yaml
            fiis_precos.schema.yaml
            fiis_processos.schema.yaml
            fiis_rankings.schema.yaml
            history_b3_indexes.schema.yaml
            history_currency_rates.schema.yaml
            history_market_indicators.schema.yaml
    golden/
        .hash
        m65_quality.json
        m65_quality.yaml
    raw/
        indicators/
            catalog.md
    embeddings/
        index.yaml
        store/
            embeddings.jsonl
            manifest.json
    policies/
        cache.yaml
        formatting.yaml
        llm_prompts.md
        quality.yaml
        rag.yaml
    concepts/
        catalog.yaml
        fiis.md
scripts/
    __init__.py
    core/
        __init__.py
        ask.py
        golden_sync.py
        validate_data_contracts.py
    observability/
        __init__.py
        gen_alerts.py
        gen_dashboards.py
        hash_guard.py
        obs_audit.py
    maintenance/
        __init__.py
    embeddings/
        __init__.py
        embeddings_build.py
        rag_retrieval_eval.py
    quality/
        __init__.py
        gen_quality_dashboard.py
        quality_bisect.py
        quality_diff_routing.py
        quality_eval_narrator.py
        quality_gate_check.sh
        quality_push.py
        quality_push_cron.py
        quality_push_cron.sh
prometheus/
    alerting_rules.yml
    prometheus.yml
    recording_rules.yml
    templates/
        alerting_rules.yml.j2
        recording_rules.yml.j2
tempo/
    tempo.yaml
.github/
    ISSUE_TEMPLATE.md
    PULL_REQUEST_TEMPLATE.md
    workflows/
        dryrun_structure.yml
        lint_and_validate.yml
        validate_dashboards.yml
k8s/
    quality/
        cronjob.yaml
app/
    __init__.py
    main.py
    orchestrator/
        routing.py
    planner/
        __init__.py
        ontology_loader.py
        param_inference.py
        planner.py
    common/
        __init__.py
        http.py
    executor/
        pg.py
    core/
        __init__.py
        context.py
        hotreload.py
    observability/
        instrumentation.py
        metrics.py
        runtime.py
    formatter/
        rows.py
    utils/
        __init__.py
        filecache.py
    rag/
        __init__.py
        hints.py
        index_reader.py
        ollama_client.py
    responder/
        __init__.py
    api/
        __init__.py
        ask.py
        debug.py
        health.py
        ops/
            __init__.py
            analytics.py
            cache.py
            metrics.py
            quality.py
            rag.py
    analytics/
        explain.py
        metrics.py
        repository.py
    cache/
        __init__.py
        rt_cache.py
    narrator/
        __init__.py
        narrator.py
        prompts.py
    builder/
        sql_builder.py
docs/
    dev/
    database/
        data_sample/
            client_fiis_positions.csv
            fiis_cadastro.csv
            fiis_dividendos.csv
            fiis_financials_revenue_schedule.csv
            fiis_financials_risk.csv
            fiis_financials_snapshot.csv
            fiis_imoveis.csv
            fiis_noticias.csv
            fiis_precos.csv
            fiis_processos.csv
            fiis_rankings.csv
        ddls/
            tables.sql
            views.sql
    devs/
        NEW_INTENTS.md
grafana/
    quality_dashboard.json
    dashboards/
        00_sirios_overview.json
        10_api_slo_pipeline.json
        20_planner_rag_intelligence.json
        30_ops_reliability.json
        _README.md
    playlists/
        sirios_ops_playlist.json
    templates/
        00_sirios_overview.json.j2
        10_api_slo_pipeline.json.j2
        20_planner_rag_intelligence.json.j2
        30_ops_reliability.json.j2
    provisioning/
        dashboards/
            dashboards.yml
        datasources/
            datasource.yml
            jsonapi.yml
            tempo.yaml
docker/
    Dockerfile.api
    Dockerfile.ollama-init
    Dockerfile.otel-collector
    Dockerfile.quality-cron
    Dockerfile.quality-runner
    Dockerfile.rag-indexer
    Dockerfile.rag-refresh-cron
    Dockerfile.tempo
    quality-cron.sh
    rag-eval-cron.sh
    rag-refresh-cron.sh
otel-collector/
    config.yaml
```

### Papel das principais pastas

| Caminho | Papel | Observações |
| --- | --- | --- |
| `/app` | Código principal da API Araquem. Concentra roteadores FastAPI, planejamento, execução de SQL, formatação, camadas de apresentação e integrações. | Estrutura modular com separação explícita por responsabilidade (planner, builder, executor, etc.). |
| `/data` | Configurações declarativas e contratos (ontologia, políticas, YAML de entidades, dados de qualidade). | Planner e builder dependem diretamente desses YAMLs. |
| `/docs` | Documentação existente (database e devs). | Sprint 0 adiciona documentação técnica em `docs/dev`. |
| `/docker`, `/docker-compose.yml` | Infraestrutura de containers para serviços auxiliares (API, RAG, métricas). | Utilizado em ambientes locais e CI. |
| `/grafana`, `/prometheus`, `/tempo` | Observabilidade (dashboards, configurações). | Integrado ao módulo `app/observability`. |
| `/k8s` | Manifests para execução em Kubernetes (jobs de qualidade). | Referência operacional. |
| `/scripts` | Scripts utilitários de manutenção e dados. | Não são invocados pela API principal. |

## 2. Descrição funcional dos módulos (nível de código)

### `app/api`
- **Responsabilidade:** expor endpoints HTTP FastAPI (`/ask`, `/healthz`, rotas operacionais). Ponto de entrada para solicitações externas.
- **Fluxo de chamada:** importa objetos compartilhados de `app.core.context` (planner, orchestrator, cache, políticas) e serviços auxiliares (analytics, narrator, responder).
- **Entradas/Saídas:** recebe payloads Pydantic (ex.: `AskPayload` em `ask.py`) e retorna `JSONResponse` com chaves `status`, `results`, `meta`, `answer`.

### `app/core`
- **Responsabilidade:** bootstrap de dependências globais. Instancia planner, executor Postgres, cache Redis, políticas declarativas e orchestrator.
- **Fluxo de chamada:** `app.api.ask` importa `cache`, `planner`, `orchestrator`, `policies` via `app.core.context`.
- **Entradas/Saídas:** lê variáveis de ambiente (`ONTOLOGY_PATH`, `REDIS_URL`, `DATABASE_URL`) e expõe instâncias configuradas.

### `app/planner`
- **Responsabilidade:** carregar ontologia YAML (`ontology_loader.py`) e executar roteamento determinístico (`planner.py`). Integra sinais RAG (`app.rag`) e thresholds declarativos.
- **Fluxo de chamada:** `app.core.context` instancia `Planner`; `app.api.ask` e `app.orchestrator.routing` chamam `planner.explain(question)`.
- **Entradas/Saídas:** entrada texto livre da pergunta; saída dict com `chosen.intent`, `chosen.entity`, `chosen.score`, `explain` detalhado.

### `app/builder`
- **Responsabilidade:** montar SQL parametrizado a partir de `data/entities/<entity>/<entity>.yaml`. Implementa regras para filtros, agregações e métricas.
- **Fluxo de chamada:** `app.orchestrator.routing.route_question` invoca `build_select_for_entity` com identificadores e `agg_params` inferidos.
- **Entradas/Saídas:** entrada `entity`, `identifiers`, `agg_params`; saída tuple `(sql, params, result_key, return_columns)`.

### `app/executor`
- **Responsabilidade:** executar SQL em Postgres com telemetria. Usa `psycopg` para queries read-only.
- **Fluxo de chamada:** `Orchestrator` chama `PgExecutor.query(sql, params)`.
- **Entradas/Saídas:** entrada string SQL e parâmetros; saída lista de dicts (linhas).

### `app/formatter`
- **Responsabilidade:** formatar linhas e renderizar templates declarativos (Jinja2). Aplica formatadores de moeda/data/percentual.
- **Fluxo de chamada:** `Orchestrator` usa `format_rows` para normalizar resultados. API usa `render_rows_template` para resposta textual.
- **Entradas/Saídas:** entrada lista de rows e metadados; saída lista formatada e string Markdown conforme template.

### `app/responder`
- **Responsabilidade:** renderizar texto legado a partir de templates Markdown (`templates.md`). Implementa lógica de fallback por métricas.
- **Fluxo de chamada:** `app.api.ask` invoca `render_answer` como baseline antes do Narrator.
- **Entradas/Saídas:** entrada `entity`, `rows`, identificadores e agregados; saída string textual.

### `app/narrator`
- **Responsabilidade:** camada opcional LLM (shadow/feature flagged). Constrói prompt determinístico e produz narrativa baseada nos facts estruturados.
- **Fluxo de chamada:** `app.api.ask` instancia `Narrator` se disponível e chama `render` para gerar `final_answer` quando habilitado.
- **Entradas/Saídas:** entrada pergunta, facts (`rows`, `primary`, `aggregates`) e meta (`intent`, `entity`); saída dict com texto, latência, tokens, score.

### `app/orchestrator`
- **Responsabilidade:** coordenar pipeline Planner → SQL builder → Executor → Formatter → Cache. Aplica gates por thresholds e políticas de cache.
- **Fluxo de chamada:** `app.api.ask` chama `orchestrator.route_question(question)` para obter payload `results` e `meta`.
- **Entradas/Saídas:** entrada pergunta e flag `explain`; saída dict com `status`, `results`, `meta` consolidado.

### `app/cache`
- **Responsabilidade:** abstrair Redis (`RedisCache`) e políticas YAML (`CachePolicies`). Implementa `read_through` com métricas e limpeza legada.
- **Fluxo de chamada:** `app.api.ask` usa `read_through`; `Orchestrator` usa cache diretamente para métricas (set/get JSON).
- **Entradas/Saídas:** entrada identificadores, função `fetch_fn`; saída dict `{"cached": bool, "value": Any, ...}`.

### `app/rag`
- **Responsabilidade:** leitura de índices de embeddings e geração de hints para o planner. `OllamaClient` produz embeddings, `hints.py` consolida pontuações por entidade.
- **Fluxo de chamada:** `Planner` consulta `cached_embedding_store` e `entity_hints_from_rag` quando RAG está habilitado.
- **Entradas/Saídas:** entrada vetor ou texto; saída lista de candidatos com score e hints agregados.

### `app/analytics`
- **Responsabilidade:** gerar payloads de explainability e sumarizar métricas. `explain.py` agrega dados determinísticos para auditoria; `repository.py` consulta `explain_events` no banco.
- **Fluxo de chamada:** `app.api.ask` e `Orchestrator` chamam `analytics.explain.explain` quando `explain=True`; rotas `/ops/analytics` usam `repository`.
- **Entradas/Saídas:** entrada IDs de request + snapshots; saída dicts com `summary`, `details`, `events`/`kpis`.

### `app/observability`
- **Responsabilidade:** padronizar métricas, tracing OTLP e registradores Prometheus. Exposto via `runtime.bootstrap`, `init_*` e funções `counter/histogram/trace`.
- **Fluxo de chamada:** todos os módulos críticos emitem métricas através da façade de instrumentation.
- **Entradas/Saídas:** entrada configurações YAML de observabilidade; saída inicialização de backends e operações de telemetria.

### `app/utils`
- **Responsabilidade:** utilidades compartilhadas (`filecache` para YAML/JSONL com memoização; helpers de hot reload via `core.hotreload`).
- **Fluxo de chamada:** Planner, Narrator, Builder reutilizam `load_yaml_cached` e `cached_embedding_store`.
- **Entradas/Saídas:** entrada caminho de arquivo; saída dados parseados e caches em memória.

### `data/*`
- **Responsabilidade:** contratos declarativos consumidos em runtime (ontologia, políticas de cache, thresholds, entidades, dashboards de qualidade).
- **Fluxo de chamada:** Planner lê `data/ontology/entity.yaml`; Builder e Formatter dependem de `data/entities/<entity>/<entity>.yaml`; Param inference consome `data/ops/param_inference.yaml`.
- **Entradas/Saídas:** arquivos YAML/JSON utilizados como fonte de verdade.
