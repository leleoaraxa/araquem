## Descrição
Histórico composto que reúne dividendos pagos, dividend yield (DY) mensal e cadastro do FII.
Cada linha representa um `ticker` em um `ref_month`, trazendo o pagamento do mês, o preço
de referência, DY mensal e métricas acumuladas (12m, último pagamento, data-com).

## Exemplos de perguntas
- "histórico de dividendos e DY do MXRF11 nos últimos 12 meses"
- "qual foi o DY mensal do HGLG11 em 2024-09?"
- "dividend yield atual do CPTS11"
- "quanto o VISC11 pagou em dividendos no mês de 2024-08?"
- "comparativo de DY mensal entre HGLG11 e VISC11"

## Respostas usando templates
### table_basic
Tabela em Markdown com uma linha por `{ticker, ref_month}`, contendo:

- **Ticker** (`ticker`)
- **Mês ref.** (`ref_month|date_br`)
- **Data-com (cutoff)** (`traded_until_date|datetime_br`)
- **Pagamento** (`payment_date|datetime_br`)
- **Dividendo (R$)** (`dividend_amt|currency_br`)
- **Dividendos mês (R$)** (`month_dividends_amt|currency_br`)
- **Preço ref. (R$)** (`month_price_ref|currency_br`)
- **DY mensal** (`dy_monthly|percent_br`)
- **DY 12m (%)** (`dy_12m_pct|percent_br`)
- **DY mensal atual (%)** (`dy_current_monthly_pct|percent_br`)
- **Dividendos 12m (R$)** (`dividends_12m_amt|currency_br`)
- **Último dividendo (R$)** (`last_dividend_amt|currency_br`)
- **Último pagamento** (`last_payment_date|datetime_br`)

A tabela é renderizada a partir do arquivo `responses/table.md.j2`.

### FALLBACK_row
Sem histórico de dividendos e DY para exibir para {ticker} no período informado.
