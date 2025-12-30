## Descrição
Séries históricas dos índices IBOV, IFIX e IFIL, com pontos e variação diária.

## Exemplos de perguntas
- "quanto fechou o IFIX ontem?"
- "qual foi a variação do IBOV na data X?"
- "mostrar IFIL da semana passada"

## Respostas usando templates
### list_basic
{index_date}: IBOV {ibov_points_count|number_br} pts ({ibov_var_pct|percent_br}); IFIX {ifix_points_count|number_br} pts ({ifix_var_pct|percent_br}); IFIL {ifil_points_count|number_br} pts ({ifil_var_pct|percent_br}).

### FALLBACK_row
Sem dados de índices para {index_date}.
