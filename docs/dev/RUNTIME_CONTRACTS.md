# Araquem — Contratos de Dados em Runtime

## 1. Payload `/ask`
- **Definição:** `AskPayload` em `app/api/ask.py` (Pydantic).
- **Campos obrigatórios:**
  - `question: str`
  - `conversation_id: str`
  - `nickname: str`
  - `client_id: str`
- **Validação:** Pydantic garante tipos básicos; sanitização adicional ocorre via `json_sanitize` antes de responder.

## 2. Estrutura da resposta `/ask`
- **Formato base:** dict com chaves `status`, `results`, `meta`, `answer`.
- **`status`:** `{ "reason": str, "message": str }`. Razões conhecidas: `ok`, `unroutable`, `gated`.
- **`results`:** dict `{ result_key: List[Dict[str, Any]] }`. `result_key` vem de `data/entities/<entity>/entity.yaml`.
- **`meta`:**
  - `planner`: saída completa do planner (ver abaixo).
  - `result_key`, `planner_intent`, `planner_entity`, `planner_score`.
  - `rows_total`: número de linhas após formatter.
  - `elapsed_ms`: latência total desde início do endpoint.
  - `aggregates`: dict com parâmetros inferidos (`agg`, `window`, `limit`, `order`).
  - `cache`: `{ "hit": bool, "key": str|None, "ttl": int|None }` (quando `read_through` executa) ou `{ "hit": bool, "key": key|None, "ttl": ttl|Any }` vindo do orchestrator.
  - `narrator`: `{ "enabled": bool, "shadow": bool, "model": str, "latency_ms": float|None, "used": bool, "strategy": str, "error": str|None, "score": float|None }`.
  - `explain`: apenas quando `?explain=true`; replica `plan['explain']`.
  - `explain_analytics`: payload retornado por `app.analytics.explain.explain` quando explain ativo.
- **`answer`:** string renderizada (Narrator se ativo; caso contrário `render_answer`).

## 3. Planner (`Planner.explain`)
- **Entrada:** `question: str`.
- **Saída:** dict com chaves principais:
  - `chosen`: `{ "intent": str|None, "entity": str|None, "score": float|None }`.
  - `explain`: `{ "decision_path": List[Dict], "scoring": { ... }, "combined_intents": [...], "combined_entities": [...], "thresholds_applied": {...} }`.
  - `rag`: quando habilitado, inclui `used`, `results`, `entity_hints`.
  - `config`: thresholds aplicados (`planner.thresholds`), flags de RAG.
- **Validação:** sem Pydantic; estrutura construída manualmente e consumida diretamente pelo endpoint e orchestrator.

## 4. Inferência de parâmetros (`infer_params`)
- **Entrada:** pergunta, intent, entity opcional, caminhos YAML.
- **Saída:** dict com subset de chaves `agg`, `window`, `limit`, `order`. Pode retornar valores `None` quando regra não aplica.
- **Uso:**
  - Em `app/api.ask` para compor `facts['aggregates']` do Narrator e para métricas (`cache_identifiers`).
  - Em `Orchestrator` para guiar o builder e formação de chave de cache.

## 5. Orchestrator (`route_question`)
- **Entrada:** `question: str`, `explain: bool`.
- **Saída:**
  ```python
  {
      "status": {"reason": "ok|unroutable|gated", "message": str},
      "results": {result_key: List[Dict[str, Any]]},
      "meta": {
          "planner": plan,
          "result_key": str|None,
          "planner_intent": str|None,
          "planner_entity": str|None,
          "planner_score": float|None,
          "rows_total": int,
          "elapsed_ms": int,
          "gate": {"blocked": bool, "reason": str|None, "min_score": float, "min_gap": float, "top2_gap": float},
          "aggregates": Dict[str, Any],
          "explain": plan["explain"]|None,
          "explain_analytics": Dict|None,
      },
  }
  ```
- **Cache interno para métricas:** quando `metrics_cache_hit=True`, injeta `meta['cache_context']` implícito via `metrics_cache_key`, `ttl`.

