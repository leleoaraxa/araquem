# client_fiis_positions

## Overview

- `id`: `client_fiis_positions`
- `result_key`: `positions`
- `sql_view`: `client_fiis_positions`
- `private`: `true`
- `description`: Posições do cliente em FIIs (PRIVADA; exige parâmetro document_number).

### Identifiers

- `document_number`: Documento do cliente (CPF/CNPJ)
- `position_date`: Data da posição
- `ticker`: Ticker do FII (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `document_number` | Documento | CPF/CNPJ do cliente (PII). |
| `position_date` | Data da posição | Data de referência. |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `fii_name` | Nome do FII | Nome do fundo. |
| `participant_name` | Participante | Corretora/participante. |
| `qty` | Quantidade | Quantidade em custódia. |
| `closing_price` | Preço fechamento | Preço de fechamento do dia. |
| `update_value` | Variação (R$) | Variação de valor. |
| `available_quantity` | Quantidade disp. | Quantidade disponível. |

## Presentation

- `kind`: `table`
- `fields.key`: `ticker`
- `fields.value`: `qty`
- `empty_message`: Sem posições disponíveis.

## Response Templates

- `data/entities/client_fiis_positions/responses/table.md.j2`

## Ask Routing Hints

- `intents`: ``metricas``
- `keywords`: ``minhas posicoes, minha carteira, posicao, quantidade, custodia, carteira de fii, carteira de fundos imobiliarios``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
