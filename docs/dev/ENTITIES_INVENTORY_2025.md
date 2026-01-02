# Inventário de Entidades Araquem (2025)

## 0. Visão Geral

| Entidade | Domínio | Objetivo resumido | Perguntas típicas | Formato de resposta | Privada? | RAG/Narrator | Tipo | default_date_field | Agregações |
|---|---|---|---|---|---|---|---|---|---|
| client_fiis_positions | carteira | Posições do cliente em FIIs com quantidades, preços e peso na carteira | “quais FIIs da minha carteira estão dando lucro”, “qual o peso do HGLG11 na minha carteira” | Tabela por ticker com qty como valor | Sim | RAG: negado / Narrator: desabilitado | D-1 | position_date | não |
| client_fiis_dividends_evolution | dividendos | Evolução mensal de dividendos da carteira do cliente | “evolução dos meus dividendos”, “renda mensal dos meus FIIs” | Tabela com ano, mês e total de dividendos | Sim | RAG: negado / Narrator: desabilitado | histórico | - | não |
| client_fiis_performance_vs_benchmark | performance | Série de performance da carteira vs benchmark (IFIX/IFIL/IBOV/CDI) | “performance da minha carteira vs IFIX”, “minha carteira está melhor que o CDI” | Tabela com data, valor e retornos carteira/benchmark | Sim | RAG: negado / Narrator: desabilitado | histórico | date_reference | não |
| fiis_registrations | cadastro | Dados cadastrais 1×1 do FII (cnpj, admin, setor, site) | “segmento do HGLG11”, “qual o CNPJ do MXRF11” | Lista simples ticker → nome | Não | RAG: negado / Narrator: desabilitado | D-1 | - | não |
| fiis_dividends | dividendos | Histórico de proventos pagos por FII | “quanto o MXRF11 distribuiu em 07/2024”, “média de dividendos do HGLG11” | Tabela/markdown com datas e valores; agregações habilitadas | Não | RAG: negado / Narrator: desabilitado | histórico | payment_date | sim |
| fiis_yield_history | yield | Histórico mensal de dividendos, preço ref. e DY | “histórico de DY do MXRF11”, “evolução do DY do KNRI11” | Tabela com mês, dividendos, preço e DY; agregações | Não | RAG: negado / Narrator: desabilitado | histórico | ref_month | sim |
| fiis_financials_snapshot | snapshot | Snapshot D-1 de indicadores financeiros (payout, EV, caixa, dívida) | “qual o market cap do MXRF11”, “payout do MCCI11” | Resumo/summary com métricas financeiras; agregações | Não | RAG: negado / Narrator: desabilitado | D-1 | updated_at | sim |
| fiis_financials_revenue_schedule | receitas | Estrutura de recebíveis por buckets de prazo e indexadores | “quanto do HGLG11 vence em 12 meses”, “exposição a IPCA/IGPM do XPML11” | Resumo detalhado em texto/tabela com percentuais por faixa; agregações | Não | RAG: negado / Narrator: desabilitado | D-1 | updated_at | sim |
| fiis_financials_risk | risco | Indicadores de risco (volatilidade, Sharpe, beta, MDD etc.) D-1 | “volatilidade do HGLG11”, “Sharpe do HGRU11” | Resumo narrativo/summary com métricas; agregações | Não | RAG: permitido / Narrator: desabilitado | D-1 | - | sim |
| fiis_real_estate | propriedades | Imóveis/ativos do FII com área, vacância, inadimplência | “quais imóveis compõem o HGLG11”, “vacância do portfólio do VISC11” | Lista de ativos com classe, endereço, área, vacância | Não | RAG: negado / Narrator: desabilitado | D-1 | updated_at | sim |
| fiis_news | noticias | Notícias D-1 sobre FIIs com título, fonte e link | “notícias sobre VISC11”, “manchetes recentes do HGLG11” | Lista de manchetes com data/hora e link | Não | RAG: permitido / Narrator: desabilitado | D-1 | published_at | lista apenas |
| fiis_quota_prices | precos | Série diária de preços (abertura, máxima, mínima, fechamento, variação) | “como fechou o HGLG11 hoje”, “variação diária do XPML11” | Tabela/markdown com candles diários; agregações | Não | RAG: negado / Narrator: desabilitado | histórico | traded_at | sim |
| fiis_legal_proceedings | processos | Processos judiciais relacionados a FIIs com risco e valores | “processos do VISC11”, “risco de perda do HGLG11 em ações” | Lista de processos com número, fase, risco, valores | Não | RAG: negado / Narrator: desabilitado | D-1 | updated_at | lista apenas |
| fiis_rankings | rankings | Posições dos FIIs em rankings (DY, valor de mercado, Sharpe etc.) | “posição do HGLG11 no IFIX”, “top FIIs por DY 12m” | Tabela com posições em múltiplos rankings | Não | RAG: negado / Narrator: desabilitado | D-1 | updated_at | lista apenas |
| fiis_overview | overview | Visão consolidada D-1 (cadastro + finanças + risco + rank) | “resumo do HGLG11”, “overview do MXRF11” | Tabela com principais indicadores financeiros e de risco | Não | RAG: negado / Narrator: desabilitado | D-1 | updated_at | não |
| history_b3_indexes | indices | Histórico D-1 de IBOV/IFIX/IFIL (pontos e variação) | “histórico do IFIX”, “variação do IBOV hoje” | Lista de datas com pontos e variações; agregações | Não | RAG: permitido / Narrator: desabilitado | histórico | index_date | sim |
| history_currency_rates | moedas | Câmbio D-1 USD/EUR em BRL com compra/venda e variação | “cotação do dólar”, “variação do euro hoje” | Lista de datas com taxas e variações; agregações | Não | RAG: permitido / Narrator: desabilitado | histórico | rate_date | sim |
| history_market_indicators | macro | Indicadores macro (IPCA, CDI, SELIC, IGPM etc.) D-1 | “CDI de ontem”, “IPCA na última leitura” | Lista de indicadores com data e valor; agregações | Não | RAG: permitido / Narrator: desabilitado | histórico | indicator_date | sim |

