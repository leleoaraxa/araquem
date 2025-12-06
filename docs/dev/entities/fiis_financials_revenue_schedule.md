# Entidade: `fiis_financials_revenue_schedule`

## 1. Objetivo

A entidade `fiis_financials_revenue_schedule` consolida o **cronograma de receitas futuras** dos FIIs, em termos de **percentual da receita contratada por faixa de vencimento** e por **indexador** (IPCA, IGPM, INPC, INCC).

Ela responde perguntas como:

- Qual é o **cronograma de recebimento de receitas** de um FII ao longo dos próximos meses/anos.
- Qual a **concentração de receitas** em prazos curtos (0–12 meses) versus longos (acima de 36 meses).
- Qual o **percentual de receitas indexadas** a IPCA, IGPM, INPC ou INCC.
- Como a **estrutura de recebíveis** de dois ou mais FIIs se compara em termos de prazo e indexador.

Camada de dados:

- **View SQL**: `fiis_financials_revenue_schedule`
- **Grão**: 1 linha por FII (`ticker`).
- **Atualização**: foto D-1 (mesmo padrão das demais entidades financeiras de FIIs).

---

## 2. Quando usar esta entidade (roteamento ideal)

O Planner deve priorizar `fiis_financials_revenue_schedule` quando a pergunta envolver, de forma clara, **cronograma de receitas futuras / recebíveis** de um FII, especialmente com foco em:

- **Prazo de vencimento** das receitas:
  - “Cronograma de receitas do HGLG11.”
  - “Receitas com vencimento em 6–9 meses do KNRI11.”
  - “Qual parte das receitas do VISC11 vence acima de 36 meses?”

- **Indexador das receitas**:
  - “Percentual de receitas do HGLG11 indexadas ao IPCA.”
  - “Receitas indexadas ao IGPM do RBRF11.”
  - “Quanto das receitas do BCFF11 está atrelado ao INPC ou INCC?”

- **Estrutura de recebíveis / qualidade de contratos**:
  - “A receita do LRDI11 está mais concentrada no curto ou no longo prazo?”
  - “Comparar a estrutura de recebíveis de HGLG11 e XPLG11.”

Essas perguntas são coerentes com:

- `intents.fiis_financials_revenue_schedule.tokens` (receita, recebíveis, vencimento, cronograma, IPCA, IGPM, INPC, INCC etc.).
- `sample_questions` definidos no schema da entidade.

---

## 3. Quando **não** usar (anti-conflitos)

O Planner **não** deve usar `fiis_financials_revenue_schedule` quando:

1. A pergunta é sobre **preço de cota, variação diária ou histórico de preços**:
   - “Quanto está o HGLG11 hoje?” → `fiis_precos`
   - “Qual foi a variação do HGLG11 nos últimos 12 meses?” → `fiis_precos` / `fiis_rankings`.

2. A pergunta é sobre **dividendos pagos, yield ou histórico de distribuição**:
   - “Quanto o HGLG11 pagou de dividendos este mês?” → `fiis_dividendos`
   - “Qual o DY médio do HGLG11 em 2024?” → `fiis_yield_history` ou `dividendos_yield`.

3. A pergunta é sobre **indicadores de risco de mercado** (volatilidade, Sharpe, drawdown etc.):
   - “Qual o risco do HGLG11?” (em termos de volatilidade) → `fiis_financials_risk`.
   - “Ranking de FIIs mais arriscados” → `fiis_financials_risk` / `fiis_rankings`.

4. A pergunta é sobre **snapshot financeiro ou fundamentos gerais**:
   - “Qual o patrimônio líquido do HGLG11?” → `fiis_financials_snapshot`.
   - “Qual o segmento, CNPJ e administrador do fundo?” → `fii_overview` / `fiis_cadastro`.

5. A pergunta é sobre **notícias, fatos relevantes ou comunicados**:
   - “Teve alguma notícia recente sobre o HGLG11?” → `fiis_noticias`.

6. A pergunta é sobre **imóveis / portfólio físico**:
   - “Quais são os imóveis do HGLG11?” → `fiis_imoveis`.

Regra prática:
Se o foco é **como e quando as receitas contratadas do FII estão distribuídas no tempo e por indexador**, a entidade correta é `fiis_financials_revenue_schedule`.
Se o foco é preço, dividendos, risco de mercado, fundamentos, processos ou notícias, outra entidade específica deve ser usada.

---

## 4. Colunas e semântica dos campos

Fonte: `data/contracts/fiis_financials_revenue_schedule.schema.yaml`.

