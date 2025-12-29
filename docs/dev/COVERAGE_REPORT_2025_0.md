# Coverage Report 2025.0

## Resumo executivo
- Geração automática a partir de YAML (determinística, ordenação alfabética).
- Escopo: Ontologia ↔ Catálogo ↔ Contracts ↔ Policies.
- Prioridades: P0 (contrato), P1 (drift flags/policies), P2 (higiene).

## Matriz de coverage por entidade
| entidade | intents | cache | rag | narrator | param_inference | schema_ok | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| carteira_enriquecida | carteira_enriquecida | ok | ok | ok | ok | ok | Entidade privada; requer document_number do contexto seguro. |
| client_fiis_dividends_evolution | client_fiis_dividends_evolution | ok | ok | ok | ok | ok | entidade privada de carteira; dados por document_number; RAG/Narrator negados por policy; resposta 100% SQL determinística |
| client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | ok | ok | ok | ok | ok | entidade privada de carteira; comparação determinística vs IFIX/IFIL/IBOV/CDI; binding de document_number via contexto seguro; benchmark_code pode ser texto do usuário |
| client_fiis_positions | client_fiis_positions | ok | ok | ok | ok | ok |  |
| dividendos_yield | dividendos_yield, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fii_overview | fii_overview, ticker_query | ok | policy_present_flag_false | ok | configured_flag_false | ok |  |
| fiis_cadastro | fiis_cadastro, ticker_query | ok | policy_present_flag_false | ok | configured_flag_false | ok |  |
| fiis_dividendos | fiis_dividendos, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_financials_revenue_schedule | fiis_financials_revenue_schedule, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_financials_risk | fiis_financials_risk, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_financials_snapshot | fiis_financials_snapshot, ticker_query | ok | policy_present_flag_false | ok | ok | ok |  |
| fiis_imoveis | fiis_imoveis, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_noticias | fiis_noticias | ok | ok | ok | ok | ok |  |
| fiis_precos | fiis_precos, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_processos | fiis_processos, ticker_query | ok | policy_present_flag_false | ok | configured_flag_false | ok |  |
| fiis_rankings | fiis_rankings, ticker_query | ok | policy_present_flag_false | ok | ok | ok |  |
| fiis_yield_history | fiis_yield_history, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| history_b3_indexes | history_b3_indexes | ok | policy_present_flag_false | denied_by_context | ok | ok |  |
| history_currency_rates | history_currency_rates | ok | policy_present_flag_false | denied_by_context | ok | ok |  |
| history_market_indicators | history_market_indicators | ok | policy_present_flag_false | denied_by_context | ok | ok |  |
| macro_consolidada | macro_consolidada | ok | ok | ok | ok | ok |  |

## Gaps P0/P1/P2
### P0
- Nenhum.

### P1
- client_fiis_performance_vs_benchmark_summary: Entity referenced in ontology is missing from catalog
- history_b3_indexes: narrator flag active but denied by context policy
- history_b3_indexes: narrator flag active but no narrator rule found
- history_currency_rates: narrator flag active but denied by context policy
- history_currency_rates: narrator flag active but no narrator rule found
- history_market_indicators: narrator flag active but denied by context policy
- history_market_indicators: narrator flag active but no narrator rule found

### P2
- dividendos_yield: catalog rag_policy=false but RAG configuration present
- dividendos_yield: some intents missing param inference configuration
- fii_overview: catalog rag_policy=false but RAG configuration present
- fii_overview: param inference config present but flag is false
- fiis_cadastro: catalog rag_policy=false but RAG configuration present
- fiis_cadastro: param inference config present but flag is false
- fiis_dividendos: catalog rag_policy=false but RAG configuration present
- fiis_dividendos: some intents missing param inference configuration
- fiis_financials_revenue_schedule: catalog rag_policy=false but RAG configuration present
- fiis_financials_revenue_schedule: some intents missing param inference configuration
- fiis_financials_risk: catalog rag_policy=false but RAG configuration present
- fiis_financials_risk: some intents missing param inference configuration
- fiis_financials_snapshot: catalog rag_policy=false but RAG configuration present
- fiis_imoveis: catalog rag_policy=false but RAG configuration present
- fiis_imoveis: some intents missing param inference configuration
- fiis_precos: catalog rag_policy=false but RAG configuration present
- fiis_precos: some intents missing param inference configuration
- fiis_processos: catalog rag_policy=false but RAG configuration present
- fiis_processos: param inference config present but flag is false
- fiis_rankings: catalog rag_policy=false but RAG configuration present
- fiis_yield_history: catalog rag_policy=false but RAG configuration present
- fiis_yield_history: some intents missing param inference configuration
- history_b3_indexes: catalog rag_policy=false but RAG configuration present
- history_currency_rates: catalog rag_policy=false but RAG configuration present
- history_market_indicators: catalog rag_policy=false but RAG configuration present

## Apêndice
### Entidades no catálogo
carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada

### Entidades na ontologia
carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada

### Intents na ontologia
carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada, ticker_query

### Policies RAG (routing)
Allow intents: —
Deny intents: carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, macro_consolidada
