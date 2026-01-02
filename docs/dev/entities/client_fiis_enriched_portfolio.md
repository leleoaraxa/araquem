# client_fiis_enriched_portfolio — Carteira privada enriquecida com métricas financeiras, risco e rankings

## 1. Objetivo da entidade

A entidade `client_fiis_enriched_portfolio` representa a **foto consolidada da carteira de FIIs do cliente em uma data de posição**, já enriquecida com:

- valores financeiros (por ativo e carteira total),
- pesos relativos na carteira,
- informações cadastrais básicas do FII (nome, setor, segmento, CNPJ),
- métricas de renda (DY mensal e DY 12m, dividendos 12m),
- métricas de risco e retorno (volatilidade, Sharpe, Sortino, beta, max drawdown),
- rankings internos (posição SIRIOS, posição no IFIX, ranking por DY 12m, ranking por Sharpe).

É uma entidade **privada**, sempre filtrada por `document_number`, que deve ser obtido apenas via contexto seguro (nunca a partir do texto livre do usuário).

---

## 2. Grão, chaves e escopo

- **Grão**: uma linha por combinação de:
  - `document_number`
  - `position_date`
  - `ticker`

- **Chave lógica**:
  - `(document_number, position_date, ticker)`

- **Escopo temporal**:
  - Entidade de **snapshot D-1** da carteira enriquecida.
  - Cada linha reflete a situação da posição **na data de posição (`position_date`)**.

- **Relacionamentos típicos**:
  - Pode ser combinada com entidades públicas por `ticker`, como:
    - `fiis_precos` (histórico de preços),
    - `fiis_financials_risk` (métricas de risco públicas),
    - `fiis_financials_snapshot` (indicadores financeiros do fundo),
    - `fiis_cadastro` / `fiis_overview` (identidade e cadastro do fundo).
  - No entanto, para perguntas do tipo **“minha carteira”, “meus FIIs”, “valor investido”**, a entidade padrão deve ser `client_fiis_enriched_portfolio`.

- **Privacidade**:
  - `document_number` é PII e **nunca** deve ser inferido a partir de texto livre.
  - O roteador só deve chegar em `client_fiis_enriched_portfolio` quando a pergunta for claramente sobre:
    - “minha carteira de FIIs”,
    - “meus FIIs”,
    - “valor investido / peso / DY dos meus FIIs”,
    - rankings e métricas de risco dentro **da carteira do cliente**.

---

## 3. Colunas e contrato (`client_fiis_enriched_portfolio.schema.yaml`)

### 3.1. Metadados do schema

- `name`: `client_fiis_enriched_portfolio`
- `description`: `Carteira privada enriquecida com métricas financeiras, risco e rankings.`
- `type`: `object`
- `required`:
  - `document_number`
  - `position_date`
  - `ticker`

### 3.2. Colunas

