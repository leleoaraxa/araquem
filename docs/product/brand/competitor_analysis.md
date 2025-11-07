# Análise da Concorrência (Julho 2025) — Sumário Executivo

Principais destaques para posicionamento comercial:

- **Benchmarks de precisão**: Araquem mantém gates ≥95% top1 vs. concorrentes com base em heurísticas ou LLMs não auditáveis.【F:data/policies/quality.yaml†L1-L12】【F:scripts/quality/quality_push.py†L1-L200】
- **Transparência operacional**: concorrentes raramente expõem rotas SQL; aqui todos os contratos YAML estão versionados e passíveis de auditoria.【F:data/entities/fiis_financials_snapshot/entity.yaml†L1-L120】
- **Integração observável**: métricas Prometheus + dashboards Grafana permitem SLAs comprováveis, diferencial em RFPs enterprise.【F:app/observability/metrics.py†L1-L120】【F:grafana/dashboards/10_api_slo_pipeline.json†L1-L200】

> **Nota:** o relatório completo de benchmarking (PDF/Slides) permanece em revisão pelo time de marketing. Solicitar acesso via canal `#brand-arena` até que a URL definitiva seja disponibilizada.
