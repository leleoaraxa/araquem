# fiis_imoveis

## Overview

- `id`: `fiis_imoveis`
- `result_key`: `imoveis_fii`
- `sql_view`: `fiis_imoveis`
- `private`: `false`
- `description`: Imóveis e propriedades de FIIs (dados operacionais 1×N)

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `asset_name` | Nome do ativo | Nome do imóvel ou ativo operacional do FII. |
| `asset_class` | Classe do ativo | Classe do ativo (ex. Imóveis para renda acabados, Imóveis para renda em construção). |
| `asset_address` | Endereço | Endereço ou localização do ativo. |
| `total_area` | Área total (m²) | Área total do imóvel em metros quadrados. |
| `units_count` | Unidades | Número de unidades/vagas/lojas do ativo. |
| `vacancy_ratio` | Vacância (%) | Percentual de vacância do ativo. |
| `non_compliant_ratio` | Inadimplência (%) | Percentual de inadimplência associado ao ativo. |
| `assets_status` | Status | Status operacional do ativo. |
| `created_at` | Criado em | Data de criação do registro. |
| `updated_at` | Atualizado em | Data da última atualização do registro. |

## Presentation

- `kind`: `list`
- `fields.key`: `asset_name`
- `fields.value`: `asset_class`
- `empty_message`: Nenhum imóvel encontrado.

## Response Templates

- `data/entities/fiis_imoveis/responses/list.md.j2`

## Ask Routing Hints

- `intents`: ``cadastro, imoveis``
- `keywords`: ``imovel, imóveis, propriedades, propriedade, ativos, portfolio, vacancia, ocupacao, unidades, area, metragem, endereco, localizacao, status operacional``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
