## Descrição
`fii_overview` traz a visão consolidada (D-1) de cada FII: cadastro básico, indicadores financeiros, métricas de risco e posições em rankings.

## Exemplos de perguntas
- "resumo do HGLG11"
- "como está o KNRI11 hoje?"
- "me dê um overview do MXRF11"
- "mostre os principais indicadores do CPTS11"
- "compare rapidamente HGLG11 e VISC11"

## Respostas usando templates
### table_basic
Tabela com a identificação do FII (ticker, nome, setor), indicadores de rendimento (DY mensal e 12m, dividendos 12m, market cap), risco (Sharpe, Sortino, volatilidade, drawdown) e posições em rankings (SIRIOS, IFIX, IFIL, DY 12m).

### FALLBACK_row
Nenhum overview disponível para o {ticker} no momento.
