# Araquem — Fluxo de Execução End-to-End

## Visão Geral
```
Cliente → FastAPI /ask → Planner.explain → Orchestrator.route_question →
  ├─ (cache read_through | policies)
  ├─ Builder.build_select_for_entity → PgExecutor.query
  ├─ Formatter.format_rows + render_rows_template
  └─ Responder.render_answer / Narrator.render → JSONResponse
```

O pipeline acima representa o fluxo real observado nos módulos `app/api/ask.py`,
`app/orchestrator/routing.py`, `app/builder/sql_builder.py`, `app/executor/pg.py`
e `app/formatter/rows.py`. Cada etapa opera sobre contratos determinísticos
impostos por YAML e estruturas Pydantic.

## Sequência detalhada (estilo UML textual)
```
AskEndpoint -> Planner: explain(question)
Planner --> AskEndpoint: plan{chosen.intent, chosen.entity, explain}
AskEndpoint -> Orchestrator: route_question(question)
Orchestrator -> Planner: explain(question)
Planner --> Orchestrator: plan
Orchestrator -> CachePolicies: get(entity)
Orchestrator -> RedisCache: get_json(key?) [se política permitir]
RedisCache --> Orchestrator: cached payload | None
Orchestrator -> Builder: build_select_for_entity(entity, identifiers, agg_params)
Builder --> Orchestrator: (sql, params, result_key, return_columns)
Orchestrator -> PgExecutor: query(sql, params)
PgExecutor --> Orchestrator: rows_raw[List[Dict]]
Orchestrator -> Formatter: format_rows(rows_raw, return_columns)
Formatter --> Orchestrator: rows_formatted
Orchestrator -> RedisCache: set_json(key, rows_formatted) [quando elegível]
Orchestrator --> AskEndpoint: {
  status, results{result_key: rows_formatted}, meta{planner,...}
}
AskEndpoint -> Responder: render_answer(entity, rows, identifiers, aggregates)
Responder --> AskEndpoint: legacy_answer
AskEndpoint -> Formatter: render_rows_template(entity, rows)
Formatter --> AskEndpoint: rendered_response
AskEndpoint -> Narrator?: render(question, facts, meta) [shadow/enable]
Narrator --> AskEndpoint: narrator_info{ text?, latency_ms, score }
AskEndpoint --> Client: JSONResponse{
  status, results, meta{..., narrator}, answer
}
```

## Detalhamento por estágio

### 1. Entrada HTTP `/ask`
- **Payload:** `AskPayload(question, conversation_id, nickname, client_id)` via Pydantic.
- **Instrumentação:** gera `request_id`, registra métricas `sirios_planner_*`, `sirios_cache_ops_total`, `sirios_narrator_*`.
- **Decisões imediatas:** verifica `plan['chosen']`; se não houver entidade, responde `unroutable` com `planner` e `explain` na meta.

### 2. Planner (`Planner.explain`)
- **Entradas:** pergunta normalizada, ontologia YAML, thresholds de `data/ops/planner_thresholds.yaml`, sinais RAG (quando habilitado).
- **Saídas:**
  - `chosen.intent`, `chosen.entity`, `chosen.score`.
  - `explain` detalhado contendo `decision_path`, `scoring`, integração RAG, gaps base/final.
- **Consumo posterior:**
  - `app/api.ask` usa `intent`/`entity` para inferência de parâmetros e roteamento Narrator.
  - `Orchestrator` reavalia gates e compõe meta.

### 3. Inferência de parâmetros (`infer_params`)
- **Onde ocorre:** em `app/api.ask` (para camada Narrator/meta) e dentro de `Orchestrator` antes do builder.
- **Entradas:** texto da pergunta, `intent`, `entity`, `entity.yaml`, `param_inference.yaml`.
- **Saídas:** dict com chaves como `agg`, `window`, `limit`, `order`. Também usado para construir identificadores de cache.

### 4. Orchestrator (`route_question`)
- **Passos:**
  1. Reexecuta `planner.explain` para ter contexto interno e `gate` thresholds.
  2. Extrai identificadores (atualmente `ticker` via regex).
  3. Calcula `agg_params` com `infer_params`.
  4. Avalia política de cache (`CachePolicies`) para métricas e prepara chave determinística `make_cache_key`.
  5. Consulta cache (`RedisCache.get_json`). Se hit válido, reutiliza `rows` e `result_key`.
  6. Quando miss, chama builder + executor + formatter, e grava cache (`set_json`) se política permitir.
  7. Monta `results = {result_key: rows_formatted}` e `meta` consolidado (planner, gate, aggregates, elapsed_ms, explain optional).
  8. Gera payload explain analytics (`app.analytics.explain.explain`) se `explain=True`.

### 5. SQL Builder (`build_select_for_entity`)
- **Contratos:** lê `data/entities/<entity>/entity.yaml` para obter `result_key`, `columns`, `sql_view`, restrições de identificadores e blocos de agregação.
- **Saída:** SQL parametrizado e lista de colunas em ordem. Suporta modos `list`, `avg`, `sum`, `metrics`, `latest`, aplicando filtros de período/janela.
- **Acoplamentos:** exige que `entity.yaml` contenha `default_date_field` quando há filtros temporais.

### 6. Executor (`PgExecutor.query`)
- **Entrada:** SQL formatado e dict de parâmetros (com `entity` adicionado para métricas).
- **Processamento:** abre conexão `psycopg`, executa query com `dict_row`, coleta métricas `sirios_sql_*`, utiliza OTEL spans.
- **Saída:** lista de dicts com colunas definidas pelo builder.

