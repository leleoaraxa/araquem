# Cache Policies

Arquivo: `data/policies/cache.yaml` (versão 1). Controla TTLs e escopos do cache read-through utilizado pelo orchestrator.

## Resumo por entidade

| Entidade | TTL (s) | Refresh | Escopo | Observações |
| --- | --- | --- | --- | --- |
| fiis_cadastro | 86400 | 01:15 | pub | Dados estáticos 1×1. |
| fiis_precos | 86400 | 01:15 | pub | Série diária. |
| fiis_dividendos | 86400 | 01:15 | pub | Histórico D-1. |
| fiis_rankings | 86400 | 01:15 | pub | Rankings agregados. |
| fiis_metrics | 43200 | 01:15 | pub | Possui `deny_if` para `window_type=count` + `value=1`. |
| fiis_imoveis | 86400 | 02:10 | pub | Dados operacionais. |
| fiis_noticias | 3600 | hourly | pub | Feed atualizado 1h. |
| fiis_processos | 43200 | 03:00 | pub | Andamentos judiciais. |
| fiis_financials_snapshot | 43200 | 01:30 | pub | Indicadores D-1. |
| fiis_financials_revenue_schedule | 43200 | 01:30 | pub | Cronograma de receitas. |
| fiis_financials_risk | 43200 | 01:30 | pub | Métricas de risco. |
| client_fiis_positions | 900 | none | prv | Posições privadas por documento. |

## Como o orchestrator utiliza

- `app/api/ask.py` consulta `policies` via `cache.read_through` apenas quando `strategy == "read_through"` e TTL > 0.【F:app/api/ask.py†L90-L150】
- Identificadores de métricas incorporam `window_norm`, `metric_key` e `ticker`; políticas privadas exigem `document_number` no payload (entity `client_fiis_positions`).【F:app/orchestrator/routing.py†L100-L160】【F:data/entities/client_fiis_positions/entity.yaml†L1-L120】
- A chave final segue `araquem:{build_id}:{scope}:{entity}:{hash}` (ver `make_cache_key`).【F:app/cache/rt_cache.py†L96-L110】

Atualize este documento quando novas entidades forem adicionadas ou TTLs ajustados.
