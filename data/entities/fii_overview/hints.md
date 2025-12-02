O que é:
- Resumo consolidado por FII combinando cadastro, preços, dividendos, risco e
  participações em índices. É a visão rápida para entender o fundo em uma única
  resposta.

Principais campos usados em respostas:
- Identidade: ticker, CNPJ, setor/tipo, gestor/administrador.
- Indicadores de preço e renda: fechamento recente, variação em janelas curtas,
  dividendos acumulados e dividend yield.
- Risco e correlação: volatilidade, beta/R² vs IFIX e drawdown histórico.
- Contexto de índices: presença no IFIX/IFIL e peso aproximado quando disponível.

Como o Araquem usa:
- Entregar respostas de "overview do {{ticker}}" com contexto macro se for
  relevante (juros, inflação, IFIX).
- Permitir comparações rápidas entre dois fundos, destacando diferenças de
  setor, renda e risco sem recomendar investimentos.
- Servir de porta de entrada para consultas detalhadas em entidades específicas
  (preços, dividendos, risco, imóveis, notícias).
