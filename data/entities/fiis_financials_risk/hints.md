O que é:
- View com métricas quantitativas de risco para FIIs, calculadas sobre séries
  históricas de preços, dividendos, IFIX e CDI/SELIC.
- Inclui volatilidade, Sharpe, Sortino, Treynor, alfa de Jensen, beta, R² e
  máximo drawdown consolidados em uma foto D-1 (sem colunas por janela).

Como interpretar:
- Retornos excedentes usam CDI/SELIC como linha de base de ativo livre de risco.
- Beta e R² comparam o fundo ao IFIX; beta > 1 indica maior sensibilidade ao
  mercado, beta < 1 indica postura mais defensiva.
- MDD (max_drawdown) mostra a pior queda acumulada na janela usada no cálculo do
  snapshot; não é previsão de nova queda.

Boas respostas no Araquem:
- Se mencionar janelas de cálculo, deixar claro que os números exibem apenas o
  último valor consolidado (sem detalhamento por período) e qual benchmark foi
  usado.
- Explicar qualitativamente o que o número representa sem recomendar compra ou
  venda.
- Relacionar métricas de risco com contexto macro (juros, inflação) quando
  pertinente, usando conceitos de `data/concepts/concepts-risk*.yaml`.

Perguntas esperadas:
- "qual o Sharpe do HGRU11?"
- "beta e R² do KNRI11 em relação ao IFIX"
- "qual foi o máximo drawdown do MXRF11 nos últimos 12 meses?"
- "esse FII oscilou mais que o IFIX?"
