# fiis_cadastro

## Overview

- `id`: `fiis_cadastro`
- `result_key`: `cadastro_fii`
- `sql_view`: `fiis_cadastro`
- `private`: `false`
- `description`: Dados cadastrais 1×1 de cada FII (admin, cnpj, site, classificação e atributos básicos)

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `fii_cnpj` | CNPJ | CNPJ do FII (identificador único). |
| `display_name` | Nome de exibição | Nome de exibição do FII (ex. nome comercial curto). |
| `b3_name` | Nome B3 | Nome de pregão na B3. |
| `classification` | Classificação | Classificação oficial do fundo. |
| `sector` | Setor | Setor de atuação do fundo. |
| `sub_sector` | Subsetor | Subsetor/indústria do fundo. |
| `management_type` | Tipo de gestão | Tipo de gestão do fundo. |
| `target_market` | Público-alvo | Público-alvo do fundo (Ex. Investidores em geral, Profissionais). |
| `is_exclusive` | Fundo exclusivo | Indica se o fundo é exclusivo (boolean). |
| `isin` | Código ISIN | Código ISIN do fundo. |
| `ipo_date` | Data IPO | Data do IPO do fundo. |
| `website_url` | Site oficial | URL oficial do fundo. |
| `admin_name` | Administrador | Nome do administrador do fundo. |
| `admin_cnpj` | CNPJ administrador | CNPJ do administrador do fundo. |
| `custodian_name` | Custodiante | Nome do custodiante do fundo. |
| `ifil_weight_pct` | Peso IFIL (%) | Peso do FII no IFIL, em percentual. |
| `ifix_weight_pct` | Peso IFIX (%) | Peso do FII no IFIX, em percentual. |
| `shares_count` | Nº de cotas emitidas | Quantidade total de cotas emitidas. |
| `shareholders_count` | Nº de cotistas | Quantidade de cotistas. |
| `created_at` | Criado em | Data de criação do registro. |
| `updated_at` | Atualizado em | Data da última atualização do registro. |

## Presentation

- `kind`: `list`
- `fields.key`: `ticker`
- `fields.value`: `display_name`
- `empty_message`: Nenhum cadastro encontrado.

## Response Templates

- `data/entities/fiis_cadastro/responses/list.md.j2`

## Ask Routing Hints

- `intents`: ``cadastro``
- `keywords`: ``cadastro, cnpj, administrador, administradora, site, custodiante, assembleia``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
  - `administrador` → admin, administradora
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
