# `/ask` e `/ask?explain=true`

O contrato `/ask` é imutável desde Guardrails v2.1.1. O endpoint aceita apenas `POST` com payload JSON validado por `AskPayload` (`question`, `conversation_id`, `nickname`, `client_id`).【F:app/api/ask.py†L18-L57】

## Requisição

```http
POST /ask?explain=true HTTP/1.1
Content-Type: application/json

{
  "question": "Quais foram os dividendos do MXRF11 nos últimos 6 meses?",
  "conversation_id": "conv-9f2c",
  "nickname": "analyst.bot",
  "client_id": "arena"
}
```

## Resposta

```json
{
  "status": {"reason": "ok", "message": "ok"},
  "results": {
    "dividendos_fii": [
      {
        "ticker": "MXRF11",
        "payment_date": "2025-10-15",
        "value": 0.12,
        "window_months": 6
      }
    ]
  },
  "meta": {
    "planner": {"chosen": {"intent": "dividendos", "entity": "fiis_dividendos"}},
    "result_key": "dividendos_fii",
    "planner_intent": "dividendos",
    "planner_entity": "fiis_dividendos",
    "planner_score": 3.5,
    "rows_total": 1,
    "elapsed_ms": 180,
    "explain": {
      "scoring": {
        "intent_top2_gap": 1.8,
        "thresholds_applied": {"gap": 1.8, "min_gap": 0.2}
      }
    },
    "explain_analytics": {
      "summary": {
        "route_id": "dividendos_fii",
        "cache_hit": false
      }
    },
    "cache": {
      "hit": false,
      "key": "araquem:dev:pub:fiis_dividendos:<hash>",
      "ttl": 86400
    },
    "aggregates": {
      "agg": "list",
      "window": "months:6"
    },
    "rendered_response": "O MXRF11 distribuiu 0.12 em 15/10/2025 (janela de 6 meses)."
  },
  "answer": "O MXRF11 distribuiu R$ 0,12 por cota nos últimos 6 meses."
}
```

> Valores numéricos são ilustrativos; a estrutura reflete exatamente os campos retornados por `app/orchestrator/routing.py` e `render_answer` ao longo do pipeline.【F:app/orchestrator/routing.py†L140-L220】【F:app/api/ask.py†L58-L220】

## Comportamentos relevantes

- **Cache read-through**: quando a política (`data/policies/cache.yaml`) define `ttl_seconds`, o orchestrator usa `read_through` e inclui `meta.cache` com chave derivada de `identifiers` + agregados. Políticas privadas (`client_fiis_positions`) usam `scope: prv` e TTL de 900 segundos.【F:app/api/ask.py†L90-L150】【F:data/policies/cache.yaml†L9-L36】
- **Inferência de agregados**: `meta.aggregates` carrega saídas de `infer_params`, sempre calculadas a partir de `data/ops/param_inference.yaml`. Nenhum parâmetro adicional é aceito via payload.【F:app/api/ask.py†L70-L110】【F:data/ops/param_inference.yaml†L9-L73】
- **Explicabilidade**: `explain=true` adiciona `explain` (árvore de decisão do planner) e `explain_analytics` (payload pronto para persistência em `explain_events`). Erros de persistência são tolerados mas registram `sirios_explain_events_failed_total`.【F:app/api/ask.py†L150-L220】

Não há variante WebSocket (`/ws`); o contrato segue exclusivamente HTTP.
