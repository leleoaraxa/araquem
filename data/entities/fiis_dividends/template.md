## Descrição
Histórico de proventos distribuídos por FII, com datas de pagamento e data-com.

## Exemplos de perguntas
- "quais dividendos o MXRF11 pagou neste mês?"
- "quando foi o último pagamento do HGLG11?"
- "qual o dividendo do CPTS11 com data-com mais recente?"

## Respostas usando templates
### list_basic
{payment_date|date_br}: {ticker} — dividendo {dividend_amt|currency_br} — último dia com {traded_until_date|date_br}

### FALLBACK_row
Não encontrei pagamentos de dividendos para {ticker} no período.
