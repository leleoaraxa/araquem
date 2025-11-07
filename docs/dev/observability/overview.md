# Observability Overview

A observabilidade do Araquem combina métricas Prometheus, tracing OTel e dashboards Grafana declarados em `data/ops/observability.yaml`.

## Métricas canônicas

- **Planner**: `sirios_planner_routed_total`, `sirios_planner_top2_gap_histogram`, `sirios_planner_blocked_by_threshold_total`, `sirios_planner_intent_score`, `sirios_planner_entity_score` — emitidos pelo orchestrator/ask.【F:app/observability/metrics.py†L16-L60】【F:app/api/ask.py†L58-L180】
- **Cache**: `sirios_cache_ops_total`, `cache_hits_total`, `cache_misses_total`, `metrics_cache_hits_total`, `metrics_cache_misses_total` — alimentados em `app/api/ask.py` e `app/cache/rt_cache.py`.【F:app/observability/metrics.py†L40-L90】【F:app/api/ask.py†L120-L170】
- **RAG**: `sirios_rag_search_total`, `rag_index_size_total`, `rag_index_docs_total`, `rag_index_density_score`, `rag_eval_*` — atualizados via `/ops/metrics/rag/*`.【F:app/observability/metrics.py†L60-L120】【F:app/api/ops/metrics.py†L1-L140】
- **Explain**: `sirios_explain_events_failed_total` monitora falhas ao persistir eventos, acionado no `/ask?explain=true`.【F:app/api/ask.py†L180-L220】

`data/ops/observability.yaml` também define thresholds (p95 ≤ 1500 ms, hit ratio ≥ 60%, recall ≥ 60%) usados pelos dashboards/templates de alerta.【F:data/ops/observability.yaml†L1-L60】

## Tracing

- `app/observability/instrumentation.py` fornece decoradores `@trace` e emissores `counter/histogram` com atributos whitelisted.
- `app/orchestrator/routing.py` adiciona atributos (`intent`, `entity`, `cache_hit`) ao span atual. Cache TTLs e métricas também entram como atributos customizados.【F:app/orchestrator/routing.py†L1-L200】
- Amostragens e PII são controladas em `data/ops/observability.yaml` (`services.gateway.tracing`, `drop_attributes`).

## Exporters

- Prometheus: `/metrics` em `app/api/health.py` usa `render_prometheus_latest` (instrumentação local).【F:app/api/health.py†L1-L80】
- OTLP: endpoint configurado em `data/ops/observability.yaml` (`global.exporters.otlp_endpoint`).【F:data/ops/observability.yaml†L80-L110】

## Auditoria

- `scripts/observability/obs_audit.py` inspeciona dashboards/templates.
- `scripts/core/audit_repo.py` possui checagens de referências quebradas.
- `tests/observability/*.py` garantem que dashboards e métricas permaneçam sincronizados com os YAMLs e JSONs.【F:tests/observability/test_dashboards_provisioning.py†L1-L120】【F:tests/observability/test_metrics_obs.py†L1-L160】
