O que é:
- Resumo consolidado por FII combinando cadastro, preços, dividendos, risco e
  participações em índices. É a visão rápida para entender o fundo em uma única
  resposta.

Principais campos usados em respostas:
- Identidade e perfil: ticker, display_name/b3_name, classificação, setor,
  subsetor, tipo de gestão, público-alvo e se é exclusivo.
- Indicadores de renda e preço: dy_monthly_pct, dy_12m_pct, dividends_12m_amt,
  last_dividend_amt e last_payment_date, além de market_cap_value,
  enterprise_value e price_book_ratio.
- Qualidade financeira: equity_per_share, revenue_per_share,
  dividend_payout_pct, growth_rate, cap_rate, leverage_ratio, equity_value e
  reservas/caixa (dividend_reserve_amt, total_cash_amt, liabilities_total_amt,
  expected_revenue_amt).
- Risco quantitativo: volatility_ratio, sharpe_ratio, treynor_ratio,
  jensen_alpha, beta_index, sortino_ratio, max_drawdown e r_squared.
- Rankings e índices: pesos no IFIX/IFIL (ifix_weight_pct/ifil_weight_pct),
  posições em rankings (users_rank_position, sirios_rank_position,
  ifix_rank_position, ifil_rank_position, rank_dy_12m, rank_dy_monthly,
  rank_dividends_12m, rank_market_cap, rank_equity, rank_sharpe,
  rank_sortino, rank_low_volatility, rank_low_drawdown) e contagem de
  cotas/cotistas (shares_count, shareholders_count).

Como o Araquem usa:
- Entregar respostas de "overview do {{ticker}}" com contexto macro se for
  relevante (juros, inflação, IFIX).
- Permitir comparações rápidas entre dois fundos, destacando diferenças de
  setor, renda e risco sem recomendar investimentos.
- Servir de porta de entrada para consultas detalhadas em entidades específicas
  (preços, dividendos, risco, imóveis, notícias).
