# Entidade: `macro_consolidada`

## 1. Objetivo

A entidade `macro_consolidada` centraliza, em uma única série temporal, os principais indicadores macroeconômicos e de mercado utilizados pelo Araquem para responder perguntas de **cenário macro**, **taxa de juros**, **inflação**, **índices de bolsa** e **câmbio**, bem como para explicar o impacto desse ambiente em **FIIs**.

Ela é a base numérica para o Narrator gerar respostas do tipo:

- “O que significa IPCA alto para FIIs?”
- “Como juros altos costumam afetar fundos imobiliários?”
- “Como está o cenário de juros, inflação e câmbio hoje para quem investe em FIIs?”

A ideia é ter uma **foto D-1 consolidada** de IPCA, Selic, CDI, IFIX, IBOV, dólar e euro, permitindo tanto respostas pontuais (valor em uma data) quanto narrativas sobre o ambiente macro que impacta FIIs.

---

## 2. Metadados da entidade

- **id**: `macro_consolidada`
- **result_key**: `macro_consolidada`
- **sql_view / tabela base**: `macro_consolidada`
- **Descrição (contrato)**: Histórico consolidado de indicadores macro, índices e câmbio (IPCA, Selic, CDI, IFIX, IBOV, USD, EUR), em base diária.

- **Chave temporal principal**:
  - `ref_date` — data de referência da observação (D, D-1 etc.)

---

## 3. Esquema de dados (contrato)

### 3.1. Estrutura do schema

Contrato em `data/contracts/macro_consolidada.schema.yaml` (versão 1):

- **Tipo raiz**: `object`
- **Descrição**: Histórico consolidado de indicadores macro, índices e câmbio.
- **Obrigatório**:
  - `ref_date`

### 3.2. Colunas principais

| Coluna          | Tipo     | Descrição                                                                                     |
|-----------------|----------|------------------------------------------------------------------------------------------------|
| `ref_date`      | date     | Data de referência (D, D-1, etc.).                                                            |
| `ipca`          | number?  | IPCA (usualmente variação ou nível do índice na data).                                        |
| `selic`         | number   | Taxa Selic (nível/meta/over diária consolidada para a data).                                  |
| `cdi`           | number?  | Taxa CDI na data (acumulado ou taxa diária equivalente).                                      |
| `ifix_points`   | number?  | Pontos do índice IFIX na data.                                                                |
| `ifix_var_pct`  | number?  | Variação percentual do IFIX no dia.                                                           |
| `ibov_points`   | number   | Pontos do índice Ibovespa (IBOV) na data.                                                     |
| `ibov_var_pct`  | number   | Variação percentual do IBOV no dia.                                                           |
| `usd_buy_amt`   | number   | Cotação de compra de USD (dólar comercial) na data.                                          |
| `usd_sell_amt`  | number   | Cotação de venda de USD na data.                                                              |
| `usd_var_pct`   | number   | Variação percentual do dólar no dia.                                                          |
| `eur_buy_amt`   | number   | Cotação de compra de EUR (euro comercial) na data.                                           |
| `eur_sell_amt`  | number   | Cotação de venda de EUR na data.                                                              |
| `eur_var_pct`   | number   | Variação percentual do euro no dia.                                                           |

Observações:

- Os campos com `nullable: true` no schema podem vir nulos dependendo da disponibilidade histórica.
- A entidade é **global** (não tem `ticker` nem `document_number`): ela descreve o ambiente econômico, não um ativo ou cliente específico.

---

## 4. Papel da `macro_consolidada` no roteamento

### 4.1. Quando deve cair em `macro_consolidada`

Use `macro_consolidada` quando a pergunta for sobre:

1. **Cenário macroeconômico e FIIs**:
   - Impacto de **juros altos/baixos** em FIIs.
   - Impacto de **IPCA/inflacao** sobre FIIs.
   - Discussões sobre **curva de juros** e ambiente de investimento em FIIs.

2. **Perguntas sobre taxa de juros / inflação (sem foco em um índice isolado)**:
   - “Como está o IPCA acumulado e a Selic hoje?”
   - “Qual é o cenário de inflação e juros no Brasil em 2025?”

