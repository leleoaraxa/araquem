# Entidade `client_fiis_dividends_evolution`

## 1. Visão geral

A entidade `client_fiis_dividends_evolution` apresenta a série mensal dos dividendos recebidos pelo cliente na carteira de FIIs. É **privada**, sempre dependente do `document_number` fornecido de forma segura.

Responde perguntas como:

- “Evolução dos dividendos da minha carteira de FIIs.”
- “Minha renda mensal com FIIs está crescendo?”
- “Quanto recebi de proventos em cada mês?”
- “Histórico de dividendos da minha carteira.”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `client_fiis_dividends_evolution`.
- **Chave lógica**: `(document_number, year_reference, month_number)`.
- **Granularidade temporal**: valores agregados por mês.
- **Uso típico**: análise de renda mensal, comparações ano a ano, acompanhamento de tendência de proventos.

Campos principais (do contrato `client_fiis_dividends_evolution.schema.yaml`):

- `document_number` (PII) — CPF/CNPJ obtido do contexto seguro.
- `year_reference` — ano de referência.
- `month_number` — número do mês (1–12).
- `month_name` — nome do mês.
- `total_dividends` — total de proventos do mês.

## 3. Identificadores e sensibilidade

- **document_number**: obrigatório e sensível; nunca aparece no texto da pergunta.
- **year_reference** e **month_number**: opcionais para filtros.

## 4. Grupos de colunas

- **Tempo**: `year_reference`, `month_number`, `month_name`.
- **Valor**: `total_dividends` (R$ por mês).
- **Metadados**: herdados da carga; não exibidos ao usuário final.

## 5. Exemplos de perguntas que devem cair em `client_fiis_dividends_evolution`

- “Renda mensal dos meus FIIs.”
- “Quanto minha carteira de FIIs recebeu de dividendos em cada mês?”
- “Evolução dos meus dividendos em FIIs.”
- “Histórico de dividendos da minha carteira.”
- “Dividendos mês a mês da minha carteira de FIIs.”

## 6. Observações

- PII tratada apenas via contexto seguro.
- A visão é mensal e não contém detalhes por FII específico; perguntas de DY ou por fundo caem em outras entidades.
