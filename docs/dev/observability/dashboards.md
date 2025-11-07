# Dashboards

## Grafana

| Arquivo | Descrição | Como carregar |
| --- | --- | --- |
| `grafana/dashboards/00_sirios_overview.json` | Visão geral API + planner. | Importar no Grafana (`Dashboards > Import`) e associar datasource `grafana`. | 
| `grafana/dashboards/10_api_slo_pipeline.json` | Latências/erros do gateway e `/ask`. | Mesmo processo acima. |
| `grafana/dashboards/20_planner_rag_intelligence.json` | Métricas do planner + densidade/recall RAG. | Requer métricas `rag_index_*` e `rag_eval_*`. |
| `grafana/dashboards/30_ops_reliability.json` | Cronjobs, cache hit ratio, quality gates. | Datasource Prometheus padrão. |
| `grafana/quality_dashboard.json` | Painel específico de qualidade consolidado. | Import direto (JSON plano). |

Os templates Jinja correspondentes estão em `grafana/templates/*.json.j2` e são gerados via `scripts/observability/gen_dashboards.py`.【F:grafana/templates/00_sirios_overview.json.j2†L1-L200】【F:scripts/observability/gen_dashboards.py†L1-L200】

## Tempo (Tracing)

- Configuração do collector Tempo: `tempo/tempo.yaml`.
- Painéis podem ser importados a partir dos templates Grafana acima (campos `tempo` já configurados).【F:tempo/tempo.yaml†L1-L120】

## Provisioning

- `grafana/provisioning/` contém manifests para dashboards/datasources automáticos.
- `tests/observability/test_dashboards_provisioning.py` garante consistência após alterações.【F:tests/observability/test_dashboards_provisioning.py†L1-L120】

## Notas

Dashboards legados/arquivados permanecem em `docs/misc/notes/`. Caso algum JSON fora da lista acima seja necessário, adicione referência explícita neste arquivo.
