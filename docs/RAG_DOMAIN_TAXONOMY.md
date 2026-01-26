# RAG domain taxonomy

## Objetivo

Definir a taxonomia de tags `domain:*` para segmentar conteúdo no RAG e isolar artefatos de engenharia via `rag:deny`.

## Convenção

- Formato: `domain:<area>_<subarea>`
- Lowercase, sem acentos, com `_` como separador.

## Lista inicial

- `domain:concepts_fiis`
- `domain:concepts_risk`
- `domain:concepts_macro`
- `domain:concepts_methodology`
- `domain:concepts_portfolio`
- `domain:engineering`
- `rag:deny` (tag de isolamento)
- Reservas: `domain:institutional_*`, `domain:support_*`

## Regras de uso

- Todo conteúdo de engenharia/ops/quality/golden deve receber `domain:engineering` **e** `rag:deny`.
- Conteúdos voltados ao usuário final **não** devem receber `rag:deny`.

## Exemplos rápidos

- `tags: ["domain:concepts_macro"]`
- `tags: ["domain:institutional_policies"]`
- `tags: ["domain:support_faq"]`
