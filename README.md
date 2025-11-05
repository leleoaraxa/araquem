# Araquem — Catálogo de Entidades

## Entidades disponíveis

| Entidade | Result key | Principais colunas |
| --- | --- | --- |
| fiis_cadastro | `cadastro_fii` | ticker, fii_cnpj, display_name, admin_name, admin_cnpj, website_url |
| fiis_precos | `precos_fii` | ticker, traded_at, close_price, open_price, max_price, min_price, daily_variation_pct |
| fiis_dividendos | `dividendos_fii` | ticker, payment_date, dividend_amt, traded_until_date |
| fiis_rankings | `rankings_fii` | ticker, users_ranking_count, sirios_ranking_count, ifix_ranking_count, created_at, updated_at |
| fiis_metrics | `fii_metrics` | ticker, metric, value, window_months, period_start, period_end |
| fiis_imoveis | `imoveis_fii` | ticker, asset_name, asset_class, asset_address, total_area, units_count, vacancy_ratio, non_compliant_ratio, assets_status, updated_at |
| fiis_processos | `processos_fii` | ticker, process_number, judgment, instance, initiation_date, cause_amt, loss_risk_pct, main_facts, loss_impact_analysis, updated_at |
| fiis_noticias | `noticias_fii` | ticker, source, title, tags, description, url, published_at, updated_at |

> Todas as entidades operam com dados D-1 já consolidados na ingestão.

## Exemplos de perguntas suportadas

- "imóveis do HGLG11" → retorna os ativos do FII via `fiis_imoveis`.
- "status dos processos do HGRU11" → lista processos judiciais usando `fiis_processos`.
- "notícias do MXRF11" → traz matérias recentes através de `fiis_noticias`.

As intents continuam roteadas pelo planner via ontologia (`cadastro`, `precos`, `dividendos`, `rankings`, `metricas`, `noticias`), mantendo o contrato `/ask` inalterado.
