# Auditoria E2E de Perguntas Conceituais — Concepts RAG Path

## 0) Inventário rápido (mapa de arquivos e pontos de entrada)

| Componente | Arquivo | Função principal | Como é acionado |
| --- | --- | --- | --- |
| Routing / Planner | `app/planner/planner.py` | `Planner.explain` normaliza a pergunta, tokeniza e escolhe intent/entity. | Chamada pelo `/ask` via `planner.explain` antes do roteamento, e também pela camada de orquestração. |【F:app/planner/planner.py†L406-L457】
| Routing / Orchestrator | `app/orchestrator/routing.py` | `route_question` monta o payload, define `meta` e injeta o contexto RAG canônico. | `/ask` chama `orchestrator.route_question`, que retorna `results` + `meta` para a apresentação. |【F:app/orchestrator/routing.py†L1020-L1081】
| RAG retrieval / hint selection | `app/rag/context_builder.py` + `app/rag/index_reader.py` | `build_context` resolve policy, busca embeddings com `EmbeddingStore.search_by_vector`. | Invocado pelo orchestrator para montar `meta["rag"]`. |【F:app/rag/context_builder.py†L435-L610】【F:app/rag/index_reader.py†L33-L75】
| Entity hints (prefixo `entity-`) | `app/rag/hints.py` | `entity_hints_from_rag` agrega scores de doc_id com prefixo `entity-`. | Usado em fluxos de hints; não considera docs `concepts-*`. |【F:app/rag/hints.py†L7-L23】
| Context Manager (histórico) | `app/presenter/presenter.py` | `present` carrega histórico via `context_manager` e envia no `meta` do Narrator. | `present` é chamado no `/ask` para montar resposta final. |【F:app/presenter/presenter.py†L397-L405】
| Narrator/Presenter (montagem de resposta) | `app/presenter/presenter.py` + `app/narrator/prompts.py` | `present` injeta `rag` no `meta` do Narrator; `_prepare_rag_payload` serializa chunks para o prompt. | `present` chama `narrator.render`, que usa `prompts.build_prompt`. |【F:app/presenter/presenter.py†L352-L377】【F:app/narrator/prompts.py†L169-L237】【F:app/narrator/prompts.py†L362-L411】

## 1) Evidências do store (concepts presentes e campo `entity`)

A partir de `data/embeddings/store/embeddings.jsonl`:

- Existem `doc_id` iniciando com `concepts-`.
- O campo `entity` está `null` nesses registros.
- As `tags` incluem a tag `concepts`.

Exemplo (10 linhas, com `doc_id`, `tags`, `entity`, `chunk_id`):

```
1  concepts-catalog  tags=[concepts, catalog, fiis, domain:concepts_fiis]  entity=null  chunk_id=concepts-catalog:0
2  concepts-catalog  tags=[concepts, catalog, fiis, domain:concepts_fiis]  entity=null  chunk_id=concepts-catalog:1
3  concepts-catalog  tags=[concepts, catalog, fiis, domain:concepts_fiis]  entity=null  chunk_id=concepts-catalog:2
4  concepts-catalog  tags=[concepts, catalog, fiis, domain:concepts_fiis]  entity=null  chunk_id=concepts-catalog:3
5  concepts-fiis     tags=[concepts, fiis, domain:concepts_fiis]          entity=null  chunk_id=concepts-fiis:0
6  concepts-fiis     tags=[concepts, fiis, domain:concepts_fiis]          entity=null  chunk_id=concepts-fiis:1
7  concepts-fiis     tags=[concepts, fiis, domain:concepts_fiis]          entity=null  chunk_id=concepts-fiis:2
8  concepts-fiis     tags=[concepts, fiis, domain:concepts_fiis]          entity=null  chunk_id=concepts-fiis:3
9  concepts-fiis     tags=[concepts, fiis, domain:concepts_fiis]          entity=null  chunk_id=concepts-fiis:4
10 concepts-fiis     tags=[concepts, fiis, domain:concepts_fiis]          entity=null  chunk_id=concepts-fiis:5
```

Evidência direta no JSONL (linhas 1–10).【F:data/embeddings/store/embeddings.jsonl†L1-L10】

## 2) Auditoria de filtros de elegibilidade (onde concepts podem ser descartados)

