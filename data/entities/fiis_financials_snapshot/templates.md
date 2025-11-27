## Descrição
Snapshot financeiro resumindo payout, alavancagem, valor de mercado e estrutura de caixa e passivos do FII.

## Exemplos de perguntas
- "qual o payout do HGLG11?"
- "quanto de caixa o MXRF11 tem hoje?"
- "qual a alavancagem do XPML11?"

## Respostas usando templates
### list_basic
{ticker}: payout {dividend_payout_pct|percent_br}, alavancagem {leverage_ratio|number_br}, EV {enterprise_value|currency_br}, MarketCap {market_cap_value|currency_br}, caixa {total_cash_amt|currency_br}, passivos {liabilities_total_amt|currency_br}

### FALLBACK_row
Não encontrei snapshot financeiro para {ticker}.
