# Quality Overview

Os quality gates do Araquem garantem precisão factual antes de liberar mudanças. As regras são declaradas em `data/policies/quality.yaml` e consumidas pelos scripts de push/cron.

## Filosofia

- **Top1 accuracy ≥ 95%** e **router hit rate ≥ 98%** são limites definidos em `targets`. Nenhuma exceção é aplicada automaticamente.【F:data/policies/quality.yaml†L1-L12】
- Gaps mínimos (top2 ≥ 0.25) evitam confusão de intents quando o planner está no limiar.【F:data/policies/quality.yaml†L7-L12】
- Quality roda sempre com dados D-1 (mesma base das entidades), evitando divergências de ingestão.

## Ferramentas

- `scripts/quality/quality_push.py` — executa projections, compara com golden set e publica métricas (usa `app/observability/metrics.py`).【F:scripts/quality/quality_push.py†L1-L200】
- `scripts/quality/quality_bisect.py` — investiga regressões.
- `scripts/quality/quality_diff_routing.py` — compara roteamentos.
- `scripts/quality/quality_gate_check.sh` — wrapper shell usado em CI/CD.
- `docker/quality-cron.sh` e `scripts/quality/quality_push_cron.py` — mantêm execuções agendadas.【F:docker/quality-cron.sh†L1-L120】

## Testes automatizados

- `tests/quality/test_quality_cron.py` valida cronjobs.
- `tests/planner/test_rag_integration_planner.py` e `tests/rag/test_quality_rag_search.py` cobrem integração RAG+quality.
- Golden set: `data/golden/m65_quality.*` alimenta regressões fixas.

Consulte [projections.md](./projections.md) para a lista atualizada de datasets avaliados.
