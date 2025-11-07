# RAG Overview

O Retrieval-Augmented Generation do Araquem reforça o planner com hints semânticos mantidos em `data/embeddings/store/`.

## Estrutura do índice

- **Manifesto**: `data/embeddings/store/manifest.json` descreve versão e metadados.
- **Embeddings**: `data/embeddings/store/embeddings.jsonl` é consumido via `cached_embedding_store` no planner.【F:app/planner/planner.py†L200-L230】
- **Index.yaml**: controla fonte de verdade e pesos (`weight: 0.25`, `min_score: 0.20`) e inclui contratos YAML/quality como documentos semânticos.【F:data/embeddings/index.yaml†L1-L86】

## Políticas

- `data/ops/planner_thresholds.yaml` habilita RAG (`enabled: true`, `k: 5`, `weight: 0.35`) com re-rank desativado (`re_rank.enabled: false`).【F:data/ops/planner_thresholds.yaml†L26-L35】
- `data/policies/rag.yaml` define perfis (`default`, `ambiguous`) com pesos BM25×semantic (`0.70/0.30`), `min_score` e `k` ajustados para cenários ambíguos.【F:data/policies/rag.yaml†L1-L16】

## Fluxo no planner

1. A pergunta é embutida via `OllamaClient` (`app/rag/ollama_client.py`).
2. `cached_embedding_store` busca top-`k` documentos acima de `min_score`.
3. `entity_hints_from_rag` agrega scores por entidade, retornando mapa `entity -> weight`.
4. A fusão linear aplica `fusion_weight = 0.35` (já que re-rank está desligado), ajustando o score final antes do cálculo do gap top2.【F:app/planner/planner.py†L200-L320】

## Scripts relacionados

- `scripts/embeddings/embeddings_build.py`: reconstroi embeddings a partir de `data/embeddings/index.yaml`.
- `scripts/embeddings/rag_retrieval_eval.py`: roda avaliação offline e registra métricas (`rag_eval_*`).
- `scripts/core/audit_repo.py`: valida referências a caminhos do índice.

## Observabilidade

- Métricas: `sirios_rag_search_total` (contagem de buscas) e gauges `rag_index_size_total`, `rag_index_docs_total`, `rag_index_density_score`, `rag_eval_*` são atualizados via `/ops/metrics/rag/register` e `/ops/metrics/rag/eval`.【F:app/observability/metrics.py†L40-L120】【F:app/api/ops/metrics.py†L1-L140】
- Dashboards Grafana (`grafana/dashboards/20_planner_rag_intelligence.json`) exibem densidade e recall.

## Estado atual

- **Blend ativo com re-rank desabilitado**: o planner usa apenas fusão linear; nenhum re-rank externo está ativo.
- **Documentos obrigatórios**: `required_entity_doc: true` garante que cada entidade mantenha contrato no índice antes de habilitar RAG para ela.【F:data/embeddings/index.yaml†L7-L20】
