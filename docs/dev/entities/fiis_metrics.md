# fiis_metrics

## Overview

- `id`: `fiis_metrics`
- `result_key`: `fii_metrics`
- `sql_view`: `fiis_metrics`
- `private`: `false`
- `description`: Métricas compute-on-read por FII (base D-1 já garantida pela ingestão).

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Ticker | Código FII (AAAA11) |
| `metric` | Métrica | Nome canônico da métrica |
| `value` | Valor | Valor numérico da métrica |
| `window_months` | Janela (meses) | Tamanho da janela temporal |
| `period_start` | Início do período | Data inicial |
| `period_end` | Fim do período | Data final |

## Presentation

- `kind`: `summary`
- `fields.key`: `metric`
- `fields.value`: `value`
- `empty_message`: Sem métricas calculadas.

## Response Templates

- `data/entities/fiis_metrics/responses/summary.md.j2`

## Ask Routing Hints

- `intents`: ``metricas``
- `keywords`: ``dy, dividend yield, preço médio, soma dividendos, contagem de dividendos, media de preco``
- `synonyms`:
  - `dy_avg` → dy, dividend yield, yield
  - `dividends_sum` → soma de dividendos, soma proventos
  - `dividends_count` → quantidade de dividendos, contagem de dividendos
  - `price_avg` → preço médio, media de preco
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
