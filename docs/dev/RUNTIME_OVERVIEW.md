# Araquem — Contratos de Dados em Runtime

## 1. Payload `/ask`
- **Definição:** `AskPayload` em `app/api/ask.py` (Pydantic).
- **Campos obrigatórios:** `question`, `conversation_id`, `nickname`, `client_id`.
- **Validação:** Pydantic + sanitização final via `json_sanitize` antes de responder.

## 2. Estrutura canônica do payload de resposta do `/ask`
- **Formato base:** dict com chaves `status`, `results`, `meta`, `answer`.
- **`status`:** `{ "reason": str, "message": str }` com motivos conhecidos `ok`, `unroutable`, `gated`.
- **`results`:** `{ result_key: List[Dict[str, Any]] }` onde `result_key` vem do `entity.yaml` usado pelo builder.
- **`answer`:** texto final decidido pela camada Presenter (`present`). Usa Narrator quando habilitado; caso contrário mantém o baseline determinístico (`render_answer`).
- **`meta` (origens principais):**
  - `planner` (planner.explain em `app/api/ask.py` e `route_question`).
  - `result_key`, `planner_intent`, `planner_entity`, `planner_score`, `rows_total`, `elapsed_ms` (endpoint).
  - `gate` (thresholds aplicados) e `aggregates` (inferência de parâmetros) vindos de `route_question` (`app/orchestrator/routing.py`).
  - `requested_metrics` derivado de `ask.metrics_synonyms` do `entity.yaml` dentro do orchestrator.
  - `cache` (hit/miss, key, ttl) construído no endpoint a partir de `read_through` ou da política explícita.
  - `rag` (contexto de RAG) montado pelo orchestrator via `rag.context_builder.build_context` e nunca sobrescrito no Presenter.
  - `narrator` (estado e telemetria) produzido pelo **Narrator** (`Narrator.render`) e
    propagado pelo Presenter (`app/presenter/presenter.py`) para `meta['narrator']`.
  - `explain` (quando `?explain=true`) = `plan['explain']`.
  - `explain_analytics` (quando `?explain=true`) produzido por `app.analytics.explain.explain` tanto no orchestrator quanto no endpoint.

## 3. Fluxo `/ask` end-to-end (caminho da pergunta até a resposta)

1) **Entrada HTTP** — `app/api/ask.py` (`ask`)
   - Gera `request_id`, chama `planner.explain(question)` e registra métricas (`sirios_planner_*`).
   - Em caso de ausência de entidade, responde `unroutable` já com `meta.planner` e `explain` (quando solicitado).

2) **Planner** — `app/planner/planner.py` (`Planner.explain`)
   - Normaliza pergunta, pontua intents/entities com ontologia (`data/ontology/entity.yaml`) e thresholds (`data/ops/planner_thresholds.yaml`).
   - Retorna `plan = {"chosen": {intent, entity, score}, "explain": {...}}` com `decision_path`, `scoring`, `thresholds_applied` e blocos de RAG/hints quando configurados.

3) **Param inference** — `app/planner/param_inference.py` (`infer_params`)
   - Rodado no endpoint e no orchestrator. Usa `param_inference.yaml` + `entity.yaml` para inferir `agg`, `window`, `limit`, `order`, `metric` e normalizar janela temporal.

4) **Orchestrator** — `app/orchestrator/routing.py` (`route_question`)
   - Reexecuta `Planner.explain` (para gate interno) e aplica thresholds YAML (`min_score`, `min_gap`) em `gate`.
   - Extrai identificadores (`extract_identifiers`) com regex de ticker, resolve `requested_metrics` via `ask.metrics_synonyms`.
   - Prepara contexto de cache de métricas (`_prepare_metrics_cache_context`) e tenta hit Redis (`metrics_cache_hit`).
   - Em miss: monta SQL com `builder.build_select_for_entity`, executa `PgExecutor.query`, formata linhas com `formatter.format_rows` e grava cache se elegível.
   - Constrói `meta` parcial: `planner`, `result_key`, `planner_intent`, `planner_entity`, `planner_score`, `rows_total`, `elapsed_ms`, `gate`, `aggregates`, `requested_metrics`, `explain`/`explain_analytics` quando solicitado.
   - Sempre preenche o contexto canônico `meta['rag']` usando `rag.context_builder.build_context` (ou fallback com erro capturado) e retorna `{status, results, meta}`.

