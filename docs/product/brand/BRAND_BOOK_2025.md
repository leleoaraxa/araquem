# Brand Book 2025 — Sumário Executivo

O Araquem é apresentado como "guardião da precisão para FIIs". Os pilares técnicos que sustentam a narrativa são:

1. **Confiabilidade verificável** — contratos NL→SQL versionados e observabilidade completa (`sirios_*`, dashboards Grafana).【F:data/entities/fiis_cadastro/entity.yaml†L1-L120】【F:app/observability/metrics.py†L1-L120】
2. **Velocidade com governança** — `/ask` síncrono, payload imutável e políticas de cache que garantem respostas rápidas sem perder rastreabilidade.【F:app/api/ask.py†L1-L220】【F:data/policies/cache.yaml†L1-L36】
3. **Atualização contínua** — quality gates e cronjobs asseguram dados D-1, evitando ruído em materiais de marketing.【F:scripts/quality/quality_push.py†L1-L200】【F:data/policies/quality.yaml†L1-L12】

> **Nota:** o PDF oficial permanece hospedado no repositório de marketing interno. Solicitar acesso via canal `#brand-arena`. Atualizar este link assim que a URL final for confirmada.
