# Entidade `history_currency_rates`

## 1. Visão geral

A entidade `history_currency_rates` traz taxas de câmbio de USD e EUR contra BRL em base D-1, com valores de compra, venda e variação diária.

Perguntas típicas:
- “Qual a cotação do dólar hoje?”
- “Quanto está o euro D-1?”
- “Variação do dólar e euro ontem.”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `history_currency_rates`.
- **Chave lógica**: `rate_date` (data/hora da observação).
- **Granularidade temporal**: D-1, uma linha por data.

Campos principais (do contrato `history_currency_rates.schema.yaml`):
- `rate_date` — data/hora da taxa.
- `usd_buy_amt`, `usd_sell_amt`, `usd_var_pct` — dólar (compra, venda, variação %).
- `eur_buy_amt`, `eur_sell_amt`, `eur_var_pct` — euro (compra, venda, variação %).
- `created_at`, `updated_at` — metadados de carga.

## 3. Identificadores

- **rate_date**: data de referência (opcional em perguntas).

## 4. Grupos de colunas

- **USD**: `usd_buy_amt`, `usd_sell_amt`, `usd_var_pct`.
- **EUR**: `eur_buy_amt`, `eur_sell_amt`, `eur_var_pct`.
- **Tempo/Metadados**: `rate_date`, `created_at`, `updated_at`.

## 5. Exemplos de perguntas que devem cair em `history_currency_rates`

- “Cotação do dólar hoje.”
- “Cotação do euro D-1.”
- “Variação percentual do dólar ontem.”
- “Qual o dólar de compra e venda na última data?”
- “Como fechou o euro na última cotação?”

## 6. Observações

- Os valores são de D-1; não cobrem intraday em tempo real.
- Intent de câmbio; termos de FIIs, carteira ou índices devem ser filtrados por antitokens da ontologia.