### 7. Formatter (`format_rows`, `render_rows_template`)
- **Format Rows:** seleciona apenas colunas declaradas, aplica formatadores por sufixo (`_pct`, `_amt`, `_at`), trata métricas (`format_metric_value`).
- **Render Rows Template:** carrega `presentation` do `entity.yaml` e renderiza `responses/<kind>.md.j2` via Jinja2. Retorno string Markdown para UI atual.

### 8. Responder/Narrator
- **Responder:** lê `templates.md` (entidade ou legado) e cria texto fallback. Usa placeholders e fallback hierárquico.
- **Narrator:** opcional; recebe `facts` (rows, primary, aggregates, identifiers) e `meta` (intent, entity, explain?). Retorna texto e telemetria.
- **Decisão de resposta:**
  - `final_answer` = narrador quando `_NARRATOR_ENABLED` verdadeiro, caso contrário `legacy_answer`.
  - `meta['narrator']` sempre preenchido com estado de execução (enabled, shadow, latency, strategy).

### 9. Resposta HTTP
- **Estrutura:**
  ```json
  {
    "status": {"reason": "ok", "message": "ok"},
    "results": {"<result_key>": [ ... rows ... ]},
    "meta": {
      "planner": plan,
      "result_key": str,
      "planner_intent": str|None,
      "planner_entity": str|None,
      "planner_score": float|None,
      "rows_total": int,
      "elapsed_ms": int,
      "aggregates": agg_params,
      "explain": {...}?,
      "explain_analytics": {...}?,
      "cache": {"hit": bool, "key": str|None, "ttl": int|None},
      "narrator": {...}
    },
    "answer": str
  }
  ```

## Mensagens trocadas e objetos intermediários

| Origem → Destino | Objeto | Descrição |
| --- | --- | --- |
| Cliente → `/ask` | JSON `{question, conversation_id, nickname, client_id}` | Contrato Pydantic `AskPayload`. |
| Planner → API/Orchestrator | Dict `plan` | Inclui `chosen`, `explain`, `combined_intents/entities`. |
| Param inference → Orchestrator/API | Dict `agg_params` | Campos `agg`, `window`, `limit`, `order` usados no builder e cache key. |
| Orchestrator → Builder | `entity`, `identifiers`, `agg_params` | Base para montar SQL. |
| Builder → Orchestrator | `(sql, params, result_key, return_columns)` | Contrato rígido para executor/formatter. |
| Executor → Orchestrator | `rows_raw: List[Dict]` | Linhas Postgres com colunas + `meta`. |
| Formatter → Orchestrator | `rows_formatted: List[Dict]` | Linhas já normalizadas e strings amigáveis. |
| Orchestrator → Cache | `{"result_key": str, "rows": List[Dict]}` | Payload serializado em Redis. |
| Responder → API | `legacy_answer: str` | Texto baseado em templates legados. |
| Narrator → API | `{"text": str, "latency_ms": float, ...}` | Resultado LLM controlado. |

## Contratos implícitos relevantes
- `plan['chosen']['entity']` deve existir para seguir pipeline; ausência gera resposta `unroutable`.
- `result_key` proveniente do YAML é usado em `results` e no cache; qualquer alteração quebra `render_rows_template` e templates legados.
- `rows` devem manter dicionário com chaves correspondentes aos nomes declarados em `columns` do YAML.
- Narrator exige `facts['rows']` list e `meta['entity']`; caso contrário retorna fallback via `_default_text`.

## Decisão de roteamento por entidade
- Planner calcula scores baseados em tokens e frases (pesos `token`/`phrase`), aplica hints RAG opcionais, depois thresholds YAML (`min_score`, `min_gap`).
- Orchestrator reforça `gate`: se `score` < `min_score` ou `top2_gap` < `min_gap`, responde `gated` com `status.reason = 'gated'`.

## Montagem de SQL pelo executor
- Builder insere filtros de identificadores (`ticker`, etc.) com `%(name)s` para proteção contra injection.
- Janelas (`window_months`, `period_start/end`, `count:N`) convertem-se em cláusulas `BETWEEN` ou `LIMIT`/`ORDER BY`.
- Agregações `avg`/`sum` usam `GROUP BY` derivado do YAML e colunas literais com cast apropriado.

## Estruturação de `results`/`meta`
- `results`: dict de listas; chave = `result_key` da entidade.
- `meta`: soma de informações do planner, thresholds, cache, aggregates, explain analytics, narrador.
- Formatter adicional `render_rows_template` gera string para UI atual (armazenada separadamente em `rendered_response`, hoje não enviada para cliente).

## Pontos de acoplamento crítico
1. **Planner ↔ YAML da ontologia:** mudanças em `data/ontology/entity.yaml` alteram tokens e entidades; qualquer inconsistência quebra roteamento e thresholds.
2. **Builder ↔ entity.yaml:** campos `columns`, `sql_view`, `identifiers`, `presentation` são usados por builder, formatter, responder e narrador.
3. **Cache policies ↔ Orchestrator:** YAML determina chaves e TTL; erro impede reaproveitamento de métricas e influencia `meta.cache`.
4. **Narrator ↔ Formatter/Responder:** narrator utiliza `rows` formatadas e `legacy_answer` como fallback; mudanças em `render_rows_template` alteram baseline textual.
5. **Explain analytics ↔ Banco:** inserção em `explain_events` depende de tabela existente; falhas registradas apenas em métricas, mas dados se perdem.
