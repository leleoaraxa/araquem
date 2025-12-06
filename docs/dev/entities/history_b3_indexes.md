# Entidade: `history_b3_indexes`

Série histórica diária dos principais índices da B3 (IBOV, IFIX, IFIL), em pontos e variação percentual diária (D-1).
É uma entidade puramente de **índices de mercado**, sem relação direta com FIIs específicos.

---

## 1. Objetivo e escopo

**Objetivo:**
Responder perguntas sobre:

- Pontos de fechamento do **IBOV**, **IFIX** e **IFIL** em D-1.
- **Variação percentual diária** desses índices em um dia específico.
- Séries históricas recentes (últimos dias/meses) dos índices.
- Consultas pontuais do tipo “quanto variou o IFIX hoje (D-1)?”, “pontos do IBOV ontem”, “histórico recente do IFIL”.

**Não faz parte do escopo:**

- Peso/posição de FIIs no IFIX/IFIL (vai para `fiis_rankings` / `fiis_cadastro`).
- Comparações de desempenho de carteira vs IFIX/IFIL (vai para `client_fiis_performance_vs_benchmark`).
- Análises macroeconômicas gerais (IPCA, CDI, Selic, etc.) – isso é `history_market_indicators` / `macro_consolidada`.

---

## 2. Contrato de dados (`history_b3_indexes`)

### 2.1. Tabela / view

- **View:** `history_b3_indexes`
- **Grão:** 1 linha por **data** (D-1) com pontos e variação diária de cada índice (IBOV, IFIX, IFIL).

### 2.2. Colunas

| Coluna              | Tipo      | Obrigatória | Descrição                                                             |
|---------------------|-----------|------------|------------------------------------------------------------------------|
| `index_date`        | datetime  | não nula   | Data/hora da observação (D-1).                                        |
| `ibov_points_count` | number    | nula       | Pontos de fechamento do IBOV (arredondado, 0 casas decimais).         |
| `ibov_var_pct`      | number    | nula       | Variação percentual diária do IBOV.                                   |
| `ifix_points_count` | number    | nula       | Pontos de fechamento do IFIX (arredondado, 0 casas decimais).         |
| `ifix_var_pct`      | number    | nula       | Variação percentual diária do IFIX.                                   |
| `ifil_points_count` | number    | nula       | Pontos de fechamento do IFIL (arredondado, 0 casas decimais).         |
| `ifil_var_pct`      | number    | nula       | Variação percentual diária do IFIL.                                   |
| `created_at`        | datetime  | não nula   | Data de criação do registro.                                          |
| `updated_at`        | datetime  | não nula   | Data da última atualização do registro.                               |

**Ordering padrão:**
- `ORDER BY index_date DESC`

**Regras de formatação (sugeridas para presenter):**

- Datas: `index_date` em `DD/MM/YYYY`.
- Pontos: inteiros (sem casas decimais).
- Variações (%): com 2 casas decimais (ex.: `1,23%`, `-0,85%`).

---

## 3. Regras de roteamento / semântica

### 3.1. Intenção principal

- **Intent:** `history_b3_indexes`
- **Bucket:** C (índices / macro-histórico)
- **options.ignore_tickers:** `true` (não depende de FII específico).

### 3.2. Sinais positivos (tokens / frases típicas)

A entidade deve ser acionada quando a pergunta fala de:

- Índices da B3, **sem foco em ranking/peso de FIIs**, por exemplo:
  - “ibovespa”, “ibov”
  - “ifix”
  - “ifil”
  - “índice da b3”, “índices da b3”

- Perguntas de **pontos** e **variação diária**:
  - “pontos do ibov”
  - “pontos do ifix”
  - “pontos do ifil”
  - “variação diária do ibov”
  - “variação do ifix no dia”
  - “quanto variou o ifil hoje (D-1)”
  - “fechamento do ibov ontem”
  - “fechamento do ifix em D-1”

- Pedidos de **histórico recente** dos índices:
  - “histórico do ifix nos últimos dias”
  - “histórico recente do ibovespa”
  - “como o ifix se comportou em [período]”
  - “série histórica do ifil nos últimos 30 dias”

### 3.3. Exemplos de perguntas que devem cair em `history_b3_indexes`

- “Ibovespa hoje (D-1)”
- “Pontos do IFIX de ontem”
- “Quanto variou o IFIL no dia?”
- “Variação diária do IBOV”
- “Histórico recente do IFIX (D-1)”
- “Como o IFIX se comportou nas últimas 4 semanas?”
- “Qual foi a variação do IBOV ontem?”
- “Fechamento de hoje (D-1) do IFIL em pontos e %?”
- “Série histórica do IFIX nos últimos 10 pregões.”

---

## 4. Casos que **não** são `history_b3_indexes`

### 4.1. `fiis_rankings`

Se a pergunta envolver **posição/peso de FIIs** no IFIX/IFIL:

- “Qual a posição do HGLG11 no IFIX?”
- “Quais FIIs têm maior peso no IFIX?”
- “Ranking dos FIIs por peso no IFIL.”

→ Deve ir para **`fiis_rankings`** (não `history_b3_indexes`).

### 4.2. `fiis_cadastro`

Se for sobre **peso de um FII específico** no IFIX/IFIL como atributo cadastral:

- “Qual o peso do HGLG11 no IFIX e no IFIL?”
- “Peso do MXRF11 no IFIX.”

→ Preferência para **`fiis_cadastro`** / `fiis_rankings` (conforme contratos) – nunca `history_b3_indexes`.

### 4.3. `history_market_indicators` / `macro_consolidada`

Se falar de **IPCA, CDI, Selic, IGPM, INPC** etc:

- “Histórico do IPCA nos últimos 12 meses.”
- “CDI acumulado no ano.”
- “Taxa Selic ontem.”

→ Vai para **`history_market_indicators`** ou **`macro_consolidada`**, não `history_b3_indexes`.

---

## 5. Diretrizes de qualidade (suite de testes)

A suíte `history_b3_indexes_suite.json` deve garantir que:

1. Perguntas sobre **pontos e variação diária** de IBOV/IFIX/IFIL caiam em `history_b3_indexes`.
2. Perguntas de **histórico recente** dos índices também roteiem para `history_b3_indexes`.
3. Perguntas com “IFIX hoje”, “variou quanto o IBOV ontem” **não** colidam com:
   - `fiis_rankings` (ranking/peso de FIIs),
   - `history_market_indicators` (IPCA, CDI, Selic…),
   - nem com entidades de FIIs (`fiis_precos`, `fiis_dividendos`, etc.).
4. As frases de exemplo da ontologia (`sample_questions`) estejam cobertas no JSON de qualidade.

