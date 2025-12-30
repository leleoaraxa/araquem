## Descrição
Indicadores quantitativos de risco por FII, consolidados em métricas como volatilidade, Sharpe e MDD.

## Exemplos de perguntas
- "qual o Sharpe do HGLG11?"
- "esse fundo tem beta alto?"
- "qual o drawdown histórico do MXRF11?"

## Respostas usando templates
### list_basic
{ticker}: Vol {volatility_ratio|number_br}, Sharpe {sharpe_ratio|number_br}, Sortino {sortino_ratio|number_br}, Treynor {treynor_ratio|number_br}, Jensen {jensen_alpha|number_br}, Beta {beta_index|number_br}, MDD {max_drawdown|percent_br}, R² {r_squared|number_br}

### FALLBACK_row
Não encontrei indicadores de risco para {ticker}.
