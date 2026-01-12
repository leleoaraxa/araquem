# Guia Didático de Entidades do Araquem

## Objetivo
Este guia lista as entidades suportadas pelo Araquem, descreve o que cada uma é/para que serve e apresenta exemplos reais de perguntas para apoiar o time de testes.

## Como usar este guia (para testadores)
- Use o **Mapa rápido** para localizar rapidamente a entidade.
- Consulte o **Catálogo detalhado** para ver descrição, finalidade, campos e exemplos reais.
- Os exemplos são literais e têm **path + índice** da fonte de qualidade.

## Mapa rápido
| entity_id | title | kind | privacidade | chaves/identificadores | onde definido |
| --- | --- | --- | --- | --- | --- |
| client_fiis_positions | Carteira do cliente – posições em FIIs | client | private: true | document_number, position_date, ticker | data/entities/client_fiis_positions/client_fiis_positions.yaml; data/contracts/entities/client_fiis_positions.schema.yaml; data/ontology/entity.yaml |
| client_fiis_dividends_evolution | Carteira do cliente – evolução dos dividendos | client | private: true | document_number, year_reference, month_number | data/entities/client_fiis_dividends_evolution/client_fiis_dividends_evolution.yaml; data/contracts/entities/client_fiis_dividends_evolution.schema.yaml; data/ontology/entity.yaml |
| client_fiis_performance_vs_benchmark | Carteira do cliente – performance vs benchmark | client | private: true | document_number, benchmark_code, date_reference | data/entities/client_fiis_performance_vs_benchmark/client_fiis_performance_vs_benchmark.yaml; data/contracts/entities/client_fiis_performance_vs_benchmark.schema.yaml; data/ontology/entity.yaml |
| client_fiis_performance_vs_benchmark_summary | Carteira do cliente – performance vs benchmark (resumo) | client | private: true | document_number, benchmark_code, date_reference | data/entities/client_fiis_performance_vs_benchmark_summary/client_fiis_performance_vs_benchmark_summary.yaml; data/contracts/entities/client_fiis_performance_vs_benchmark_summary.schema.yaml; data/ontology/entity.yaml |
| fiis_registrations | FIIs – Cadastro | snapshot | private: false | ticker | data/entities/fiis_registrations/fiis_registrations.yaml; data/contracts/entities/fiis_registrations.schema.yaml; data/ontology/entity.yaml |
| fiis_dividends | FIIs – Dividendos históricos | historical | private: false | ticker, payment_date | data/entities/fiis_dividends/fiis_dividends.yaml; data/contracts/entities/fiis_dividends.schema.yaml; data/ontology/entity.yaml |
| fiis_yield_history | FIIs – Dividend yield mensal | historical | private: false | ticker, ref_month | data/entities/fiis_yield_history/fiis_yield_history.yaml; data/contracts/entities/fiis_yield_history.schema.yaml; data/ontology/entity.yaml |
| fiis_overview | FIIs – Visão consolidada (overview) | snapshot | private: false | ticker | data/entities/fiis_overview/fiis_overview.yaml; data/contracts/entities/fiis_overview.schema.yaml; data/ontology/entity.yaml |
| fiis_financials_snapshot | FIIs – Indicadores financeiros (snapshot D-1) | snapshot | private: false | ticker, updated_at | data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml; data/contracts/entities/fiis_financials_snapshot.schema.yaml; data/ontology/entity.yaml |
| fiis_financials_revenue_schedule | FIIs – Cronograma de receitas e indexadores | snapshot | private: false | ticker, updated_at | data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml; data/contracts/entities/fiis_financials_revenue_schedule.schema.yaml; data/ontology/entity.yaml |
| fiis_financials_risk | FIIs – Indicadores de risco (D-1) | snapshot | private: false | ticker | data/entities/fiis_financials_risk/fiis_financials_risk.yaml; data/contracts/entities/fiis_financials_risk.schema.yaml; data/ontology/entity.yaml |
| fiis_real_estate | FIIs – Imóveis e propriedades | snapshot | private: false | ticker, asset_name | data/entities/fiis_real_estate/fiis_real_estate.yaml; data/contracts/entities/fiis_real_estate.schema.yaml; data/ontology/entity.yaml |
| fiis_news | FIIs – Notícias (D-1) | historical | private: false | ticker, published_at | data/entities/fiis_news/fiis_news.yaml; data/contracts/entities/fiis_news.schema.yaml; data/ontology/entity.yaml |
| fiis_quota_prices | FIIs – Preços diários | historical | private: false | ticker, traded_at | data/entities/fiis_quota_prices/fiis_quota_prices.yaml; data/contracts/entities/fiis_quota_prices.schema.yaml; data/ontology/entity.yaml |
| fiis_legal_proceedings | FIIs – Processos judiciais | snapshot | private: false | ticker, process_number | data/entities/fiis_legal_proceedings/fiis_legal_proceedings.yaml; data/contracts/entities/fiis_legal_proceedings.schema.yaml; data/ontology/entity.yaml |
| fiis_rankings | FIIs – Rankings e posições | snapshot | private: false | ticker | data/entities/fiis_rankings/fiis_rankings.yaml; data/contracts/entities/fiis_rankings.schema.yaml; data/ontology/entity.yaml |
| history_b3_indexes | Mercado – Índices B3 (D-1) | historical | private: false | index_date | data/entities/history_b3_indexes/history_b3_indexes.yaml; data/contracts/entities/history_b3_indexes.schema.yaml; data/ontology/entity.yaml |
| history_currency_rates | Mercado – Taxas de câmbio (D-1) | historical | private: false | rate_date | data/entities/history_currency_rates/history_currency_rates.yaml; data/contracts/entities/history_currency_rates.schema.yaml; data/ontology/entity.yaml |
| history_market_indicators | Mercado – Indicadores macro (D-1) | historical | private: false | indicator_date, indicator_name | data/entities/history_market_indicators/history_market_indicators.yaml; data/contracts/entities/history_market_indicators.schema.yaml; data/ontology/entity.yaml |
| fiis_dividends_yields | FIIs – Dividendos + DY (composta) | historical | private: false | ticker, ref_month | data/entities/fiis_dividends_yields/fiis_dividends_yields.yaml; data/contracts/entities/fiis_dividends_yields.schema.yaml; data/ontology/entity.yaml |
| client_fiis_enriched_portfolio | Carteira privada – posição enriquecida | historical | private: true | document_number, position_date, ticker | data/entities/client_fiis_enriched_portfolio/client_fiis_enriched_portfolio.yaml; data/contracts/entities/client_fiis_enriched_portfolio.schema.yaml; data/ontology/entity.yaml |
| consolidated_macroeconomic | Mercado – Macro consolidada | historical | private: false | ref_date | data/entities/consolidated_macroeconomic/consolidated_macroeconomic.yaml; data/contracts/entities/consolidated_macroeconomic.schema.yaml; data/ontology/entity.yaml |

## Catálogo detalhado
### client_fiis_positions

**Identificação**

