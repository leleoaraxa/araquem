## Descrição
Posições do investidor em FIIs, incluindo quantidades custodiadas, valores e participante responsável.

## Exemplos de perguntas
- "quais FIIs tenho na carteira?"
- "quantas cotas possuo de MXRF11?"
- "qual o valor total da posição de HGLG11?"

## Respostas usando templates
### list_header
Posições do documento **{document_number}**:

### list_basic
{position_date|date_br}: {ticker} — {qty|int_br} cotas (@ {closing_price|currency_br}); disponível {available_quantity|int_br}; Δ {update_value|currency_br} — {participant_name}

### FALLBACK_row
Não encontrei posições para o documento informado.
