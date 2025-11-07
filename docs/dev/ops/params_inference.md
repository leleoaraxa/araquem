# Param Inference

Arquivo: `data/ops/param_inference.yaml`. Define regras declarativas para intents temporais e métricas sem alterar o payload `/ask`.

## Intents cobertas

### dividendos
- `default_agg`: `list`
- `default_window`: `count=6`
- Keywords especiais: `latest`, `list`, `avg`, `sum`
- Window keywords: `months` (3,6,12,24) e `count` (3,6,12,24)

### precos
- `default_agg`: `latest`
- `default_window`: `count=1`
- Keywords: `latest`, `list`, `avg`
- Window keywords: mesmas faixas do módulo `dividendos`

### metricas
- `default_agg`: `metrics`
- `default_window`: `months=12`
- `default_metric`: `dividends_sum`
- `metric_keywords`: `dividends_sum`, `dividends_count`, `price_avg`, `dy_avg`
- `ytd_keywords`: reconhece janelas YTD (`ytd`, `ano atual`)

Todas as listas acima derivam diretamente do YAML.【F:data/ops/param_inference.yaml†L9-L73】

## Execução

`app/planner/param_inference.py` carrega o YAML para inferir `agg_params` antes do builder. O orchestrator injeta o resultado em `meta.aggregates` e usa para cache (`window_norm`, `metric`).【F:app/planner/param_inference.py†L1-L200】【F:app/api/ask.py†L70-L150】

## Manutenção

- Ajustes em keywords exigem atualização de testes (`tests/core/test_param_inference.py`).
- Não adicionar intents novas sem ADR/ontologia — mantenha sincronia com `data/ontology/entity.yaml`.
