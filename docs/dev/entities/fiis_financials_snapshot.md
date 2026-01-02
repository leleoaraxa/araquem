# Entidade `fiis_financials_snapshot`

## 1. Visão geral

A entidade `fiis_financials_snapshot` é a foto consolidada **D-1** de cada FII, com os principais indicadores econômico-financeiros do fundo, em nível de **fundo como um todo** (não por ativo individual).

Ela responde perguntas do tipo:

- “Qual o patrimônio líquido do HGLG11?”
- “Qual o valor patrimonial por cota do XPLG11?”
- “Qual a alavancagem atual do ALMI11?”
- “Qual a ABL e a vacância do HGLG11?”
- “Qual a receita total do fundo neste snapshot?”

Diferente de:

- `fiis_dividends`: histórico de pagamentos de dividendos (por data/pagamento).
- `fiis_quota_prices`: preço / cotação por dia.
- `fiis_real_estate`: detalhes por imóvel ou ativo (endereço, tipo, etc.).
- `fiis_financials_revenue_schedule`: cronograma de receitas futuras por bucket/prazo.

Aqui a visão é **agregada no tempo (D-1) e no fundo (por ticker)**, com métricas de estrutura de capital, patrimônio, receitas, ABL e vacância.

---

## 2. Origem dos dados e contrato

- **View/Tabela base**: `public.fiis_financials_snapshot`
- **Chave lógica**: `(ticker, ref_date)`
- **Granularidade temporal**: snapshot **D-1** (foto do dia anterior, uma linha por fundo/dia).
- **Uso típico**:
  - Consultas unitárias por ticker (ex.: “payout do HGLG11”).
  - Comparações simples entre fundos (via filtros por ticker na mesma data).
  - Painéis de diagnóstico (patrimônio, ABL, vacância, alavancagem).

Contrato de schema (resumido a partir de `data/contracts/fiis_financials_snapshot.schema.yaml`):

- `ticker`: código do fundo no formato `AAAA11`.
- `ref_date`: data de referência da foto (D-1).
- `pl_total`: patrimônio líquido total do fundo.
- `pl_per_share`: patrimônio líquido por cota (valor patrimonial por cota).
- `shares_total`: número total de cotas emitidas.
- `mkt_cap`: market cap (valor de mercado).
- `p_vp`: relação preço / valor patrimonial (P/VP).
- `div_reserve_total`: reserva de dividendos (quando existir).
- `payout_ratio`: payout (indicador de distribuição).
- `cash_total`: caixa total do fundo.
- `debt_total`: dívida total.
- `net_debt`: dívida líquida.
- `leverage_ratio`: alavancagem (dívida líquida / patrimônio / outro critério do contrato).
- `revenue_total`: receita total (aluguel + outras receitas, conforme contrato).
- `revenue_per_share`: receita por cota.
- `properties_count`: quantidade de imóveis/ativos (foto agregada).
- `abl_total`: área bruta locável total.
- `vacancy_physical`: vacância física.
- `vacancy_financial`: vacância financeira.
- `sector`: setor/setor ANBIMA (quando disponível).
- Outras colunas auxiliares e de controle, conforme schema.

---

## 3. Colunas – grupos semânticos

Para uso na documentação e no Narrator, é útil pensar em blocos de métricas:

### 3.1. Identificação

- `ticker`
- `ref_date`
- `sector` (quando existir no snapshot)

### 3.2. Patrimônio e valor por cota

- `pl_total` – patrimônio líquido total.
- `shares_total` – número de cotas.
- `pl_per_share` – valor patrimonial por cota (VP/cota).
- `mkt_cap` – valor de mercado.
- `p_vp` – relação preço / VP (P/VP).

### 3.3. Caixa, dívida e alavancagem

- `cash_total` – caixa.
- `debt_total` – dívida bruta.
- `net_debt` – dívida líquida.
- `leverage_ratio` – indicador de alavancagem (contrato define a fórmula).
- `div_reserve_total` – reserva de dividendos (quando preenchida).

### 3.4. Receita e renda operacional

- `revenue_total` – receita total do fundo na janela que alimenta o snapshot.
- `revenue_per_share` – receita por cota.
- Eventuais desdobramentos de receita, se previstos no schema (receita de aluguel, outras receitas, etc.).

### 3.5. Imóveis, ABL e vacância

- `properties_count` – quantidade de imóveis/ativos.
- `abl_total` – área bruta locável.
- `vacancy_physical` – vacância física.
- `vacancy_financial` – vacância financeira.

### 3.6. Metadados de cálculo

- Qualquer coluna que represente flags, versões de cálculo, ou campos auxiliares para reconciliar com outras visões (por exemplo, hashes, fontes de dados, carimbos de origem etc.), conforme o schema.

---

## 4. Exemplos de perguntas que devem cair em `fiis_financials_snapshot`

