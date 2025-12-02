O que é:
- Séries históricas de preços diários dos FIIs, com abertura, máxima, mínima e
  fechamento ajustado.

Principais colunas:
- ticker e data: identificam o ponto da série.
- close_price e adj_close_price: referências de fechamento (bruto e ajustado).
- open_price, max_price, min_price: preços de abertura, máxima e mínima do dia.
- daily_variation_pct: oscilação percentual diária em relação ao pregão
  anterior.

Como o Araquem usa:
- Calcular variações em janelas (1d, 1m, 3m, 12m) e contextualizar movimentos de
  preço com macro ou eventos específicos.
- Servir de base para métricas de risco (volatilidade, drawdown) combinadas com
  benchmarks da B3.
- Apoiar respostas rápidas como "quanto fechou o HGLG11 ontem?" ou
  "qual a variação do KNRI11 nos últimos 30 dias?".
