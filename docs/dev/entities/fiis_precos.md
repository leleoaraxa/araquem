# fiis_precos

## Overview

- `id`: `fiis_precos`
- `result_key`: `precos_fii`
- `sql_view`: `fiis_precos`
- `private`: `false`
- `description`: Série diária de preços por FII (fechamento, abertura, variação, máxima e mínima)

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `traded_at` | Data de negociação | Data do pregão (yyyy-mm-dd). |
| `close_price` | Preço de fechamento | Preço de fechamento do dia. |
| `adj_close_price` | Fechamento ajustado | Preço de fechamento ajustado por eventos. |
| `open_price` | Preço de abertura | Preço de abertura do dia. |
| `max_price` | Máxima do dia | Maior preço negociado no dia. |
| `min_price` | Mínima do dia | Menor preço negociado no dia. |
| `daily_variation_pct` | Variação diária (%) | Variação percentual do dia vs. anterior. |
| `created_at` | Criado em | Data de criação do registro. |
| `updated_at` | Atualizado em | Data da última atualização do registro. |

## Presentation

- `kind`: `table`
- `fields.key`: `traded_at`
- `fields.value`: `close_price`
- `empty_message`: Sem preços para exibir.

## Response Templates

- `data/entities/fiis_precos/responses/table.md.j2`

## Ask Routing Hints

- `intents`: ``precos``
- `keywords`: ``preco, cotacao, abertura, fechar, fechamento, maxima, minima, variacao, diaria, hoje``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
  - `traded_at` → negociacao
  - `close_price` → fechamento, fechar
  - `adj_close_price` → ajustado
  - `open_price` → abertura, abrir
  - `max_price` → maxima, máxima
  - `min_price` → minima, mínima
  - `daily_variation_pct` → variacao, variação, variação diária, oscilação
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
