# Entidade `client_fiis_performance_vs_benchmark`

## 1. Visão geral

A entidade `client_fiis_performance_vs_benchmark` traz a série de performance da carteira de FIIs do cliente comparada a um benchmark (ex.: IFIX, IFIL, IBOV, CDI). É **privada**, requerendo `document_number` vindo de contexto seguro.

Perguntas usuais:
- “Como foi a performance da minha carteira de FIIs versus o IFIX nos últimos 12 meses?”
- “Minha carteira está melhor ou pior que o CDI?”
- “Qual foi a rentabilidade da carteira contra o IFIL em 2024?”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `client_fiis_performance_vs_benchmark`.
- **Chave lógica**: `(document_number, benchmark_code, date_reference)`.
- **Granularidade temporal**: observação por data de referência.

Campos principais (do contrato `client_fiis_performance_vs_benchmark.schema.yaml`):
- `document_number` (PII) — identificador seguro do cliente.
- `benchmark_code` — código do benchmark (IFIX, IFIL, IBOV, CDI etc.).
- `date_reference` — data de referência.
- `portfolio_amount` — valor da carteira em R$ na data.
- `portfolio_return_pct` — retorno percentual da carteira.
- `benchmark_value` — nível/valor do benchmark na data.
- `benchmark_return_pct` — retorno percentual do benchmark.

## 3. Identificadores e sensibilidade

- **document_number**: obrigatório e sensível; não aparece em perguntas.
- **benchmark_code**: define a referência de comparação.
- **date_reference**: opcional para filtros de períodos.

## 4. Grupos de colunas

- **Performance da carteira**: `portfolio_amount`, `portfolio_return_pct`.
- **Benchmark**: `benchmark_code`, `benchmark_value`, `benchmark_return_pct`.
- **Tempo**: `date_reference`.

## 5. Exemplos de perguntas que devem cair em `client_fiis_performance_vs_benchmark`

- “Performance da minha carteira de FIIs versus o IFIX nos últimos 12 meses.”
- “Comparar o retorno da minha carteira de FIIs com o IFIL.”
- “Minha carteira de FIIs está melhor ou pior que o CDI?”
- “Qual foi a rentabilidade da minha carteira de FIIs versus o IFIX em 2024?”
- “Como a carteira performou frente ao IBOV no mês passado?”

## 6. Observações

- PII sempre via contexto autenticado.
- Foco em desempenho consolidado da carteira; perguntas de posições individuais ou renda mensal pertencem a outras entidades.