## 1. Detalhamento por entidade

### 1.1. client_fiis_positions

**Intent:** client_fiis_positions

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Posições privadas do cliente em FIIs, incluindo quantidades, preços, rentabilidade e peso na carteira, exigindo `document_number` seguro.

**O que ela atende (perguntas comuns)**

- “quais FIIs da minha carteira estão dando lucro”
- “qual o peso do HGLG11 na minha carteira”
- “em qual corretora estão minhas cotas do MXRF11”

**Como ela responde**

- Formato em **tabela** com chave `ticker` e valor `qty`; mensagem vazia padrão.
- Colunas exibem ticker, quantidade, preço médio/fechamento, peso na carteira, rentabilidade e participante de custódia.
- Entidade privada com `default_date_field: position_date`; sem agregações.

**Privacidade e políticas**

- `private: true`; requer `document_number` obrigatório.
- RAG negado no roteador; Narrator desabilitado globalmente.
- Relatório de consistência ressalta entidade cliente com RAG/Narrator bloqueados e isolamento por documento.

### 1.2. client_fiis_dividends_evolution

**Intent:** client_fiis_dividends_evolution

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Evolução mensal dos dividendos recebidos na carteira de FIIs do cliente (requer `document_number`).

**O que ela atende (perguntas comuns)**

- “evolução dos meus dividendos em FIIs”
- “quanto minha carteira recebeu de dividendos mês a mês”
- “renda mensal dos meus FIIs”

**Como ela responde**

- **Tabela** com ano, mês (nome/número) e total de dividendos; mensagem vazia padronizada.
- Colunas principais: `year_reference`, `month_number`/`month_name`, `total_dividends`. Sem agregações.
- Não possui suporte a múltiplos tickers; `default_date_field` ausente (série mensal por campos de ano/mês).

**Privacidade e políticas**

- `private: true`; `params.required: [document_number]`.
- RAG negado; Narrator desabilitado.
- Relatório destaca dados sensíveis e bloqueio de RAG/Narrator.

### 1.3. client_fiis_performance_vs_benchmark

**Intent:** client_fiis_performance_vs_benchmark

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Série temporal de performance da carteira de FIIs do cliente comparada a benchmarks (IFIX, IFIL, IBOV, CDI).

**O que ela atende (perguntas comuns)**