3. **Relação macro x FIIs / mercado imobiliário**:
   - “Por que juros altos derrubam FIIs de tijolo?”
   - “Como a queda da Selic tende a impactar fundos imobiliários?”

4. **Visão consolidada de vários indicadores na mesma resposta**:
   - IPCA + Selic + CDI + IFIX + dólar, em um único panorama narrativo.

### 4.2. Diferença para entidades vizinhas

- **vs. `history_market_indicators`**
  - `history_market_indicators` é mais **numérica/histórica** para um indicador específico (IPCA, CDI, Selic etc., janelas, acumulados).
  - `macro_consolidada` é o **hub conceitual** de macro, com ênfase em **FIIs**, cenário e narrativa.
  - Perguntas conceituais como “O que significa IPCA alto para FIIs?” → `macro_consolidada`.
  - Perguntas puramente numéricas como “Qual foi o IPCA de março de 2025?” → `history_market_indicators`.

- **vs. `history_b3_indexes`**
  - `history_b3_indexes` fala de **pontos/variação de IFIX/IFIL/IBOV** com foco em histórico de índices.
  - `macro_consolidada` traz IFIX/IBOV junto com juros, inflação e câmbio, para responder sobre o **cenário macro geral**.

- **vs. `history_currency_rates`**
  - `history_currency_rates` responde “quanto está o dólar/euro hoje” ou série histórica específica.
  - `macro_consolidada` responde perguntas do tipo “como a alta do dólar entra no cenário macro para FIIs”.

---

## 5. Casos que NÃO devem cair em `macro_consolidada`

1. **Preço ou indicadores de FIIs específicos**
   - Perguntas com `ticker` focadas em preço, DY, dividendos, vacância, etc.
   - Ex.: “Quanto está o HGLG11 hoje?” → `fiis_precos`, não `macro_consolidada`.
   - Ex.: “Qual o DY do MXRF11 nos últimos 12 meses?” → `fiis_yield_history`.

2. **Carteira do cliente ou performance personalizada**
   - Ex.: “Como está a rentabilidade da minha carteira de FIIs vs IFIX?” → `client_fiis_performance_vs_benchmark`.
   - Ex.: “Dividendos mensais da minha carteira?” → `client_fiis_dividends_evolution` / `client_fiis_enriched_portfolio`.

3. **Histórico puro de um único indicador**
   - Ex.: “Histórico do IFIX nos últimos 6 meses” → `history_b3_indexes`.
   - Ex.: “Histórico do dólar comercial em 2025” → `history_currency_rates`.
   - Ex.: “IPCA de março de 2025” → `history_market_indicators`.

---

## 6. Exemplos canônicos de perguntas (macro_consolidada)

Alguns exemplos alinhados à ontologia (intent `macro_consolidada`):

- “O que significa IPCA alto para FIIs?”
- “Como juros altos costumam afetar fundos imobiliários?”
- “Como está o cenário macro hoje (Selic, IPCA, câmbio) para FIIs?”
- “Quais são as principais tendências de juros e inflação para investidores de FIIs?”
- “Como a queda da Selic tende a impactar FIIs de tijolo?”
- “Como a alta do dólar pode afetar FIIs de recebíveis?”
- “Me dá um panorama macro (Selic, IPCA, CDI, IFIX e dólar) pensando em FIIs.”

Essas perguntas devem ser usadas como referência para curadoria de `routing_samples.json` e para testes em `macro_consolidada_suite.json`.

---

## 7. Resumo operacional

- **Natureza**: entidade global, sem `ticker`, com dados D-1 consolidados de macro, índices e câmbio.
- **Uso principal**: responder perguntas conceituais e de cenário macro relacionadas a FIIs, usando números reais (IPCA, Selic, CDI, IFIX, IBOV, USD, EUR) como base para o Narrator.
- **Evitar colisões**:
  - Numérico puro → entidades `history_*`.
  - Ativo específico (FII) → entidades de FIIs (`fiis_*`, `fiis_overview`).
  - Carteira/cliente → entidades `client_*` / `client_fiis_enriched_portfolio`.

Com isso, `macro_consolidada` fica claramente posicionada como o “hub macro para FIIs” dentro da ontologia.
