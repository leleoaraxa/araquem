# Audit – Capabilities (Static & Live)

Relatório gerado automaticamente por `scripts/audit/audit_capabilities.py`.

## Tabela por entidade
| entity | has_contract | has_entity_yaml | supports_multi_ticker | multi_ticker_template | response_kinds | has_hints_md | in_quality_suite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| carteira_enriquecida | yes | yes | yes | no | table | no | yes |
| client_fiis_dividends_evolution | yes | yes | no | no | table | no | yes |
| client_fiis_performance_vs_benchmark | yes | yes | - | no | table | no | yes |
| client_fiis_positions | yes | yes | - | no | table | yes | yes |
| dividendos_yield | yes | yes | yes | no | table | no | yes |
| fii_overview | yes | yes | yes | no | table | no | yes |
| fiis_cadastro | yes | yes | yes | no | list | yes | yes |
| fiis_dividendos | yes | yes | yes | yes | table | yes | yes |
| fiis_financials_revenue_schedule | yes | yes | yes | no | table | yes | yes |
| fiis_financials_risk | yes | yes | yes | no | table | yes | yes |
| fiis_financials_snapshot | yes | yes | yes | no | table | yes | yes |
| fiis_imoveis | yes | yes | yes | yes | table | yes | yes |
| fiis_noticias | yes | yes | yes | yes | list | yes | yes |
| fiis_precos | yes | yes | yes | no | table | yes | yes |
| fiis_processos | yes | yes | yes | yes | list | yes | yes |
| fiis_rankings | yes | yes | yes | no | table | yes | yes |
| fiis_yield_history | yes | yes | yes | yes | table | no | yes |
| history_b3_indexes | yes | yes | - | no | table | yes | yes |
| history_currency_rates | yes | yes | - | no | table | yes | yes |
| history_market_indicators | yes | yes | - | no | table | yes | yes |
| macro_consolidada | yes | yes | - | no | table | no | yes |

## Ready
- client_fiis_dividends_evolution
- fiis_dividendos
- fiis_imoveis
- fiis_noticias
- fiis_processos
- fiis_yield_history

## Ready but unused
- carteira_enriquecida: supports_multi_ticker no YAML mas template não agrupa por ticker
- dividendos_yield: supports_multi_ticker no YAML mas template não agrupa por ticker
- fii_overview: supports_multi_ticker no YAML mas template não agrupa por ticker
- fiis_cadastro: supports_multi_ticker no YAML mas template não agrupa por ticker
- fiis_financials_revenue_schedule: supports_multi_ticker no YAML mas template não agrupa por ticker
- fiis_financials_risk: supports_multi_ticker no YAML mas template não agrupa por ticker
- fiis_financials_snapshot: supports_multi_ticker no YAML mas template não agrupa por ticker
- fiis_precos: supports_multi_ticker no YAML mas template não agrupa por ticker
- fiis_rankings: supports_multi_ticker no YAML mas template não agrupa por ticker

## Missing / Gaps
- carteira_enriquecida: render multi-ticker ausente no template
- dividendos_yield: render multi-ticker ausente no template
- fii_overview: render multi-ticker ausente no template
- fiis_cadastro: render multi-ticker ausente no template
- fiis_financials_revenue_schedule: render multi-ticker ausente no template
- fiis_financials_risk: render multi-ticker ausente no template
- fiis_financials_snapshot: render multi-ticker ausente no template
- fiis_precos: render multi-ticker ausente no template
- fiis_rankings: render multi-ticker ausente no template

## Ontologia – intents por entidade
- carteira_enriquecida: carteira_enriquecida
- client_fiis_dividends_evolution: client_fiis_dividends_evolution
- client_fiis_performance_vs_benchmark: client_fiis_performance_vs_benchmark
- client_fiis_positions: client_fiis_positions
- dividendos_yield: dividendos_yield, ticker_query
- fii_overview: fii_overview, ticker_query
- fiis_cadastro: fiis_cadastro, ticker_query
- fiis_dividendos: fiis_dividendos, ticker_query
- fiis_financials_revenue_schedule: fiis_financials_revenue_schedule, ticker_query
- fiis_financials_risk: fiis_financials_risk, ticker_query
- fiis_financials_snapshot: fiis_financials_snapshot, ticker_query
- fiis_imoveis: fiis_imoveis, ticker_query
- fiis_noticias: fiis_noticias
- fiis_precos: fiis_precos, ticker_query
- fiis_processos: fiis_processos, ticker_query
- fiis_rankings: fiis_rankings, ticker_query
- fiis_yield_history: fiis_yield_history, ticker_query
- history_b3_indexes: history_b3_indexes
- history_currency_rates: history_currency_rates
- history_market_indicators: history_market_indicators
- macro_consolidada: macro_consolidada