- “performance da minha carteira de FIIs versus o IFIX”
- “minha carteira está melhor ou pior que o CDI”
- “comparar o retorno da minha carteira com o IFIL”

**Como ela responde**

- **Tabela** com data, benchmark, valores e retornos de carteira/benchmark; mensagem vazia padrão.
- Colunas: `benchmark_code`, `portfolio_amount`, `portfolio_return_pct`, `benchmark_value`, `benchmark_return_pct`; data em `date_reference`. Agregações desabilitadas.
- `default_date_field: date_reference` (série histórica).

**Privacidade e políticas**

- `private: true`; exige `document_number`.
- RAG negado; Narrator desabilitado; notas de privacidade no relatório.

### 1.4. fiis_registrations

**Intent:** fiis_registrations

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Dados cadastrais estáticos de cada FII (CNPJ, administrador, classificação, setor, site, cotas e cotistas).

**O que ela atende (perguntas comuns)**

- “segmento do HGLG11”
- “qual o CNPJ do MXRF11”
- “quem é o custodiante do XPML11”

**Como ela responde**

- **Lista** com chave `ticker` e valor `display_name`; respostas simples via template markdown.
- Colunas incluem CNPJ, nomes, classificação, setor/subsetor, gestão, público-alvo, ISIN, IPO, pesos IFIX/IFIL, cotas e cotistas.
- Suporta múltiplos tickers; sem agregações.

**Privacidade e políticas**

- `private: false` (dados públicos).
- RAG negado; Narrator desabilitado.
- Relatório marca snapshot cadastral com RAG negado e sem inferência temporal.

### 1.5. fiis_dividends

**Intent:** fiis_dividends

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Histórico de proventos (dividendos) pagos por FII, com datas de pagamento e data-com.

**O que ela atende (perguntas comuns)**

- “quanto o MXRF11 distribuiu em 07/2024”
- “média de dividendos do HGLG11 nos últimos 12 meses”

**Como ela responde**

- **Tabela**/markdown: para um ticker único, mostra pagamentos e valores; suporta múltiplos tickers com seções por FII.
- Colunas: `payment_date`, `dividend_amt`, `traded_until_date`; `default_date_field: payment_date`.
- Agregações habilitadas com janelas e médias/somas; lista padrão 10 registros.

**Privacidade e políticas**

- Pública (`private: false`).
- RAG negado; Narrator desabilitado.
- Relatório reforça entidade histórica com consultas via SQL e janelas definidas.

### 1.6. fiis_yield_history

**Intent:** fiis_yield_history

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Histórico mensal de dividendos por cota, preço de referência e dividend yield (DY) de cada FII.

**O que ela atende (perguntas comuns)**

- “historico de dividend yield do MXRF11 nos últimos 12 meses”
- “evolução do DY do KNRI11”
- “DY mensal do HGLG11 em 2024-05”

**Como ela responde**

- **Tabela** com ticker, mês de referência (`ref_month`), dividendos, preço e DY; valor monetário e percentuais formatados.
- Campos principais: `dividends_sum`, `price_ref`, `dy_monthly`; `default_date_field: ref_month`. Agregações habilitadas com janelas padrão.

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado.
- Relatório indica entidade histórica mensal com RAG negado e janelas via inferência.

### 1.7. fiis_financials_snapshot

**Intent:** fiis_financials_snapshot

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Snapshot D-1 de indicadores financeiros do FII (payout, alavancagem, EV, market cap, caixa, passivos, DY, variações).

**O que ela atende (perguntas comuns)**

- “qual o market cap do MXRF11”
- “quanto foi o último dividendo do HGLG11”
- “qual o payout do MCCI11”

**Como ela responde**

- **Resumo** em lista de métricas por ticker; agregações habilitadas.
- Colunas incluem DY mensal/12m, dividendos 12m, valores de mercado, P/BV, payout, crescimento, cap rate, alavancagem, caixa e passivos; data de atualização em `updated_at` (D-1).
- Suporta múltiplos tickers; `default_date_field: updated_at`.

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado.
- Relatório marca snapshot D-1 com consultas determinísticas.

### 1.8. fiis_financials_revenue_schedule

