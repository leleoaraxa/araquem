# Audit Multi-Ticker

Timestamp: 2025-12-16T22:41:00
Endpoint: POST http://localhost:8000/ask (explain=True)
Command: python scripts/audit/audit_multiticker.py

| label | question | status.reason | gate.reason | gate.top2_gap | gate.min_gap | gate.min_score | intent | entity | result_key | intent_gap_base | intent_gap_final | thr_min_score | thr_min_gap | thr_gap | thr_accepted | thr_source | answer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mt_factual_prices | preço de HGLG11 e KNRI11 | Internal Server Error | None | None | None | None | None | None | None | None | None | None | None | None | None | None |  |
| mt_factual_dividends | dividendos de HGLG11, KNRI11 e MXRF11 | Internal Server Error | None | None | None | None | None | None | None | None | None | None | None | None | None | None |  |
| mt_conceptual_compare | compare HGLG11 e KNRI11 em setor, renda e risco | gated | low_gap | 0.0 | 0.2 | 0.85 | client_fiis_dividends_evolution | fiis_financials_risk | None | 0.0 | 0.0 | 0.85 | 0.2 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| mt_conceptual_macro | como CDI versus DY 12m impacta FIIs como HGLG11 e MXRF11 | gated | low_score | 0.0 | 0.1 | 0.8 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | 0.0 | 0.0 | 0.8 | 0.1 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| mt_conceptual_no_ticker | como CDI vs DY 12m afeta FIIs (sem tickers) | gated | low_score | 1.1 | 0.2 | 0.9 | macro_consolidada | macro_consolidada | None | 1.1 | 1.1 | 0.9 | 0.2 | 1.1 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| pure_conceptual_max_drawdown | o que significa max drawdown alto | gated | low_score | 1.1 | 0.2 | 0.85 | fiis_financials_risk | fiis_financials_risk | None | 1.1 | 1.1 | 0.85 | 0.2 | 1.1 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| pure_conceptual_sharpe | o que é um sharpe ratio negativo | Internal Server Error | None | None | None | None | None | None | None | None | None | None | None | None | None | None |  |
| multi_intent_sector_yield | setor do HGLG11 e renda/dividendos esperados | request_error: [Errno 104] Connection reset by peer |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| multi_intent_sector_risk | setor do KNRI11 e risco de vacância | Internal Server Error | None | None | None | None | None | None | None | None | None | None | None | None | None | None |  |
| multi_intent_rankings | ranking de HGLG11 e MXRF11 por yield e por risco | gated | low_score | 0.0 | 0.2 | 1.0 | fiis_rankings | fiis_rankings | None | 0.0 | 0.0 | 1.0 | 0.2 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| macro_multi_entity | efeito do CDI e inflação no IFIX e IBOV em 2024 | gated | low_score | 0.0 | 0.1 | 0.8 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | 0.0 | 0.0 | 0.8 | 0.1 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| macro_currency | como dólar e euro variaram versus o real em 2023 | Internal Server Error | None | None | None | None | None | None | None | None | None | None | None | None | None | None |  |
