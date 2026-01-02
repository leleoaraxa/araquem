# Entidade: `fiis_rankings`

## 1. Objetivo

A entidade `fiis_rankings` consolida, em um único snapshot por FII, as **posições em rankings relativos** a:

- Engajamento / preferência de **usuários SIRIOS**;
- Ranking interno da **SIRIOS**;
- Participação em índices da B3 (**IFIX** e **IFIL**);
- Rankings quantitativos por características financeiras:
  - Dividend yield 12 meses (`rank_dy_12m`);
  - Dividend yield mensal (`rank_dy_monthly`);
  - Dividendos pagos em 12 meses (`rank_dividends_12m`);
  - Valor de mercado (`rank_market_cap`);
  - Patrimônio líquido (`rank_equity`);
  - Sharpe (`rank_sharpe`);
  - Sortino (`rank_sortino`);
  - Menor volatilidade (`rank_low_volatility`);
  - Menor drawdown (`rank_low_drawdown`).

Ela responde perguntas como:

- “Qual a **posição atual do HGLG11 no ranking de usuários**?”
- “Como está a **posição do HGLG11 no ranking da SIRIOS**?”
- “O **FPAB11 já fez parte do IFIX**?”
- “Quais são os **FIIs com melhor Sharpe** hoje?”
- “Quais são os **FIIs com menor volatilidade**?”

Camada de dados:

- **View SQL**: `fiis_rankings`
- **Grão**: 1 linha por FII (`ticker`).
- **Atualização**: foto D-1 (mesma política das demais entidades de FIIs).

---

## 2. Quando usar esta entidade (roteamento ideal)

O Planner deve priorizar `fiis_rankings` quando a pergunta envolver **posição relativa, ranking, top/bottom ou destaque** de FIIs, especialmente nos seguintes contextos:

### 2.1. Rankings de usuários / SIRIOS

- “Qual a posição atual do HGLG11 no ranking de usuários?”
- “Como está a posição do HGLG11 no ranking da SIRIOS?”
- “Como evoluiu a posição do HGRU11 no ranking de usuários ao longo do tempo?”
  *(mesmo que a view não traga histórico, o roteamento correto é para `fiis_rankings`)*

### 2.2. Rankings IFIX / IFIL

- “Qual é hoje a posição do HGRU11 no ranking do IFIL?”
- “O FPAB11 já fez parte do IFIX?”
- “Quais FIIs têm posição relevante no IFIX/IFIL?”

### 2.3. Rankings por métricas financeiras

- “Ranking dos FIIs com melhor Sharpe ratio.”
- “Top FIIs por menor volatilidade.”
- “Quais FIIs têm o **maior dividend yield 12 meses**?”
- “Quais FIIs têm o **maior valor de mercado**?”
- “Quais FIIs têm **maior patrimônio líquido**?”

Essas perguntas se alinham diretamente a:

- `intents.fiis_rankings.tokens.include` e `phrases.include` na ontologia;
- `sample_questions` definidos no schema.

---

## 3. Quando **não** usar (anti-conflitos)

O Planner **não** deve usar `fiis_rankings` quando a pergunta for sobre:

1. **Preço / cotação / variação diária**:
   - “Quanto está o HGLG11 hoje?” → `fiis_precos`
   - “Quais FIIs mais subiram hoje?”
     *(apesar de parecer um ranking, é ranking de preço diário → hoje está mais próximo de `fiis_precos` / futura entidade intraday; por ora, evitar empurrar tudo para `fiis_rankings` se o foco for preço.)*

2. **Dividendos ou yield de um FII específico (nível absoluto)**:
   - “Quanto o HGLG11 pagou de dividendos este mês?” → `fiis_dividends`
   - “Qual o DY do HGLG11 nos últimos 12 meses?” → `fiis_yield_history` / `fiis_dividends_yields`.

3. **Dados financeiros do FII (PL, VP/cota, vacância, caixa, dívida)**:
   - “Qual o patrimônio líquido do HGLG11?” → `fiis_financials_snapshot`
   - “Qual a vacância do HGLG11?” → `fiis_financials_snapshot`

4. **Estrutura de receitas futuras / recebíveis**:
   - “Como está distribuída a receita futura do HGLG11?” → `fiis_financials_revenue_schedule`.

5. **Imóveis / portfólio físico**:
   - “Quais são os imóveis do HGLG11?” → `fiis_imoveis`.

6. **Notícias / fatos relevantes**:
   - “Teve alguma notícia recente sobre o HGLG11?” → `fiis_noticias`.

Regra prática:
Se o foco é **“quem está em primeiro / último / top N, posição, ranking, destaque, campeões, lanternas, melhor/pior desempenho relativo”**, a entidade correta é `fiis_rankings`.
Se o foco é **valor absoluto**, use a entidade especializada (preços, dividendos, snapshot, risco, etc.).

---

## 4. Colunas e semântica dos campos

Fonte: `data/contracts/fiis_rankings.schema.yaml` e amostra `fiis_rankings.csv`.

