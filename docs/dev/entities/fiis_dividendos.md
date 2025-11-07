# fiis_dividendos

## Overview

- `id`: `fiis_dividendos`
- `result_key`: `dividendos_fii`
- `sql_view`: `fiis_dividendos`
- `private`: `false`
- `description`: Histórico de proventos (dividendos) por FII

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `payment_date` | Data de pagamento | Data em que o dividendo foi pago. |
| `dividend_amt` | Valor (R$ por cota) | Valor do dividendo/provento por cota. |
| `traded_until_date` | Data-com (cutoff) | Último dia com direito ao provento (data-com). |
| `created_at` | Criado em | Data de criação do registro. |
| `updated_at` | Atualizado em | Data da última atualização do registro. |

## Presentation

- `kind`: `table`
- `fields.key`: `payment_date`
- `fields.value`: `dividend_amt`
- `empty_message`: Sem dividendos para exibir.

## Response Templates

- `data/entities/fiis_dividendos/responses/table.md.j2`

## Ask Routing Hints

- `intents`: ``dividendos``
- `keywords`: ``dividendo, dividendos, provento, proventos, rendimento, rendimentos, pagamento, paga, pagou, yield, dy``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
  - `dividend_amt` → dividendo, provento, rendimento, yield, dy, valor
  - `payment_date` → pagamento, data de pagamento, paga, pagou
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