1) **Config declarativa (não consumida em runtime):**
   - `data/embeddings/index.yaml` define `hint_filters.allowlist/denylist` e `required_entity_doc: true`, mas não há uso desses flags em runtime (somente a presença declarativa no index).【F:data/embeddings/index.yaml†L9-L15】
   - **Impacto:** neste repositório, esses filtros não são aplicados em `build_context`/`search` e, portanto, não filtram concepts em runtime.

2) **Prefixo de entidade só quando tag `entity:*` existe (build do índice):**
   - Durante `embeddings_build`, o `doc_id` só recebe prefixo `entity-` quando `_extract_entity_from_tags` acha uma tag de entidade; caso contrário permanece `concepts-*`, com `entity=None`.【F:scripts/embeddings/embeddings_build.py†L181-L203】
   - **Impacto:** docs `concepts-*` não recebem prefixo `entity-` e ficam com `entity=None`.

3) **Hints por prefixo `entity-` ignoram concepts:**
   - `entity_hints_from_rag` só agrega hints quando `doc_id` inicia com `entity-` (regex), descartando docs `concepts-*`.【F:app/rag/hints.py†L7-L22】
   - **Impacto:** mesmo se concepts forem recuperados pelo RAG, eles não contribuem para hints de entidade via `entity_hints_from_rag`.

4) **Policy RAG bloqueia intents (denylist):**
   - `get_rag_policy` retorna `enabled=False` quando `intent` está no `deny_intents` da policy.【F:app/rag/context_builder.py†L121-L131】
   - `data/policies/rag.yaml` contém `deny_intents` com intents comuns de FIIs (ex.: `fiis_dividends_yields`, `fiis_financials_snapshot`, etc.).【F:data/policies/rag.yaml†L29-L57】
   - **Impacto:** perguntas conceituais roteadas para intents negadas desabilitam o RAG com razão `intent_denied`.

## 3) Trace Report — execução E2E (Q1–Q4)

**Ambiente:** execução via `scripts/diagnostics/trace_concepts_flow.py` (FastAPI TestClient) com `RAG_TRACE=1`. A infraestrutura de Redis/Postgres/OTEL não estava disponível no ambiente de execução, portanto há warnings e erros de conexão nos logs (não afetam o payload para Q1–Q3, mas Q4 falhou na leitura de cache). O trace abaixo está sanitizado (sem textos de chunks).

### Q1 — "o que é dividend yield em fiis?"
```json
{
  "planner": {
    "chosen_intent": "fiis_dividends_yields",
    "chosen_entity": "fiis_dividends_yields",
    "chosen_score": 3.8499999999999996,
    "top2": [
      {"intent": "fiis_dividends_yields", "score": 3.8499999999999996},
      {"intent": "client_fiis_enriched_portfolio", "score": 0.55}
    ],
    "thresholds": {"min_score": 0.9, "min_gap": 0.2, "gap": 3.3, "accepted": true, "source": "base", "score_for_gate": 3.8499999999999996, "reason": null},
    "gate_source": "base"
  },
  "rag": {
    "enabled": false,
    "policy": {"enabled": false, "reason": "intent_denied", "mode": null, "collections": null, "max_chunks": null, "min_score": null},
    "chunks_total": 0,
    "chunks": []
  },
  "context_final": {"rows_total": 0, "rag_chunks": 0},
  "path": "no_data"
}
```

### Q2 — "como funciona vacancia fisica e vacancia financeira?"
```json
{
  "planner": {
    "chosen_intent": "fiis_financials_snapshot",
    "chosen_entity": "fiis_financials_snapshot",
    "chosen_score": 7.699999999999999,
    "top2": [
      {"intent": "fiis_financials_snapshot", "score": 7.699999999999999},
      {"intent": "fiis_real_estate", "score": 6.6}
    ],
    "thresholds": {"min_score": 1.0, "min_gap": 0.2, "gap": 1.0999999999999996, "accepted": true, "source": "base", "score_for_gate": 7.699999999999999, "reason": null},
    "gate_source": "base"
  },
  "rag": {
    "enabled": false,
    "policy": {"enabled": false, "reason": "intent_denied", "mode": null, "collections": null, "max_chunks": null, "min_score": null},
    "chunks_total": 0,
    "chunks": []
  },
  "context_final": {"rows_total": 0, "rag_chunks": 0},
  "path": "no_data"
}
```

