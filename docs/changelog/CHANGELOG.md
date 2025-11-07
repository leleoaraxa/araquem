# CHANGELOG (Recente)

## M10 — Novembro/2025
- Reorganização profissional da pasta `docs/` com hierarquia Dev/Product/Changelog/Misc e geração automática de páginas por entidade (`data/entities/*/entity.yaml`).【F:docs/README.md†L1-L24】【F:docs/dev/entities/index.md†L1-L12】
- Referências atualizadas para scripts pós-migração (`scripts/quality/quality_push.py`, `scripts/observability/gen_dashboards.py`).【F:scripts/quality/quality_push.py†L1-L200】【F:scripts/observability/gen_dashboards.py†L1-L200】

## M9 — Outubro/2025
- Novas entidades financeiras (`fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`) e posições privadas (`client_fiis_positions`) disponíveis para o planner.【F:data/entities/fiis_financials_snapshot/entity.yaml†L1-L120】【F:data/entities/client_fiis_positions/entity.yaml†L1-L120】
- Templates de resposta e tests ampliados para cobrir métricas e posições (`tests/entities/test_responder_metrics.py`, `tests/entities/test_responder_imoveis.py`).【F:tests/entities/test_responder_metrics.py†L1-L120】【F:tests/entities/test_responder_imoveis.py†L1-L160】

## M8 — Setembro/2025
- Compute-on-read D-1 consolidado via `data/ops/param_inference.yaml` e integração com cache de métricas (`app/orchestrator/routing.py`).【F:data/ops/param_inference.yaml†L1-L73】【F:app/orchestrator/routing.py†L1-L200】
- Scripts `scripts/core/audit_repo.py` e `scripts/quality/quality_diff_routing.py` atualizados para a nova árvore de dados.【F:scripts/core/audit_repo.py†L1-L200】【F:scripts/quality/quality_diff_routing.py†L1-L160】

## M7 — Agosto/2025
- Blend RAG habilitado com peso 0.35 e re-rank desativado (`planner_thresholds.yaml`, `app/planner/planner.py`).【F:data/ops/planner_thresholds.yaml†L26-L35】【F:app/planner/planner.py†L200-L320】
- Correção do `route_id` no `/ask?explain=true`, garantindo persistência estável em `explain_events`.【F:app/api/ask.py†L150-L220】