## 6. Builder (`build_select_for_entity`)
- **Entrada:** `entity: str`, `identifiers: Dict[str, Any]`, `agg_params: Dict[str, Any]`.
- **Saída:** tuple `(sql: str, params: Dict[str, Any], result_key: str, return_columns: List[str])`.
- **Dependências declarativas:**
  - `entity.yaml` deve conter `result_key`, `sql_view`, `columns`, `identifiers`, `presentation`, `aggregations`.
  - Quando `agg_params['agg'] == 'metrics'`, espera-se bloco `metrics` com `query`, `columns`, `placeholders`.

## 7. Executor (`PgExecutor.query`)
- **Entrada:** SQL e params.
- **Saída:** `List[Dict[str, Any]]` com colunas definidas pelo SELECT. Cada row pode conter sub-dict `meta` (ex: métricas) utilizado pelo formatter.
- **Erros:** exceções `psycopg.Error` propagadas para orchestrator.

## 8. Formatter
- **`format_rows(rows, columns)`** → `List[Dict[str, Any]]` mantendo somente colunas declaradas.
- **`render_rows_template(entity, rows)`** → `str` (Markdown) ou `""` se template inexistente.
- **Dependência:** `entity.yaml` → `presentation.kind`, `presentation.fields.key/value`, template Jinja2 em `responses/`.

## 9. Cache (`read_through`)
- **Entrada:** cache Redis, políticas, entity, identificadores, função fetch.
- **Saída:** `{ "cached": bool, "value": Any, "key": str|None, "ttl": int|None }`.
- **Guardrails:** ignora políticas ausentes; evita cache quando `fetch_fn` retorna payload considerado vazio (`_is_empty_payload`).

## 10. Narrator
- **`Narrator.render(question, facts, meta)`** → dict:
  ```python
  {
      "text": str,
      "score": float,
      "hints": {"style": str},
      "tokens": {"in": int, "out": int},
      "latency_ms": float,
      "error": str|None,
      "enabled": bool,
      "shadow": bool,
  }
  ```
- **Entrada `facts`:**
  - `rows`, `primary`, `result_key`, `aggregates`, `identifiers`, `ticker`, `fund` (derivado de rows/identifiers).
  - `meta`: `intent`, `entity`, `explain` opcional.
- **Fallback:** se Narrator indisponível/desabilitado, retorna baseline `text` com score 1.0 (se houver texto) e `error` indicando motivo.

## 11. Explain Analytics (`app.analytics.explain.explain`)
- **Entrada:**
  - `request_id: str`
  - `planner_output: Dict`
  - `metrics: Dict` (latência, cache_hit, route_source)
- **Saída:**
  ```python
  {
      "request_id": str,
      "timestamp": ISO8601,
      "summary": str,
      "details": {
          "intent": str|None,
          "entity": str|None,
          "view": str|None,
          "route_id": str,
          "cache_hit": bool|None,
          "latency_ms": float|None,
          "route_source": str|None,
          "notes": str|None,
      }
  }
  ```
- **Persistência:** endpoint `/ask` opcionalmente insere linha em `explain_events` com `request_id`, `question`, `intent`, `entity`, `route_id`, `features` JSON.

## 12. Rotas operacionais relevantes
- `/ops/cache/bust`: body `{ "entity": str, "identifiers": Dict[str, Any] }`; exige header `X-Ops-Token`.
- `/ops/analytics/explain`: GET/POST aceita filtros (`window`, `intent`, `entity`, `route_id`, `cache_hit`) e retorna resumo ou lista de eventos.
- `/metrics`: resposta Prometheus plain text (`render_prometheus_latest`).

## 13. Elementos persistidos em Redis/Postgres
- **Redis:** chave `araquem:{build_id}:{scope}:{entity}:{hash(identifiers)}` armazenando `{ "result_key": str, "rows": List[Dict] }`.
- **Postgres:** tabela `explain_events` com colunas (`request_id`, `question`, `intent`, `entity`, `route_id`, `features` JSONB, `sql_view`, `sql_hash`, `cache_policy`, `latency_ms`). Inserida no endpoint quando `explain=True`.
