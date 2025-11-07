# Product Positioning

Araquem entrega respostas factuais sobre Fundos Imobiliários (FIIs) a partir de perguntas em linguagem natural. O produto combina roteamento determinístico, contratos NL→SQL e hints semânticos para manter precisão em ambientes regulados.

## Proposta de valor

- **Precisão end-to-end**: o planner roteia intents para entidades específicas (`fiis_*`, `client_fiis_positions`) com regras declarativas e thresholds rígidos.【F:app/planner/planner.py†L1-L320】【F:data/ops/planner_thresholds.yaml†L1-L35】
- **Cobertura completa de FIIs**: contratos YAML descrevem cadastro, preços, dividendos, rankings, métricas financeiras e posições privadas quando autorizadas.【F:data/entities/fiis_cadastro/entity.yaml†L1-L120】【F:data/entities/fiis_metrics/entity.yaml†L1-L120】【F:data/entities/client_fiis_positions/entity.yaml†L1-L120】
- **Respostas imediatas**: `/ask` é síncrono, com caching read-through e templates Jinja que retornam texto e JSON prontos para UI.【F:app/api/ask.py†L1-L220】【F:app/responder/__init__.py†L1-L160】
- **Governança declarativa**: parâmetros de agregação, políticas de cache e quality gates ficam em YAML versionado, evitando drift operacional.【F:data/ops/param_inference.yaml†L1-L73】【F:data/policies/cache.yaml†L1-L36】【F:data/policies/quality.yaml†L1-L12】

## Diferenciais

- **Observabilidade de ponta a ponta** com métricas `sirios_*`, dashboards Grafana e tracing OTel prontos para auditoria.【F:app/observability/metrics.py†L1-L120】【F:grafana/dashboards/20_planner_rag_intelligence.json†L1-L200】
- **RAG blend controlado** (re-rank desligado por padrão) garante recall sem comprometer explicabilidade; ajustes são governados via YAML e scripts versionados.【F:data/ops/planner_thresholds.yaml†L26-L35】【F:scripts/embeddings/rag_retrieval_eval.py†L1-L200】
- **Qualidade contínua** com projections e cronjobs versionados (`scripts/quality/*`, `data/ops/quality/*.json`).【F:scripts/quality/quality_push.py†L1-L200】【F:data/ops/quality/projection_fiis_dividendos.json†L1-L20】

## Público alvo

- **Times de investimento** que precisam de respostas rápidas sobre FIIs sem depender de SQL.
- **Operações e compliance** interessados em rastreabilidade (logs, métricas, explainability).

## Roadmap imediato

1. Revisitar ativação do re-rank assim que as métricas de recall superarem thresholds definidas em `data/ops/observability.yaml`.
2. Expandir entidades privadas além de FIIs (depende de novos contratos YAML + autorização legal).
3. Integrar dashboards de brand/marketing para reforçar posicionamento em materiais externos (ver seção Brand).