Foco: perguntas sobre **estrutura financeira, patrimônio, ABL, vacância, receita**, sempre em nível de fundo (não de imóvel específico, não de cronograma futuro e não de histórico longo).

Exemplos:

1. **Patrimônio / VP**
   - “Qual o patrimônio líquido do HGLG11?”
   - “Qual o valor patrimonial por cota do XPLG11?”
   - “Qual o P/VP atual do ALMI11?”

2. **Alavancagem / dívida**
   - “Qual o nível de alavancagem do HGLG11 hoje?”
   - “Quanto o XPLG11 tem de dívida e caixa?”
   - “O ALMI11 está muito alavancado?”

3. **Receitas / renda operacional**
   - “Qual a receita total do HGLG11 nesse último snapshot?”
   - “Qual a receita por cota do XPLG11?”
   - “Quanto o fundo ALMI11 gera de receita operacional?”

4. **ABL, vacância e ativos**
   - “Qual a ABL total do HGLG11?”
   - “Qual a vacância física do XPLG11?”
   - “Quantos imóveis o ALMI11 tem e qual a vacância financeira?”

5. **Combinações simples**
   - “Me dá um resumo financeiro do HGLG11 (PL, P/VP, alavancagem, vacância).”
   - “Quais os principais indicadores financeiros do XPLG11 hoje?”

Essas perguntas devem ser roteadas para o intent `fiis_financials_snapshot` e entidade `fiis_financials_snapshot`.

---

## 5. Regras de roteamento na ontologia (resumo)

Na ontologia (`data/ontology/entity.yaml`), o intent `fiis_financials_snapshot` está configurado com:

- **Tokens de include** típicos:
  - `snapshot`, `payout`, `alavancagem`, `leverage`, `market cap`, `patrimonio`, `patrimonio liquido`,
  - `valor patrimonial`, `vp`, `vp por cota`, `pl`, `caixa`, `passivos`, `cap rate`, `receita`, `renda`,
  - `ABL`, `area bruta locavel`, `vacancia`, `setor`, `contratos`, `imoveis`, `portfolio_imoveis`.

- **Phrases de include** (exemplos do contrato):
  - “payout do <ticker>”
  - “alavancagem do <ticker>”
  - “market cap do <ticker>”
  - “patrimonio liquido do <ticker>”
  - “valor patrimonial da cota do <ticker>”
  - “vacancia do <ticker>” / “ABL do <ticker>”
  - “receita total do <ticker>”, “contratos do <ticker>”, “imoveis do <ticker>” (no contexto financeiro consolidado).

- **Excludes principais** (para evitar colisão com outras entidades):
  - Termos de **preço** e variação intradiária → `fiis_quota_prices` (preco, cotacao, variacao, alta, baixa, hoje, ontem).
  - Termos de **dividendos / DY** → `fiis_dividends`, `fiis_yield_history`, `fiis_dividends_yields` (dividendo, dividendos, dy, yield, provento).
  - Termos de **notícias, processos, ranking** → roteados para `fiis_news`, `fiis_processos`, `fiis_rankings`.
  - Termos de **macro / índices / câmbio** → `history_market_indicators`, `history_b3_indexes`, `history_currency_rates`.

Resumindo: sempre que o usuário perguntar sobre **fundamentos financeiros agregados do fundo**, a entidade alvo é `fiis_financials_snapshot`.

---

## 6. Pontos de atenção e qualidade

1. **Foto D-1**
   - As respostas devem sempre ser interpretadas como “foto mais recente disponível” (D-1), mesmo que o usuário pergunte “hoje”.
   - Em textuais (Narrator), pode ser relevante explicitar a data `ref_date`.

2. **Zeros e valores nulos**
   - Alguns fundos podem não ter dívida (`debt_total = 0`) ou não ter imóveis físicos (FOF, FII de papel).
   - A lógica de apresentação deve deixar claro quando a métrica é zero real vs. dado ausente.

3. **Diferença para outras entidades**
   - Vacância/ABL aqui são indicadores consolidados; detalhes por imóvel ficam em `fiis_real_estate`.
   - Receitas futuras (por bucket) ficam em `fiis_financials_revenue_schedule`.
   - Indicadores de risco quantitativos (Sharpe, MDD, etc.) ficam em `fiis_financials_risk`.

4. **Suíte de qualidade**
   - A suíte `data/ops/quality/payloads/fiis_financials_snapshot_suite.json` garante que perguntas com termos como “patrimônio líquido”, “valor patrimonial”, “alavancagem”, “ABL”, “vacância”, “receita total” caiam corretamente em `fiis_financials_snapshot`.
  - Testes negativos (já cobertos em `negativos_indices_suite.json` e outras suítes) ajudam a evitar colisão com macro, índices e preço/dividendo.