| Coluna                | Tipo     | Descrição resumida                                                                                         |
|-----------------------|----------|-------------------------------------------------------------------------------------------------------------|
| `document_number`     | string   | Documento do cliente (CPF/CNPJ). Chave privada usada para filtrar a carteira do usuário.                   |
| `position_date`       | date     | Data de posição da carteira (snapshot da carteira nesse dia).                                              |
| `ticker`              | string   | Código do FII (formato `AAAA11`).                                                                           |
| `fii_name`            | string   | Nome do fundo imobiliário na B3.                                                                           |
| `qty`                 | integer  | Quantidade de cotas do FII na carteira do cliente.                                                         |
| `closing_price`       | number   | Preço de fechamento da cota na data de posição.                                                            |
| `position_value`      | number   | Valor financeiro da posição no FII (`qty * closing_price`).                                               |
| `portfolio_value`     | number   | Valor total da carteira de FIIs do cliente na data de posição.                                            |
| `weight_pct`          | number   | Peso percentual da posição na carteira (`position_value / portfolio_value`).                              |
| `sector`              | string   | Setor principal do FII (ex.: Logístico, Lajes Corporativas, Shoppings etc.).                              |
| `sub_sector`          | string   | Subsetor / segmento mais detalhado do FII.                                                                 |
| `classification`      | string   | Classificação do fundo (ex.: Tijolo, Papel, Híbrido, FoF etc.).                                           |
| `management_type`     | string   | Tipo de gestão (ex.: Ativa, Passiva).                                                                      |
| `target_market`       | string   | Público-alvo / mercado-alvo do fundo (ex.: Geral, Investidor Profissional).                               |
| `fii_cnpj`            | string   | CNPJ do fundo imobiliário.                                                                                 |
| `dy_12m_pct`          | number   | Dividend Yield de 12 meses da posição (percentual).                                                       |
| `dy_monthly_pct`      | number   | Dividend Yield mensal (percentual) atribuído ao FII/posição.                                              |
| `dividends_12m_amt`   | number   | Total de dividendos recebidos/pagos pelo FII nos últimos 12 meses (valor financeiro).                      |
| `market_cap_value`    | number   | Market cap estimado do FII (valor de mercado do fundo).                                                   |
| `equity_value`        | number   | Patrimônio líquido estimado do FII associado à posição.                                                   |
| `volatility_ratio`    | number   | Medida de volatilidade da cota do FII (índice de risco).                                                  |
| `sharpe_ratio`        | number   | Índice de Sharpe do FII (retorno ajustado ao risco).                                                      |
| `sortino_ratio`       | number   | Índice de Sortino do FII (foca em volatilidade negativa).                                                 |
| `max_drawdown`        | number   | Máximo drawdown histórico do FII (maior queda acumulada).                                                 |
| `beta_index`          | number   | Beta da cota em relação a um índice de referência (tipicamente IFIX).                                     |
| `sirios_rank_position`| integer  | Posição do FII em um ranking interno SIRIOS (ex.: ranking proprietário de qualidade).                     |
| `ifix_rank_position`  | integer  | Posição do FII dentro do IFIX (quando aplicável).                                                          |
| `rank_dy_12m`         | integer  | Ranking do FII por DY de 12 meses dentro do universo/peer definido.                                       |
| `rank_sharpe`         | integer  | Ranking do FII por Sharpe dentro do universo/peer definido.                                               |

---

## 4. Usos típicos e exemplos de perguntas

### 4.1. Perguntas-alvo para `client_fiis_enriched_portfolio`

Exemplos de perguntas que devem **rotear para `client_fiis_enriched_portfolio`**:

- “Me mostra a **visão consolidada da minha carteira de FIIs**.”
- “Quais são os **FIIs da minha carteira** e o **valor investido em cada um**?”
- “Qual é o **peso de cada FII** na minha carteira hoje?”
- “Qual é o **DY mensal dos meus FIIs**?”
- “Qual foi o **DY de 12 meses** da minha carteira de FIIs?”
- “Quais setores mais **pesam na minha carteira de FIIs**?”
- “Qual FII tem o **maior peso** na minha carteira hoje?”
- “Ranking dos meus FIIs por **DY 12m**.”
- “Ranking dos meus FIIs por **Sharpe**.”
- “Quais FIIs da **minha carteira** aparecem no IFIX e em que **posição**?”

### 4.2. Cuidados de uso (overlaps com outras entidades)

- Perguntas sobre **dividendos ao longo do tempo da carteira** (mês a mês, evolução, histórico) tendem a ser melhores candidatas a `client_fiis_dividends_evolution`.
- Perguntas sobre **performance da carteira vs. benchmark** (IFIX, CDI, etc.) são alvo de `client_fiis_performance_vs_benchmark`.
- Perguntas sobre **posições básicas, quantidades e custódia** (sem enriquecimento de risco/DY) podem ser alvo de `client_fiis_positions`.

Em caso de dúvida, use a seguinte regra prática:

- Se a pergunta fala em **“visão consolidada / meus FIIs / carteira de FIIs + DY / Sharpe / rankings internos”**, o alvo preferencial é `client_fiis_enriched_portfolio`.
