# fiis_processos

## Overview

- `id`: `fiis_processos`
- `result_key`: `processos_fii`
- `sql_view`: `fiis_processos`
- `private`: `false`
- `description`: Processos judiciais associados a FIIs (dados 1×N com risco e andamento)

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `process_number` | Número do processo | Identificador do processo judicial. |
| `judgment` | Julgamento | Situação ou fase de julgamento do processo. |
| `instance` | Instância | Instância em que o processo tramita. |
| `initiation_date` | Data de início | Data de distribuição ou início do processo. |
| `cause_amt` | Valor da causa | Valor envolvido na causa. |
| `process_parts` | Partes | Partes envolvidas no processo. |
| `loss_risk_pct` | Risco de perda (%) | Percentual estimado de risco de perda. |
| `main_facts` | Fatos principais | Principais fatos alegados ou descritos no processo. |
| `loss_impact_analysis` | Análise de impacto | Avaliação do impacto potencial do processo. |
| `created_at` | Criado em | Data de criação do registro. |
| `updated_at` | Atualizado em | Data da última atualização do registro. |

## Presentation

- `kind`: `list`
- `fields.key`: `process_number`
- `fields.value`: `judgment`
- `empty_message`: Nenhum processo encontrado.

## Response Templates

- `data/entities/fiis_processos/responses/list.md.j2`

## Ask Routing Hints

- `intents`: ``cadastro, processos``
- `keywords`: ``processo, processos, judicial, judiciais, andamento, status, litígio, litgio, causa, risco de perde, partes envolvidas, valor da causa, fatos principais, impacto, análise de impacto``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