| Coluna                     | Tipo     | Semântica prática                                                                 |
|----------------------------|----------|------------------------------------------------------------------------------------|
| `ticker`                   | string   | Código do FII (AAAA11).                                                            |
| `users_rank_position`      | integer  | Posição do FII no ranking de **usuários** da SIRIOS (ex.: 1 = mais bem posicionado). |
| `users_rank_net_movement`  | integer  | Variação líquida de posição do FII em rankings de usuários (subidas – quedas).    |
| `sirios_rank_position`     | integer  | Posição do FII no ranking **interno da SIRIOS**.                                   |
| `sirios_rank_net_movement` | integer  | Movimentos de posição do FII no ranking SIRIOS em recortes de tempo.              |
| `ifix_rank_position`       | integer  | Posição do FII no ranking do **IFIX**.                                             |
| `ifix_rank_net_movement`   | integer  | Movimentos de posição do FII no ranking do IFIX.                                   |
| `ifil_rank_position`       | integer  | Posição do FII no ranking do **IFIL**.                                             |
| `ifil_rank_net_movement`   | integer  | Movimentos de posição do FII no ranking do IFIL.                                   |
| `rank_dy_12m`              | integer  | Posição do FII no ranking por **dividend yield 12 meses** (1 = maior DY 12m).      |
| `rank_dy_monthly`          | integer  | Posição no ranking por **dividend yield mensal**.                                  |
| `rank_dividends_12m`       | integer  | Posição no ranking por **dividendos pagos em 12 meses** (valor absoluto R$).      |
| `rank_market_cap`          | integer  | Posição no ranking por **valor de mercado**.                                       |
| `rank_equity`              | integer  | Posição no ranking por **patrimônio líquido**.                                     |
| `rank_sharpe`              | integer  | Posição no ranking por **Sharpe ratio** (1 = melhor Sharpe).                       |
| `rank_sortino`             | integer  | Posição no ranking por **Sortino ratio**.                                          |
| `rank_low_volatility`      | integer  | Posição no ranking por **menor volatilidade** (1 = menor volatilidade).           |
| `rank_low_drawdown`        | integer  | Posição no ranking por **menor drawdown** (1 = menor drawdown histórico).         |
| `created_at`               | datetime | Data de criação do registro na view.                                              |
| `updated_at`               | datetime | Data da última atualização do registro.                                           |

Observações importantes:

- Todos os `*_position` são **números ordinais** (1, 2, 3, …).
- Campos `*_net_movement` indicam variação líquida de posição em uma janela (ex.: mês, ano) – interpretação contextual deve ser feita pelo Narrator.
- Não há métricas de valor absoluto aqui (preço, PL, DY); somente **posição relativa** em rankings.

---

## 5. Exemplos de perguntas-alvo (Planner / Routing)

Sugestões de perguntas que **devem** cair em `fiis_rankings`:

1. “Qual a posição atual do HGLG11 no ranking de usuários?”
2. “Como está a posição do HGLG11 no ranking da SIRIOS?”
3. “Qual é hoje a posição do HGRU11 no ranking do IFIL?”
4. “Como foi a variação de posição do HGLG11 no ranking da SIRIOS neste ano?”
5. “O FPAB11 já fez parte do IFIX?”
6. “Ranking dos FIIs com melhor Sharpe ratio.”
7. “Top FIIs por menor volatilidade.”
8. “Quais FIIs têm maior dividend yield 12 meses?”
9. “Quais FIIs têm o maior valor de mercado?”
10. “Quais FIIs têm maior patrimônio líquido?”
11. “Quais são os FIIs com menor drawdown?”
12. “Quais setores ou FIIs se destacam no ranking da SIRIOS este mês?”

Essas perguntas são coerentes com:

- `intents.fiis_rankings.tokens.include` (ranking, top, melhores, piores, campeões, lanternas, desempenho relativo).
- `intents.fiis_rankings.phrases.include` (ranking por DY, ranking no IFIX/IFIL, top N por métrica).

---

## 6. Notas para o Planner / Builder

- `fiis_rankings` está no **bucket B** da ontologia (grupo de entidades “ranking / carteira / cliente”) e compartilha o identificador `ticker` com as demais entidades de FIIs.
- Palavras-chave de ativação típicas:
  - “ranking”, “rank”, “posição”, “posicao”, “top”, “melhores”, “piores”, “maiores”, “menores”, “destaques”, “campeões”, “lanternas”;
  - menções a Sharpe, Sortino, volatilidade, drawdown, DY 12m, dividendos 12m etc., quando o foco é **ranking global** e não um único fundo.
- Anti-conflitos relevantes:
  - Termos de preço puro (quanto está, cotação, variação diária) → `fiis_precos`.
  - Termos de snapshot financeiro (PL, VP/cota, vacância, caixa) → `fiis_financials_snapshot`.
  - Termos de fluxo de dividendos (“quanto pagou”, “dividendos do HGLG11 em…”) → `fiis_dividends`, `fiis_yield_history`, `fiis_dividends_yields`.

O Builder deve:

- Utilizar sempre `ticker` como filtro quando a pergunta envolve um fundo específico.
- Para perguntas de ranking global (ex.: “top 5 FIIs por Sharpe”), selecionar ordenação apropriada (`rank_sharpe ASC`) e limitar o número de linhas (ex.: top 5, top 10), conforme regra de negócio definida fora da ontologia.

---

## 7. Notas para o Narrator / Presenter

- Deixar claro que a resposta está baseada em **ranking relativo** e não em valores absolutos.
- Em respostas com top N:
  - Explicar brevemente o critério (ex.: “Sharpe maior”, “menor volatilidade”, “maior DY 12m”).
  - Evitar linguagem prescritiva (“melhor investimento garantido”); focar em **comparação objetiva**.
- Quando usar `*_net_movement`:
  - Explicar em linguagem natural: “subiu X posições em relação ao período anterior” ou “perdeu Y posições”.
- Em rankings ligados a risco (volatilidade, drawdown):
  - Deixar claro que **menor valor é melhor** no contexto do ranking (ex.: menor volatilidade, menor drawdown).

