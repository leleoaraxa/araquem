O que é:
- Resumo consolidado por FII combinando cadastro, preços, dividendos, risco e
  participações em índices. É a visão rápida para entender o fundo em uma única
  resposta.

Principais campos usados em respostas:
- Identidade e perfil: ticker, display_name/b3_name, classificação, setor,
  subsetor, tipo de gestão, público-alvo e se é exclusivo.
- Indicadores de renda e preço: campos de dividend yield recente (mensal e 12m),
  dividendos acumulados, último pagamento e medidas de tamanho/valoração do
  fundo (market cap, enterprise value, relação preço/valor patrimonial).
- Qualidade financeira: métricas por cota e agregadas (patrimônio líquido,
  receita, payout, crescimento, cap rate, alavancagem, variações recentes de
  preço/patrimônio) e dados de reservas, caixa, passivos e receitas esperadas.
- Risco quantitativo: consolidado de volatilidade, Sharpe, Sortino, Treynor,
  alfa/beta, R² e máximo drawdown calculados sobre séries de preços versus
  benchmarks.
- Rankings e índices: pesos em IFIX/IFIL, posições em rankings internos de
  renda, tamanho, risco/popularidade e escala do fundo (contagem de
  cotas/cotistas).

Como o Araquem usa:
- Entregar respostas de "overview do {{ticker}}" com contexto macro se for
  relevante (juros, inflação, IFIX).
- Permitir comparações rápidas entre dois fundos, destacando diferenças de
  setor, renda e risco sem recomendar investimentos.
- Servir de porta de entrada para consultas detalhadas em entidades específicas
  (preços, dividendos, risco, imóveis, notícias).
