# Planner Thresholds

Fonte: `data/ops/planner_thresholds.yaml` (versão 20251106).【F:data/ops/planner_thresholds.yaml†L1-L35】

## Defaults globais

- `min_score`: 1.0
- `min_gap`: 0.5
- `apply_on`: `base`

## Overrides por intent

| Intent | min_score | min_gap |
| --- | --- | --- |
| cadastro | 1.0 | 0.2 |
| precos | 1.0 | 0.2 |
| dividendos | 1.0 | 0.2 |
| metricas | 1.0 | 0.2 |
| imoveis | 1.0 | 0.2 |
| processos | 1.0 | 0.2 |
| noticias | 1.0 | 0.2 |
| rankings | 1.0 | 0.2 |

## Overrides por entidade

Todas as entidades cadastradas (`fiis_*`, `client_fiis_positions`) replicam `min_score 1.0` e `min_gap 0.2`. A lista completa está no YAML para fácil diff.【F:data/ops/planner_thresholds.yaml†L11-L27】

## Configuração RAG

- `enabled: true`
- `k: 5`
- `min_score: 0.20`
- `weight: 0.35`
- `re_rank.enabled: false` (modo `blend`, `weight: 0.25` reservado para futura ativação)

Qualquer alteração deve ser acompanhada de atualização em [RAG Overview](../rag/index.md) e revalidação dos datasets de quality.
