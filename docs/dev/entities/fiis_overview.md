# Entidade `fiis_overview`

## 1. Descrição e escopo

A entidade `fiis_overview` consolida, em **uma linha por FII**, os principais indicadores cadastrais, de preço, rendimento, risco e ranking utilizados pela SIRIOS para dar uma visão executiva do fundo.

Ela funciona como um **"painel 360°" determinístico** para perguntas do tipo:

- "me dá um overview do HGLG11"
- "quais os principais indicadores do MXRF11"
- "me de uma visao geral do VISC11"

Características gerais:

- **Fonte de dados**: views derivadas de preços diários, dividendos, cadastro, métricas financeiras e rankings (IFIX/IFIL e rankings internos SIRIOS).
- **Granularidade**: 1 registro por `ticker`.
- **Atualização**: fotografia D-1 (ou última data disponível) de todos os indicadores consolidados.
- **Uso principal**: responder perguntas de overview (resumo do fundo, indicadores principais, risco, liquidez, tamanho, descontos/prêmios, etc.).

A rota canônica de atendimento dessas perguntas é:

- `intent`: `fiis_overview`
- `entity`: `fiis_overview`
- `sql_view`: `fiis_overview`

---

## 2. Exemplos canônicos de perguntas

Abaixo alguns exemplos que **devem** ser roteados para `fiis_overview`:

1. "resumo do HGLG11"
2. "overview do KNRI11"
3. "quais os principais indicadores do CPTS11"
4. "me de uma visao geral do VISC11"
5. "overview do MXRF11"
6. "resumo dos principais indicadores de HGLG11"
7. "quero um resumo completo do HGLG11"
8. "panorama do fundo MXRF11"
9. "quais os destaques do VISC11 hoje"
10. "comparativo de overview entre HGLG11, MXRF11 e VISC11"

Essas perguntas devem:

- Identificar corretamente o(s) `ticker(s)` citado(s).
- Selecionar as linhas correspondentes em `fiis_overview`.
- Permitir que o Narrator monte textos resumidos usando esses campos como fatos determinísticos.

---

## 3. Colunas e contratos

A tabela abaixo resume as colunas expostas em `fiis_overview`. O schema completo está em `data/contracts/fiis_overview.schema.yaml` e é a fonte da verdade.