### Overlaps literais (top 10)
- fii_overview x fiis_financials_snapshot: abl, alavancagem, alta, baixa, beta, calendario, cambio, campeoes, cdi, cotacao, cronograma, curva, destaques, dividendo, dividendos, dy, fato, fatos, gestora, igpm, imprensa, inflacao, ipca, juros, lanternas, macro, maiores fiis, mandato, mdd, melhores, nome, noticia, noticias, objetivo, patrimonio, patrimonio_liquido, piores, pl, preco, processo, proventos, ranking, razao, relevante, risco, selic, sharpe, sortino, top, vacancia, valor_patrimonial, variacao, volatilidade, vp, yield
- fii_overview x fiis_noticias: abl, alta, baixa, beta, cdi, classe, contratos, cotacao, dividendo, dividendos, dolar, dy, eur, euro, fato, fatos, ifix, igpm, imoveis, imprensa, indicadores, inflacao, ipca, mandato, mdd, nome, noticia, noticias, ocupacao, overview, patrimonio, pl, posicao, preco, proventos, ranking, receita, relevante, risco, segmento, selic, sharpe, snapshot, sortino, usd, vacancia, variacao, volatilidade, yield
- fii_overview x fiis_yield_history: alavancagem, alta, baixa, cambio, campeoes, contratos, cotacao, curva, destaques, dividendo, dividendos, dy, fato, gestor, gestora, imoveis, imprensa, indicadores, inflacao, ipca, juros, lanternas, macro, melhores, noticia, ocupacao, overview, patrimonio, patrimonio_liquido, piores, preco, proventos, ranking, resumo, segmento, selic, snapshot, top, vacancia, valor_patrimonial, variacao, vp
- fiis_dividendos x fiis_yield_history: alta, baixa, cambio, campeoes, carteira, carteira de fiis, comunicado, cotacao, cotacoes, curva, destaques, dividend yield, dividendo, dividendos, dy, dy em, fato, imprensa, inflacao, ipca, juros, lanternas, macro, melhores, meus fiis, minha carteira, minha carteira de fiis, noticia, oscilacao, payout, piores, preco, precos, provento, proventos, ranking, rendimento, selic, top, variacao
- fiis_dividendos x fiis_financials_snapshot: alta, baixa, beta, cambio, campeoes, cotacao, curva, destaques, dividendo, dividendos, dy, fato, imprensa, inflacao, ipca, juros, lanternas, macro, mdd, melhores, noticia, oscilacao, pagamento, payout, payout e a reserva de dividendos do <ticker>, payout e reserva de dividendos do <ticker>, piores, preco, proventos, ranking, reserva de dividendos, risco, selic, sharpe, sortino, top, treynor, variacao, volatilidade, yield
- fii_overview x fiis_financials_risk: alta, baixa, beta, cambio, campeoes, cdi, contratos, cotacao, destaques, dividendo, dividendos, dy, gestor, imoveis, inflacao, ipca, lanternas, macro, mdd, melhores, overview, patrimonio, patrimonio_liquido, piores, pl, posicao, preco, proventos, ranking, risco, selic, sharpe, snapshot, sortino, top, vacancia, variacao, volatilidade, yield
- fiis_yield_history x fiis_financials_snapshot: administrador, alavancagem, alta, baixa, cambio, campeoes, cnpj, cotacao, curva, destaques, dividendo, dividendos, dy, fato, gestora, imprensa, inflacao, ipca, juros, lanternas, macro, melhores, noticia, oscilacao, patrimonio, patrimonio_liquido, payout, piores, preco, proventos, ranking, selic, top, vacancia, valor_patrimonial, valor_patrimonial_cota, variacao, vp
- fiis_financials_snapshot x fiis_noticias: abl, administrador, alta, baixa, beta, cdi, cnpj, cotacao, dividendo, dividendos, dy, fato, fatos, igpm, imprensa, inflacao, ipca, mandato, mdd, nome, noticia, noticias, oscilacao, patrimonio, pl, preco, proventos, ranking, relevante, risco, selic, sharpe, sortino, vacancia, variacao, volatilidade, yield
- fiis_financials_snapshot x fiis_financials_risk: alta, baixa, beta, cambio, campeoes, cdi, cnpj, cotacao, destaques, dividendo, dividendos, dy, inflacao, ipca, lanternas, macro, mdd, melhores, pagamento, patrimonio, patrimonio_liquido, piores, pl, preco, proventos, ranking, risco, selic, sharpe, soma, sortino, top, vacancia, variacao, volatilidade, yield
- fiis_noticias x fiis_processos: abl, alta, baixa, beta, carteira, cdi, contratos, cotacao, dividendos, dy, ifil, ifix, imoveis, mdd, movimentos, noticia, noticias, ocupacao, patrimonio, peso, pl, posicao, posicoes, preco, proventos, ranking, receita, rendimento, reportagem, selic, sharpe, sortino, vacancia, variacao, volatilidade, yield

