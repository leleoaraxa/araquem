# QA Quality Datasets

Este documento descreve quais datasets de QA são considerados canônicos para o índice RAG e quais arquivos o cron de qualidade publica.

## Fonte canônica
- `data/golden/m65_quality.yaml` é a única fonte oficial (golden) para os cenários de QA.
- O arquivo JSON equivalente (`data/golden/m65_quality.json`) permanece apenas como legado/histórico e **não** deve ser indexado nem utilizado como referência principal.

## Sincronização do `routing_samples.json`
- O arquivo `data/ops/quality/routing_samples.json` é gerado automaticamente a partir do YAML canônico via `scripts/core/golden_sync.py`.
- Pipelines/CI devem chamar `python scripts/core/golden_sync.py --in data/golden/m65_quality.yaml --out data/ops/quality/routing_samples.json --check` antes de builds/deploys; se houver divergência, rode o mesmo comando sem `--check` para atualizar o JSON.

## Publicação no `/ops/quality/push`
O endpoint aceita somente payloads com o campo `"type"` definido como:
- `routing`
- `projection`

Exemplo de corpo mínimo aceito:
```json
{
  "type": "routing",
  "samples": [
    { "input": "...", "expected": "..." }
  ]
}
```

Qualquer arquivo sem o campo `type` ou com valores diferentes é ignorado pelo cron, incluindo:
- `data/ops/quality_experimental/param_inference_samples.json`
- `data/ops/quality_experimental/rag_search_basics.json`
- `data/ops/quality_experimental/planner_rag_integration.json`
- `data/ops/quality_experimental/m66_projection.json`

## Execução do cron
Para validar o filtro localmente, execute o cron em modo dry-run:
```bash
QUALITY_SAMPLES_GLOB="data/ops/quality/*.json" \
API_URL="http://localhost:8000" \
QUALITY_OPS_TOKEN="dummy" \
python scripts/quality/quality_push_cron.py --dry-run
```
O comando lista `[post]` apenas para arquivos compatíveis e `[skip]` para os demais.