**Intent:** fiis_financials_revenue_schedule

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Estrutura temporal dos recebíveis do FII por buckets de vencimento e indexadores (IGPM, IPCA, INPC, INCC).

**O que ela atende (perguntas comuns)**

- “como está distribuída a receita futura do MXRF11 por índice”
- “cronograma de recebíveis do CPTS11”
- “qual a exposição do VISC11 a IPCA e IGPM”

**Como ela responde**

- **Resumo** textual/tabela listando percentuais por faixas (0–3m até >36m e indeterminado) e por indexador; agregações habilitadas.
- Colunas abrangem buckets trimestrais e percentuais de indexadores; `default_date_field: updated_at`.
- Suporta múltiplos tickers; janelas e agregações padrão via inference.

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado (LLM off).
- Relatório aponta snapshot de cronograma com RAG negado e narrator desligado.

### 1.9. fiis_financials_risk

**Intent:** fiis_financials_risk

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Indicadores de risco quantitativo do FII (volatilidade, Sharpe, Treynor, Jensen, beta, Sortino, drawdown, R²) em base D-1.

**O que ela atende (perguntas comuns)**

- “volatilidade do HGLG11”
- “Índice de Treynor do HGLG11”
- “Sharpe do HGRU11”

**Como ela responde**

- **Summary** com métrica e breve explicação; também suporta comparações quando múltiplos tickers.
- Colunas incluem volatilidade, Sharpe, Sortino, Treynor, Jensen alpha, beta, max drawdown e R²; `default_date_field` ausente (snapshot). Agregações habilitadas.

**Privacidade e políticas**

- Pública; RAG permitido (coleções conceituais) mas Narrator desligado (strict, max rows 0).
- Relatório indica RAG conceitual e narrator determinístico off.

### 1.10. fiis_real_estate

**Intent:** fiis_real_estate

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Imóveis e ativos operacionais dos FIIs com classe, localização, área, unidades, vacância e inadimplência; base D-1.

**O que ela atende (perguntas comuns)**

- “quais imóveis compõem o HGLG11”
- “onde ficam os galpões do XPLG11”
- “qual a vacância do portfólio do VISC11”

**Como ela responde**

- **Lista** com chave `asset_name` e valor `asset_class`; colunas detalham endereço, área, unidades, vacância, inadimplência e status.
- `default_date_field: updated_at`; agregações habilitadas (listas).

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado.
- Relatório aponta snapshot de propriedades com RAG negado e sem inferência temporal.

### 1.11. fiis_news

**Intent:** fiis_news

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Notícias e matérias D-1 sobre FIIs, consolidando fonte, título, tags e links.

**O que ela atende (perguntas comuns)**

- “quais notícias saíram sobre VISC11”
- “tem alguma matéria recente citando HGLG11”
- “últimas manchetes do setor de shoppings”

**Como ela responde**

- **Lista** de até 10 itens recentes com data/hora, título, fonte e URL.
- Colunas principais: `source`, `title`, `tags`, `description`, `url`, `published_at`. `default_date_field: published_at`. Agregações habilitadas (listas).

**Privacidade e políticas**

- Pública; RAG permitido (coleções de notícias e conceitos); Narrator desabilitado.
- Relatório indica entidade textual histórica com RAG permitido e sem narrator.

### 1.12. fiis_quota_prices

**Intent:** fiis_quota_prices

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Série diária de preços por FII (abertura, máxima, mínima, fechamento, variação).

**O que ela atende (perguntas comuns)**

- “como fechou o HGLG11 hoje”
- “qual foi a variação do MXRF11 ontem”
- “variação diária do XPML11 nos últimos 5 pregões”

**Como ela responde**

- **Tabela/markdown** com datas e preços; para único registro, frase resumindo candle; agregações habilitadas com janelas (médias/somas).
- Colunas principais: `traded_at`, `open_price`, `max_price`, `min_price`, `close_price`, `daily_variation_pct`; `default_date_field: traded_at`.

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado.
- Relatório: entidade histórica de preços, RAG negado, janelas em param inference.

### 1.13. fiis_legal_proceedings

**Intent:** fiis_legal_proceedings

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Processos judiciais associados a FIIs, com números, julgamento, instância, valores, risco de perda e fatos principais.

