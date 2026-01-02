## Descrição
Histórico consolidado de indicadores macroeconômicos, índices de mercado e câmbio por data de referência (`ref_date`).

## Exemplos de perguntas
- "histórico macro consolidado de outubro"
- "IPCA e SELIC em 2025-11-12"
- "IFIX e IBOV do dia 2025-11-14"
- "dólar e euro no mesmo dia de referência"
- "comparativo de CDI e SELIC na última semana"

## Respostas usando templates
### table_basic
Tabela em Markdown com uma linha por `ref_date`, contendo:

- **Data ref.** (`ref_date|date_br`)
- **IPCA** (`ipca|number` ou `"-"` se nulo)
- **SELIC** (`selic|number`)
- **CDI** (`cdi|number`)
- **IFIX (pts)** (`ifix_points`)
- **IFIX var. (%)** (`ifix_var_pct|percent_br`)
- **IBOV (pts)** (`ibov_points`)
- **IBOV var. (%)** (`ibov_var_pct|percent_br`)
- **USD compra/venda (R$)** (`usd_buy_amt|currency_br`, `usd_sell_amt|currency_br`)
- **USD var. (%)** (`usd_var_pct|percent_br`)
- **EUR compra/venda (R$)** (`eur_buy_amt|currency_br`, `eur_sell_amt|currency_br`)
- **EUR var. (%)** (`eur_var_pct|percent_br`)

A tabela é renderizada a partir do arquivo `responses/table.md.j2`.

### FALLBACK_row
Sem histórico macro para exibir no período informado.
