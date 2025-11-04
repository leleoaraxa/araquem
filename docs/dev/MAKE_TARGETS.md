# Make Targets — Araquem
- `make dashboards` — Renderiza dashboards Grafana a partir de `data/ops/observability.yaml` para `grafana/dashboards`. Usa `scripts/gen_dashboards.py` internamente.【F:Makefile†L1-L6】
- `make alerts` — Gera regras de recording/alerting Prometheus via `scripts/gen_alerts.py`. Mantém `prometheus/recording_rules.yml` e `alerting_rules.yml` atualizados.【F:Makefile†L6-L9】
- `make audit` — Executa `scripts/obs_audit.py` garantindo consistência de dashboards e rules.【F:Makefile†L9-L11】
- `make ci` — Pipeline completo: dashboards + alerts + audit e depois `pytest -q` para validar a stack.【F:Makefile†L11-L13】
- `make obs-check` — Auditoria rápida: roda `scripts/obs_audit.py`, subset de testes Pytest focados em métricas/planner/cache/executor/ask e verifica exportação `/metrics`. Ideal para checagem local antes de PR.【F:Makefile†L13-L17】
