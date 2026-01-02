# Entidade `fiis_registrations`

## Visão geral

A entidade `fiis_registrations` expõe os **dados cadastrais estáticos** de cada FII listado, incluindo:

- Identificação básica: `ticker`, `fii_cnpj`, nomes de exibição e de pregão na B3
- Classificação e segmentação: `classification`, `sector`, `sub_sector`, `management_type`, `target_market`, `is_exclusive`
- Identificadores de mercado: `isin`, `ipo_date`, pesos em índices (`ifil_weight_pct`, `ifix_weight_pct`)
- Estrutura de administração: administrador e custodiante (`admin_name`, `admin_cnpj`, `custodian_name`)
- Informações de capital: `shares_count`, `shareholders_count`
- Metadados técnicos de carga: `created_at`, `updated_at`

É uma **foto atual do cadastro oficial** dos FIIs (sem histórico de versões).

---

## Metadados técnicos

- **id / intent principal**: `fiis_registrations`
- **result_key** (no payload do `/ask`): `fiis_registrations`
- **Origem física**: view/tabela `fiis_registrations` (schema público)
- **Grão**: 1 linha por `ticker`
- **Identificadores principais**:
  - `ticker` – código do FII no padrão `AAAA11`

A entidade é usada para responder perguntas do tipo:

- CNPJ do FII
- Nome de pregão / nome de exibição
- Classificação, setor, subsetor, tipo de gestão, público-alvo, exclusividade
- ISIN, data de IPO
- Peso em IFIX/IFIL
- Quantidade de cotas e número de cotistas
- Site oficial
- Dados do administrador e do custodiante

---

## Esquema de dados

### Tabela de colunas

| Coluna              | Tipo      | Nullable | Descrição                                                   |
|---------------------|----------|----------|-------------------------------------------------------------|
| `ticker`            | string   | false    | Código do FII (formato `AAAA11`).                          |
| `fii_cnpj`          | string   | false    | CNPJ do fundo.                                             |
| `display_name`      | string   | false    | Nome de exibição do fundo.                                 |
| `b3_name`           | string   | true     | Nome de pregão na B3.                                      |
| `classification`    | string   | true     | Classificação oficial do fundo.                            |
| `sector`            | string   | true     | Setor de atuação principal.                                |
| `sub_sector`        | string   | true     | Subsetor / indústria do fundo.                             |
| `management_type`   | string   | true     | Tipo de gestão (ex.: ativa, passiva).                      |
| `target_market`     | string   | true     | Público-alvo do fundo.                                     |
| `is_exclusive`      | boolean  | true     | Indica se o fundo é exclusivo.                             |
| `isin`              | string   | true     | Código ISIN do fundo.                                      |
| `ipo_date`          | date     | true     | Data do IPO do fundo.                                      |
| `website_url`       | string   | true     | Site oficial do fundo.                                     |
| `admin_name`        | string   | true     | Nome do administrador.                                     |
| `admin_cnpj`        | string   | true     | CNPJ do administrador.                                     |
| `custodian_name`    | string   | true     | Nome do custodiante.                                       |
| `ifil_weight_pct`   | number   | true     | Peso do fundo no índice IFIL (em %).                       |
| `ifix_weight_pct`   | number   | true     | Peso do fundo no índice IFIX (em %).                       |
| `shares_count`      | number   | true     | Quantidade total de cotas emitidas.                        |
| `shareholders_count`| number   | true     | Quantidade de cotistas do fundo.                           |
| `created_at`        | datetime | false    | Data de criação do registro de cadastro.                   |
| `updated_at`        | datetime | false    | Data da última atualização do cadastro.                    |

---

## Relação com a ontologia / intents

A entidade `fiis_registrations` é ativada pela intent homônima:

- **Intent**: `fiis_registrations`
- **Bucket**: `B` (grupo de entidades mais “estruturais / comparativas”)
- **Vocabulário-chave**:
  - Tokens típicos: `cadastro`, `cnpj`, `administrador`, `custodiante`, `site`, `url`, `nome de pregão`, `classificacao`, `setor`, `subsetor`, `gestao`, `publico alvo`, `isin`, `ipo`, `peso no ifix`, `peso no ifil`, `numero de cotas`, `numero de cotistas`, `fundo exclusivo` etc.
  - Frases típicas (exemplos):
    - `cnpj do <ticker>` / `qual o cnpj do <ticker>`
    - `administrador do <ticker>`
    - `custodiante do <ticker>`
    - `site do <ticker>` / `url oficial do <ticker>`
    - `nome de pregão do <ticker>` / `nome de exibição do <ticker>`
    - `classificacao do <ticker>`
    - `setor do <ticker>` / `subsetor do <ticker>`
    - `tipo de gestao do <ticker>`
    - `publico alvo do <ticker>`
    - `codigo isin do <ticker>`
    - `data do ipo do <ticker>`
    - `peso no ifix do <ticker>` / `peso no ifil do <ticker>`
    - `numero de cotas emitidas do <ticker>`
    - `numero de cotistas do <ticker>`

A ontologia exclui termos relacionados a **preço, dividendos, risco, ranking, vacância, DY, notícias, etc.**, para evitar colisão com outras intents como `fiis_precos`, `fiis_dividends`, `fiis_financials_snapshot`, `fiis_rankings`, `fiis_real_estate`, `fiis_news`.

---

## Exemplos de perguntas esperadas

Alguns exemplos de perguntas que devem rotear para `fiis_registrations`:

1. **CNPJ / identificação**
   - “Qual o CNPJ do HGLG11?”
   - “Me diga o CNPJ do fundo ALMI11.”

2. **Nome de pregão / exibição**
   - “Qual é o nome de pregão do HGLG11 na B3?”
   - “Qual é o nome de exibição do fundo ALMI11?”

3. **Classificação, setor, subsetor**
   - “Qual é a classificação oficial do XPLG11?”
   - “Qual o setor e o subsetor do HGLG11?”

4. **Gestão e público-alvo**
   - “O HGLG11 é um fundo de gestão ativa ou passiva?”
   - “Qual é o público-alvo do XPLG11?”

5. **ISIN e IPO**
   - “Qual é o código ISIN do HGLG11?”
   - “Qual foi a data do IPO do ALMI11?”

6. **Site oficial**
   - “Qual é o site oficial do fundo XPLG11?”

7. **Administrador / custodiante**
   - “Qual é o administrador e o CNPJ do administrador do HGLG11?”
   - “Quem é o custodiante do XPLG11?”

8. **Pesos em índices e capital**
   - “Qual é o peso do HGLG11 no IFIX e no IFIL?”
   - “Quantas cotas emitidas e quantos cotistas o HGLG11 possui?”
   - “O ALMI11 é um fundo exclusivo?”

Esses exemplos devem ser refletidos no arquivo de qualidade
`data/ops/quality/payloads/fiis_registrations_suite.json` para garantir o roteamento correto.
