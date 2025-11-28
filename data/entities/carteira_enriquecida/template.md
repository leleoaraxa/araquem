## Descrição
Visão privada que cruza posição do cliente, cadastro do FII, métricas financeiras, risco e rankings.
Cada linha representa um ativo na carteira do cliente em uma `position_date`, com valores, pesos,
DY, indicadores de risco e posições em rankings.

## Exemplos de perguntas
- "peso do HGLG11 na minha carteira"
- "valor investido em MXRF11 na carteira"
- "DY mensal dos meus FIIs"
- "ranking de Sharpe dos meus FIIs na carteira"
- "listar posições da minha carteira em 2025-10-21"

## Respostas usando templates
### table_basic
Tabela em Markdown com uma linha por `{document_number, position_date, ticker}`, contendo:

- **Ticker** (`ticker`)
- **Data da posição** (`position_date|date_br`)
- **Nome** (`fii_name`)
- **Quantidade** (`qty`)
- **Preço fechamento** (`closing_price|currency_br`)
- **Valor da posição** (`position_value|currency_br`)
- **Valor da carteira** (`portfolio_value|currency_br`)
- **Peso (%)** (`weight_pct|percentage_br`)
- **DY mensal (%)** (`dy_monthly_pct|percentage_br`)
- **DY 12m (%)** (`dy_12m_pct|percentage_br`)
- **Dividendos 12m (R$)** (`dividends_12m_amt|currency_br`)
- **Volatilidade** (`volatility_ratio|number`)
- **Sharpe** (`sharpe_ratio|number`)
- **Sortino** (`sortino_ratio|number`)
- **Máx. drawdown** (`max_drawdown|number`)
- **Beta** (`beta_index|number`)
- **Rankings** (`sirios_rank_position`, `ifix_rank_position`, `rank_dy_12m`, `rank_sharpe`)

A tabela é renderizada a partir do arquivo `responses/table.md.j2`.

### FALLBACK_row
Sem posições disponíveis para o cliente e data informados.
