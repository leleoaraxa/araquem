# Releases (Histórico)

| Release | Data | Destaques |
| --- | --- | --- |
| M10 | 2025-11 | Reestruturação de documentação, alinhamento de scripts e geração automática das páginas de entidades.【F:docs/README.md†L1-L24】【F:docs/dev/entities/index.md†L1-L12】 |
| M9 | 2025-10 | Ampliação do catálogo financeiro (snapshot, revenue, risk) e suporte a posições privadas para clientes.【F:data/entities/fiis_financials_snapshot/entity.yaml†L1-L120】【F:data/entities/client_fiis_positions/entity.yaml†L1-L120】 |
| M8 | 2025-09 | Param inference compute-on-read + sincronização de scripts/qualidade para nova hierarquia de dados.【F:data/ops/param_inference.yaml†L1-L73】【F:scripts/quality/quality_push.py†L1-L200】 |
| M7 | 2025-08 | Ativação do blend RAG (re-rank off) e correções de persistência `route_id` no `/ask?explain=true`.【F:data/ops/planner_thresholds.yaml†L26-L35】【F:app/api/ask.py†L150-L220】 |

Releases anteriores permanecem documentados nos relatórios legados em `docs/misc/notes/`.