| Campo | Tipo | Descrição |
|---|---|---|
| `ticker` | `text` | Ticker do FII no formato AAAA11. |
| `display_name` | `text` | Nome de exibição amigável do fundo. |
| `b3_name` | `text` | Nome de pregão do fundo na B3. |
| `cnpj` | `text` | CNPJ do fundo. |
| `segment` | `text` | Segmento principal do fundo (ex.: Logístico, Shoppings, CRI etc.). |
| `subsegment` | `text` | Subsegmento do fundo, quando aplicável. |
| `management_type` | `text` | Tipo de gestão (ex.: Ativa, Passiva, Híbrida). |
| `target_audience` | `text` | Público-alvo (Geral, Investidor Profissional, Qualificado etc.). |
| `ipo_date` | `date` | Data do IPO do fundo. |
| `quotas_issued` | `numeric` | Quantidade de cotas emitidas. |
| `quotaholders` | `numeric` | Número de cotistas. |
| `market_cap` | `numeric` | Valor de mercado aproximado (preço de tela x cotas emitidas). |
| `enterprise_value` | `numeric` | Enterprise Value estimado do fundo, quando disponível. |
| `last_price` | `numeric` | Último preço de negociação considerado no snapshot. |
| `price_date` | `date` | Data de referência do último preço (`last_price`). |
| `dy_current` | `numeric` | Dividend yield corrente (base anualizada do último provento conhecido). |
| `dy_12m` | `numeric` | Dividend yield acumulado dos últimos 12 meses. |
| `dy_24m` | `numeric` | Dividend yield acumulado dos últimos 24 meses. |
| `price_to_book` | `numeric` | Relação preço/valor patrimonial (P/VP). |
| `nav_per_share` | `numeric` | Valor patrimonial por cota (NAV/cota). |
| `premium_discount_nav` | `numeric` | Percentual de prêmio/desconto em relação ao NAV. |
| `avg_daily_volume_3m` | `numeric` | Volume financeiro médio diário em 3 meses. |
| `avg_daily_volume_6m` | `numeric` | Volume financeiro médio diário em 6 meses. |
| `liquidity_bucket` | `text` | Classificação de liquidez em faixas (ex.: Alta, Média, Baixa). |
| `vol_12m` | `numeric` | Volatilidade anualizada em 12 meses. |
| `sharpe_12m` | `numeric` | Índice de Sharpe em 12 meses. |
| `sortino_12m` | `numeric` | Índice de Sortino em 12 meses. |
| `beta` | `numeric` | Beta do fundo em relação a um benchmark (geralmente IFIX). |
| `max_drawdown` | `numeric` | Máximo drawdown observado na janela de cálculo. |
| `treynor_ratio` | `numeric` | Índice de Treynor em 12 meses. |
| `jensen_alpha` | `numeric` | Alpha de Jensen em 12 meses. |
| `r2` | `numeric` | Coeficiente de determinação (R²) em relação ao benchmark. |
| `ifix_weight` | `numeric` | Peso do fundo no índice IFIX, quando aplicável. |
| `ifil_weight` | `numeric` | Peso do fundo no índice IFIL, quando aplicável. |
| `sirios_rank_position` | `integer` | Posição do fundo em ranking proprietário SIRIOS. |
| `sirios_rank_score` | `numeric` | Score numérico do ranking proprietário SIRIOS. |
| `rank_bucket` | `text` | Faixa do ranking (ex.: Top 10, Top 50, Long tail). |
| `has_processos` | `boolean` | Indica se há processos judiciais mapeados para o fundo (`fiis_processos`). |
| `has_noticias` | `boolean` | Indica se há notícias recentes mapeadas para o fundo (`fiis_noticias`). |
| `has_risk_metrics` | `boolean` | Indica se há métricas de risco calculadas (`fiis_financials_risk`). |
| `has_revenue_schedule` | `boolean` | Indica se há cronograma de receitas disponível (`fiis_financials_revenue_schedule`). |
| `has_properties` | `boolean` | Indica se há imóveis detalhados na entidade `fiis_real_estate`. |
| `vacancy_physical` | `numeric` | Vacância física consolidada (quando disponível). |
| `vacancy_economic` | `numeric` | Vacância econômica consolidada (quando disponível). |
| `properties_count` | `integer` | Número de propriedades/captações vinculadas ao fundo. |
| `main_regions` | `text` | Regiões principais de atuação (ex.: SP, RJ, Sul). |
| `main_sectors` | `text` | Setores principais dos inquilinos (ex.: Varejo, Logística, Escritórios). |
| `leverage_ratio` | `numeric` | Indicador de alavancagem, quando disponível. |
| `payout_ratio` | `numeric` | Payout (dividendos / resultado) estimado. |
| `last_dividend_amount` | `numeric` | Valor do último dividendo pago por cota. |
| `last_dividend_ref_month` | `date` | Mês de referência do último dividendo considerado. |
| `created_at` | `timestamp` | Data de criação do registro na visão consolidada. |
| `updated_at` | `timestamp` | Data da última atualização do registro na visão consolidada. |

Observações importantes:

- `ticker` é a chave principal de negócio (normalizada no formato `AAAA11` na camada de dados).
- Campos de preço e rendimento (`last_price`, `dy_12m`, `dy_24m` etc.) sempre refletem a **última data disponível** nas bases de preços e dividendos.
- Campos de risco (`vol_12m`, `sharpe_12m`, `beta`, `max_drawdown`, etc.) são calculados em janelas padronizadas e documentadas nas funções de risco.
- Campos de ranking (`ifix_weight`, `ifil_weight`, `sirios_rank_position`, etc.) são "foto do dia" dos índices e rankings internos.
- Campos de flags (`has_processos`, `has_noticias`, `has_risk_metrics`, etc.) indicam se existem informações complementares em outras entidades, mas o detalhamento é sempre feito nas entidades específicas (`fiis_processos`, `fiis_noticias`, `fiis_financials_risk` etc.).