5) **Presenter** — `app/presenter/presenter.py` (`present`)
   - Recebe `plan`, `results` e `meta` do orchestrator, além de `identifiers` e `aggregates` calculados no endpoint.
   - Constrói `facts` (`build_facts`) com `result_key`, `rows`, `primary`, `identifiers`, `aggregates`, `requested_metrics`, `ticker`/`fund` e score do planner.
   - Gera baseline determinístico via `render_answer` + `render_rows_template`.
   - Monta um `narrator_rag_context` usando `rag.context_builder.build_context` com a política carregada (`load_rag_policy`) **apenas para consumo interno do Narrator**; `meta['rag']` continua sendo o valor recebido do Orchestrator.
   - Aciona Narrator (quando presente e habilitado) para gerar texto LLM ou shadow; preenche `narrator_meta` com `enabled`, `shadow`, `model`, `latency_ms`, `error`, `used`, `strategy`, `score`, além de `rag` (interno).
   - Decide `answer` final (`Narrator` quando `enabled`, caso contrário baseline) e devolve `PresentResult` para o endpoint.

6) **Resposta HTTP** — `app/api/ask.py`
   - Monta payload final com `status`, `results` (direto do orchestrator), `meta` (endpoint + presenter) e `answer` (Presenter).
   - Em `?explain=true`, gera `explain_analytics` e insere registros em `explain_events` e `narrator_events` no Postgres (best-effort).
   - Sanitiza JSON e responde via `JSONResponse`.

## 4. Campos de `meta` e origem
- **`meta.planner`** — retorno bruto de `Planner.explain` (endpoint e orchestrator).
- **`meta.gate`** — thresholds aplicados em `route_question` (`min_score`, `min_gap`, `top2_gap`, `blocked`, `reason`).
- **`meta.result_key` / `meta.rows_total` / `meta.aggregates` / `meta.requested_metrics`** — montados no orchestrator após formatter e inferência (`extract_requested_metrics`).
- **`meta.cache`** — endpoint (`read_through` ou fallback manual) com `{hit, key, ttl}` a partir do resultado do cache/política.
- **`meta.explain`** — opcional (`plan['explain']`) propagado pelo endpoint e pelo orchestrator quando `explain=True`.
- **`meta.explain_analytics`** — produzido por `app.analytics.explain.explain` tanto no orchestrator quanto no endpoint (latência, cache_hit, route_source, route_id).
- **`meta.rag`** — contexto de RAG construído em `route_question` via `rag.context_builder.build_context` (aplica `data/policies/rag.yaml`, collections, chunks, flags `enabled`/`error`).
- **`meta.narrator`** — preenchido pelo Presenter/Narrator (`present` + `Narrator.render`): `{enabled, shadow, model, latency_ms, error, used, strategy, score, rag}`.
- **`meta.requested_metrics`** — lista inferida pelo orchestrator (ask.metrics_synonyms) replicada no endpoint.
- **`meta.elapsed_ms`** — latência end-to-end do endpoint (`ask`).

## 5. Componentes do pipeline
- **Planner (`app/planner/planner.py`)** — decide intent/entity e expõe `plan['explain']` com `decision_path`, `scoring`, `thresholds_applied`, `rag`/`hints` quando habilitados.
- **Param inference (`app/planner/param_inference.py`)** — usa `param_inference.yaml` + `entity.yaml` para campos `agg`, `window`, `limit`, `order`, `metric`, `window_months`/`period_start`/`period_end`.
- **Orchestrator (`app/orchestrator/routing.py`)** — aplica gate, cache de métricas, chama builder/executor/formatter, injeta `meta.rag`, `requested_metrics`, `explain_analytics`.
- **Builder (`app/builder/sql_builder.py`)** — monta `(sql, params, result_key, return_columns)` com base em `entity.yaml` (`columns`, `sql_view`, `aggregations`, `metrics`).
- **Executor (`app/executor/pg.py`)** — executa SQL com `psycopg`, emite métricas `sirios_sql_*` e retorna `List[Dict]`.
- **Formatter (`app/formatter/rows.py`)** — `format_rows` mantém colunas declaradas e aplica formatadores; `render_rows_template` gera Markdown a partir de `responses/*.md.j2` conforme `presentation` do YAML.
- **Presenter (`app/presenter/presenter.py`)** — consolida facts, baseline (`render_answer` + template), constrói `narrator_meta` e seleciona `answer` final.
- **Narrator (`app/narrator/narrator.py`, `app/narrator/prompts.py`)** — renderer opcional; aplica policy de narrador (env + entidade) e retorna texto/telemetria, incluindo shadow mode.
- **RAG (`app/rag/context_builder.py`)** — monta contexto determinístico com `enabled`, `used_collections`, `chunks`, `total_chunks`, `policy` mínima.
- **Explain Analytics (`app/analytics/explain.py`)** — gera snapshot `{summary, details{intent, entity, view, route_id, cache_hit, latency_ms, route_source}}` para uso interno e persistência best-effort em `explain_events`.

