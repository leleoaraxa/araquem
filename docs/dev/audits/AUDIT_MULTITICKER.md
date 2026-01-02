# Audit Multi-Ticker

Timestamp: 2025-12-16T20:40:09
Endpoint: POST http://localhost:8000/ask (explain=True)
Command: python scripts/audit/audit_multiticker.py

| label | question | status.reason | gate.reason | gate.top2_gap | gate.min_gap | gate.min_score | intent | entity | result_key | intent_gap_base | intent_gap_final | thr_min_score | thr_min_gap | thr_gap | thr_accepted | thr_source | answer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mt_factual_prices | preço de HGLG11 e KNRI11 | ok | None | None | None | None | fiis_precos | fiis_precos | precos_fii | 4.4 | 3.6466989254605355 | 0.9 | 0.0 | 3.6466989254605355 | True | final | | Data | Código | Preço de fechamento (R$) | Preço ajusta... |
| mt_factual_dividends | dividendos de HGLG11, KNRI11 e MXRF11 | ok | None | None | None | None | fiis_dividends | fiis_dividends | dividendos_fii | 1.1 | 1.0521463818279453 | 0.9 | 0.15 | 1.0521463818279453 | True | final | **Dividendos de MXRF11**

    Último pagamento em 12/12/2... |
| mt_conceptual_compare | compare HGLG11 e KNRI11 em setor, renda e risco | gated | low_gap | 0.0 | 0.2 | 0.85 | client_fiis_dividends_evolution | fiis_financials_risk | None | 0.0 | 0.0 | 0.85 | 0.2 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| mt_conceptual_macro | como CDI versus DY 12m impacta FIIs como HGLG11 e MXRF11 | gated | low_score | 0.0 | 0.1 | 0.8 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | 0.0 | 0.0 | 0.8 | 0.1 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| mt_conceptual_no_ticker | como CDI vs DY 12m afeta FIIs (sem tickers) | ok | None | None | None | None | macro_consolidada | macro_consolidada | ref_date | 1.1 | 0.9349999999999998 | 0.9 | 0.2 | 0.9349999999999998 | False | final | **Último registro em 14/11/2025**

  - IPCA: **-**
  - Ju... |
| pure_conceptual_max_drawdown | o que significa max drawdown alto | gated | low_score | 1.032647057350364 | 0.2 | 0.85 | fiis_financials_risk | fiis_financials_risk | None | 1.1 | 1.032647057350364 | 0.85 | 0.2 | 1.032647057350364 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| pure_conceptual_sharpe | o que é um sharpe ratio negativo | ok | None | None | None | None | fiis_financials_risk | fiis_financials_risk | None | 1.1 | 1.0386326586467103 | 0.85 | 0.2 | 1.0386326586467103 | True | final | Nenhum registro encontrado. |
| multi_intent_sector_yield | setor do HGLG11 e renda/dividendos esperados | gated | low_gap | 0.11698533883764717 | 0.15 | 0.9 | fiis_dividends | fiis_dividends | None | 0.0 | 0.11698533883764717 | 0.9 | 0.15 | 0.11698533883764717 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| multi_intent_sector_risk | setor do KNRI11 e risco de vacância | ok | None | None | None | None | fiis_registrations | fiis_registrations | cadastro_fii | 1.1 | 1.045452623070723 | 1.0 | 0.2 | 1.045452623070723 | True | final | **KNRI11 — Kinea Renda Imobiliria Fundo Investimento Imob... |
| multi_intent_rankings | ranking de HGLG11 e MXRF11 por yield e por risco | gated | low_score | 0.0 | 0.2 | 1.0 | fiis_rankings | fiis_rankings | None | 0.0 | 0.0 | 1.0 | 0.2 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| macro_multi_entity | efeito do CDI e inflação no IFIX e IBOV em 2024 | gated | low_score | 0.0 | 0.1 | 0.8 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | None | 0.0 | 0.0 | 0.8 | 0.1 | 0.0 | False | final | Não consegui decidir com segurança entre rotas possíveis ... |
| macro_currency | como dólar e euro variaram versus o real em 2023 | ok | None | None | None | None | history_currency_rates | history_currency_rates | history_currency_rates | 1.1 | 1.046244276660814 | 0.8 | 0.1 | 1.046244276660814 | True | final | **Taxas de câmbio (D-1)**

  Última data 17/11/2025:
  - ... |
