# Qualidade de roteamento

- `data/ops/quality/routing_samples.json` é **gerado** pelas suítes canônicas (`data/ops/quality/payloads/*_suite.json`). Não edite manualmente; use `python scripts/quality/build_routing_samples.py`.
- Para garantir alinhamento entre suites e roteamento, use `python scripts/quality/validate_routing_drift.py` antes dos testes de qualidade.