### Q3 — "o que significa p/vp em fundos imobiliarios?"
```json
{
  "planner": {
    "chosen_intent": "fiis_financials_snapshot",
    "chosen_entity": "fiis_financials_snapshot",
    "chosen_score": 3.3,
    "top2": [
      {"intent": "fiis_financials_snapshot", "score": 3.3},
      {"intent": "fiis_dividends_yields", "score": 1.1}
    ],
    "thresholds": {"min_score": 1.0, "min_gap": 0.2, "gap": 2.1999999999999997, "accepted": true, "source": "base", "score_for_gate": 3.3, "reason": null},
    "gate_source": "base"
  },
  "rag": {
    "enabled": false,
    "policy": {"enabled": false, "reason": "intent_denied", "mode": null, "collections": null, "max_chunks": null, "min_score": null},
    "chunks_total": 0,
    "chunks": []
  },
  "context_final": {"rows_total": 0, "rag_chunks": 0},
  "path": "no_data"
}
```

### Q4 (controle SQL) — "quais foram os dividendos do HGLG11 no ultimo ano?"
```json
{
  "error": "Error -2 connecting to redis:6379. Name or service not known.",
  "question": "quais foram os dividendos do HGLG11 no ultimo ano?"
}
```

> Nota: o trace mostra o RAG desabilitado para Q1–Q3 com `reason=intent_denied`, que é coerente com o `deny_intents` de `rag.yaml`.【F:data/policies/rag.yaml†L29-L57】

## 4) Ponto de junção (SQL vs RAG) + diagrama

### Ponto exato de junção
1. **Orchestrator injeta RAG no meta** (`meta["rag"]`) após o roteamento/SQL. Esse objeto é o ponto onde a trilha SQL e a trilha RAG se encontram antes da apresentação final.【F:app/orchestrator/routing.py†L1023-L1081】
2. **Presenter repassa `meta["rag"]` ao Narrator** como `narrator_rag_context`, que depois é serializado no prompt via `_prepare_rag_payload` e incluído no bloco `Contexto auxiliar` do prompt.【F:app/presenter/presenter.py†L352-L377】【F:app/narrator/prompts.py†L169-L237】【F:app/narrator/prompts.py†L362-L411】

### Diagrama ASCII
```
/ask
  └─> planner.explain (Planner)
        └─> orchestrator.route_question
              ├─> SQL executor (se identifiers ok)
              ├─> build_rag_context (meta["rag"])
              └─> meta/results
                    └─> presenter.present
                          ├─> narrator_rag_context <- meta["rag"]
                          └─> narrator.prompts._prepare_rag_payload
                                └─> prompt final com Contexto auxiliar
```

## Conclusão

**Hipótese principal:**
- As perguntas conceituais estão sendo roteadas para intents de entidades SQL (`fiis_dividends_yields`, `fiis_financials_snapshot`), e o RAG fica **desabilitado** porque essas intents estão na denylist de `rag.yaml`, resultando em `reason=intent_denied` no snapshot de policy.【F:data/policies/rag.yaml†L29-L57】【F:app/rag/context_builder.py†L121-L131】

**Hipóteses alternativas (com evidências):**
1. **Mesmo que o RAG fosse habilitado, os docs `concepts-*` não geram hints de entidade** porque `entity_hints_from_rag` só considera doc_ids com prefixo `entity-`. Isso reduz o impacto de concepts na fase de hints/rota baseada em entidade.【F:app/rag/hints.py†L7-L22】【F:scripts/embeddings/embeddings_build.py†L181-L203】
2. **O prompt do Narrator pode descartar o contexto RAG** quando a policy efetiva não permite `use_rag_in_prompt`, já que `prompts.build_prompt` define `rag=None` se o flag estiver desligado.【F:app/narrator/prompts.py†L362-L372】

---

## How to run

1) Gerar o trace (usa TestClient e `RAG_TRACE=1`):
```
RAG_TRACE=1 python scripts/diagnostics/trace_concepts_flow.py
```

2) Gerar embeddings (se necessário para atualizar `data/embeddings/store`):
```
python scripts/embeddings/embeddings_build.py --index data/embeddings/index.yaml --out data/embeddings/store
```
