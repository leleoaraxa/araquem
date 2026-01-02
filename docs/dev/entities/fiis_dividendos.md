# Entidade: `fiis_dividendos`

## 1. Objetivo

A entidade `fiis_dividendos` responde perguntas sobre **valores de dividendos/proventos por FII ao longo do tempo**, com foco em:

- Histórico de pagamentos (por data ou por mês/ano).
- Dividendos/proventos de um FII em um determinado período (ex.: ano, últimos 12 meses, últimos N meses).
- Último dividendo pago.
- Próximo dividendo já anunciado (quando disponível na base).
- Total de dividendos pagos em um intervalo (quando o builder fizer agregação).

Sempre em **valor absoluto por cota** (R$/cota), não em termos percentuais (para percentuais, o alvo é `fiis_yield_history` ou `fiis_dividends_yields`).

---

## 2. Perguntas típicas (CANON)

Exemplos CANON (devem cair em `fiis_dividendos`):

1. `lista de proventos do HGLG11`
2. `dividendos do CXTL11`
3. `proventos do CXTL11`
4. `rendimento do CXTL11` (quando o contexto é claramente “rendimento em proventos”, não percentual)
5. `quais foram os dividendos do KNRI11 em 2023?`
6. `quais foram os proventos do KNRI11 em 2023?`
7. `quais foram os rendimentos do KNRI11 em 2023?`
8. `dividendos pagos pelo KNRI11 em 2024`
9. `proventos pagos pelo KNRI11 em 2024`
10. `rendimentos pagos pelo KNRI11 em 2024`
11. `qual o valor do dividendo do KNRI11 pago em 2024?`
12. `quais os dividendos do HGLG11 esse mês?`
13. `total de dividendos do VISC11 nos últimos 6 meses`
14. `qual foi o último dividendo pago pelo MXRF11?`
15. `quais proventos o MXRF11 pagou em janeiro de 2025?`

---

## 3. Colunas e contratos

### 3.1. View e contrato

- **View SQL**: `fiis_dividendos`
- **Contrato em `data/contracts/entities`**: `fiis_dividendos` (tabela/contract padrão da entidade)

### 3.2. Colunas principais

| Coluna             | Tipo   | Descrição                                                                                  |
|--------------------|--------|--------------------------------------------------------------------------------------------|
| `ticker`           | text   | Ticker do FII no formato `AAAA11`.                                                         |
| `payment_date`     | date   | Data de pagamento do dividendo/provento.                                                  |
| `dividend_amt`     | number | Valor do dividendo/provento **por cota** (R$/cota).                                       |
| `traded_until_date`| date   | Último dia com direito ao provento (data-com, pregão em que o investidor precisa estar posicionado). |

Colunas técnicas adicionais (timestamps, chaves internas etc.) não entram na resposta final ao usuário, mas podem existir no contrato/view.

### 3.3. Semântica

- Cada linha representa **um pagamento de dividendo/provento** de um FII em uma data específica.
- O builder é responsável por:
  - Filtrar a janela de tempo (ex.: últimos 12 meses, ano calendário, mês específico).
  - Agregar, quando necessário (ex.: total no período, média mensal).

---

## 4. Regras de roteamento

### 4.1. Deve cair em `fiis_dividendos` quando…

1. A pergunta contém **ticker de FII** + algum termo relacionado a **dividendos/proventos/rendimentos em dinheiro**:
   - Tokens típicos: `dividendo`, `dividendos`, `provento`, `proventos`, `rendimento`, `rendimentos`, `distribuicao de rendimentos`, `pagamentos`, `data com`, `data ex`, `quanto distribuiu`, etc.
2. O usuário pede:
   - **Histórico de pagamentos**: “histórico de dividendos do HGLG11”, “dividendos pagos pelo KNRI11 em 2024”.
   - **Valores em um período**: “dividendos do MXRF11 nos últimos 12 meses”, “proventos em 2023”.
   - **Último / próximo pagamento**: “último dividendo do VISC11”, “próximo provento do MXRF11”.
3. A intenção é claramente **valor absoluto em R$/cota**, não percentual.

Exemplos de rota correta:

- `quais os dividendos do HGLG11 esse mês?` → `fiis_dividendos`
- `dividendos pagos pelo MXRF11 em 2024` → `fiis_dividendos`
- `lista de proventos do KNRI11` → `fiis_dividendos`
- `qual foi o último dividendo do VISC11?` → `fiis_dividendos`
- `quanto o HGLG11 distribuiu de dividendos em março de 2025?` → `fiis_dividendos`

### 4.2. Ticker

