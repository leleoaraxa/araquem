# Entidade `history_market_indicators`

## 1. Visão geral

`history_market_indicators` reúne indicadores macroeconômicos diários em base D-1 (IPCA, CDI, SELIC, IGPM etc.), com valor numérico por data.

Perguntas típicas:
- “Qual a SELIC hoje?”
- “CDI D-1.”
- “Qual foi o IPCA do dia?”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `history_market_indicators`.
- **Chave lógica**: `(indicator_date, indicator_name)`.
- **Granularidade temporal**: D-1, uma linha por indicador/data.

Campos principais (do contrato `history_market_indicators.schema.yaml`):
- `indicator_date` — data da observação.
- `indicator_name` — nome/sigla do indicador (IPCA, CDI, SELIC, IGPM, INCC etc.).
- `indicator_amt` — valor/taxa do indicador.
- `created_at`, `updated_at` — metadados de carga.

## 3. Identificadores

- **indicator_date** e **indicator_name** compõem a chave e podem ser usados em filtros.

## 4. Grupos de colunas

- **Identificação**: `indicator_name`.
- **Valor**: `indicator_amt`.
- **Tempo/Metadados**: `indicator_date`, `created_at`, `updated_at`.

## 5. Exemplos de perguntas que devem cair em `history_market_indicators`

- “SELIC hoje.”
- “CDI do dia.”
- “IPCA D-1.”
- “Qual o IGPM atual?”
- “Taxa do INCC hoje.”

## 6. Observações

- Indicadores estão em base D-1; não cobrem intraday.
- Intent dedicado a indicadores macro; perguntas de câmbio ou FIIs devem ser roteadas para suas entidades específicas.
