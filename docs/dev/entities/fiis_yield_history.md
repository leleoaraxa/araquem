# docs/dev/entities/fiis_yield_history.md

# fiis_yield_history — histórico de dividend yield (DY) mensal por FII

## 1. Visão geral

A entidade **fiis_yield_history** entrega o **histórico mensal de dividend yield (DY)** de um FII, sempre em base **D-1 / mês de referência**, com as seguintes colunas principais:

- `ticker`: código do fundo (ex.: `HGLG11`, `MXRF11`, `VISC11`).
- `ref_month`: mês de referência (normalizado como primeiro dia do mês, ex.: `2024-01-01` para jan/24).
- `dividends_sum`: soma dos dividendos pagos naquele mês (por cota).
- `price_ref`: preço de referência usado para cálculo do DY naquele mês.
- `dy_monthly`: **dividend yield mensal** naquele mês (dividends_sum / price_ref).

Exemplo real (HGLG11):

| ticker | ref_month  | dividends_sum | price_ref | dy_monthly |
|--------|------------|---------------|-----------|------------|
| HGLG11 | 2024-01-01 | 1.10          | 165.26    | 0.006656   |
| HGLG11 | 2024-02-01 | 1.10          | 169.99    | 0.006471   |

> Em termos de produto: esta entidade responde perguntas do tipo **"como o DY se comportou ao longo do tempo"** para um **único FII**.

---

## 2. Perguntas que DEVEM cair em fiis_yield_history

Regra mental: sempre que o usuário falar de **DY histórico / DY mensal / série de dividend yield de UM FII**, a rota correta é **fiis_yield_history**.

Padrões principais (sempre com ticker presente):

- Histórico de DY mensal:
  - “Qual o **DY histórico do HGLG11**?”
  - “Me mostra o **histórico de dividend yield do MXRF11**.”
  - “Quero ver o **DY por mês do VISC11**.”

- Janela de tempo (12m / 24m / desde ano X):
  - “Como foi o **DY mensal do HGLG11 nos últimos 12 meses**?”
  - “Qual foi o **DY do MXRF11 nos últimos 24 meses**?”
  - “Evolução do **dividend yield do VISC11 desde 2023**.”

- DY 12m / 24m, mas como série (não um único número agregado):
  - “Mostra o **DY 12m mês a mês do HGLG11**.”
  - “Gráfico com o **DY mensal do MXRF11** nos últimos 2 anos.”

- DY em um mês específico:
  - “Qual foi o **dividend yield do MXRF11 em outubro de 2024**?”
  - “DY de **janeiro de 2024 do VISC11**.”

Palavras-chave importantes que puxam esta entidade (junto com um ticker):

- `dy`, `dy mensal`, `dividend yield`, `historico de dy`, `evolucao do dy`,
- `dy 12m`, `dy 24m`, `serie historica de dy`, `dy ao longo do tempo`, `dy por mes`, `dy ultimo ano`.

---

## 3. Perguntas que NÃO devem cair em fiis_yield_history (mas são parecidas)

Aqui é onde costumam acontecer colisões semânticas:

### 3.1. Perguntas de **preço/cotação** → fiis_quota_prices

- “Quanto está o HGLG11 hoje?”
- “Como está o MXRF11 na B3 agora?”
- “Preço histórico do VISC11.”

Mesmo se o usuário não falar a palavra “preço” explicitamente, mas estiver perguntando **“quanto está”**, o destino é **fiis_quota_prices**, nunca fiis_yield_history.

---

### 3.2. Perguntas de **dividendos em dinheiro** → fiis_dividends

- “Quais foram os **dividendos do HGLG11 nos últimos 12 meses**?”
- “Quanto o **MXRF11 pagou de dividendos** em 2024?”
- “Histórico de **proventos do VISC11**.”

Se o foco é **valor pago de dividendos**, e não o DY (%) por mês, a rota é **fiis_dividends**.

---

### 3.3. Perguntas de **dividendos + DY / comparações de DY** → fiis_dividends_yields

- “Me mostra **dividendos e DY do HGLG11**.”
- “Comparação de **dividendos e dividend yield** entre HGLG11 e MXRF11.”
- “Quero ver um comparativo de **dividendos e dy** dos principais FIIs de logística.”

Esses casos devem cair em **fiis_dividends_yields** (comparativo / pacote dividendos + DY), não em fiis_yield_history.

---

### 3.4. Perguntas de **DY da carteira / meus FIIs** → client_fiis_enriched_portfolio

- “Qual o **DY dos meus FIIs**?”
- “DY mensal da **minha carteira de FIIs**.”
- “Renda e DY dos **meus FIIs**.”

Aqui o alvo é a visão **da carteira do cliente**, não de um único FII → entidade correta: **client_fiis_enriched_portfolio**.

---

### 3.5. Perguntas sobre **indicadores de risco** → fiis_financials_risk

- “Sharpe do HGLG11.”
- “Volatilidade do MXRF11.”
- “Sortino, beta, MDD do VISC11.”

