# Ontology Lint Report
Gerado em: 2026-01-01T21:47:16.731506+00:00

## A) Acentuação
Nenhuma ocorrência encontrada.

## B) Duplicidade

### Duplicatas exatas
Nenhuma duplicata exata encontrada.

### Duplicatas normalizadas
Nenhuma duplicata normalizada encontrada.

## C) Conflitos include vs exclude
Nenhum conflito encontrado.

## D) Tokens include genéricos / suspeitos
Substituído pelo Collision Gate.

## E) Resumo Executivo
* Totais: A = 0, B = 0, C = 0, D = 0, F = 10

Top 20 tokens mais colidentes (normalize):
Token | # Intents
--- | ---
historico | 5
ifix | 5
carteira | 4
cdi | 4
comparativo | 4
distribuicao | 4
dividendos | 4
evolucao | 4
ibov | 4
ifil | 4
proventos | 4
comparacao | 3
comparar | 3
dy | 3
fechamento | 3
indice | 3
indices | 3
ipca | 3
meu | 3
minha | 3

## F) Collision Gate
Status: FAIL
Tipo | Campo | Token | #Intents | Max | Intents
--- | --- | --- | --- | --- | ---
forbidden_token | tokens.include | historico | 5 | 3 | client_fiis_dividends_evolution, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators
short_token | tokens.include | ev | 1 | 3 | fiis_financials_snapshot
short_token | tokens.include | pl | 1 | 3 | fiis_financials_snapshot
short_token | tokens.include | vp | 1 | 3 | fiis_financials_snapshot
too_many_intents | tokens.include | carteira | 4 | 3 | carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary
too_many_intents | tokens.include | comparativo | 4 | 3 | client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, dividendos_yield, macro_consolidada
too_many_intents | tokens.include | distribuicao | 4 | 3 | client_fiis_positions, fiis_dividendos, fiis_financials_revenue_schedule, fiis_processos
too_many_intents | tokens.include | dividendos | 4 | 3 | carteira_enriquecida, client_fiis_dividends_evolution, dividendos_yield, fiis_dividendos
too_many_intents | tokens.include | evolucao | 4 | 3 | client_fiis_dividends_evolution, fiis_yield_history, history_currency_rates, history_market_indicators
too_many_intents | tokens.include | proventos | 4 | 3 | carteira_enriquecida, client_fiis_dividends_evolution, dividendos_yield, fiis_dividendos

Top 20 tokens mais colidentes (informativo):
Token | # Intents
--- | ---
historico | 5
ifix | 5
carteira | 4
cdi | 4
comparativo | 4
distribuicao | 4
dividendos | 4
evolucao | 4
ibov | 4
ifil | 4
proventos | 4
comparacao | 3
comparar | 3
dy | 3
fechamento | 3
indice | 3
indices | 3
ipca | 3
meu | 3
minha | 3