- entity_id: `client_fiis_positions`
- title: Carteira do cliente – posições em FIIs (fonte: data/entities/catalog.yaml)
- kind: client (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/client_fiis_positions/client_fiis_positions.yaml; data/contracts/entities/client_fiis_positions.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Posições do cliente em FIIs (PRIVADA; exige parâmetro document_number obtido de contexto seguro, nunca do texto livre do usuário).
(fonte: data/entities/client_fiis_positions/client_fiis_positions.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): client_fiis_positions. Requer identificadores: document_number. (fonte: data/entities/client_fiis_positions/client_fiis_positions.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/client_fiis_positions.schema.yaml
- Campos em destaque (5–15):
  - `document_number`: documento do cliente (CPF/CNPJ)
  - `position_date`: data da posição
  - `ticker`: código do FII (AAAA11)
  - `fii_name`: nome do fundo
  - `participant_name`: corretora/participante
  - `qty`: quantidade em custódia
  - `closing_price`: preço de fechamento do dia
  - `update_value`: variação de valor
  - `available_quantity`: quantidade disponível
  - `average_price`: preço médio da posição

**Exemplos reais de perguntas**
- Pergunta: “Em qual corretora estão minhas cotas do XPML11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[32]
  - expected_entity: client_fiis_positions; expected_intent: client_fiis_positions
- Pergunta: “Minhas posições de FIIs”
  - Fonte: data/ops/quality/routing_samples.json#payloads[33]
  - expected_entity: client_fiis_positions; expected_intent: client_fiis_positions
- Pergunta: “Peso do HGLG11 na minha carteira de FIIs”
  - Fonte: data/ops/quality/routing_samples.json#payloads[34]
  - expected_entity: client_fiis_positions; expected_intent: client_fiis_positions
- Pergunta: “Qual meu preço médio do CPTS11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[35]
  - expected_entity: client_fiis_positions; expected_intent: client_fiis_positions
- Pergunta: “Quanto tenho de quantidade em custódia de MXRF11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[36]
  - expected_entity: client_fiis_positions; expected_intent: client_fiis_positions

**Observações de teste**
default_date_field: position_date. Entidade marcada como privada (private: true). requires_identifiers: document_number. (fonte: data/entities/client_fiis_positions/client_fiis_positions.yaml)

### client_fiis_dividends_evolution

**Identificação**

- entity_id: `client_fiis_dividends_evolution`
- title: Carteira do cliente – evolução dos dividendos (fonte: data/entities/catalog.yaml)
- kind: client (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/client_fiis_dividends_evolution/client_fiis_dividends_evolution.yaml; data/contracts/entities/client_fiis_dividends_evolution.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Evolução mensal dos dividendos da carteira de FIIs do cliente (PRIVADA; exige document_number obtido de contexto seguro, nunca do texto livre do usuário).
(fonte: data/entities/client_fiis_dividends_evolution/client_fiis_dividends_evolution.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): client_fiis_dividends_evolution. Requer identificadores: document_number. (fonte: data/entities/client_fiis_dividends_evolution/client_fiis_dividends_evolution.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/client_fiis_dividends_evolution.schema.yaml
- Campos em destaque (5–15):
  - `document_number`: documento do cliente (CPF/CNPJ)
  - `year_reference`: ano de referência
  - `month_number`: número do mês (1-12)
  - `month_name`: nome do mês
  - `total_dividends`: total de dividendos no mês

**Exemplos reais de perguntas**
- Pergunta: “Evolução dos dividendos da minha carteira de FIIs”
  - Fonte: data/ops/quality/routing_samples.json#payloads[14]
  - expected_entity: client_fiis_dividends_evolution; expected_intent: client_fiis_dividends_evolution
- Pergunta: “Histórico de dividendos da minha carteira”
  - Fonte: data/ops/quality/routing_samples.json#payloads[15]
  - expected_entity: client_fiis_dividends_evolution; expected_intent: client_fiis_dividends_evolution
- Pergunta: “Minha renda mensal com FIIs está crescendo”
  - Fonte: data/ops/quality/routing_samples.json#payloads[16]
  - expected_entity: client_fiis_dividends_evolution; expected_intent: client_fiis_dividends_evolution
- Pergunta: “Quanto minha carteira de FIIs recebeu de dividendos em cada mês”
  - Fonte: data/ops/quality/routing_samples.json#payloads[17]
  - expected_entity: client_fiis_dividends_evolution; expected_intent: client_fiis_dividends_evolution
- Pergunta: “Renda mensal dos meus FIIs”
  - Fonte: data/ops/quality/routing_samples.json#payloads[18]
  - expected_entity: client_fiis_dividends_evolution; expected_intent: client_fiis_dividends_evolution

**Observações de teste**
Entidade marcada como privada (private: true). requires_identifiers: document_number. (fonte: data/entities/client_fiis_dividends_evolution/client_fiis_dividends_evolution.yaml)

### client_fiis_performance_vs_benchmark

**Identificação**

- entity_id: `client_fiis_performance_vs_benchmark`
- title: Carteira do cliente – performance vs benchmark (fonte: data/entities/catalog.yaml)
- kind: client (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/client_fiis_performance_vs_benchmark/client_fiis_performance_vs_benchmark.yaml; data/contracts/entities/client_fiis_performance_vs_benchmark.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Série temporal da performance da carteira de FIIs do cliente versus um benchmark (PRIVADA; exige document_number obtido de contexto seguro, nunca do texto livre do usuário). Cada linha representa a performance da carteira e do benchmark em uma data de referência.
(fonte: data/entities/client_fiis_performance_vs_benchmark/client_fiis_performance_vs_benchmark.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): client_fiis_performance_vs_benchmark. Requer identificadores: document_number. (fonte: data/entities/client_fiis_performance_vs_benchmark/client_fiis_performance_vs_benchmark.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/client_fiis_performance_vs_benchmark.schema.yaml
- Campos em destaque (5–15):
  - `document_number`: documento do cliente (CPF/CNPJ)
  - `benchmark_code`: código do benchmark (IFIX, IFIL, IBOV, CDI)
  - `date_reference`: data de referência
  - `portfolio_amount`: valor total da carteira
  - `portfolio_return_pct`: retorno da carteira (%)
  - `benchmark_value`: valor/nível do benchmark
  - `benchmark_return_pct`: retorno do benchmark (%)

**Exemplos reais de perguntas**
- Pergunta: “Como foi a performance da minha carteira de FIIs versus o IFIX nos últimos 12 meses”
  - Fonte: data/ops/quality/routing_samples.json#payloads[19]
  - expected_entity: client_fiis_performance_vs_benchmark; expected_intent: client_fiis_performance_vs_benchmark
- Pergunta: “Comparar o retorno da minha carteira de FIIs com o IFIL”
  - Fonte: data/ops/quality/routing_samples.json#payloads[20]
  - expected_entity: client_fiis_performance_vs_benchmark; expected_intent: client_fiis_performance_vs_benchmark
- Pergunta: “Minha carteira de FIIs está melhor ou pior que o CDI”
  - Fonte: data/ops/quality/routing_samples.json#payloads[21]
  - expected_entity: client_fiis_performance_vs_benchmark; expected_intent: client_fiis_performance_vs_benchmark
- Pergunta: “Performance da minha carteira frente ao IBOV no último mês”
  - Fonte: data/ops/quality/routing_samples.json#payloads[22]
  - expected_entity: client_fiis_performance_vs_benchmark; expected_intent: client_fiis_performance_vs_benchmark
- Pergunta: “Qual foi a rentabilidade da minha carteira de FIIs versus o IFIX em 2024”
  - Fonte: data/ops/quality/routing_samples.json#payloads[23]
  - expected_entity: client_fiis_performance_vs_benchmark; expected_intent: client_fiis_performance_vs_benchmark

**Observações de teste**
default_date_field: date_reference. Entidade marcada como privada (private: true). requires_identifiers: document_number. (fonte: data/entities/client_fiis_performance_vs_benchmark/client_fiis_performance_vs_benchmark.yaml)

### client_fiis_performance_vs_benchmark_summary

**Identificação**

- entity_id: `client_fiis_performance_vs_benchmark_summary`
- title: Carteira do cliente – performance vs benchmark (resumo) (fonte: data/entities/catalog.yaml)
- kind: client (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/client_fiis_performance_vs_benchmark_summary/client_fiis_performance_vs_benchmark_summary.yaml; data/contracts/entities/client_fiis_performance_vs_benchmark_summary.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Resumo (última leitura) da performance da carteira de FIIs do cliente frente a benchmarks, retornando apenas o registro mais recente por benchmark e calculando o excesso de retorno.
(fonte: data/entities/client_fiis_performance_vs_benchmark_summary/client_fiis_performance_vs_benchmark_summary.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): client_fiis_performance_vs_benchmark_summary. Requer identificadores: document_number. (fonte: data/entities/client_fiis_performance_vs_benchmark_summary/client_fiis_performance_vs_benchmark_summary.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/client_fiis_performance_vs_benchmark_summary.schema.yaml
- Campos em destaque (5–15):
  - `document_number`: documento do cliente (CPF/CNPJ)
  - `benchmark_code`: código do benchmark (IFIX, IFIL, IBOV, CDI)
  - `date_reference`: data de referência (mais recente por benchmark)
  - `portfolio_amount`: valor total da carteira na última data
  - `portfolio_return_pct`: retorno acumulado da carteira (%)
  - `benchmark_value`: valor/nível do benchmark na última data
  - `benchmark_return_pct`: retorno acumulado do benchmark (%)
  - `excess_return_pct`: excesso de retorno (carteira - benchmark) em p.p.

**Exemplos reais de perguntas**
- Pergunta: “Carteira vs IFIX no fechamento do período mais recente”
  - Fonte: data/ops/quality/routing_samples.json#payloads[24]
  - expected_entity: client_fiis_performance_vs_benchmark_summary; expected_intent: client_fiis_performance_vs_benchmark_summary
- Pergunta: “Excesso de retorno da carteira frente ao benchmark na última data”
  - Fonte: data/ops/quality/routing_samples.json#payloads[25]
  - expected_entity: client_fiis_performance_vs_benchmark_summary; expected_intent: client_fiis_performance_vs_benchmark_summary
- Pergunta: “Performance acumulada da carteira contra o IBOV (resumo)”
  - Fonte: data/ops/quality/routing_samples.json#payloads[26]
  - expected_entity: client_fiis_performance_vs_benchmark_summary; expected_intent: client_fiis_performance_vs_benchmark_summary
- Pergunta: “Performance da minha carteira contra IBOV até agora (visão resumida)”
  - Fonte: data/ops/quality/routing_samples.json#payloads[27]
  - expected_entity: client_fiis_performance_vs_benchmark_summary; expected_intent: client_fiis_performance_vs_benchmark_summary
- Pergunta: “Resumo carteira vs CDI D-1”
  - Fonte: data/ops/quality/routing_samples.json#payloads[28]
  - expected_entity: client_fiis_performance_vs_benchmark_summary; expected_intent: client_fiis_performance_vs_benchmark_summary

**Observações de teste**
default_date_field: date_reference. Entidade marcada como privada (private: true). requires_identifiers: document_number. (fonte: data/entities/client_fiis_performance_vs_benchmark_summary/client_fiis_performance_vs_benchmark_summary.yaml)

### fiis_registrations

**Identificação**

- entity_id: `fiis_registrations`
- title: FIIs – Cadastro (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_registrations/fiis_registrations.yaml; data/contracts/entities/fiis_registrations.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Dados cadastrais 1×1 de cada FII (admin, cnpj, site, classificação e atributos básicos)
(fonte: data/entities/fiis_registrations/fiis_registrations.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_registrations. Requer identificadores: tickers. (fonte: data/entities/fiis_registrations/fiis_registrations.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_registrations.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11)
  - `fii_cnpj`: CNPJ
  - `display_name`: nome de exibição
  - `b3_name`: nome de pregão na B3
  - `classification`: classificação oficial
  - `sector`: setor de atuação
  - `sub_sector`: subsetor/indústria do fundo
  - `management_type`: tipo de gestão
  - `target_market`: público-alvo
  - `is_exclusive`: é exclusivo?

**Exemplos reais de perguntas**
- Pergunta: “O HGLG11 é um fundo de gestão ativa ou passiva?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[56]
  - expected_entity: fiis_registrations; expected_intent: fiis_registrations
- Pergunta: “Qual foi a data do IPO do ALMI11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[57]
  - expected_entity: fiis_registrations; expected_intent: fiis_registrations
- Pergunta: “Qual o CNPJ do HGLG11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[58]
  - expected_entity: fiis_registrations; expected_intent: fiis_registrations
- Pergunta: “Qual é a classificação oficial do XPLG11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[59]
  - expected_entity: fiis_registrations; expected_intent: fiis_registrations
- Pergunta: “Qual é o administrador e o CNPJ do administrador do HGLG11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[60]
  - expected_entity: fiis_registrations; expected_intent: fiis_registrations

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_registrations/fiis_registrations.yaml)

### fiis_dividends

**Identificação**

- entity_id: `fiis_dividends`
- title: FIIs – Dividendos históricos (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_dividends/fiis_dividends.yaml; data/contracts/entities/fiis_dividends.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Histórico de proventos (dividendos) por FII
(fonte: data/entities/fiis_dividends/fiis_dividends.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_dividends. Requer identificadores: tickers. (fonte: data/entities/fiis_dividends/fiis_dividends.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_dividends.schema.yaml
- Campos em destaque (5–15):
  - `ticker`
  - `payment_date`: data de pagamento
  - `dividend_amt`: valor do dividendo/provento por cota
  - `traded_until_date`: Último dia com direito ao provento (data-com)
  - `created_at`: data de criação do registro
  - `updated_at`: data da última atualização do registro

**Exemplos reais de perguntas**
- Pergunta: “Dividendos do HGLG11 em cada mês do último ano”
  - Fonte: data/ops/quality/routing_samples.json#payloads[69]
  - expected_entity: fiis_dividends; expected_intent: fiis_dividends
- Pergunta: “Dividendos pagos pelo HGLG11 nos últimos 12 meses”
  - Fonte: data/ops/quality/routing_samples.json#payloads[70]
  - expected_entity: fiis_dividends; expected_intent: fiis_dividends
- Pergunta: “Dividendos que o KNRI11 pagou em janeiro de 2025”
  - Fonte: data/ops/quality/routing_samples.json#payloads[71]
  - expected_entity: fiis_dividends; expected_intent: fiis_dividends
- Pergunta: “Lista de pagamentos de proventos do VINO11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[72]
  - expected_entity: fiis_dividends; expected_intent: fiis_dividends
- Pergunta: “Me mostra a distribuição de rendimentos do KNRI11 mês a mês”
  - Fonte: data/ops/quality/routing_samples.json#payloads[73]
  - expected_entity: fiis_dividends; expected_intent: fiis_dividends

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: payment_date. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_dividends/fiis_dividends.yaml)

### fiis_yield_history

**Identificação**

- entity_id: `fiis_yield_history`
- title: FIIs – Dividend yield mensal (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_yield_history/fiis_yield_history.yaml; data/contracts/entities/fiis_yield_history.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Serie histórica do dividend yield por mes/ano.
(fonte: data/entities/fiis_yield_history/fiis_yield_history.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_yield_history. Requer identificadores: tickers. (fonte: data/entities/fiis_yield_history/fiis_yield_history.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_yield_history.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11).
  - `ref_month`: mês de referência (primeiro dia do mês).
  - `dividends_sum`: soma dos dividendos pagos no mês (R$ por cota).
  - `price_ref`: preço de referência da cota no mês (última cotação disponível).
  - `dy_monthly`: dividend yield mensal (dividends_sum / price_ref).

**Exemplos reais de perguntas**
- Pergunta: “Como foi o dy mensal do HGLG11 nos ultimos 12 meses?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[175]
  - expected_entity: fiis_yield_history; expected_intent: fiis_yield_history
- Pergunta: “Como o dy mensal do VISC11 se comportou nos ultimos 24 meses?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[176]
  - expected_entity: fiis_yield_history; expected_intent: fiis_yield_history
- Pergunta: “DY de janeiro de 2024 do VISC11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[177]
  - expected_entity: fiis_yield_history; expected_intent: fiis_yield_history
- Pergunta: “DY por mes do HGLG11 em 2023.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[178]
  - expected_entity: fiis_yield_history; expected_intent: fiis_yield_history
- Pergunta: “Evolucao do dy do VISC11 desde 2023.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[179]
  - expected_entity: fiis_yield_history; expected_intent: fiis_yield_history

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: ref_month. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_yield_history/fiis_yield_history.yaml)

### fiis_overview

**Identificação**

- entity_id: `fiis_overview`
- title: FIIs – Visão consolidada (overview) (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_overview/fiis_overview.yaml; data/contracts/entities/fiis_overview.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Visão consolidada D-1 do FII combinando cadastro, indicadores financeiros, risco quantitativo e posições em rankings.
(fonte: data/entities/fiis_overview/fiis_overview.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_overview. Requer identificadores: tickers. (fonte: data/entities/fiis_overview/fiis_overview.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_overview.schema.yaml
- Required: ticker, display_name
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11).
  - `display_name`: nome de exibição do FII.
  - `b3_name`: nome de pregão na B3.
  - `classification`: classificação geral do FII.
  - `sector`: setor do FII.
  - `sub_sector`: subsetor do FII.
  - `management_type`: tipo de gestão.
  - `target_market`: mercado-alvo do FII.
  - `is_exclusive`: indica fundo exclusivo.
  - `ifil_weight_pct`: peso no IFIL (percentual).

**Exemplos reais de perguntas**
- Pergunta: “Apresenta um overview detalhado do HGLG11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[44]
  - expected_entity: fiis_overview; expected_intent: fiis_overview
- Pergunta: “Comparativo de overview entre HGLG11, MXRF11 e VISC11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[45]
  - expected_entity: fiis_overview; expected_intent: fiis_overview
- Pergunta: “Ficha resumo do fundo MXRF11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[46]
  - expected_entity: fiis_overview; expected_intent: fiis_overview
- Pergunta: “Ficha tecnica resumida do VISC11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[47]
  - expected_entity: fiis_overview; expected_intent: fiis_overview
- Pergunta: “Me mostre um panorama geral do HGLG11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[48]
  - expected_entity: fiis_overview; expected_intent: fiis_overview

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_overview/fiis_overview.yaml)

### fiis_financials_snapshot

**Identificação**

- entity_id: `fiis_financials_snapshot`
- title: FIIs – Indicadores financeiros (snapshot D-1) (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml; data/contracts/entities/fiis_financials_snapshot.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Snapshot D-1 de indicadores financeiros por FII (valores, razões, caixa e endividamento).
(fonte: data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_financials_snapshot. Requer identificadores: tickers. (fonte: data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_financials_snapshot.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11).
  - `dy_monthly_pct`: dividend yield mensal.
  - `dy_pct`: dividend yield em base anualizada.
  - `sum_anual_dy_amt`: soma dos proventos distribuídos no ano.
  - `last_dividend_amt`: valor do último dividendo pago.
  - `last_payment_date`: data do último pagamento de dividendo.
  - `market_cap_value`: valor de mercado.
  - `enterprise_value`: EV (valor da firma).
  - `price_book_ratio`: relação preço/patrimônio (P/BV).
  - `equity_per_share`: patrimônio líquido por cota.

**Exemplos reais de perguntas**
- Pergunta: “Comparando ALMI11 e HGLG11, qual deles tem maior patrimônio líquido hoje?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[101]
  - expected_entity: fiis_financials_snapshot; expected_intent: fiis_financials_snapshot
- Pergunta: “Me traga um resumo financeiro do HGLG11: patrimônio, P/VP e alavancagem.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[102]
  - expected_entity: fiis_financials_snapshot; expected_intent: fiis_financials_snapshot
- Pergunta: “O XPLG11 está alavancado? Qual o nível de alavancagem dele?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[103]
  - expected_entity: fiis_financials_snapshot; expected_intent: fiis_financials_snapshot
- Pergunta: “Quais são os principais indicadores financeiros do XPLG11 hoje (PL, VP/cota, vacância)?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[104]
  - expected_entity: fiis_financials_snapshot; expected_intent: fiis_financials_snapshot
- Pergunta: “Qual a ABL total do HGLG11 e qual a vacância física?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[105]
  - expected_entity: fiis_financials_snapshot; expected_intent: fiis_financials_snapshot

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: updated_at. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml)

### fiis_financials_revenue_schedule

**Identificação**

- entity_id: `fiis_financials_revenue_schedule`
- title: FIIs – Cronograma de receitas e indexadores (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml; data/contracts/entities/fiis_financials_revenue_schedule.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Estrutura temporal de recebíveis e indexadores de receita por FII (percentuais sobre a receita).
(fonte: data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_financials_revenue_schedule. Requer identificadores: tickers. (fonte: data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_financials_revenue_schedule.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11).
  - `revenue_due_0_3m_pct`: receita com vencimento em 0–3 meses.
  - `revenue_due_3_6m_pct`: receita com vencimento em 3–6 meses.
  - `revenue_due_6_9m_pct`: receita com vencimento em 6–9 meses.
  - `revenue_due_9_12m_pct`: receita com vencimento em 9–12 meses.
  - `revenue_due_12_15m_pct`: receita com vencimento em 12–15 meses.
  - `revenue_due_15_18m_pct`: receita com vencimento em 15–18 meses.
  - `revenue_due_18_21m_pct`: receita com vencimento em 18–21 meses.
  - `revenue_due_21_24m_pct`: receita com vencimento em 21–24 meses.
  - `revenue_due_24_27m_pct`: receita com vencimento em 24–27 meses.

**Exemplos reais de perguntas**
- Pergunta: “As receitas do HGLG11 estão mais concentradas no curto prazo ou no longo prazo?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[84]
  - expected_entity: fiis_financials_revenue_schedule; expected_intent: fiis_financials_revenue_schedule
- Pergunta: “Como está distribuída a receita futura do HGLG11 por faixa de vencimento?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[85]
  - expected_entity: fiis_financials_revenue_schedule; expected_intent: fiis_financials_revenue_schedule
- Pergunta: “Compare o cronograma de receitas de HGLG11 e XPLG11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[86]
  - expected_entity: fiis_financials_revenue_schedule; expected_intent: fiis_financials_revenue_schedule
- Pergunta: “Qual a estrutura de recebíveis do HGLG11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[87]
  - expected_entity: fiis_financials_revenue_schedule; expected_intent: fiis_financials_revenue_schedule
- Pergunta: “Qual percentual das receitas do HGLG11 tem vencimento acima de 36 meses?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[88]
  - expected_entity: fiis_financials_revenue_schedule; expected_intent: fiis_financials_revenue_schedule

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: updated_at. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml)

### fiis_financials_risk

**Identificação**

- entity_id: `fiis_financials_risk`
- title: FIIs – Indicadores de risco (D-1) (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_financials_risk/fiis_financials_risk.yaml; data/contracts/entities/fiis_financials_risk.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Indicadores de risco do FII (volatilidade, Sharpe, Treynor, Jensen, beta, Sortino, Drawdown, R²), D-1.
(fonte: data/entities/fiis_financials_risk/fiis_financials_risk.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_financials_risk. Requer identificadores: tickers. (fonte: data/entities/fiis_financials_risk/fiis_financials_risk.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_financials_risk.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11).
  - `volatility_ratio`: indicador de volatilidade (VR).
  - `sharpe_ratio`: índice de Sharpe (SR).
  - `treynor_ratio`: índice de Treynor (TR).
  - `jensen_alpha`: alfa de Jensen (α).
  - `beta_index`: beta índice (β).
  - `sortino_ratio`: índice de Sortino (SoR).
  - `max_drawdown`: máxima queda pico→vale (MDD), reportada em módulo (0.00–1.00).
  - `r_squared`: coeficiente de determinação (R²), 0.00–1.00.
  - `created_at`: data de criação.

**Exemplos reais de perguntas**
- Pergunta: “Beta do XPLG11 em relação ao IFIX”
  - Fonte: data/ops/quality/routing_samples.json#payloads[96]
  - expected_entity: fiis_financials_risk; expected_intent: fiis_financials_risk
- Pergunta: “Coeficiente de determinação do CPTS11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[97]
  - expected_entity: fiis_financials_risk; expected_intent: fiis_financials_risk
- Pergunta: “Max drawdown do MXRF11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[98]
  - expected_entity: fiis_financials_risk; expected_intent: fiis_financials_risk
- Pergunta: “Qual FII está mais volátil hoje”
  - Fonte: data/ops/quality/routing_samples.json#payloads[99]
  - expected_entity: fiis_financials_risk; expected_intent: fiis_financials_risk
- Pergunta: “Qual o Sharpe do HGLG11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[100]
  - expected_entity: fiis_financials_risk; expected_intent: fiis_financials_risk

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_financials_risk/fiis_financials_risk.yaml)

### fiis_real_estate

**Identificação**

- entity_id: `fiis_real_estate`
- title: FIIs – Imóveis e propriedades (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_real_estate/fiis_real_estate.yaml; data/contracts/entities/fiis_real_estate.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Imóveis e propriedades de FIIs (dados operacionais 1×N)
(fonte: data/entities/fiis_real_estate/fiis_real_estate.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_real_estate. Requer identificadores: tickers. (fonte: data/entities/fiis_real_estate/fiis_real_estate.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_real_estate.schema.yaml
- Campos em destaque (5–15):
  - `ticker`
  - `asset_name`: Nome do imóvel ou ativo operacional
  - `asset_class`: imóveis para renda acabados, imóveis para renda em construção
  - `asset_address`: endereço ou localização
  - `total_area`: área total do imóvel em metros quadrados
  - `units_count`: número de unidades/vagas/lojas do ativo
  - `vacancy_ratio`: percentual de vacância do ativo
  - `non_compliant_ratio`: percentual de inadimplência associado ao ativo
  - `assets_status`: status operacional do ativo
  - `created_at`: data de criação do registro

**Exemplos reais de perguntas**
- Pergunta: “Quais ativos do MXRF11 estão inadimplentes”
  - Fonte: data/ops/quality/routing_samples.json#payloads[116]
  - expected_entity: fiis_real_estate; expected_intent: fiis_real_estate
- Pergunta: “Quais endereços fazem parte do VISC11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[117]
  - expected_entity: fiis_real_estate; expected_intent: fiis_real_estate
- Pergunta: “Quais imóveis compõem o HGLG11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[118]
  - expected_entity: fiis_real_estate; expected_intent: fiis_real_estate
- Pergunta: “Qual o tamanho em metros quadrados dos imóveis do KNRI11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[119]
  - expected_entity: fiis_real_estate; expected_intent: fiis_real_estate
- Pergunta: “Vacância dos ativos do XPML11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[120]
  - expected_entity: fiis_real_estate; expected_intent: fiis_real_estate

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: updated_at. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_real_estate/fiis_real_estate.yaml)

### fiis_news

**Identificação**

- entity_id: `fiis_news`
- title: FIIs – Notícias (D-1) (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_news/fiis_news.yaml; data/contracts/entities/fiis_news.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Notícias e matérias relevantes sobre FIIs (fonte externa consolidada D-1)
(fonte: data/entities/fiis_news/fiis_news.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_news. Requer identificadores: tickers. (fonte: data/entities/fiis_news/fiis_news.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_news.schema.yaml
- Campos em destaque (5–15):
  - `ticker`
  - `source`: fonte ou veículo
  - `title`: título da matéria/notícia
  - `tags`: palavras-chave associadas à notícia
  - `description`: resumo curto ou descrição da notícia
  - `url`: link completo para a notícia
  - `image_url`: URL de imagem de destaque
  - `published_at`: data/hora de publicação da notícia
  - `created_at`: data de criação do registro
  - `updated_at`: data da última atualização do registro

**Exemplos reais de perguntas**
- Pergunta: “Houve algum fato relevante envolvendo contratos ou locatários do HGLG11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[121]
  - expected_entity: fiis_news; expected_intent: fiis_news
- Pergunta: “Me atualize com as notícias mais recentes sobre o setor logístico de FIIs.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[122]
  - expected_entity: fiis_news; expected_intent: fiis_news
- Pergunta: “Mostre as últimas manchetes sobre FIIs em geral.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[123]
  - expected_entity: fiis_news; expected_intent: fiis_news
- Pergunta: “O que saiu na mídia sobre o HGLG11 no último mês?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[124]
  - expected_entity: fiis_news; expected_intent: fiis_news
- Pergunta: “Quais foram as três últimas notícias publicadas sobre o HGLG11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[125]
  - expected_entity: fiis_news; expected_intent: fiis_news

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: published_at. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_news/fiis_news.yaml)

### fiis_quota_prices

**Identificação**

- entity_id: `fiis_quota_prices`
- title: FIIs – Preços diários (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_quota_prices/fiis_quota_prices.yaml; data/contracts/entities/fiis_quota_prices.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Consulta de preço/cotação/variação das cotas de FIIs (histórico ou atual).
(fonte: data/entities/fiis_quota_prices/fiis_quota_prices.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_quota_prices. Requer identificadores: tickers. (fonte: data/entities/fiis_quota_prices/fiis_quota_prices.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_quota_prices.schema.yaml
- Campos em destaque (5–15):
  - `ticker`
  - `traded_at`: data de referência
  - `close_price`: preço de fechamento
  - `adj_close_price`: preço de fechamento ajustado
  - `open_price`: preço de abertura
  - `max_price`: máxima do dia
  - `min_price`: mínima do dia
  - `daily_variation_pct`: variação percentual do dia vs. anterior
  - `created_at`: data de criação do registro
  - `updated_at`: data da última atualização do registro

**Exemplos reais de perguntas**
- Pergunta: “Como está o preço do VINO agora?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[133]
  - expected_entity: fiis_quota_prices; expected_intent: fiis_quota_prices
- Pergunta: “Como está o KNRI11 e o XPLG11 hoje?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[134]
  - expected_entity: fiis_quota_prices; expected_intent: fiis_quota_prices
- Pergunta: “Me mostra o preço do VINO11 agora”
  - Fonte: data/ops/quality/routing_samples.json#payloads[135]
  - expected_entity: fiis_quota_prices; expected_intent: fiis_quota_prices
- Pergunta: “Máxima e mínima do MXRF11 em 27/10/2025”
  - Fonte: data/ops/quality/routing_samples.json#payloads[136]
  - expected_entity: fiis_quota_prices; expected_intent: fiis_quota_prices
- Pergunta: “Mínima do HGLG11 no dia 27/10/2025”
  - Fonte: data/ops/quality/routing_samples.json#payloads[137]
  - expected_entity: fiis_quota_prices; expected_intent: fiis_quota_prices

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: traded_at. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_quota_prices/fiis_quota_prices.yaml)

### fiis_legal_proceedings

**Identificação**

- entity_id: `fiis_legal_proceedings`
- title: FIIs – Processos judiciais (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_legal_proceedings/fiis_legal_proceedings.yaml; data/contracts/entities/fiis_legal_proceedings.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Processos judiciais associados a FIIs (dados 1×N com risco e andamento)
(fonte: data/entities/fiis_legal_proceedings/fiis_legal_proceedings.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_legal_proceedings. Requer identificadores: tickers. (fonte: data/entities/fiis_legal_proceedings/fiis_legal_proceedings.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_legal_proceedings.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11)
  - `process_number`: identificador/número do processo judicial.
  - `judgment`: situação ou fase de julgamento do processo.
  - `instance`: instância em que o processo tramita.
  - `initiation_date`: data de distribuição ou início do processo.
  - `cause_amt`: valor envolvido na causa.
  - `process_parts`: partes envolvidas no processo.
  - `loss_risk_pct`: percentual estimado de risco de perda.
  - `main_facts`: principais fatos alegados ou descritos no processo.
  - `loss_impact_analysis`: avaliação do impacto potencial do processo.

**Exemplos reais de perguntas**
- Pergunta: “Desde quando existem processos contra o ALMI11 e como está o andamento deles?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[147]
  - expected_entity: fiis_legal_proceedings; expected_intent: fiis_legal_proceedings
- Pergunta: “Existe algum processo relevante contra o ALMI11 que possa afetar o fundo?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[148]
  - expected_entity: fiis_legal_proceedings; expected_intent: fiis_legal_proceedings
- Pergunta: “Me dá um resumo das ações judiciais envolvendo o ALMI11.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[149]
  - expected_entity: fiis_legal_proceedings; expected_intent: fiis_legal_proceedings
- Pergunta: “O ALMI11 tem processos judiciais em aberto?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[150]
  - expected_entity: fiis_legal_proceedings; expected_intent: fiis_legal_proceedings
- Pergunta: “Quais processos existem contra o ALMI11?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[151]
  - expected_entity: fiis_legal_proceedings; expected_intent: fiis_legal_proceedings

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: updated_at. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_legal_proceedings/fiis_legal_proceedings.yaml)

### fiis_rankings

**Identificação**

- entity_id: `fiis_rankings`
- title: FIIs – Rankings e posições (fonte: data/entities/catalog.yaml)
- kind: snapshot (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_rankings/fiis_rankings.yaml; data/contracts/entities/fiis_rankings.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Rankings de FIIs (top/maiores/melhores/menores) por métricas como liquidez, dividend yield, patrimônio líquido, Sharpe, volatilidade, drawdown e presença em índices (usuários, Sírios, IFIX e IFIL).
(fonte: data/entities/fiis_rankings/fiis_rankings.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_rankings. Requer identificadores: tickers. (fonte: data/entities/fiis_rankings/fiis_rankings.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_rankings.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11)
  - `users_rank_position`: posição do FII no ranking de usuários.
  - `users_rank_net_movement`: quantidade de movimentos (subidas/quedas) registrados em rankings de usuários.
  - `sirios_rank_position`: posição do FII no ranking da SIRIOS.
  - `sirios_rank_net_movement`: quantidade de movimentos (subidas/quedas) registrados em rankings da SIRIOS.
  - `ifix_rank_position`: posição do FII no ranking do IFIX.
  - `ifix_rank_net_movement`: movimentos de posição do FII em recortes de ranking do IFIX.
  - `ifil_rank_position`: posição do FII no ranking do IFIL.
  - `ifil_rank_net_movement`: movimentos de posição do FII em recortes de ranking do IFIL.
  - `rank_dy_12m`: posição do FII no ranking por dividend yield 12 meses.

**Exemplos reais de perguntas**
- Pergunta: “Qual é o peso do HGLG11 no IFIX e no IFIL?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[159]
  - expected_entity: fiis_rankings; expected_intent: fiis_rankings
- Pergunta: “como está a posição do HGLG11 no ranking da SIRIOS?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[160]
  - expected_entity: fiis_rankings; expected_intent: fiis_rankings
- Pergunta: “como evoluiu a posição do HGRU11 no ranking de usuários ao longo do tempo?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[161]
  - expected_entity: fiis_rankings; expected_intent: fiis_rankings
- Pergunta: “como foi a variação de posição do HGLG11 no ranking da SIRIOS neste ano?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[162]
  - expected_entity: fiis_rankings; expected_intent: fiis_rankings
- Pergunta: “peso do MCCI11 no IFIX”
  - Fonte: data/ops/quality/routing_samples.json#payloads[163]
  - expected_entity: fiis_rankings; expected_intent: fiis_rankings

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: updated_at. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_rankings/fiis_rankings.yaml)

### history_b3_indexes

**Identificação**

- entity_id: `history_b3_indexes`
- title: Mercado – Índices B3 (D-1) (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/history_b3_indexes/history_b3_indexes.yaml; data/contracts/entities/history_b3_indexes.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Índices de mercado da B3 (IBOV, IFIX, IFIL) em base D-1.
(fonte: data/entities/history_b3_indexes/history_b3_indexes.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): history_b3_indexes. (fonte: data/entities/history_b3_indexes/history_b3_indexes.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/history_b3_indexes.schema.yaml
- Campos em destaque (5–15):
  - `index_date`: data/hora da observação (D-1)
  - `ibov_points_count`: pontos do IBOV (arred. 0 casas)
  - `ibov_var_pct`: variação percentual diária do IBOV
  - `ifix_points_count`: pontos do IFIX (arred. 0 casas)
  - `ifix_var_pct`: variação percentual diária do IFIX
  - `ifil_points_count`: pontos do IFIL (arred. 0 casas)
  - `ifil_var_pct`: variação percentual diária do IFIL
  - `created_at`: data de criação do registro
  - `updated_at`: data da última atualização do registro

**Exemplos reais de perguntas**
- Pergunta: “Como o IFIX se comportou nos últimos 10 pregões?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[190]
  - expected_entity: history_b3_indexes; expected_intent: history_b3_indexes
- Pergunta: “Fechamento de ontem do Ibovespa em pontos e porcentagem”
  - Fonte: data/ops/quality/routing_samples.json#payloads[191]
  - expected_entity: history_b3_indexes; expected_intent: history_b3_indexes
- Pergunta: “Histórico do IBOV nos últimos 5 dias úteis”
  - Fonte: data/ops/quality/routing_samples.json#payloads[192]
  - expected_entity: history_b3_indexes; expected_intent: history_b3_indexes
- Pergunta: “Histórico recente do IFIX (D-1)”
  - Fonte: data/ops/quality/routing_samples.json#payloads[193]
  - expected_entity: history_b3_indexes; expected_intent: history_b3_indexes
- Pergunta: “Ibovespa hoje (D-1)”
  - Fonte: data/ops/quality/routing_samples.json#payloads[194]
  - expected_entity: history_b3_indexes; expected_intent: history_b3_indexes

**Observações de teste**
default_date_field: index_date. Entidade marcada como não privada (private: false). (fonte: data/entities/history_b3_indexes/history_b3_indexes.yaml)

### history_currency_rates

**Identificação**

- entity_id: `history_currency_rates`
- title: Mercado – Taxas de câmbio (D-1) (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/history_currency_rates/history_currency_rates.yaml; data/contracts/entities/history_currency_rates.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Taxas de câmbio (USD/EUR em BRL) em base D-1.
(fonte: data/entities/history_currency_rates/history_currency_rates.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): history_currency_rates. (fonte: data/entities/history_currency_rates/history_currency_rates.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/history_currency_rates.schema.yaml
- Campos em destaque (5–15):
  - `rate_date`: data/hora da observação (D-1)
  - `usd_buy_amt`: dólar (compra) em BRL
  - `usd_sell_amt`: dólar (venda) em BRL
  - `usd_var_pct`: variação percentual diária do USD
  - `eur_buy_amt`: euro (compra) em BRL
  - `eur_sell_amt`: euro (venda) em BRL
  - `eur_var_pct`: variação percentual diária do EUR
  - `created_at`: data de criação do registro
  - `updated_at`: data da última atualização do registro

**Exemplos reais de perguntas**
- Pergunta: “Como está o dólar hoje?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[207]
  - expected_entity: history_currency_rates; expected_intent: history_currency_rates
- Pergunta: “Cotação do dólar hoje”
  - Fonte: data/ops/quality/routing_samples.json#payloads[208]
  - expected_entity: history_currency_rates; expected_intent: history_currency_rates
- Pergunta: “Cotação do euro D-1”
  - Fonte: data/ops/quality/routing_samples.json#payloads[209]
  - expected_entity: history_currency_rates; expected_intent: history_currency_rates
- Pergunta: “Qual foi a última cotação do euro”
  - Fonte: data/ops/quality/routing_samples.json#payloads[210]
  - expected_entity: history_currency_rates; expected_intent: history_currency_rates
- Pergunta: “Quanto está o dólar para compra e venda”
  - Fonte: data/ops/quality/routing_samples.json#payloads[211]
  - expected_entity: history_currency_rates; expected_intent: history_currency_rates

**Observações de teste**
default_date_field: rate_date. Entidade marcada como não privada (private: false). (fonte: data/entities/history_currency_rates/history_currency_rates.yaml)

### history_market_indicators

**Identificação**

- entity_id: `history_market_indicators`
- title: Mercado – Indicadores macro (D-1) (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/history_market_indicators/history_market_indicators.yaml; data/contracts/entities/history_market_indicators.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Indicadores macroeconômicos do mercado (IPCA, CDI, SELIC, IGPM etc.), em base D-1.
(fonte: data/entities/history_market_indicators/history_market_indicators.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): history_market_indicators. (fonte: data/entities/history_market_indicators/history_market_indicators.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/history_market_indicators.schema.yaml
- Campos em destaque (5–15):
  - `indicator_date`: data/hora da observação do indicador (D-1)
  - `indicator_name`: nome ou código do indicador (ex.: IPCA, CDI, SELIC, IGPM)
  - `indicator_amt`: valor numérico do indicador (taxa, índice ou ponto)
  - `created_at`: data de criação do registro
  - `updated_at`: data da última atualização do registro

**Exemplos reais de perguntas**
- Pergunta: “CDI d-1”
  - Fonte: data/ops/quality/routing_samples.json#payloads[213]
  - expected_entity: history_market_indicators; expected_intent: history_market_indicators
- Pergunta: “IPCA do dia”
  - Fonte: data/ops/quality/routing_samples.json#payloads[214]
  - expected_entity: history_market_indicators; expected_intent: history_market_indicators
- Pergunta: “Qual a SELIC hoje”
  - Fonte: data/ops/quality/routing_samples.json#payloads[215]
  - expected_entity: history_market_indicators; expected_intent: history_market_indicators
- Pergunta: “Qual o IGPM atual”
  - Fonte: data/ops/quality/routing_samples.json#payloads[216]
  - expected_entity: history_market_indicators; expected_intent: history_market_indicators
- Pergunta: “Taxa do INCC hoje”
  - Fonte: data/ops/quality/routing_samples.json#payloads[217]
  - expected_entity: history_market_indicators; expected_intent: history_market_indicators

**Observações de teste**
default_date_field: indicator_date. Entidade marcada como não privada (private: false). (fonte: data/entities/history_market_indicators/history_market_indicators.yaml)

### fiis_dividends_yields

**Identificação**

- entity_id: `fiis_dividends_yields`
- title: FIIs – Dividendos + DY (composta) (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/fiis_dividends_yields/fiis_dividends_yields.yaml; data/contracts/entities/fiis_dividends_yields.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Histórico mensal de dividendos, dividend yield (DY) e cadastro do FII em uma única visão composta.
(fonte: data/entities/fiis_dividends_yields/fiis_dividends_yields.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): fiis_dividends_yields. Requer identificadores: tickers. (fonte: data/entities/fiis_dividends_yields/fiis_dividends_yields.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/fiis_dividends_yields.schema.yaml
- Campos em destaque (5–15):
  - `ticker`: código do FII (AAAA11).
  - `display_name`: nome completo do fundo imobiliário.
  - `sector`: setor de atuação do FII.
  - `sub_sector`: segmento específico dentro do setor.
  - `classification`: classificação do portfólio (ex. Tijolo, Papel).
  - `management_type`: tipo de gestão (Ativa/Passiva).
  - `target_market`: público-alvo do fundo.
  - `traded_until_date`: último dia com direito ao provento (data-com).
  - `payment_date`: data de pagamento do dividendo.
  - `dividend_amt`: valor do dividendo pago por cota.

**Exemplos reais de perguntas**
- Pergunta: “Histórico de dividendos e dy do MXRF11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[39]
  - expected_entity: fiis_dividends_yields; expected_intent: fiis_dividends_yields
- Pergunta: “O que é dividend yield em FIIs”
  - Fonte: data/ops/quality/routing_samples.json#payloads[40]
  - expected_entity: fiis_dividends_yields; expected_intent: fiis_dividends_yields
- Pergunta: “Qual o DY de 12 meses do HGLG11”
  - Fonte: data/ops/quality/routing_samples.json#payloads[41]
  - expected_entity: fiis_dividends_yields; expected_intent: fiis_dividends_yields
- Pergunta: “Quanto o CPTS11 pagou de dividendos e dy em 08/2023”
  - Fonte: data/ops/quality/routing_samples.json#payloads[42]
  - expected_entity: fiis_dividends_yields; expected_intent: fiis_dividends_yields
- Pergunta: “Último dividendo pago pelo VISC11 e o dy correspondente”
  - Fonte: data/ops/quality/routing_samples.json#payloads[43]
  - expected_entity: fiis_dividends_yields; expected_intent: fiis_dividends_yields

**Observações de teste**
Suporta múltiplos tickers (options.supports_multi_ticker: true). default_date_field: ref_month. Entidade marcada como não privada (private: false). requires_identifiers: tickers. (fonte: data/entities/fiis_dividends_yields/fiis_dividends_yields.yaml)

### client_fiis_enriched_portfolio

**Identificação**

- entity_id: `client_fiis_enriched_portfolio`
- title: Carteira privada – posição enriquecida (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/client_fiis_enriched_portfolio/client_fiis_enriched_portfolio.yaml; data/contracts/entities/client_fiis_enriched_portfolio.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Visão privada e composta da carteira do cliente, cruzando posição, cadastro do FII, métricas financeiras, risco e rankings por ativo.
(fonte: data/entities/client_fiis_enriched_portfolio/client_fiis_enriched_portfolio.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): client_fiis_enriched_portfolio. Requer identificadores: document_number. (fonte: data/entities/client_fiis_enriched_portfolio/client_fiis_enriched_portfolio.yaml)

**Campos / contratos (visão do testador)**
- Schema: data/contracts/entities/client_fiis_enriched_portfolio.schema.yaml
- Campos em destaque (5–15):
  - `document_number`: identificador do cliente (document_number).
  - `position_date`: data de referência da posição.
  - `ticker`: ticker do FII (AAAA11).
  - `fii_name`: nome do fundo imobiliário.
  - `qty`: quantidade de cotas na carteira.
  - `closing_price`: preço de fechamento usado na posição.
  - `position_value`: valor da posição no ativo (qty * preço).
  - `portfolio_value`: valor total da carteira na data.
  - `weight_pct`: peso do ativo na carteira (percentual).
  - `sector`: setor do FII.

**Exemplos reais de perguntas**
- Pergunta: “Me mostra a visão consolidada da minha carteira de FIIs.”
  - Fonte: data/ops/quality/routing_samples.json#payloads[0]
  - expected_entity: client_fiis_enriched_portfolio; expected_intent: client_fiis_enriched_portfolio
- Pergunta: “Quais FIIs da minha carteira aparecem no IFIX e qual a posição de cada um no índice?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[1]
  - expected_entity: client_fiis_enriched_portfolio; expected_intent: client_fiis_enriched_portfolio
- Pergunta: “Quais setores mais pesam na minha carteira de FIIs?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[2]
  - expected_entity: client_fiis_enriched_portfolio; expected_intent: client_fiis_enriched_portfolio
- Pergunta: “Quais são os FIIs da minha carteira e o valor investido em cada um?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[3]
  - expected_entity: client_fiis_enriched_portfolio; expected_intent: client_fiis_enriched_portfolio
- Pergunta: “Qual FII da minha carteira tem o melhor índice de Sharpe?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[4]
  - expected_entity: client_fiis_enriched_portfolio; expected_intent: client_fiis_enriched_portfolio

**Observações de teste**
default_date_field: position_date. Entidade marcada como privada (private: true). requires_identifiers: document_number. (fonte: data/entities/client_fiis_enriched_portfolio/client_fiis_enriched_portfolio.yaml)

### consolidated_macroeconomic

**Identificação**

- entity_id: `consolidated_macroeconomic`
- title: Mercado – Macro consolidada (fonte: data/entities/catalog.yaml)
- kind: historical (fonte: data/entities/catalog.yaml)
- Fonte(s): data/entities/consolidated_macroeconomic/consolidated_macroeconomic.yaml; data/contracts/entities/consolidated_macroeconomic.schema.yaml; data/entities/catalog.yaml; data/ontology/entity.yaml

**Definição (o que é)**
Histórico consolidado de indicadores macroeconômicos, índices de mercado e câmbio por data de referência.
(fonte: data/entities/consolidated_macroeconomic/consolidated_macroeconomic.yaml)

**Finalidade (para que serve)**
Atende ao(s) intent(s): consolidated_macroeconomic. (fonte: data/entities/consolidated_macroeconomic/consolidated_macroeconomic.yaml)

**Campos / contratos (visão do testador)**
Sem schema explícito nas fontes. Verificado: data/contracts/entities/consolidated_macroeconomic.schema.yaml.

**Exemplos reais de perguntas**
- Pergunta: “Cenário macro atual: juros, inflação e câmbio estão favoráveis ou desfavoráveis para FIIs?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[220]
  - expected_entity: consolidated_macroeconomic; expected_intent: consolidated_macroeconomic
- Pergunta: “Como a alta do dólar influencia o cenário para FIIs de recebíveis e fundos em geral?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[221]
  - expected_entity: consolidated_macroeconomic; expected_intent: consolidated_macroeconomic
- Pergunta: “Como a combinação de Selic em queda e dólar volátil costuma impactar os fundos imobiliários?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[222]
  - expected_entity: consolidated_macroeconomic; expected_intent: consolidated_macroeconomic
- Pergunta: “Como a curva de juros projetada pode afetar o preço dos FIIs nos próximos anos?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[223]
  - expected_entity: consolidated_macroeconomic; expected_intent: consolidated_macroeconomic
- Pergunta: “Como a queda da Selic tende a impactar FIIs de tijolo?”
  - Fonte: data/ops/quality/routing_samples.json#payloads[224]
  - expected_entity: consolidated_macroeconomic; expected_intent: consolidated_macroeconomic

**Observações de teste**
default_date_field: ref_date. Entidade marcada como não privada (private: false). (fonte: data/entities/consolidated_macroeconomic/consolidated_macroeconomic.yaml)

## Apêndice A — Inventário de fontes lidas
- data/contracts/entities/client_fiis_dividends_evolution.schema.yaml
- data/contracts/entities/client_fiis_enriched_portfolio.schema.yaml
- data/contracts/entities/client_fiis_performance_vs_benchmark.schema.yaml
- data/contracts/entities/client_fiis_performance_vs_benchmark_summary.schema.yaml
- data/contracts/entities/client_fiis_positions.schema.yaml
- data/contracts/entities/consolidated_macroeconomic.schema.yaml
- data/contracts/entities/fiis_dividends.schema.yaml
- data/contracts/entities/fiis_dividends_yields.schema.yaml
- data/contracts/entities/fiis_financials_revenue_schedule.schema.yaml
- data/contracts/entities/fiis_financials_risk.schema.yaml
- data/contracts/entities/fiis_financials_snapshot.schema.yaml
- data/contracts/entities/fiis_legal_proceedings.schema.yaml
- data/contracts/entities/fiis_news.schema.yaml
- data/contracts/entities/fiis_overview.schema.yaml
- data/contracts/entities/fiis_quota_prices.schema.yaml
- data/contracts/entities/fiis_rankings.schema.yaml
- data/contracts/entities/fiis_real_estate.schema.yaml
- data/contracts/entities/fiis_registrations.schema.yaml
- data/contracts/entities/fiis_yield_history.schema.yaml
- data/contracts/entities/history_b3_indexes.schema.yaml
- data/contracts/entities/history_currency_rates.schema.yaml
- data/contracts/entities/history_market_indicators.schema.yaml
- data/entities/catalog.yaml
- data/entities/client_fiis_dividends_evolution/client_fiis_dividends_evolution.yaml
- data/entities/client_fiis_enriched_portfolio/client_fiis_enriched_portfolio.yaml
- data/entities/client_fiis_performance_vs_benchmark/client_fiis_performance_vs_benchmark.yaml
- data/entities/client_fiis_performance_vs_benchmark_summary/client_fiis_performance_vs_benchmark_summary.yaml
- data/entities/client_fiis_positions/client_fiis_positions.yaml
- data/entities/consolidated_macroeconomic/consolidated_macroeconomic.yaml
- data/entities/fiis_dividends/fiis_dividends.yaml
- data/entities/fiis_dividends_yields/fiis_dividends_yields.yaml
- data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml
- data/entities/fiis_financials_risk/fiis_financials_risk.yaml
- data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml
- data/entities/fiis_legal_proceedings/fiis_legal_proceedings.yaml
- data/entities/fiis_news/fiis_news.yaml
- data/entities/fiis_overview/fiis_overview.yaml
- data/entities/fiis_quota_prices/fiis_quota_prices.yaml
- data/entities/fiis_rankings/fiis_rankings.yaml
- data/entities/fiis_real_estate/fiis_real_estate.yaml
- data/entities/fiis_registrations/fiis_registrations.yaml
- data/entities/fiis_yield_history/fiis_yield_history.yaml
- data/entities/history_b3_indexes/history_b3_indexes.yaml
- data/entities/history_currency_rates/history_currency_rates.yaml
- data/entities/history_market_indicators/history_market_indicators.yaml
- data/ontology/entity.yaml
- data/ops/quality/payloads/client_fiis_dividends_evolution_suite.json
- data/ops/quality/payloads/client_fiis_enriched_portfolio_suite.json
- data/ops/quality/payloads/client_fiis_performance_vs_benchmark_suite.json
- data/ops/quality/payloads/client_fiis_performance_vs_benchmark_summary_suite.json
- data/ops/quality/payloads/client_fiis_positions_suite.json
- data/ops/quality/payloads/consolidated_macroeconomic_suite.json
- data/ops/quality/payloads/entities_sqlonly/client_fiis_dividends_evolution_suite.json
- data/ops/quality/payloads/entities_sqlonly/client_fiis_enriched_portfolio_suite.json
- data/ops/quality/payloads/entities_sqlonly/client_fiis_performance_vs_benchmark_suite.json
- data/ops/quality/payloads/entities_sqlonly/client_fiis_performance_vs_benchmark_summary_suite.json
- data/ops/quality/payloads/entities_sqlonly/client_fiis_positions_suite.json
- data/ops/quality/payloads/entities_sqlonly/consolidated_macroeconomic_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_dividends_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_dividends_yields_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_financials_revenue_schedule_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_financials_risk_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_financials_snapshot_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_legal_proceedings_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_news_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_overview_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_quota_prices_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_rankings_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_real_estate_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_registrations_suite.json
- data/ops/quality/payloads/entities_sqlonly/fiis_yield_history_suite.json
- data/ops/quality/payloads/entities_sqlonly/history_b3_indexes_suite.json
- data/ops/quality/payloads/entities_sqlonly/history_currency_rates_suite.json
- data/ops/quality/payloads/entities_sqlonly/history_market_indicators_suite.json
- data/ops/quality/payloads/fiis_dividends_suite.json
- data/ops/quality/payloads/fiis_dividends_yields_suite.json
- data/ops/quality/payloads/fiis_financials_revenue_schedule_suite.json
- data/ops/quality/payloads/fiis_financials_risk_suite.json
- data/ops/quality/payloads/fiis_financials_snapshot_suite.json
- data/ops/quality/payloads/fiis_legal_proceedings_suite.json
- data/ops/quality/payloads/fiis_news_suite.json
- data/ops/quality/payloads/fiis_overview_suite.json
- data/ops/quality/payloads/fiis_quota_prices_suite.json
- data/ops/quality/payloads/fiis_rankings_suite.json
- data/ops/quality/payloads/fiis_real_estate_suite.json
- data/ops/quality/payloads/fiis_registrations_suite.json
- data/ops/quality/payloads/fiis_yield_history_suite.json
- data/ops/quality/payloads/history_b3_indexes_suite.json
- data/ops/quality/payloads/history_currency_rates_suite.json
- data/ops/quality/payloads/history_market_indicators_suite.json
- data/ops/quality/payloads/negativos_indices_suite.json
- data/ops/quality/routing_samples.json
