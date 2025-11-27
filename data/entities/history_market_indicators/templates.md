## Descrição
Séries históricas de indicadores de mercado como CDI, SELIC, IPCA e outros benchmarks.

## Exemplos de perguntas
- "qual foi o CDI ontem?"
- "quanto está o IPCA acumulado no último dado?"
- "mostrar a SELIC na data X"

## Respostas usando templates
### list_basic
{indicator_date}: {indicator_name} — {indicator_amt|number_br}

### FALLBACK_row
Sem dados para o indicador {indicator_name} em {indicator_date}.
