# fiis_financials_risk

## Overview

- `id`: `fiis_financials_risk`
- `result_key`: `financials_risk`
- `sql_view`: `fiis_financials_risk`
- `private`: `false`
- `description`: Métricas de risco do FII (volatilidade, Sharpe, Treynor, Jensen, beta), D-1.

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `volatility_ratio` | Volatilidade | Indicador de volatilidade. |
| `sharpe_ratio` | Sharpe | Índice de Sharpe. |
| `treynor_ratio` | Treynor | Índice de Treynor. |
| `jensen_alpha` | Alfa de Jensen | Alfa de Jensen. |
| `beta_index` | Beta | Beta do fundo. |
| `created_at` | Criado em | Data de criação. |
| `updated_at` | Atualizado em | Data da última atualização. |

## Presentation

- `kind`: `summary`
- `fields.key`: `ticker`
- `fields.value`: `volatility_ratio`
- `empty_message`: Sem indicadores de risco disponíveis.

## Response Templates

- `data/entities/fiis_financials_risk/responses/summary.md.j2`

## Ask Routing Hints

- `intents`: ``metricas``
- `keywords`: ``risco, volatilidade, sharpe, treynor, jensen, alfa, beta, volatilidade, desvio-padrão, drawdown, risco ajustado, performance ajustada, risco vs retorno``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