- Ticker deve ser reconhecido pelo intent `ticker_query` como um `AAAA11`.
- Perguntas sem ticker tendem a ser:
  - de carteira (`minha carteira`, `meus fiis`) → outras entidades (`client_fiis_dividends_evolution`, `client_fiis_enriched_portfolio`);
  - de ranking de dividendos/dy → `fiis_rankings` / `fiis_dividends_yields`.

### 4.3. Diferença para DY / Yield / Carteira

- Se a pergunta enfatiza **percentual**, `dy`, `dividend yield`, `dy 12m`, etc., o alvo padrão **não é** `fiis_dividendos`, e sim:
  - `fiis_yield_history` – histórico de DY.
  - `fiis_dividends_yields` – combinação de dividendos + DY, comparações, etc.
- Se a pergunta fala de **“meus dividendos”, “minha carteira”, “meus FIIs”**, o alvo deve ser:
  - `client_fiis_dividends_evolution` ou `client_fiis_enriched_portfolio`.

---

## 5. Casos que **NÃO** devem cair em `fiis_dividendos`

### 5.1. DY / Yield (percentual)

Devem ir para `fiis_yield_history` ou `fiis_dividends_yields`, não para `fiis_dividendos`:

- `dy do HGLG11 nos últimos 12 meses`
- `historico de dy do KNRI11`
- `dividend yield do MXRF11`
- `comparar dy de HGLG11 e KNRI11`
- `dy mensal do VISC11`

### 5.2. Dividendos da **minha carteira**

Devem ir para entidades de cliente (não para `fiis_dividendos`):

- `quanto minha carteira de fiis recebeu de dividendos em cada mes?` → `client_fiis_dividends_evolution`
- `renda mensal dos meus fiis` → `client_fiis_dividends_evolution` / `client_fiis_enriched_portfolio`
- `dividendos da minha carteira no último ano`

### 5.3. Comparações/Rankings

Quando o foco é **ranking/comparação de FIIs**, o alvo é `fiis_rankings` ou `fiis_dividends_yields`:

- `top fiis por dividend yield`
- `fiis com maior rendimento em dividendos`
- `ranking de fiis por dividendos`
- `comparar dividendos e dy do HGLG11 e KNRI11`

### 5.4. Macro / Indicadores / Índices

Perguntas sobre **IPCA, CDI, Selic, IFIX, IFIL, dólar, euro** não devem cair aqui:

- `impacto do ipca alto nos fiis` → `macro_consolidada`
- `historico do ipca nos ultimos anos` → `history_market_indicators`
- `quanto variou o ifix hoje?` → `history_b3_indexes`
- `variacao diaria do dolar` → `history_currency_rates`

---

## 6. Colisões principais e como separar

### 6.1. `fiis_dividendos` vs `fiis_yield_history`

- **fiis_dividendos**: responde valores **em R$** por cota.
  - Perguntas com foco em “quanto pagou”, “valor do dividendo”, “proventos pagos”.
- **fiis_yield_history**: responde **percentuais de DY**.
  - Perguntas com `dy`, `dividend yield`, `retorno percentual`, `yields`, `dy 12m`, `dy mensal`.

Regra prática:

- Se aparecer `dy`, `dividend yield`, `percentual`, a rota preferencial é `fiis_yield_history` ou `fiis_dividends_yields`, **não** `fiis_dividendos`.

### 6.2. `fiis_dividendos` vs `fiis_dividends_yields`

- **fiis_dividendos**: só valor em dinheiro, por FII, por data/período.
- **fiis_dividends_yields**: perguntas pedindo **dividendos + DY juntos**, ou comparações de **dividendos e dy** entre FIIs.

Exemplos que vão para `fiis_dividends_yields`:

- `dividendos e dy do HGLG11`
- `historico de dividendos e dividend yield do MXRF11`
- `comparar dividendos e dy de HGLG11 e KNRI11`

### 6.3. `fiis_dividendos` vs `client_fiis_dividends_evolution`

- **fiis_dividendos**: dados públicos, por FII, sem relação com carteira do cliente.
- **client_fiis_dividends_evolution**: dividendos **da carteira do cliente** (usa `document_number` seguro).

Sinais fortes de cliente:

- `minha carteira`, `meus fiis`, `meus dividendos`, `minha renda`, `quanto eu recebi`, etc.

Esses devem **NÃO** cair em `fiis_dividendos`.

---

## 7. Resumo operacional

- Usar `fiis_dividendos` para perguntas de **histórico de proventos por FII**, em valor absoluto.
- Evitar colisões com:
  - `fiis_yield_history` / `fiis_dividends_yields` (percentuais, DY).
  - `client_fiis_dividends_evolution` (minha carteira).
  - `macro_consolidada` / `history_*` (IPCA, CDI, IFIX, dólar/euro).
- O quality suite desta entidade vai focar em **perguntas CANON de proventos por FII** com ticker explícito.
