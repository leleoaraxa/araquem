## Descrição
Histórico diário de câmbio de dólar e euro, com preços de compra, venda e variação percentual.

## Exemplos de perguntas
- "como fechou o dólar ontem?"
- "qual a variação do euro na última cotação?"
- "mostrar câmbio recente para contextualizar FIIs dolarizados"

## Respostas usando templates
### list_basic
{rate_date}: USD {usd_sell_amt|number_br} (venda) / {usd_buy_amt|number_br} (compra) — ΔUSD {usd_var_pct|percent_br}; EUR {eur_sell_amt|number_br} (venda) / {eur_buy_amt|number_br} (compra) — ΔEUR {eur_var_pct|percent_br}.

### FALLBACK_row
Sem dados de câmbio para {rate_date}.