| Coluna | Tipo / Exemplo | Semântica prática |
|--------|------------------|--------------------|
| `ticker` | `HGLG11` | código do FII (AAAA11). |
| `revenue_due_0_3m_pct` | `0.25` → 25% da receita | receita com vencimento em 0–3 meses. |
| `revenue_due_3_6m_pct` | `0.25` → 25% da receita | receita com vencimento em 3–6 meses. |
| `revenue_due_6_9m_pct` | `0.25` → 25% da receita | receita com vencimento em 6–9 meses. |
| `revenue_due_9_12m_pct` | `0.25` → 25% da receita | receita com vencimento em 9–12 meses. |
| `revenue_due_12_15m_pct` | `0.25` → 25% da receita | receita com vencimento em 12–15 meses. |
| `revenue_due_15_18m_pct` | `0.25` → 25% da receita | receita com vencimento em 15–18 meses. |
| `revenue_due_18_21m_pct` | `0.25` → 25% da receita | receita com vencimento em 18–21 meses. |
| `revenue_due_21_24m_pct` | `0.25` → 25% da receita | receita com vencimento em 21–24 meses. |
| `revenue_due_24_27m_pct` | `0.25` → 25% da receita | receita com vencimento em 24–27 meses. |
| `revenue_due_27_30m_pct` | `0.25` → 25% da receita | receita com vencimento em 27–30 meses. |
| `revenue_due_30_33m_pct` | `0.25` → 25% da receita | receita com vencimento em 30–33 meses. |
| `revenue_due_33_36m_pct` | `0.25` → 25% da receita | receita com vencimento em 33–36 meses. |
| `revenue_due_over_36m_pct` | `0.25` → 25% da receita | receita com vencimento acima de 36 meses. |
| `revenue_due_undetermined_pct` | `0.25` → 25% da receita | receita com vencimento indeterminado. |
| `revenue_igpm_pct` | `0.40` → 40% da receita | percentual de receitas indexadas ao IGPM. |
| `revenue_inpc_pct` | `0.40` → 40% da receita | percentual de receitas indexadas ao INPC. |
| `revenue_ipca_pct` | `0.40` → 40% da receita | percentual de receitas indexadas ao IPCA. |
| `revenue_incc_pct` | `0.40` → 40% da receita | percentual de receitas indexadas ao INCC. |
| `created_at` | `2025-11-01 09:00:00` | data de criação do registro. |
| `updated_at` | `2025-11-01 09:00:00` | data da última atualização do registro. |

Observações importantes:

- Todos os campos `revenue_*_pct` são **frações entre 0 e 1**, mas são apresentados ao usuário como **percentuais** (por exemplo, `0.25` → `25%`).
- A soma das faixas de vencimento (`revenue_due_*`) tende a se aproximar de 100% das receitas contratadas, mas pode haver pequenas diferenças por arredondamento ou contratos fora de escopo.
- Os percentuais por indexador (`revenue_igpm_pct`, `revenue_inpc_pct`, `revenue_ipca_pct`, `revenue_incc_pct`) representam a **composição da receita** por tipo de reajuste, não necessariamente somando 100% se houver receitas com outros indexadores ou prefixadas fora da base.

---

## 5. Exemplos de perguntas-alvo (Planner / Routing)

Sugestões de perguntas que **devem** cair em `fiis_financials_revenue_schedule`:

1. “Cronograma de receitas do HGLG11.”
2. “Receitas com vencimento em 6–9 meses do HGLG11.”
3. “Qual percentual das receitas do HGLG11 vence acima de 36 meses?”
4. “Quanto das receitas do HGLG11 tem vencimento indeterminado?”
5. “Percentual de receitas do HGLG11 indexadas ao IPCA.”
6. “Percentual de receitas do HGLG11 indexadas ao IGPM.”
7. “Receitas do HGLG11 atreladas ao INPC e ao INCC.”
8. “A receita do HGLG11 está mais concentrada no curto prazo ou no longo prazo?”
9. “Comparar a estrutura de recebíveis de HGLG11 e XPLG11.”
10. “Como está distribuída a receita futura do HGLG11 por faixa de vencimento e indexador?”

Esses exemplos devem ser coerentes com:

- Tokens e frases cadastrados na ontologia para `fiis_financials_revenue_schedule`.
- `sample_questions` do schema.

---

## 6. Notas para o Planner / Builder

- Entidade está no **bucket A** (grupo FIIs) e compartilha o mesmo identificador `ticker` com as demais entidades de FIIs.
- Palavras-chave de ativação típicas:
  - “receita”, “receitas futuras”, “recebíveis”, “cronograma”, “vencimento”, “estrutura de recebíveis”;
  - menções explícitas a faixas de prazo (“0–3 meses”, “6–9 meses”, “acima de 36 meses”);
  - menções a indexadores (“IPCA”, “IGPM”, “INPC”, “INCC”, “indexadas ao IPCA”).
- Anti-conflitos relevantes:
  - Termos de preço (“cota”, “subiu”, “caiu”, “cotação”) → `fiis_precos`.
  - Termos de dividendos (“dividendos pagos”, “DY”, “renda mensal”) → `fiis_dividendos` / `fiis_yield_history` / `dividendos_yield`.
  - Termos de risco quantitativo (“volatilidade”, “Sharpe”, “drawdown”) → `fiis_financials_risk`.
- O Builder deve:
  - usar sempre o `ticker` normalizado (AAAA11) como filtro principal;
  - retornar **todas** as colunas percentuais, permitindo ao Presenter/Narrator montar comparações entre faixas de prazo e indexadores.

---

## 7. Notas para o Narrator / Presenter

- Reforçar que se trata de **projeções de receitas baseadas em contratos atuais** e que a distribuição pode mudar ao longo do tempo (novos contratos, reajustes, vencimentos e rescisões).
- Explicar termos de forma simples quando necessário:
  - “IGPM, IPCA, INPC, INCC” como diferentes índices de inflação / construção.
  - “Vencimento acima de 36 meses” como receitas de **longo prazo**.
- Em comparações entre FIIs:
  - deixar claro qual critério está sendo usado (por exemplo, maior percentual de receitas no longo prazo, maior exposição a IPCA etc.);
  - evitar juízos de valor fortes (“melhor” ou “pior”) e focar em **características da estrutura de receitas**.
- Quando houver concentração muito alta em curto prazo ou em um único indexador, é útil destacar isso como ponto de atenção, sempre de forma descritiva e não prescritiva.
