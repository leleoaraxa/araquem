# Audit Multi-Ticker

Timestamp: 2025-12-16T19:48:33
Endpoint: POST http://localhost:8000/ask (explain=True)
Command: python scripts/audit/audit_multiticker.py

| label | question | status.reason | gate.reason | gate.top2_gap | gate.min_gap | gate.min_score | intent | entity | result_key | intent_gap_base | intent_gap_final | thr_min_score | thr_min_gap | thr_gap | thr_accepted | thr_source | answer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mt_factual_prices | preço de HGLG11 e KNRI11 | request_error: timed out |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| mt_factual_dividends | dividendos de HGLG11, KNRI11 e MXRF11 | request_error: timed out |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| mt_conceptual_compare | compare HGLG11 e KNRI11 em setor, renda e risco | request_error: timed out |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| mt_conceptual_macro | como CDI versus DY 12m impacta FIIs como HGLG11 e MXRF11 | gated | low_score | 0.0 | 0.1 | 0.8 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | 0.0 | 0.0 | 0.8 | 0.1 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| mt_conceptual_no_ticker | como CDI vs DY 12m afeta FIIs (sem tickers) | request_error: timed out |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| pure_conceptual_max_drawdown | o que significa max drawdown alto | request_error: timed out |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| pure_conceptual_sharpe | o que é um sharpe ratio negativo | request_error: timed out |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| multi_intent_sector_yield | setor do HGLG11 e renda/dividendos esperados | gated | low_gap | 0.11698533883764717 | 0.15 | 0.9 | fiis_dividendos | fiis_dividendos | None | 0.0 | 0.11698533883764717 | 0.9 | 0.15 | 0.11698533883764717 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| multi_intent_sector_risk | setor do KNRI11 e risco de vacância | ok | None | None | None | None | fiis_cadastro | fiis_cadastro | cadastro_fii | 1.1 | 1.045452623070723 | 1.0 | 0.2 | 1.045452623070723 | True | final | **KNRI11 — Kinea Renda Imobiliria Fundo Investimento Imob... |
| multi_intent_rankings | ranking de HGLG11 e MXRF11 por yield e por risco | request_error: timed out |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| macro_multi_entity | efeito do CDI e inflação no IFIX e IBOV em 2024 | gated | low_score | 0.0 | 0.1 | 0.8 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | 0.0 | 0.0 | 0.8 | 0.1 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| macro_currency | como dólar e euro variaram versus o real em 2023 | ok | None | None | None | None | history_currency_rates | history_currency_rates | history_currency_rates | 1.1 | 1.046244276660814 | 0.8 | 0.1 | 1.046244276660814 | True | final | **Taxas de câmbio (D-1)**

  Última data 17/11/2025:
  - ... |