### Literais presentes em intents de 3+ entidades
- `[A-Za-z]{4}11` em intents ticker_query cobrindo entidades dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history
- `preco medio` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_positions, fiis_precos cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_positions, fiis_precos
- `pm` em intents client_fiis_dividends_evolution, client_fiis_positions, fiis_precos cobrindo entidades client_fiis_dividends_evolution, client_fiis_positions, fiis_precos
- `rendimento mensal` em intents client_fiis_positions, fiis_dividendos, fiis_financials_revenue_schedule cobrindo entidades client_fiis_positions, fiis_dividendos, fiis_financials_revenue_schedule
- `lanternas` em intents client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history cobrindo entidades client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history
- `cdi` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, history_b3_indexes, history_market_indicators, macro_consolidada cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, history_b3_indexes, history_market_indicators, macro_consolidada
- `sharpe` em intents client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos cobrindo entidades client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos
- `processos` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_precos, fiis_processos, fiis_rankings cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_precos, fiis_processos, fiis_rankings
- `atual` em intents client_fiis_positions, fiis_financials_revenue_schedule, history_market_indicators, macro_consolidada cobrindo entidades client_fiis_positions, fiis_financials_revenue_schedule, history_market_indicators, macro_consolidada
- `posicoes` em intents client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_noticias, fiis_processos, fiis_rankings cobrindo entidades client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_noticias, fiis_processos, fiis_rankings
- `preco_medio` em intents client_fiis_dividends_evolution, client_fiis_positions, fiis_precos cobrindo entidades client_fiis_dividends_evolution, client_fiis_positions, fiis_precos
- `cotas` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro
- `dy` em intents carteira_enriquecida, client_fiis_performance_vs_benchmark, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades carteira_enriquecida, client_fiis_performance_vs_benchmark, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `dividendos` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `proventos` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos, fiis_yield_history cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos, fiis_yield_history
- `valor` em intents client_fiis_positions, fiis_financials_revenue_schedule, history_market_indicators cobrindo entidades client_fiis_positions, fiis_financials_revenue_schedule, history_market_indicators
- `ifix` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, history_b3_indexes, history_market_indicators, macro_consolidada cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, history_b3_indexes, history_market_indicators, macro_consolidada
- `piores` em intents client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_rankings, fiis_yield_history cobrindo entidades client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_rankings, fiis_yield_history
- `dividendo` em intents client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history cobrindo entidades client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history
- `ranking` em intents client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes cobrindo entidades client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes
- `ibov` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_precos, history_b3_indexes, history_market_indicators, macro_consolidada cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_precos, history_b3_indexes, history_market_indicators, macro_consolidada
- `cpf` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions
- `ifil` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, history_b3_indexes, history_market_indicators cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, history_b3_indexes, history_market_indicators
- `distribuicao` em intents client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_processos cobrindo entidades client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_processos
- `imoveis` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_financials_risk, fiis_imoveis, fiis_noticias, fiis_processos, fiis_yield_history cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_financials_risk, fiis_imoveis, fiis_noticias, fiis_processos, fiis_yield_history
- `provento` em intents client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_yield_history cobrindo entidades client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_yield_history
- `posicao` em intents client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_financials_risk, fiis_noticias, fiis_processos, fiis_rankings, history_b3_indexes cobrindo entidades client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_cadastro, fiis_financials_risk, fiis_noticias, fiis_processos, fiis_rankings, history_b3_indexes
- `minhas` em intents client_fiis_dividends_evolution, client_fiis_positions, dividendos_yield, fiis_dividendos cobrindo entidades client_fiis_dividends_evolution, client_fiis_positions, dividendos_yield, fiis_dividendos
- `vacancia` em intents client_fiis_positions, fii_overview, fiis_cadastro, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades client_fiis_positions, fii_overview, fiis_cadastro, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `documento` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions
- `melhores` em intents client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_rankings, fiis_yield_history cobrindo entidades client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_rankings, fiis_yield_history
- `benchmark` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_precos cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_precos
- `destaques` em intents client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_precos, fiis_yield_history cobrindo entidades client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_precos, fiis_yield_history
- `judicial` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_financials_snapshot, fiis_imoveis, fiis_processos, fiis_rankings cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_financials_snapshot, fiis_imoveis, fiis_processos, fiis_rankings
- `peso` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_noticias, fiis_processos, fiis_rankings, history_b3_indexes cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_noticias, fiis_processos, fiis_rankings, history_b3_indexes
- `processo` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_financials_snapshot, fiis_imoveis, fiis_processos, fiis_rankings cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fii_overview, fiis_financials_snapshot, fiis_imoveis, fiis_processos, fiis_rankings
- `rendimento` em intents carteira_enriquecida, client_fiis_positions, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades carteira_enriquecida, client_fiis_positions, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `meu` em intents client_fiis_dividends_evolution, client_fiis_positions, dividendos_yield, fiis_dividendos cobrindo entidades client_fiis_dividends_evolution, client_fiis_positions, dividendos_yield, fiis_dividendos
- `renda` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_noticias cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_noticias
- `minha` em intents client_fiis_dividends_evolution, client_fiis_positions, dividendos_yield, fiis_dividendos cobrindo entidades client_fiis_dividends_evolution, client_fiis_positions, dividendos_yield, fiis_dividendos
- `top` em intents client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_rankings, fiis_yield_history cobrindo entidades client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_rankings, fiis_yield_history
- `imovel` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_financials_risk, fiis_imoveis cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_financials_risk, fiis_imoveis
- `campeoes` em intents client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history cobrindo entidades client_fiis_positions, fii_overview, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history
- `carteira de fiis` em intents client_fiis_positions, dividendos_yield, fiis_dividendos, fiis_yield_history cobrindo entidades client_fiis_positions, dividendos_yield, fiis_dividendos, fiis_yield_history
- `cnpj` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_yield_history cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_positions, fiis_cadastro, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_yield_history
- `versus` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_precos cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_precos
- `mes a mes` em intents carteira_enriquecida, client_fiis_dividends_evolution, dividendos_yield, fiis_yield_history cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, dividendos_yield, fiis_yield_history
- `mes` em intents carteira_enriquecida, client_fiis_dividends_evolution, fiis_dividendos, fiis_noticias cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, fiis_dividendos, fiis_noticias
- `12 meses` em intents carteira_enriquecida, client_fiis_dividends_evolution, fiis_yield_history cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, fiis_yield_history
- `judiciais` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_processos, fiis_rankings cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_processos, fiis_rankings
- `mensal` em intents carteira_enriquecida, client_fiis_dividends_evolution, fiis_dividendos cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, fiis_dividendos
- `receitas` em intents client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule cobrindo entidades client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule
- `receita` em intents client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule, fiis_noticias, fiis_processos cobrindo entidades client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule, fiis_noticias, fiis_processos
- `recebiveis` em intents client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule cobrindo entidades client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule
- `carteira` em intents client_fiis_dividends_evolution, dividendos_yield, fiis_dividendos, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades client_fiis_dividends_evolution, dividendos_yield, fiis_dividendos, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `evolucao` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_processos, history_currency_rates, history_market_indicators, macro_consolidada cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_processos, history_currency_rates, history_market_indicators, macro_consolidada
- `relatorio gerencial` em intents client_fiis_dividends_evolution, fiis_financials_snapshot, fiis_imoveis cobrindo entidades client_fiis_dividends_evolution, fiis_financials_snapshot, fiis_imoveis
- `indice de referencia` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_precos cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_precos
- `reserva de dividendos` em intents client_fiis_dividends_evolution, fiis_dividendos, fiis_financials_snapshot cobrindo entidades client_fiis_dividends_evolution, fiis_dividendos, fiis_financials_snapshot
- `payout` em intents client_fiis_dividends_evolution, fiis_cadastro, fiis_dividendos, fiis_financials_snapshot, fiis_yield_history cobrindo entidades client_fiis_dividends_evolution, fiis_cadastro, fiis_dividendos, fiis_financials_snapshot, fiis_yield_history
- `historico` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fii_overview, fiis_dividendos, fiis_rankings, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fii_overview, fiis_dividendos, fiis_rankings, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada
- `indice` em intents client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule, fiis_precos, fiis_rankings, history_b3_indexes cobrindo entidades client_fiis_dividends_evolution, fii_overview, fiis_financials_revenue_schedule, fiis_precos, fiis_rankings, history_b3_indexes
- `historico de dividendos` em intents client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_dividendos cobrindo entidades client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_dividendos
- `ultimos 12 meses` em intents client_fiis_dividends_evolution, fiis_dividendos, history_market_indicators, macro_consolidada cobrindo entidades client_fiis_dividends_evolution, fiis_dividendos, history_market_indicators, macro_consolidada
- `vs` em intents carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_precos cobrindo entidades carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, fiis_precos
- `acumulado` em intents client_fiis_performance_vs_benchmark, fiis_dividendos, fiis_precos, macro_consolidada cobrindo entidades client_fiis_performance_vs_benchmark, fiis_dividendos, fiis_precos, macro_consolidada
- `comparacao` em intents carteira_enriquecida, client_fiis_performance_vs_benchmark, dividendos_yield, fiis_precos, fiis_processos cobrindo entidades carteira_enriquecida, client_fiis_performance_vs_benchmark, dividendos_yield, fiis_precos, fiis_processos
- `preco hoje` em intents client_fiis_performance_vs_benchmark, fiis_precos, fiis_rankings cobrindo entidades client_fiis_performance_vs_benchmark, fiis_precos, fiis_rankings
- `acao` em intents client_fiis_performance_vs_benchmark, fiis_financials_snapshot, fiis_imoveis, fiis_processos, fiis_rankings cobrindo entidades client_fiis_performance_vs_benchmark, fiis_financials_snapshot, fiis_imoveis, fiis_processos, fiis_rankings
- `ibovespa` em intents client_fiis_performance_vs_benchmark, fii_overview, fiis_precos, history_b3_indexes cobrindo entidades client_fiis_performance_vs_benchmark, fii_overview, fiis_precos, history_b3_indexes
- `fechamento` em intents client_fiis_performance_vs_benchmark, fiis_dividendos, fiis_precos, fiis_rankings, history_b3_indexes cobrindo entidades client_fiis_performance_vs_benchmark, fiis_dividendos, fiis_precos, fiis_rankings, history_b3_indexes
- `ipca` em intents client_fiis_performance_vs_benchmark, fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history, history_b3_indexes, history_market_indicators, macro_consolidada cobrindo entidades client_fiis_performance_vs_benchmark, fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history, history_b3_indexes, history_market_indicators, macro_consolidada
- `noticia` em intents client_fiis_performance_vs_benchmark, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history cobrindo entidades client_fiis_performance_vs_benchmark, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history
- `peso do` em intents carteira_enriquecida, client_fiis_performance_vs_benchmark, fiis_rankings cobrindo entidades carteira_enriquecida, client_fiis_performance_vs_benchmark, fiis_rankings
- `abertura` em intents client_fiis_performance_vs_benchmark, fiis_dividendos, fiis_precos cobrindo entidades client_fiis_performance_vs_benchmark, fiis_dividendos, fiis_precos
- `fato relevante` em intents client_fiis_performance_vs_benchmark, fiis_cadastro, fiis_noticias cobrindo entidades client_fiis_performance_vs_benchmark, fiis_cadastro, fiis_noticias
- `yield` em intents carteira_enriquecida, client_fiis_performance_vs_benchmark, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos cobrindo entidades carteira_enriquecida, client_fiis_performance_vs_benchmark, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos
- `acoes` em intents client_fiis_performance_vs_benchmark, fiis_processos, fiis_rankings cobrindo entidades client_fiis_performance_vs_benchmark, fiis_processos, fiis_rankings
- `incc` em intents client_fiis_performance_vs_benchmark, fiis_financials_revenue_schedule, history_market_indicators cobrindo entidades client_fiis_performance_vs_benchmark, fiis_financials_revenue_schedule, history_market_indicators
- `comparar` em intents carteira_enriquecida, client_fiis_performance_vs_benchmark, dividendos_yield, fii_overview, fiis_processos, history_market_indicators, macro_consolidada cobrindo entidades carteira_enriquecida, client_fiis_performance_vs_benchmark, dividendos_yield, fii_overview, fiis_processos, history_market_indicators, macro_consolidada
- `noticias` em intents client_fiis_performance_vs_benchmark, fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos cobrindo entidades client_fiis_performance_vs_benchmark, fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos
- `performance` em intents carteira_enriquecida, client_fiis_performance_vs_benchmark, fii_overview, fiis_precos, fiis_processos cobrindo entidades carteira_enriquecida, client_fiis_performance_vs_benchmark, fii_overview, fiis_precos, fiis_processos
- `comparativo` em intents client_fiis_performance_vs_benchmark, dividendos_yield, fii_overview, history_market_indicators, macro_consolidada cobrindo entidades client_fiis_performance_vs_benchmark, dividendos_yield, fii_overview, history_market_indicators, macro_consolidada
- `media` em intents fiis_cadastro, fiis_financials_revenue_schedule, fiis_financials_snapshot cobrindo entidades fiis_cadastro, fiis_financials_revenue_schedule, fiis_financials_snapshot
- `contratos` em intents fii_overview, fiis_cadastro, fiis_financials_risk, fiis_noticias, fiis_processos, fiis_yield_history cobrindo entidades fii_overview, fiis_cadastro, fiis_financials_risk, fiis_noticias, fiis_processos, fiis_yield_history
- `treynor` em intents fiis_cadastro, fiis_dividendos, fiis_financials_snapshot cobrindo entidades fiis_cadastro, fiis_dividendos, fiis_financials_snapshot
- `preco` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history
- `abl` em intents fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_noticias, fiis_processos cobrindo entidades fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_noticias, fiis_processos
- `baixa` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `beta` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos, fiis_rankings cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos, fiis_rankings
- `volatilidade` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos
- `cotacoes` em intents fiis_cadastro, fiis_dividendos, fiis_yield_history cobrindo entidades fiis_cadastro, fiis_dividendos, fiis_yield_history
- `mdd` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos
- `nome` em intents fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_noticias cobrindo entidades fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_noticias
- `alta` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `variacao` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history, history_b3_indexes cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history, history_b3_indexes
- `sortino` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos
- `alavancagem` em intents fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_yield_history cobrindo entidades fii_overview, fiis_cadastro, fiis_financials_snapshot, fiis_yield_history
- `vacancia do` em intents fiis_cadastro, fiis_imoveis, fiis_rankings cobrindo entidades fiis_cadastro, fiis_imoveis, fiis_rankings
- `risco` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias
- `setor` em intents fiis_cadastro, fiis_noticias, fiis_precos, fiis_yield_history cobrindo entidades fiis_cadastro, fiis_noticias, fiis_precos, fiis_yield_history
- `cotacao` em intents fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_currency_rates cobrindo entidades fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_currency_rates
- `r2` em intents fiis_cadastro, fiis_dividendos, fiis_rankings cobrindo entidades fiis_cadastro, fiis_dividendos, fiis_rankings
- `segmento` em intents fii_overview, fiis_cadastro, fiis_noticias, fiis_precos, fiis_yield_history cobrindo entidades fii_overview, fiis_cadastro, fiis_noticias, fiis_precos, fiis_yield_history
- `precos` em intents fiis_cadastro, fiis_dividendos, fiis_yield_history cobrindo entidades fiis_cadastro, fiis_dividendos, fiis_yield_history
- `administrador` em intents fiis_cadastro, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history cobrindo entidades fiis_cadastro, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history
- `euro` em intents fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada cobrindo entidades fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada
- `cambio` em intents fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_precos, fiis_yield_history, history_currency_rates, macro_consolidada cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_precos, fiis_yield_history, history_currency_rates, macro_consolidada
- `mandato` em intents fii_overview, fiis_financials_snapshot, fiis_noticias, fiis_precos cobrindo entidades fii_overview, fiis_financials_snapshot, fiis_noticias, fiis_precos
- `igpm` em intents fii_overview, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_noticias, history_market_indicators cobrindo entidades fii_overview, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_noticias, history_market_indicators
- `inflacao` em intents fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_yield_history
- `fato` em intents fii_overview, fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_yield_history cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_yield_history
- `curva` em intents fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_yield_history, history_market_indicators cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_yield_history, history_market_indicators
- `selic` em intents fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_market_indicators, macro_consolidada cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_market_indicators, macro_consolidada
- `valor_patrimonial` em intents fii_overview, fiis_financials_snapshot, fiis_yield_history cobrindo entidades fii_overview, fiis_financials_snapshot, fiis_yield_history
- `usd` em intents fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators cobrindo entidades fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators
- `panorama` em intents fii_overview, history_market_indicators, macro_consolidada cobrindo entidades fii_overview, history_market_indicators, macro_consolidada
- `eur` em intents fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators cobrindo entidades fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators
- `juros` em intents fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_yield_history cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_yield_history
- `relevante` em intents fii_overview, fiis_financials_snapshot, fiis_noticias cobrindo entidades fii_overview, fiis_financials_snapshot, fiis_noticias
- `indicadores` em intents fii_overview, fiis_noticias, fiis_yield_history cobrindo entidades fii_overview, fiis_noticias, fiis_yield_history
- `cronograma` em intents fii_overview, fiis_financials_revenue_schedule, fiis_financials_snapshot cobrindo entidades fii_overview, fiis_financials_revenue_schedule, fiis_financials_snapshot
- `fatos` em intents fii_overview, fiis_financials_snapshot, fiis_noticias cobrindo entidades fii_overview, fiis_financials_snapshot, fiis_noticias
- `overview` em intents carteira_enriquecida, fii_overview, fiis_financials_risk, fiis_noticias, fiis_precos, fiis_yield_history cobrindo entidades carteira_enriquecida, fii_overview, fiis_financials_risk, fiis_noticias, fiis_precos, fiis_yield_history
- `classe` em intents carteira_enriquecida, fii_overview, fiis_noticias cobrindo entidades carteira_enriquecida, fii_overview, fiis_noticias
- `pontos` em intents fii_overview, fiis_rankings, history_b3_indexes cobrindo entidades fii_overview, fiis_rankings, history_b3_indexes
- `macro` em intents fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history, macro_consolidada cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history, macro_consolidada
- `gestora` em intents fii_overview, fiis_financials_snapshot, fiis_yield_history cobrindo entidades fii_overview, fiis_financials_snapshot, fiis_yield_history
- `ocupacao` em intents fii_overview, fiis_imoveis, fiis_noticias, fiis_processos, fiis_yield_history cobrindo entidades fii_overview, fiis_imoveis, fiis_noticias, fiis_processos, fiis_yield_history
- `dolar` em intents fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada cobrindo entidades fii_overview, fiis_noticias, fiis_precos, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada
- `vp` em intents fii_overview, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_yield_history cobrindo entidades fii_overview, fiis_financials_revenue_schedule, fiis_financials_snapshot, fiis_yield_history
- `gestor` em intents fii_overview, fiis_financials_risk, fiis_yield_history cobrindo entidades fii_overview, fiis_financials_risk, fiis_yield_history
- `snapshot` em intents fii_overview, fiis_financials_risk, fiis_noticias, fiis_precos, fiis_yield_history cobrindo entidades fii_overview, fiis_financials_risk, fiis_noticias, fiis_precos, fiis_yield_history
- `patrimonio` em intents carteira_enriquecida, fii_overview, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history cobrindo entidades carteira_enriquecida, fii_overview, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_precos, fiis_processos, fiis_yield_history
- `pl` em intents fii_overview, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos cobrindo entidades fii_overview, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_noticias, fiis_processos
- `patrimonio_liquido` em intents fii_overview, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history cobrindo entidades fii_overview, fiis_financials_risk, fiis_financials_snapshot, fiis_yield_history
- `imprensa` em intents fii_overview, fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_rankings, fiis_yield_history cobrindo entidades fii_overview, fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_rankings, fiis_yield_history
- `ontem` em intents fiis_precos, fiis_rankings, history_b3_indexes cobrindo entidades fiis_precos, fiis_rankings, history_b3_indexes
- `hoje` em intents fiis_financials_revenue_schedule, fiis_noticias, fiis_precos, fiis_rankings, history_b3_indexes, macro_consolidada cobrindo entidades fiis_financials_revenue_schedule, fiis_noticias, fiis_precos, fiis_rankings, history_b3_indexes, macro_consolidada
- `minha carteira` em intents carteira_enriquecida, dividendos_yield, fiis_dividendos, fiis_noticias, fiis_rankings, fiis_yield_history, history_market_indicators cobrindo entidades carteira_enriquecida, dividendos_yield, fiis_dividendos, fiis_noticias, fiis_rankings, fiis_yield_history, history_market_indicators
- `minha carteira de fiis` em intents carteira_enriquecida, dividendos_yield, fiis_dividendos, fiis_rankings, fiis_yield_history cobrindo entidades carteira_enriquecida, dividendos_yield, fiis_dividendos, fiis_rankings, fiis_yield_history
- `oscilacao` em intents fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_yield_history cobrindo entidades fiis_dividendos, fiis_financials_snapshot, fiis_noticias, fiis_yield_history
- `comunicado` em intents fiis_dividendos, fiis_noticias, fiis_rankings, fiis_yield_history cobrindo entidades fiis_dividendos, fiis_noticias, fiis_rankings, fiis_yield_history
- `pagamento` em intents fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot cobrindo entidades fiis_dividendos, fiis_financials_risk, fiis_financials_snapshot
- `meus fiis` em intents carteira_enriquecida, dividendos_yield, fiis_dividendos, fiis_noticias, fiis_rankings, fiis_yield_history cobrindo entidades carteira_enriquecida, dividendos_yield, fiis_dividendos, fiis_noticias, fiis_rankings, fiis_yield_history
- `quanto pagou de dividendos` em intents dividendos_yield, fiis_dividendos, fiis_financials_revenue_schedule cobrindo entidades dividendos_yield, fiis_dividendos, fiis_financials_revenue_schedule
- `soma` em intents fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot cobrindo entidades fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot
- `indices` em intents fiis_financials_revenue_schedule, fiis_rankings, history_b3_indexes cobrindo entidades fiis_financials_revenue_schedule, fiis_rankings, history_b3_indexes
- `d-1` em intents fiis_financials_revenue_schedule, history_b3_indexes, history_market_indicators cobrindo entidades fiis_financials_revenue_schedule, history_b3_indexes, history_market_indicators
- `inpc` em intents fiis_financials_revenue_schedule, fiis_financials_risk, fiis_noticias, history_b3_indexes, history_market_indicators cobrindo entidades fiis_financials_revenue_schedule, fiis_financials_risk, fiis_noticias, history_b3_indexes, history_market_indicators
- `significado` em intents dividendos_yield, fiis_financials_risk, history_market_indicators, macro_consolidada cobrindo entidades dividendos_yield, fiis_financials_risk, history_market_indicators, macro_consolidada
- `cenario macro` em intents fiis_processos, history_currency_rates, history_market_indicators, macro_consolidada cobrindo entidades fiis_processos, history_currency_rates, history_market_indicators, macro_consolidada
- `panorama macro` em intents fiis_processos, history_market_indicators, macro_consolidada cobrindo entidades fiis_processos, history_market_indicators, macro_consolidada
- `do dia` em intents history_b3_indexes, history_market_indicators, macro_consolidada cobrindo entidades history_b3_indexes, history_market_indicators, macro_consolidada

## Policies / Narrator
- Modo conceitual suportado: sim
- Fallback quando rows == 0: não

## Quality assets
- Suites encontradas: 431 amostras de roteamento; 0 amostras RAG
- Amostras multi-ticker: routing=9, rag=0
- Amostras multi-intent: routing=0, rag=0

## Live results
- (API indisponível ou requests não instalado)
