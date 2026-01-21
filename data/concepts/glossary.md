# Glossário e Catálogo de Conceitos SIRIOS (FIIs)

## O que é o catálogo de conceitos?

- O catálogo de conceitos é a fonte de verdade em YAML que descreve termos e definições do domínio de FIIs na SIRIOS.
- Ele organiza conceitos como carteira do investidor, concentração e diversificação, risco e retorno, e outras noções usadas nas respostas.
- Quando alguém pergunta por “catálogo de conceitos” ou “glossário de termos”, o objetivo é encontrar esses conceitos base.
- Este documento ponte resume e referencia os conceitos já existentes no catálogo e nos contratos de entidade.

## Glossário de termos (exemplos)

- **catálogo de conceitos**: conjunto de definições do domínio SIRIOS, com nomes, aliases e descrições.
- **glossário de termos**: visão textual resumida para consultas humanas sobre conceitos e termos.
- **carteira do investidor**: conjunto de posições em FIIs de um cliente, usado para perguntas como “minha carteira”.
- **concentração e diversificação**: medida de distribuição da carteira por FII, setor e tipo de fundo.
- **posições do cliente (client_fiis_positions)**: entidade que representa as posições do investidor em FIIs.
- **carteira enriquecida (carteira_enriquecida / client_fiis_enriched_portfolio)**: visão enriquecida da carteira com atributos adicionais.
- **concepts_catalog**: referência ao catálogo de conceitos como fonte central de definições.

## Carteira do investidor: concentração e diversificação

- **Definição curta:** concentração e diversificação mostram como a carteira do investidor está distribuída entre FIIs, setores e tipos de fundos.
- **Termos relacionados:** carteira do investidor, client_fiis_positions, client_fiis_enriched_portfolio, conceitos de risco/retorno.
- **Perguntas típicas:**
  - “o que é concentração e diversificação?”
  - “minha carteira está concentrada em poucos FIIs?”
  - “como a carteira está distribuída por setor?”

## Como navegar pelos conceitos

- Se a consulta for sobre **glossário de termos**, procure pelo catálogo de conceitos e por esta visão resumida.
- Se a consulta mencionar **carteira do investidor**, busque conceitos ligados a client_fiis_positions.
- Se a consulta citar **concentração e diversificação**, o conceito está definido no domínio de carteira.

## Referências internas

- Catálogo de conceitos: concepts_catalog.
- Conceitos de carteira: “Carteira de FIIs do investidor” e “Concentração e diversificação”.
- Entidades relacionadas: client_fiis_positions, client_fiis_enriched_portfolio.

## Termos ligados a carteira e dados privados

- **carteira do investidor**: termos associados incluem “minha carteira” e “posições em FIIs”.
- **client_fiis_positions**: entidade base para posições individuais por FII.
- **fiis_registrations**: cadastro de FIIs usado como referência de identificação.
- **fiis_financials_snapshot**: métricas financeiras que ajudam a contextualizar posições.
- **fiis_financials_risk**: indicadores de risco associados aos ativos da carteira.

## Termos ligados a risco e retorno

- **risco e retorno da carteira**: conceito que consolida risco/retorno no nível da carteira.
- **histórico de índices (history_b3_indexes)**: referência para comparação com benchmarks.
- **indicadores macro (history_market_indicators)**: contexto macroeconômico para análises.

## Dicas rápidas para consultas

- Use “glossário de termos” quando buscar definições rápidas e exemplos de conceitos.
- Use “catálogo de conceitos” quando quiser a fonte de verdade com nomes e aliases.
- Use “carteira do investidor” para perguntas sobre posições, alocação e concentração.
- Use “concentração e diversificação” para distribuição por FII, setor e tipo.