Mesmo que o usuário fale de “retorno” ou “desempenho”, se o foco é **risco/índices**, a entidade é **fiis_financials_risk**, não fiis_yield_history.

---

## 4. Mapeamento pergunta → filtros/colunas

Abaixo alguns exemplos de como o Planner/Builder devem interpretar perguntas típicas para montar a query:

### 4.1. “Qual o DY histórico do HGLG11?”

- **Entidade**: fiis_yield_history
- **Filtros**:
  - `ticker = 'HGLG11'`
  - sem restrição de data explícita (padrão: pegar toda a série disponível ou janela default definida na camada de negócio)
- **Colunas principais**:
  - `ref_month`, `dy_monthly`
  - opcionalmente `dividends_sum`, `price_ref` para contexto adicional

---

### 4.2. “Como foi o DY mensal do HGLG11 nos últimos 12 meses?”

- **Entidade**: fiis_yield_history
- **Filtros**:
  - `ticker = 'HGLG11'`
  - `ref_month >= CURRENT_DATE - INTERVAL '12 months'`
- **Colunas**:
  - `ref_month`, `dy_monthly`

---

### 4.3. “Qual foi o dividend yield do MXRF11 em outubro de 2024?”

- **Entidade**: fiis_yield_history
- **Filtros**:
  - `ticker = 'MXRF11'`
  - `ref_month` dentro de `2024-10` (mês de outubro/24)
- **Colunas**:
  - `ref_month`, `dy_monthly`
  - `dividends_sum`, `price_ref` (se forem exibidos no detail)

---

### 4.4. “Me mostra o DY por mês do VISC11 nos últimos 24 meses.”

- **Entidade**: fiis_yield_history
- **Filtros**:
  - `ticker = 'VISC11'`
  - `ref_month >= CURRENT_DATE - INTERVAL '24 months'`
- **Colunas**:
  - `ref_month`, `dy_monthly`

---

## 5. Pontos de atenção semântica

1. **Evitar colisão com fiis_dividends_yields**
   - Se a pergunta trouxer expressões como:
     - “**dividendos e dy**”
     - “**comparacao de dividendos e dy**”
     - “**comparar dividendos e yield**”
   - → isso é **fiis_dividends_yields**, não fiis_yield_history.

2. **Evitar colisão com fiis_dividends**
   - Palavras como “**dividendos**, **proventos**, **quanto pagou**” sem foco claro em DY histórico indicam fiis_dividends.
   - A entidade fiis_yield_history tem **anti-tokens** para termos como:
     - “dy atual”, “ultimo dy”, “dividendos”, “dividendo”, “provento”, “proventos”, “acumulado”, “rendimento atual”, “yield atual”.
   - Ou seja, perguntas sobre **“DY atual / último DY”** tendem a ser tratadas em outra visão (ex.: fiis_dividends_yields ou snapshot / presenter), não aqui.

3. **Evitar confusão com índices de mercado (history_b3_indexes)**
   - Perguntas como:
     - “quanto está o IFIX hoje?”
     - “variação diária do IFIX”
   - Devem ir para **history_b3_indexes** (já coberto na suíte de negativos de índices), nunca para fiis_yield_history.

4. **Ticker obrigatório**
   - fiis_yield_history **sempre** precisa de um `ticker` (entidade individual).
   - Perguntas sem ticker, do tipo “DY médio dos FIIs de logística”, pertencem a outras visões agregadas (ex.: rankings, carteiras, etc.), não a esta entidade.

---

## 6. Checklist de qualidade para a suíte fiis_yield_history

A suíte `fiis_yield_history_suite.json` deve garantir:

1. **Cobertura de frases-chave de DY histórico**
   - “dy historico”, “historico de dy”, “dy mensal”, “dy 12m”, “evolucao do dy”, “dy ao longo do tempo”, sempre com ticker.

2. **Cobertura de janelas de tempo**
   - Perguntas com “ultimos 12 meses”, “ultimos 24 meses”, “desde 2023”, “em 2024”.

3. **Cobertura de mês específico**
   - Pelo menos 1–2 perguntas com “em outubro de 2024”, “em janeiro de 2023”, etc.

4. **Cobertura de múltiplos FIIs da base real**
   - Usar exemplos com `HGLG11`, `MXRF11`, `VISC11` (garantidos pelo sample do banco).

5. **Ausência de colisões óbvias**
   - Nenhuma pergunta da suíte deve conter:
     - “dividendos e dy”, “dividendos e yield”, “dy e dividendos”
     - “meus fiis”, “minha carteira”
     - “quanto está”, “preço hoje”
   - Para evitar que fiis_yield_history concorra com **fiis_dividends_yields**, **client_fiis_enriched_portfolio** ou **fiis_quota_prices**.

6. **Integração com o quality gate**
   - Ao rodar:
     - `python scripts/quality/quality_push.py data/ops/quality/payloads/fiis_yield_history_suite.json ...`
   - Esperado:
     - `matched = N` (todas as amostras)
     - `missed = 0`
   - E `quality_list_misses.py` **sem misses** para as perguntas de DY histórico.

---
