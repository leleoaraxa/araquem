## Descrição
Notícias recentes que mencionam FIIs, com título, fonte e data de publicação.

## Exemplos de perguntas
- "quais notícias saíram sobre VISC11?"
- "tem alguma matéria recente citando HGLG11?"
- "mostre as últimas manchetes do setor de shoppings"

## Respostas usando templates
### list_basic
{published_at|datetime_br}: {title} — {source} ({url})

### FALLBACK_row
Não encontrei notícias recentes para {ticker}.
