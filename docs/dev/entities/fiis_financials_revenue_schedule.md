# fiis_financials_revenue_schedule

## Overview

- `id`: `fiis_financials_revenue_schedule`
- `result_key`: `financials_revenue`
- `sql_view`: `fiis_financials_revenue_schedule`
- `private`: `false`
- `description`: Estrutura temporal de recebíveis e indexadores de receita por FII (percentuais sobre a receita).

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `revenue_due_0_3m_pct` | 0–3m (%) | Receita com vencimento em 0–3 meses. |
| `revenue_due_3_6m_pct` | 3–6m (%) | Receita com vencimento em 3–6 meses. |
| `revenue_due_6_9m_pct` | 6–9m (%) | Receita com vencimento em 6–9 meses. |
| `revenue_due_9_12m_pct` | 9–12m (%) | Receita com vencimento em 9–12 meses. |
| `revenue_due_12_15m_pct` | 12–15m (%) | Receita com vencimento em 12–15 meses. |
| `revenue_due_15_18m_pct` | 15–18m (%) | Receita com vencimento em 15–18 meses. |
| `revenue_due_18_21m_pct` | 18–21m (%) | Receita com vencimento em 18–21 meses. |
| `revenue_due_21_24m_pct` | 21–24m (%) | Receita com vencimento em 21–24 meses. |
| `revenue_due_24_27m_pct` | 24–27m (%) | Receita com vencimento em 24–27 meses. |
| `revenue_due_27_30m_pct` | 27–30m (%) | Receita com vencimento em 27–30 meses. |
| `revenue_due_30_33m_pct` | 30–33m (%) | Receita com vencimento em 30–33 meses. |
| `revenue_due_33_36m_pct` | 33–36m (%) | Receita com vencimento em 33–36 meses. |
| `revenue_due_over_36m_pct` | maior 36m (%) | Receita com vencimento acima de 36 meses. |
| `revenue_due_undetermined_pct` | Indeterminado (%) | Receita com vencimento indeterminado. |
| `revenue_igpm_pct` | IGPM (%) | Percentual de receitas indexadas ao IGPM. |
| `revenue_inpc_pct` | INPC (%) | Percentual de receitas indexadas ao INPC. |
| `revenue_ipca_pct` | IPCA (%) | Percentual de receitas indexadas ao IPCA. |
| `revenue_incc_pct` | INCC (%) | Percentual de receitas indexadas ao INCC. |
| `created_at` | Criado em | Data de criação. |
| `updated_at` | Atualizado em | Data da última atualização. |

## Presentation

- `kind`: `table`
- `fields.key`: `ticker`
- `fields.value`: `revenue_due_0_3m_pct`
- `empty_message`: Sem cronograma de receitas disponível.

## Response Templates

- `data/entities/fiis_financials_revenue_schedule/responses/table.md.j2`

## Ask Routing Hints

- `intents`: ``metricas``
- `keywords`: ``receitas, recebiveis, vencimento, estrutura de recebiveis, prazo, buckets, indexador, igpm, ipca, inpc, incc, duration da receita, cronograma de receitas``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
  - `revenue_ipca_pct` → ipca
  - `revenue_igpm_pct` → igpm
  - `revenue_inpc_pct` → inpc
  - `revenue_incc_pct` → incc
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