**O que ela atende (perguntas comuns)**

- “o VISC11 tem processos em andamento?”
- “qual o risco de perda do HGLG11 em ações judiciais?”
- “há causas relevantes envolvendo MXRF11?”

**Como ela responde**

- **Lista** com processo e status (chave `process_number`, valor `judgment`); agregações habilitadas para listagens.
- Colunas exibem instância, início, valor da causa, partes, risco, fatos e análise de impacto; `default_date_field: updated_at`.

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado.
- Relatório: snapshot estruturado sem inferência temporal.

### 1.14. fiis_rankings

**Intent:** fiis_rankings

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Rankings que posicionam FIIs por popularidade, índices IFIX/IFIL, dividend yield, dividendos, valor de mercado, patrimônio, Sharpe, Sortino, volatilidade e drawdown.

**O que ela atende (perguntas comuns)**

- “qual a posição do HGLG11 no IFIX?”
- “como o KNRI11 está no ranking de Sharpe?”
- “quais FIIs lideram o DY de 12 meses?”

**Como ela responde**

- **Tabela** com chave `ticker` e múltiplas colunas de ranking (usuários, Sírios, IFIX/IFIL, DY, dividendos, valor de mercado, Sharpe, volatilidade, drawdown).
- Agregações habilitadas (listas) e suporte a múltiplos tickers; dados de snapshot (`updated_at`).

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado.
- Relatório: ranking determinístico sem inferência temporal.

### 1.15. fiis_overview

**Intent:** fiis_overview

**Contexto:** usa contexto conversacional (herda ticker e última entidade de FII para perguntas encadeadas).

**Nome e objetivo**
Visão consolidada D-1 do FII combinando cadastro, indicadores financeiros, risco e rankings.

**O que ela atende (perguntas comuns)**

- “resumo do HGLG11”
- “overview do KNRI11”
- “como está o MXRF11 hoje?”

**Como ela responde**

- **Tabela** com identificação (ticker, nome, setor, gestão), DY mensal/12m, dividendos 12m, market cap, Sharpe/Sortino/volatilidade/drawdown e posições em rankings SIRIOS/IFIX/IFIL/DY12m.
- Suporta múltiplos tickers; agregações desabilitadas; snapshot D-1 (campos de atualização para financials, risk, rankings).

**Privacidade e políticas**

- Pública; RAG negado; Narrator desabilitado.
- Relatório nota view composta D-1 com consultas determinísticas.

### 1.16. history_b3_indexes

**Intent:** history_b3_indexes

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Histórico D-1 dos índices IBOV, IFIX e IFIL com pontos e variação diária.

**O que ela atende (perguntas comuns)**

- “histórico do IFIX nos últimos 6 meses”
- “como o IFIX se comportou em 2024”
- “variação do IBOV hoje”

**Como ela responde**

- **Lista** de datas com pontos e variações de IBOV/IFIX/IFIL; agregações habilitadas (listas).
- `default_date_field: index_date`; campos de pontos e variações para cada índice (D-1).

**Privacidade e políticas**

- Pública; RAG permitido (perfil macro); Narrator desabilitado.
- Relatório: entidade macro histórica com RAG permitido e janelas via param inference.

### 1.17. history_currency_rates

**Intent:** history_currency_rates

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Taxas de câmbio D-1 de USD/EUR em BRL, com compra/venda e variação diária.

**O que ela atende (perguntas comuns)**

- “como fechou o dólar ontem?”
- “qual a variação do euro na última cotação?”
- “câmbio recente para FIIs dolarizados”

**Como ela responde**

- **Lista** de datas com taxas de venda/compra e variações de USD e EUR; agregações habilitadas (listas).
- `default_date_field: rate_date`; campos para compra/venda e variação de USD/EUR.

**Privacidade e políticas**

- Pública; RAG permitido (macro); Narrator desabilitado.
- Relatório: entidade de câmbio histórica com RAG permitido e janelas padrão.

### 1.18. history_market_indicators

**Intent:** history_market_indicators

**Contexto:** não usa contexto conversacional (sem herança de ticker/entidade).

**Nome e objetivo**
Indicadores macroeconômicos (IPCA, CDI, SELIC, IGPM etc.) em base D-1.

