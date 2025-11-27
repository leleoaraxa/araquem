## Descrição
Cotações diárias dos FIIs, com preços de abertura, máxima, mínima, fechamento e variação do dia.

## Exemplos de perguntas
- "como fechou o HGLG11 hoje?"
- "qual foi a variação do MXRF11 ontem?"
- "mostrar o candle do KNRI11 na data X"

## Respostas usando templates
### list_basic
{traded_at|date_br}: {ticker} — fechamento {close_price|currency_br} (abertura {open_price|currency_br}, máx {max_price|currency_br}, mín {min_price|currency_br}) — var {daily_variation_pct|percent_br}

### FALLBACK_row
Não encontrei cotações recentes para {ticker}.
