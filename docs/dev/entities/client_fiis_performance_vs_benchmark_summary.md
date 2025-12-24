# Entidade `client_fiis_performance_vs_benchmark_summary`

## 1. Visão geral

A entidade `client_fiis_performance_vs_benchmark_summary` entrega a **última leitura** da performance da carteira de FIIs do cliente por benchmark (IFIX, IFIL, IBOV, CDI), incluindo o excesso de retorno (carteira - benchmark). É **privada** e requer `document_number` vindo de contexto seguro.

Perguntas usuais:
- “Resumo da performance da minha carteira de FIIs versus o IFIX.”
- “Última leitura da carteira vs CDI.”
- “Performance acumulada vs IBOV (resumo).”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `client_fiis_performance_vs_benchmark_summary` (derivada da view histórica `client_fiis_performance_vs_benchmark`).
- **Chave lógica**: `(document_number, benchmark_code)` – apenas a linha mais recente por benchmark.
- **Granularidade temporal**: última data disponível por benchmark.

Campos principais (do contrato `client_fiis_performance_vs_benchmark_summary.schema.yaml`):
- `document_number` (PII) — identificador seguro do cliente.
- `benchmark_code` — código do benchmark (IFIX, IFIL, IBOV, CDI).
- `date_reference` — data de referência mais recente.
- `portfolio_amount` — valor da carteira em R$ na última data.
- `portfolio_return_pct` — retorno acumulado da carteira.
- `benchmark_value` — valor/nível do benchmark.
- `benchmark_return_pct` — retorno acumulado do benchmark.
- `excess_return_pct` — retorno da carteira menos retorno do benchmark (p.p.).

## 3. Identificadores e sensibilidade

- **document_number**: obrigatório e sensível; não aparece em perguntas.
- **benchmark_code**: define a referência de comparação.
- **date_reference**: indica a data mais recente exibida.

## 4. Observações

- PII sempre via contexto autenticado.
- A entidade é **resumo**: perguntas de série histórica continuam em `client_fiis_performance_vs_benchmark`.
- Não há suporte a multi-ticker; o identificador é `document_number`.
