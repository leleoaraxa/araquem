# Sirios Dashboards

These dashboards are generated from `scripts/gen_dashboards.py` using the parameters in `data/ops/observability.yaml`.

To regenerate after updating bindings, thresholds, or defaults:

```bash
python scripts/gen_dashboards.py --config data/ops/observability.yaml --out grafana/dashboards
```

Do not edit the JSON files manually—changes will be overwritten on the next generation run.
