# Changelog - Concepts

## Mudanças

- Padronização do schema de todos os arquivos em `data/concepts/` para o formato
  `version + domain + owner + sections`.
- Normalização de `domain` para kebab-case e alinhamento entre arquivos de
  suporte e institucionais.
- Atualização do `catalog.yaml` para refletir 100% dos concepts atuais.
- Inclusão dos novos concepts no índice de embeddings.

## Unificações

- Unificação aplicada apenas no nível de estrutura (schema). Conteúdos de suporte
  e institucionais foram mantidos em arquivos separados para preservar
  granularidade e evitar regressões.

## Impactos esperados

- Baixo risco: mudanças apenas estruturais e de catalogação, sem alterar o
  conteúdo semântico das respostas.
