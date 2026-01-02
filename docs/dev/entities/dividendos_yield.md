# Entidade `dividendos_yield`

## 1. Visão geral

`dividendos_yield` consolida o histórico mensal de dividendos e dividend yield (DY) dos FIIs, junto com dados cadastrais básicos do fundo. Combina pagamento, datas e indicadores de yield em uma única visão.

Responde perguntas como:
- “Histórico de dividendos e DY do MXRF11.”
- “Quanto o CPTS11 pagou de dividendo e DY em 08/2023?”
- “O que é dividend yield em FIIs?”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `dividendos_yield`.
- **Chave lógica**: `(ticker, ref_month, payment_date)`.
- **Granularidade temporal**: registros mensais e por pagamento.

Campos principais (do contrato `dividendos_yield.schema.yaml`):
- Identificação: `ticker`, `display_name`, `sector`, `sub_sector`, `classification`, `management_type`, `target_market`.
- Datas: `traded_until_date` (data-com), `payment_date`, `ref_month`, `last_payment_date`.
- Valores e yield: `dividend_amt`, `month_dividends_amt`, `month_price_ref`, `dy_monthly`, `dy_12m_pct`, `dy_current_monthly_pct`, `dividends_12m_amt`, `last_dividend_amt`.

## 3. Identificadores

- **ticker**: código AAAA11; suporta múltiplos tickers.

## 4. Grupos de colunas

- **Cadastro**: `display_name`, `sector`, `sub_sector`, `classification`, `management_type`, `target_market`.
- **Datas e referência**: `ref_month`, `traded_until_date`, `payment_date`, `last_payment_date`.
- **Dividendos e preço**: `dividend_amt`, `month_dividends_amt`, `month_price_ref`, `dividends_12m_amt`, `last_dividend_amt`.
- **Indicadores de DY**: `dy_monthly`, `dy_current_monthly_pct`, `dy_12m_pct`.

## 5. Exemplos de perguntas que devem cair em `dividendos_yield`

- “Histórico de dividendos e DY do MXRF11.”
- “Quanto o CPTS11 pagou de dividendos e DY em 08/2023?”
- “Qual o DY de 12 meses do HGLG11?”
- “Último dividendo pago pelo VISC11 e respectivo yield.”
- “O que é dividend yield em FIIs?”

## 6. Observações

- Indicadores de yield são mensais ou acumulados em 12 meses conforme colunas específicas.
- A visão é por FII; perguntas sobre carteira do cliente devem ir para intents `client_*` ou `client_fiis_enriched_portfolio`.
