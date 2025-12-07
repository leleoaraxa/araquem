# Entidade `client_fiis_positions`

## 1. Visão geral

A entidade `client_fiis_positions` registra as posições do cliente em FIIs em uma data de referência, com quantidade em custódia, preço médio, rentabilidade e peso por fundo. É uma visão **privada**, dependente do `document_number` recebido de forma segura (nunca digitado pelo usuário).

Ela responde perguntas como:

- “Minhas posições de FIIs hoje?”
- “Qual o peso do HGLG11 na minha carteira?”
- “Em qual corretora estão minhas cotas do XPML11?”
- “Quanto tenho de quantidade em custódia de MXRF11?”
- “Qual o meu preço médio em CPTS11?”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `client_fiis_positions`.
- **Chave lógica**: `(document_number, position_date, ticker)`.
- **Granularidade temporal**: foto da posição na data (`position_date`).
- **Uso típico**: consultas por carteira do cliente, distribuição por FII, corretora de custódia, peso na carteira e rentabilidade da posição.

Campos principais (do contrato `client_fiis_positions.schema.yaml`):

- `document_number` (PII via contexto seguro) — identificador do cliente.
- `position_date` — data da posição.
- `ticker` — código do FII (AAAA11).
- `fii_name` — nome do fundo.
- `participant_name` — corretora/participante custodiante.
- `qty` / `available_quantity` — quantidade total e disponível de cotas.
- `closing_price` — preço de fechamento do dia.
- `average_price` — preço médio do cliente.
- `profitability_percentage` — rentabilidade da posição.
- `percentage` — peso do fundo na carteira.
- `update_value` — variação de valor da posição (R$).
- `created_at`, `updated_at` — metadados de carga.

## 3. Identificadores e sensibilidade

- **document_number**: obrigatório e sensível (CPF/CNPJ), sempre obtido via payload seguro.
- **position_date**: opcional para filtros de referência.
- **ticker**: identificador de ativo, sem PII.

## 4. Grupos de colunas úteis

- **Identificação**: `document_number`, `position_date`, `ticker`, `fii_name`, `participant_name`.
- **Quantidade e custódia**: `qty`, `available_quantity`.
- **Preço e rentabilidade**: `closing_price`, `average_price`, `profitability_percentage`, `update_value`.
- **Alocação**: `percentage` (peso na carteira).
- **Metadados**: `created_at`, `updated_at`.

## 5. Exemplos de perguntas que devem cair em `client_fiis_positions`

- “Minhas posições na B3.”
- “Distribuição da minha carteira de FIIs por fundo.”
- “Peso do XPML11 na minha carteira de FIIs.”
- “Em qual corretora estão minhas cotas de HGLG11?”
- “Qual meu preço médio do MXRF11?”
- “Rentabilidade da minha posição em VISC11.”

## 6. Observações

- PII nunca deve aparecer no texto da pergunta; `document_number` vem do contexto autenticado.
- Os dados são de posição consolidada por dia; perguntas de performance histórica longa pertencem a outras entidades.
