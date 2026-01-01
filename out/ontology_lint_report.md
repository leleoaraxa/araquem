# Ontology Lint Report
Gerado em: 2026-01-01T21:14:10.406745+00:00

## A) Acentuação
Nenhuma ocorrência encontrada.

## B) Duplicidade

### Duplicatas exatas
Nenhuma duplicata exata encontrada.

### Duplicatas normalizadas
Nenhuma duplicata normalizada encontrada.

## C) Conflitos include vs exclude
Intent | Campo | Valor
--- | --- | ---
dividendos_yield | phrases | dy 12m
fiis_financials_snapshot | phrases | quantos cotistas tem o <ticker>

## D) Tokens include genéricos / suspeitos
Intent | Token | Critérios
--- | --- | ---
client_fiis_dividends_evolution | historico | alta colisão (6 intents)
client_fiis_dividends_evolution | mensal | stoplist temporal
client_fiis_dividends_evolution | mes | stoplist temporal
client_fiis_dividends_evolution | meses | stoplist temporal
client_fiis_performance_vs_benchmark | ano | stoplist temporal
client_fiis_performance_vs_benchmark | anual | stoplist temporal
client_fiis_performance_vs_benchmark | mensal | stoplist temporal
client_fiis_performance_vs_benchmark | mes | stoplist temporal
client_fiis_performance_vs_benchmark | meses | stoplist temporal
client_fiis_performance_vs_benchmark_summary | ultima | stoplist temporal
client_fiis_performance_vs_benchmark_summary | ultimo | stoplist temporal
client_fiis_positions | atual | stoplist temporal
fiis_dividendos | historico | alta colisão (6 intents)
fiis_dividendos | mensal | stoplist temporal
fiis_dividendos | mes | stoplist temporal
fiis_financials_snapshot | ev | comprimento <= 2
fiis_financials_snapshot | pl | comprimento <= 2
fiis_financials_snapshot | vp | comprimento <= 2
fiis_noticias | hoje | stoplist temporal
fiis_noticias | mes | stoplist temporal
fiis_noticias | semana | stoplist temporal
fiis_noticias | ultimo | stoplist temporal
fiis_precos | hoje | stoplist temporal
fiis_precos | ontem | stoplist temporal
fiis_processos | re | comprimento <= 2
fiis_yield_history | historico | alta colisão (6 intents)
fiis_yield_history | mensal | stoplist temporal
fiis_yield_history | meses | stoplist temporal
history_b3_indexes | historico | alta colisão (6 intents)
history_b3_indexes | hoje | stoplist temporal
history_b3_indexes | ontem | stoplist temporal
history_currency_rates | historico | alta colisão (6 intents)
history_market_indicators | atual | stoplist temporal
history_market_indicators | historico | alta colisão (6 intents)

## E) Resumo Executivo
* Totais: A = 0, B = 0, C = 2, D = 34

Top 20 tokens mais colidentes (normalize):
Token | # Intents
--- | ---
historico | 6
ifix | 5
carteira | 4
cdi | 4
comparativo | 4
distribuicao | 4
dividendos | 4
evolucao | 4
ibov | 4
ifil | 4
mensal | 4
mes | 4
proventos | 4
comparacao | 3
comparar | 3
dy | 3
fechamento | 3
hoje | 3
indice | 3
indices | 3