**O que ela atende (perguntas comuns)**

- “qual foi o CDI ontem?”
- “quanto está o IPCA na última leitura?”
- “mostrar a SELIC na data X”

**Como ela responde**

- **Lista** com data, nome do indicador e valor; agregações habilitadas (listas).
- `default_date_field: indicator_date`; campos `indicator_name` e `indicator_amt` (taxa/índice).

**Privacidade e políticas**

- Pública; RAG permitido (macro); Narrator desabilitado.
- Relatório: entidade macro histórica com RAG permitido e inferência de janelas curtas.

---

## fiis_dividends_yields

**Tipo:** histórica (métrica composta, pública, multi-ticker).
**Grão:** `{ticker, ref_month}`; `result_key: ticker`; `default_date_field: ref_month`.
**Fonte:** view `public.fiis_dividends_yields` + CSV `docs/database/samples/fiis_dividends_yields.csv`.
**Escopo:** dividendos pagos, DY mensal/12m, cadastro do FII, último pagamento.

**O que retorna (colunas principais)**
- `ticker`, `display_name`, `sector`, `sub_sector`, `classification`, `management_type`, `target_market`
- `traded_until_date`, `payment_date`, `dividend_amt`, `ref_month`, `month_dividends_amt`, `month_price_ref`
- `dy_monthly`, `dy_12m_pct`, `dy_current_monthly_pct`, `dividends_12m_amt`, `last_dividend_amt`, `last_payment_date`

**Privacidade e políticas**
- Pública; `requires_identifiers: [ticker]`; `supports_multi_ticker: true`.
- RAG negado; Narrator desabilitado; param_inference com janelas 3–24m e contagem.
- Qualidade: range para DY e dividendo; cache público diário.

---

## client_fiis_enriched_portfolio

**Tipo:** histórica (privada, multi-ticker).
**Grão:** `{document_number, position_date, ticker}`; `result_key: document_number`; `default_date_field: position_date`.
**Fonte:** view `public.client_fiis_enriched_portfolio` + CSV `docs/database/samples/client_fiis_enriched_portfolio.csv`.
**Escopo:** posição do cliente com cadastro do FII, métricas de risco, DY e rankings.

**O que retorna (colunas principais)**
- `document_number`, `position_date`, `ticker`, `fii_name`, `qty`, `closing_price`, `position_value`, `portfolio_value`, `weight_pct`
- `sector`, `sub_sector`, `classification`, `management_type`, `target_market`, `fii_cnpj`
- `dy_12m_pct`, `dy_monthly_pct`, `dividends_12m_amt`, `market_cap_value`, `equity_value`
- `volatility_ratio`, `sharpe_ratio`, `sortino_ratio`, `max_drawdown`, `beta_index`, `sirios_rank_position`, `ifix_rank_position`, `rank_dy_12m`, `rank_sharpe`

**Privacidade e políticas**
- `private: true`; `requires_identifiers: [document_number]` com binding `context.client_id`; inferência desabilitada.
- RAG e Narrator negados; cache escopo `prv`; contexto proibido para ticker/data.
- Qualidade: frescor 30m, ranges para pesos, DY, risco.

---

## consolidated_macroeconomic

**Tipo:** histórica (macro).
**Grão:** `{ref_date}`; `result_key: ref_date`; `default_date_field: ref_date`.
**Fonte:** view `public.consolidated_macroeconomic` + CSV `docs/database/samples/consolidated_macroeconomic.csv`.
**Escopo:** IPCA, SELIC/CDI, IFIX/IBOV, dólar/euro (compra, venda, variações) por data.

**O que retorna (colunas principais)**
- `ref_date`, `ipca`, `selic`, `cdi`, `ifix_points`, `ifix_var_pct`, `ibov_points`, `ibov_var_pct`
- `usd_buy_amt`, `usd_sell_amt`, `usd_var_pct`, `eur_buy_amt`, `eur_sell_amt`, `eur_var_pct`

**Privacidade e políticas**
- Pública; sem identificadores; janelas padrão de histórico (1–12 meses e contagens).
- RAG e Narrator negados; cache público diário; qualidade com ranges para variações e câmbio.
- Param_inference habilitado com janelas curtas e contagens.
