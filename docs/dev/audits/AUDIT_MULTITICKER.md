# Audit Multi-Ticker

Endpoint: POST /ask (explain=False)

| label | question | status.reason | gate.reason | intent | entity | result_key | top2_gap | min_gap | min_score | answer |
|---|---|---|---|---|---|---|---|---|---|---|
| mt_factual_prices | preço de HGLG11 e KNRI11 | ok | None | fiis_precos | fiis_precos | None | None | None | None |  |
| mt_factual_dividends | dividendos de HGLG11, KNRI11 e MXRF11 | ok | None | fiis_dividendos | fiis_dividendos | None | None | None | None |  |
| mt_conceptual_compare | compare HGLG11 e KNRI11 em setor, renda e risco | ok | None | client_fiis_dividends_evolution | fiis_financials_risk | None | None | None | None |  |
| mt_conceptual_macro | como CDI versus DY 12m impacta FIIs como HGLG11 e MXRF11 | ok | None | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | None | None | None |  |
| mt_conceptual_no_ticker | como CDI vs DY 12m afeta FIIs (sem tickers) | ok | None | macro_consolidada | macro_consolidada | None | None | None | None |  |
| pure_conceptual_max_drawdown | o que significa max drawdown alto | ok | None | fiis_financials_risk | fiis_financials_risk | None | None | None | None |  |
| pure_conceptual_sharpe | o que é um sharpe ratio negativo | ok | None | fiis_financials_risk | fiis_financials_risk | None | None | None | None |  |
| multi_intent_sector_yield | setor do HGLG11 e renda/dividendos esperados | ok | None | client_fiis_dividends_evolution | fiis_dividendos | None | None | None | None |  |
| multi_intent_sector_risk | setor do KNRI11 e risco de vacância | ok | None | fiis_cadastro | fiis_cadastro | None | None | None | None |  |
| multi_intent_rankings | ranking de HGLG11 e MXRF11 por yield e por risco | ok | None | fiis_rankings | fiis_rankings | None | None | None | None |  |
| macro_multi_entity | efeito do CDI e inflação no IFIX e IBOV em 2024 | ok | None | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | None | None | None |  |
| macro_currency | como dólar e euro variaram versus o real em 2023 | ok | None | history_currency_rates | history_currency_rates | None | None | None | None |  |