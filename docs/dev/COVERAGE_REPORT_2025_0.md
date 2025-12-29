# Coverage Report 2025.0

## Resumo executivo
- Geração automática e determinística a partir dos YAMLs versionados.
- Entidades no catálogo analisadas: 22. Intents na ontologia: 23.
- Gaps identificados: P0=0, P1=0, P2=26.
- Escopo: Ontologia ↔ Catálogo ↔ Contracts/Schemas ↔ Policies (cache, rag, narrator, param_inference).

## Escopo e fontes de verdade (paths)
- Ontologia: `data/ontology/entity.yaml`
- Catálogo: `data/entities/catalog.yaml`
- Schemas: `data/contracts/entities/`
- Policies: `data/policies/` (cache.yaml, rag.yaml, narrator.yaml, context.yaml)
- Param inference: `data/ops/param_inference.yaml`

## Metodologia
- Leitura 100% estática dos YAMLs do repositório, sem chamadas externas.
- Ordenação determinística (alfabética) para registros, gaps e apêndices.
- Checagens aplicadas:
  - **catalog_vs_ontology**: Entidades referenciadas na ontologia devem existir no catálogo.
  - **paths**: Catálogo deve apontar para entity.yaml e schema existentes.
  - **schemas**: Schemas devem ser tabulares (bloco columns) e consistentes com o nome da entidade.
  - **cache_policy**: Flag cache_policy=true exige regra em data/policies/cache.yaml.
  - **rag_policy**: Flag rag_policy=false não pode ter rota ativa/configuração; flag true requer intents permitidos.
  - **narrator_policy**: Flag narrator_policy=true exige regra e não pode ser negada por contexto.
  - **param_inference**: Flag param_inference=true requer intents configurados em data/ops/param_inference.yaml.
- Severidades:
  - **P0**: Quebra contratual ou ausência de fonte: paths inexistentes, schema não tabular, JSON Schema em vez de tabela.
  - **P1**: Drift entre flags e policies que afeta execução: ontologia sem catálogo, cache/narrator/rag marcados mas sem regra ou bloqueados por contexto.
  - **P2**: Higiene e aderência: configurações presentes com flag desativada ou intents faltantes em parametrização.

## Matriz de coverage por entidade
| entidade | bucket | intents | cache | rag | narrator | param_inference | schema_ok | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| carteira_enriquecida | B | carteira_enriquecida | ok | ok | ok | ok | ok | Entidade privada; requer document_number do contexto seguro. |
| client_fiis_dividends_evolution | B | client_fiis_dividends_evolution | ok | ok | ok | ok | ok | entidade privada de carteira; dados por document_number; RAG/Narrator negados por policy; resposta 100% SQL determinística |
| client_fiis_performance_vs_benchmark | B | client_fiis_performance_vs_benchmark | ok | ok | ok | ok | ok | entidade privada de carteira; comparação determinística vs IFIX/IFIL/IBOV/CDI; binding de document_number via contexto seguro; benchmark_code pode ser texto do usuário |
| client_fiis_performance_vs_benchmark_summary | B | client_fiis_performance_vs_benchmark_summary | ok | ok | ok | ok | ok | entidade privada dependente de document_number |
| client_fiis_positions | B | client_fiis_positions | ok | ok | ok | ok | ok |  |
| dividendos_yield | A | dividendos_yield, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fii_overview | A | fii_overview, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_cadastro | A | fiis_cadastro, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_dividendos | A | fiis_dividendos, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_financials_revenue_schedule | A | fiis_financials_revenue_schedule, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_financials_risk | A | fiis_financials_risk, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_financials_snapshot | A | fiis_financials_snapshot, ticker_query | ok | policy_present_flag_false | ok | ok | ok |  |
| fiis_imoveis | A | fiis_imoveis, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_noticias | A | fiis_noticias | ok | ok | ok | ok | ok |  |
| fiis_precos | A | fiis_precos, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_processos | A | fiis_processos, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_rankings | A | fiis_rankings, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| fiis_yield_history | A | fiis_yield_history, ticker_query | ok | policy_present_flag_false | ok | partial | ok |  |
| history_b3_indexes | C | history_b3_indexes | ok | policy_present_flag_false | ok | ok | ok |  |
| history_currency_rates | C | history_currency_rates | ok | policy_present_flag_false | ok | ok | ok |  |
| history_market_indicators | C | history_market_indicators | ok | policy_present_flag_false | ok | ok | ok |  |
| macro_consolidada | C | macro_consolidada | ok | ok | ok | ok | ok |  |

## Gaps (P0/P1/P2) e definições
- Definições objetivas e exemplos:
  - P0: paths inexistentes, schema não tabular ou divergente; impede execução.
  - P1: drift de flags vs policies (cache, narrator, rag) ou ontologia sem catálogo; bloqueio lógico.
  - P2: higienização (flags desativadas com config ativa, intents sem parametrização).

### P0 (Quebra contratual ou ausência de fonte: paths inexistentes, schema não tabular, JSON Schema em vez de tabela.)
- Nenhum.

### P1 (Drift entre flags e policies que afeta execução: ontologia sem catálogo, cache/narrator/rag marcados mas sem regra ou bloqueados por contexto.)
- Nenhum.

### P2 (Higiene e aderência: configurações presentes com flag desativada ou intents faltantes em parametrização.)
- dividendos_yield: catalog rag_policy=false but RAG configuration present
- dividendos_yield: some intents missing param inference configuration
- fii_overview: catalog rag_policy=false but RAG configuration present
- fii_overview: some intents missing param inference configuration
- fiis_cadastro: catalog rag_policy=false but RAG configuration present
- fiis_cadastro: some intents missing param inference configuration
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
- fiis_processos: some intents missing param inference configuration
- fiis_rankings: catalog rag_policy=false but RAG configuration present
- fiis_rankings: some intents missing param inference configuration
- fiis_yield_history: catalog rag_policy=false but RAG configuration present
- fiis_yield_history: some intents missing param inference configuration
- history_b3_indexes: catalog rag_policy=false but RAG configuration present
- history_currency_rates: catalog rag_policy=false but RAG configuration present
- history_market_indicators: catalog rag_policy=false but RAG configuration present

## Apêndice
### Entidades no catálogo
carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada

### Entidades na ontologia
carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada

### Intents na ontologia
carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada, ticker_query

### Policies RAG (routing)
Allow intents: —
Deny intents: carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, macro_consolidada
