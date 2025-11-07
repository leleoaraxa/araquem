# RAG Evaluation

A avaliação de retrieval garante que o blend sem re-rank permaneça confiável.

## Datasets

- `data/ops/quality_experimental/rag_eval_set.json` — conjunto base.
- `data/ops/quality_experimental/rag_eval_last.json` — última execução registrada.
- `data/ops/quality_experimental/rag_search_basics.json` — cenários controlados.
- Projections adicionais (`projection_fiis_*`) validam consistência entity/doc-id para o índice.【F:data/ops/quality/projection_fiis_dividendos.json†L1-L20】

## Processo

1. Execute `python scripts/embeddings/rag_retrieval_eval.py --samples data/ops/quality_experimental/rag_eval_set.json`.
2. O script calcula métricas (`recall@5`, `recall@10`, `mrr`, `ndcg@10`) e atualiza os gauges via `register_rag_eval_metrics`.【F:scripts/embeddings/rag_retrieval_eval.py†L1-L200】【F:app/observability/metrics.py†L60-L120】
3. Opcional: publique os resultados chamando `POST /ops/metrics/rag/eval` com o payload produzido (ver `app/api/ops/metrics.py`).【F:app/api/ops/metrics.py†L80-L140】
4. Para rodar regressões completas, inclua `--refresh-index` para reconstruir embeddings conforme `data/embeddings/index.yaml`.

## Quality gates

`data/ops/planner_thresholds.yaml` define `rag.min_score` e peso; qualquer ajuste requer revalidação com os datasets acima.

`data/ops/observability.yaml` estabelece limites mínimos (`rag_eval_recall_at_5 >= 60%`, `rag_eval_ndcg_at_10 >= 0.60`); dashboards em `grafana/dashboards/20_planner_rag_intelligence.json` exibem histórico.【F:data/ops/observability.yaml†L1-L60】

## Automação

- `scripts/quality/quality_push.py` inclui etapas para validar RAG quando rodado com `--checks rag`. Ajuste caminhos após reorganização (`scripts/quality/*`).【F:scripts/quality/quality_push.py†L1-L200】
- Cronjobs (Docker/K8s) continuam apontando para os mesmos scripts (`docker/quality-cron.sh`, `k8s/quality/cronjob.yaml`).【F:docker/quality-cron.sh†L1-L120】【F:k8s/quality/cronjob.yaml†L1-L120】

Qualquer mudança no blend (ativar re-rank, alterar `weight`) deve ser acompanhada de nova execução do fluxo acima e atualização explícita dos dashboards.