## 6. Diagrama sequencial (texto)
```
Usuário → /ask (ask.py) → planner.explain
/ask → orchestrator.route_question → {gate, cache?, builder → executor → formatter, rag_context}
Orchestrator → /ask: {status, results, meta}
/ask → presenter.present → {facts, baseline, narrator_meta, answer}
Presenter → Narrator (opcional, shadow/enable)
/ask → usuário: {status, results, meta{planner, gate, aggregates, rag, narrator, cache, explain*}, answer}
```

## 7. Contratos e acoplamentos
- `result_key` vem do `entity.yaml` e é usado por orchestrator, presenter e Narrator; também compõe o cache de métricas.
- `rows` seguem as colunas de `entity.yaml`/`return_columns`; formatter remove qualquer coluna fora do contrato.
- `facts` do Presenter dependem de `plan['chosen']`, `aggregates`, `identifiers`, `requested_metrics` e do resultado formatado.
- `rag_context` é determinístico; Narrator pode optar por usar ou ignorar conforme policy (`use_rag_in_prompt`).
- `meta.narrator` é sempre preenchido (mesmo sem Narrator ativo) para garantir auditabilidade.

# Araquem — Fluxo de Execução End-to-End

## Visão Geral
```
Cliente → FastAPI /ask → Planner.explain → Orchestrator.route_question →
  ├─ (cache de métricas | políticas)
  ├─ Builder.build_select_for_entity → PgExecutor.query
  ├─ Formatter.format_rows + render_rows_template
  └─ Presenter.present (Responder + Narrator) → JSONResponse
```

O pipeline acima representa o fluxo real observado nos módulos `app/api/ask.py`,
`app/orchestrator/routing.py`, `app/builder/sql_builder.py`, `app/executor/pg.py`,
`app/formatter/rows.py`, `app/presenter/presenter.py` e `app/narrator/*`.
Cada etapa opera sobre contratos determinísticos impostos por YAML, ontologia e Pydantic.

## Sequência detalhada (estilo UML textual)
```
AskEndpoint -> Planner: explain(question)
Planner --> AskEndpoint: plan{chosen.intent, chosen.entity, explain}
AskEndpoint -> Orchestrator: route_question(question)
Orchestrator -> Planner: explain(question)
Planner --> Orchestrator: plan
Orchestrator -> CachePolicies: build cache context (metrics)
Orchestrator -> RedisCache: get_json(key?)
RedisCache --> Orchestrator: cached payload | None
Orchestrator -> Builder: build_select_for_entity(entity, identifiers, agg_params)
Builder --> Orchestrator: (sql, params, result_key, return_columns)
Orchestrator -> PgExecutor: query(sql, params)
PgExecutor --> Orchestrator: rows_raw[List[Dict]]
Orchestrator -> Formatter: format_rows(rows_raw, return_columns)
Formatter --> Orchestrator: rows_formatted
Orchestrator -> RedisCache: set_json(key, rows_formatted) [quando elegível]
Orchestrator --> AskEndpoint: {status, results{result_key: rows_formatted}, meta{planner,..., rag}}
AskEndpoint -> Presenter: present(plan, results, meta, identifiers, aggregates)
Presenter -> Responder: render_answer(...)
Presenter -> Formatter: render_rows_template(...)
Presenter -> Narrator?: render(question, facts, meta_for_narrator)
Narrator --> Presenter: narrator_info{text?, latency_ms, score, strategy}
Presenter --> AskEndpoint: PresentResult{answer, narrator_meta, facts}
AskEndpoint --> Client: JSONResponse{status, results, meta{..., narrator}, answer}
```
