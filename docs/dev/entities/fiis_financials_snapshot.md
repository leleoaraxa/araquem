# fiis_financials_snapshot

## Overview

- `id`: `fiis_financials_snapshot`
- `result_key`: `financials_snapshot`
- `sql_view`: `fiis_financials_snapshot`
- `private`: `false`
- `description`: Snapshot D-1 de indicadores financeiros por FII (valores, razões, caixa e endividamento).

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `dy_monthly_pct` | DY mensal (%) | Dividend yield mensal. |
| `dy_pct` | DY (%) | Dividend yield em base anualizada. |
| `sum_anual_dy_amt` | Soma anual de DY | Soma dos proventos distribuídos no ano. |
| `last_dividend_amt` | Último dividendo | Valor do último dividendo pago. |
| `last_payment_date` | Último pagamento | Data do último pagamento de dividendo. |
| `market_cap_value` | Market Cap | Valor de mercado. |
| `enterprise_value` | Enterprise Value | EV (valor da firma). |
| `price_book_ratio` | Preço/Patrimônio | Relação preço/patrimônio (P/BV). |
| `equity_per_share` | Patrimônio por cota | Patrimônio líquido por cota. |
| `revenue_per_share` | Receita por cota | Receita por cota. |
| `dividend_payout_pct` | Payout (%) | Percentual de payout de dividendos. |
| `growth_rate` | Taxa de crescimento | Crescimento estimado. |
| `cap_rate` | Cap rate | Taxa de capitalização. |
| `leverage_ratio` | Alavancagem | Indicador de alavancagem. |
| `equity_value` | Patrimônio (R$) | Valor do patrimônio. |
| `variation_month_ratio` | Var. mês (%) | Variação percentual no mês. |
| `variation_year_ratio` | Var. ano (%) | Variação percentual no ano. |
| `equity_month_ratio` | Var. patrimônio mês (%) | Variação do patrimônio no mês. |
| `dividend_reserve_amt` | Reserva de dividendos | Montante em reserva de dividendos. |
| `admin_fee_due_amt` | Taxa de adm. devida | Despesa/obrigação com taxa de administração. |
| `perf_fee_due_amt` | Taxa de perf. devida | Despesa/obrigação com taxa de performance. |
| `total_cash_amt` | Caixa total | Caixa disponível. |
| `expected_revenue_amt` | Receita esperada | Receita esperada (projeção). |
| `liabilities_total_amt` | Passivos totais | Total de passivos. |
| `created_at` | Criado em | Data de criação. |
| `updated_at` | Atualizado em | Data da última atualização. |

## Presentation

- `kind`: `summary`
- `fields.key`: `ticker`
- `fields.value`: `dy_pct`
- `empty_message`: Sem indicadores financeiros disponíveis.

## Response Templates

- `data/entities/fiis_financials_snapshot/responses/summary.md.j2`

## Ask Routing Hints

- `intents`: ``metricas``
- `keywords`: ``payout, alavancagem, caixa, endividamento, ev, enterprise value, market cap, patrimonio, preco/patrimonio, price book, cap rate, crescimento, leverage, dividas``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
  - `dividend_payout_pct` → payout, distribuicao
  - `leverage_ratio` → alavancagem, endividamento
  - `enterprise_value` → ev, enterprise
  - `market_cap_value` → market cap, valor de mercado
  - `price_book_ratio` → preco/patrimonio, p/bv
  - `total_cash_amt` → caixa, caixa total
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
