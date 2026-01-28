# Ask Suite Report

_Generated at: 2026-01-28 15:50:11 UTC_

## Summary

- Total: **236**
- Pass: **235**
- Fail: **0**
- Skip: **0**
- Error: **1**

## Metrics

- Accuracy (intent): **100.0%** (235 checked)
- Accuracy (entity): **100.0%** (235 checked)

### Latency (ms)

- p50: 335.6
- p95: 628.3
- avg: 371.5
- max: 2301.7

## Cases

| # | Question | Expected Intent | Expected Entity | Chosen Intent | Chosen Entity | Status | Latency (ms) |
|---:|---|---|---|---|---|---|---:|
| 1 | Evolução dos dividendos da minha carteira de FIIs | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 685.3 |
| 2 | Histórico de dividendos da minha carteira | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 380.6 |
| 3 | Minha renda mensal com FIIs está crescendo | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 434.5 |
| 4 | Quanto minha carteira de FIIs recebeu de dividendos em cada mês | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 302.1 |
| 5 | Renda mensal dos meus FIIs | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 293.5 |
| 6 | Me mostra a visão consolidada da minha carteira de FIIs. | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 503.8 |
| 7 | Quais FIIs da minha carteira aparecem no IFIX e qual a posição de cada um no índice? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 420.7 |
| 8 | Quais setores mais pesam na minha carteira de FIIs? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 335.8 |
| 9 | Quais são os FIIs da minha carteira e o valor investido em cada um? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 363.5 |
| 10 | Qual FII da minha carteira tem o melhor índice de Sharpe? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 309.3 |
| 11 | Qual FII da minha carteira tem o pior max drawdown? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 303.7 |
| 12 | Qual FII tem o maior peso na minha carteira hoje? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 465.4 |
| 13 | Qual é o DY de 12 meses da minha carteira de FIIs? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 467.7 |
| 14 | Qual é o DY mensal dos meus FIIs? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 334.8 |
| 15 | Qual é o peso de cada FII na minha carteira hoje? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 355.0 |
| 16 | Qual é o total de dividendos dos meus FIIs acumulado em 12 meses? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 283.3 |
| 17 | Quanto valem meus FIIs hoje no total? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 563.2 |
| 18 | Ranking dos meus FIIs por DY de 12 meses. | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 305.7 |
| 19 | Ranking dos meus FIIs por Sharpe. | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 333.9 |
| 20 | Como foi a performance da minha carteira de FIIs versus o IFIX nos últimos 12 meses | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 2301.7 |
| 21 | Comparar o retorno da minha carteira de FIIs com o IFIL | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 364.1 |
| 22 | Minha carteira de FIIs está melhor ou pior que o CDI | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 344.7 |
| 23 | Performance da minha carteira frente ao IBOV no último mês | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 450.9 |
| 24 | Qual foi a rentabilidade da minha carteira de FIIs versus o IFIX em 2024 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 410.0 |
| 25 | Resumo da performance da minha carteira de FIIs versus o IFIX | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 402.6 |
| 26 | Última leitura da carteira vs CDI | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 316.6 |
| 27 | Performance acumulada da carteira contra o IBOV (resumo) | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 339.9 |
| 28 | Visão resumida carteira de FIIs vs IFIL até hoje | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 273.9 |
| 29 | Excesso de retorno da carteira frente ao benchmark na última data | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 370.5 |
| 30 | Carteira vs IFIX no fechamento do período mais recente | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 255.7 |
| 31 | Resumo carteira vs CDI D-1 | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 384.2 |
| 32 | Performance da minha carteira contra IBOV até agora (visão resumida) | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 292.8 |
| 33 | distribuição da minha carteira de fiis por fundo | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 457.8 |
| 34 | Em qual corretora estão minhas cotas do XPML11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 347.7 |
| 35 | Minhas posições de FIIs | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 421.9 |
| 36 | Peso do HGLG11 na minha carteira de FIIs | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 486.4 |
| 37 | Qual meu preço médio do CPTS11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 358.2 |
| 38 | Quanto tenho de quantidade em custódia de MXRF11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 407.0 |
| 39 | Rentabilidade da minha posição em VISC11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 433.6 |
| 40 | Cenário macro atual: juros, inflação e câmbio estão favoráveis ou desfavoráveis para FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 363.0 |
| 41 | Como a alta do dólar influencia o cenário para FIIs de recebíveis e fundos em geral? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 239.6 |
| 42 | Como a combinação de Selic em queda e dólar volátil costuma impactar os fundos imobiliários? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 315.1 |
| 43 | Como a queda da Selic tende a impactar FIIs de tijolo? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 522.5 |
| 44 | Como está o cenário macro hoje para FIIs, considerando Selic, IPCA e câmbio? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 653.8 |
| 45 | Como juros altos costumam afetar fundos imobiliários? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 300.7 |
| 46 | Como um ambiente de juros altos e inflação controlada afeta fundos imobiliários? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 514.0 |
| 47 | Me dá um panorama macro consolidado (IPCA, Selic, CDI, IFIX e dólar) pensando em FIIs hoje. | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 364.4 |
| 48 | Me explica o cenário de juros e inflação no Brasil em 2025 e o impacto para FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 365.5 |
| 49 | O ambiente de juros e inflação em 2025 está mais favorável para FIIs de tijolo ou de papel? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 296.7 |
| 50 | O que significa IPCA alto para FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 353.0 |
| 51 | Qual é a importância do IPCA e da Selic para quem vive de renda com FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 320.9 |
| 52 | Qual é a relação entre Selic, CDI e o desempenho médio dos FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 367.1 |
| 53 | Qual é o impacto de um IPCA acelerando e Selic estável nos FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 385.5 |
| 54 | Dividendos do HGLG11 em cada mês do último ano | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 444.7 |
| 55 | Dividendos pagos pelo HGLG11 nos últimos 12 meses | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 311.3 |
| 56 | Dividendos que o KNRI11 pagou em janeiro de 2025 | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 495.4 |
| 57 | Lista de pagamentos de proventos do VINO11 | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 370.5 |
| 58 | Me mostra a distribuição de rendimentos do KNRI11 mês a mês | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 568.1 |
| 59 | Me mostra o histórico de dividendos do KNRI11 | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 451.5 |
| 60 | Proventos já anunciados do MXRF11 para os próximos meses | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 363.9 |
| 61 | Quais foram os dividendos do HGLG11 com data com em outubro de 2025? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 496.8 |
| 62 | Quais os dividendos do HGLG11 esse mês? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 242.8 |
| 63 | Quais os proventos mensais do HGLG11 em 2025? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 364.4 |
| 64 | Quais proventos o MXRF11 pagou em 2024? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 309.3 |
| 65 | Qual foi o último dividendo pago pelo HGLG11? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 270.8 |
| 66 | Qual é o próximo pagamento de dividendos do MXRF11? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 345.2 |
| 67 | Quanto o MXRF11 distribuiu de dividendos em março de 2025? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 384.3 |
| 68 | Total de dividendos do VISC11 nos últimos 6 meses | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 276.3 |
| 69 | Histórico de dividendos e dy do MXRF11 | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 285.7 |
| 70 | O que é dividend yield em FIIs | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 748.6 |
| 71 | Qual o DY de 12 meses do HGLG11 | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 243.5 |
| 72 | Quanto o CPTS11 pagou de dividendos e dy em 08/2023 | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 374.6 |
| 73 | Último dividendo pago pelo VISC11 e o dy correspondente | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 296.6 |
| 74 | As receitas do HGLG11 estão mais concentradas no curto prazo ou no longo prazo? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 233.7 |
| 75 | Como está distribuída a receita futura do HGLG11 por faixa de vencimento? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 321.5 |
| 76 | Compare o cronograma de receitas de HGLG11 e XPLG11. | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 407.9 |
| 77 | cronograma de receitas do LRDI11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 407.7 |
| 78 | percentual de receitas do BCFF11 indexadas ao INPC | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 347.5 |
| 79 | percentual de receitas do RBRF11 indexadas ao IGPM | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 381.7 |
| 80 | Qual a estrutura de recebíveis do HGLG11? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 301.8 |
| 81 | Qual percentual das receitas do HGLG11 tem vencimento acima de 36 meses? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 396.8 |
| 82 | receitas com vencimento acima de 36 meses do VISC11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 361.0 |
| 83 | receitas com vencimento em 6-9 meses do KNRI11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 302.7 |
| 84 | receitas com vencimento indeterminado do MXRF11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 342.8 |
| 85 | receitas indexadas ao IPCA do HGLG11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 347.0 |
| 86 | Beta do XPLG11 em relação ao IFIX | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 277.7 |
| 87 | Coeficiente de determinação do CPTS11 | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 286.7 |
| 88 | Max drawdown do MXRF11 | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 295.2 |
| 89 | Qual FII está mais volátil hoje | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 304.0 |
| 90 | Qual o Sharpe do HGLG11 | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 456.8 |
| 91 | Comparando ALMI11 e HGLG11, qual deles tem maior patrimônio líquido hoje? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 473.1 |
| 92 | Me traga um resumo financeiro do HGLG11: patrimônio, P/VP e alavancagem. | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 547.8 |
| 93 | O XPLG11 está alavancado? Qual o nível de alavancagem dele? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 624.9 |
| 94 | Quais são os principais indicadores financeiros do XPLG11 hoje (PL, VP/cota, vacância)? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 670.8 |
| 95 | Qual a ABL total do HGLG11 e qual a vacância física? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 371.5 |
| 96 | Qual a dívida líquida do ALMI11 no último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 656.2 |
| 97 | Qual a receita por cota do XPLG11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 379.4 |
| 98 | Qual a receita total do HGLG11 no último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 337.6 |
| 99 | Qual a vacância financeira do XPLG11 hoje? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 317.2 |
| 100 | Qual o P/VP atual do ALMI11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 354.7 |
| 101 | Qual o patrimônio líquido do HGLG11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 358.4 |
| 102 | Qual o payout e a reserva de dividendos do HGLG11 no último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 367.1 |
| 103 | Qual o valor patrimonial por cota do XPLG11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 377.2 |
| 104 | Quanto de caixa e dívida o HGLG11 tem hoje? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 293.3 |
| 105 | Quantos imóveis o ALMI11 tem no portfólio, segundo o último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 327.0 |
| 106 | Desde quando existem processos contra o ALMI11 e como está o andamento deles? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 292.2 |
| 107 | Existe algum processo judicial relevante contra o ALMI11 que possa afetar o fundo? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 256.2 |
| 108 | Me dá um resumo das ações judiciais envolvendo o ALMI11. | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 438.7 |
| 109 | O ALMI11 tem processos judiciais em aberto? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 239.7 |
| 110 | Quais processos existem contra o ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 330.2 |
| 111 | Quais são os principais fatos dos processos do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 311.1 |
| 112 | Quais são os processos do ALMI11 em 1ª instância? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 341.2 |
| 113 | Qual o risco de perda dos processos judiciais do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 289.2 |
| 114 | Qual o status das ações judiciais do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 338.2 |
| 115 | Qual o valor total das causas dos processos do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 262.1 |
| 116 | Quanto o ALMI11 pode perder se perder todas as ações judiciais? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 350.0 |
| 117 | Quantos processos judiciais o ALMI11 possui hoje? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 318.1 |
| 118 | Houve algum fato relevante envolvendo contratos ou locatários do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 471.4 |
| 119 | Me atualize com as notícias mais recentes sobre o setor logístico de FIIs. | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 300.5 |
| 120 | Mostre as últimas manchetes sobre FIIs em geral. | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 277.8 |
| 121 | O que saiu na mídia sobre o HGLG11 no último mês? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 297.9 |
| 122 | Quais foram as três últimas notícias publicadas sobre o HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 307.4 |
| 123 | Quais foram as últimas notícias do XPLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 317.4 |
| 124 | Quais matérias recentes destacaram o desempenho do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 331.3 |
| 125 | Quais notícias recentes existem sobre fundos imobiliários logísticos como HGLG11 e XPLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 949.0 |
| 126 | Quais são as últimas notícias do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 286.5 |
| 127 | Resuma as principais notícias do HGLG11 desta semana. | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 296.2 |
| 128 | Tem alguma notícia negativa recente sobre o HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 270.5 |
| 129 | Teve algum fato relevante recente do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 335.4 |
| 130 | Apresenta um overview detalhado do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 396.6 |
| 131 | Comparativo de overview entre HGLG11, MXRF11 e VISC11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 374.0 |
| 132 | Ficha resumo do fundo MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 286.8 |
| 133 | Ficha tecnica resumida do VISC11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 278.0 |
| 134 | Me mostre um panorama geral do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 325.0 |
| 135 | Panorama do fundo MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 269.7 |
| 136 | Principais pontos do fundo MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 303.0 |
| 137 | Quais os destaques do VISC11 hoje? | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 447.8 |
| 138 | Quero um resumo completo do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 672.1 |
| 139 | Resumo dos principais indicadores de HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 582.4 |
| 140 | Resumo geral do MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 505.1 |
| 141 | Visao geral do VISC11 como investimento. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 261.2 |
| 142 | Como está o KNRI11 e o XPLG11 hoje? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 330.5 |
| 143 | Como está o preço do VINO agora? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 301.2 |
| 144 | Me mostra o preço do VINO11 agora | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 333.1 |
| 145 | Máxima e mínima do MXRF11 em 27/10/2025 | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 279.6 |
| 146 | Mínima do HGLG11 no dia 27/10/2025 | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 365.2 |
| 147 | O HGLG11 subiu ou caiu hoje? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 383.9 |
| 148 | Preço de fechamento de ontem do KNRI11 | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 323.3 |
| 149 | Qual a cotação atual do KNRI11? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 269.7 |
| 150 | Qual foi a cotação de ontem do VISC11? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 254.4 |
| 151 | Qual foi a máxima do HGLG11 em 27/10/2025? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 433.6 |
| 152 | Qual foi o último preço negociado de XPLG11? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 578.1 |
| 153 | Quanto está o HGLG11 hoje? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 282.7 |
| 154 | Quanto fechou o HGLG11 ontem? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 330.6 |
| 155 | Quanto o KNRI11 variou hoje em porcentagem? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 265.9 |
| 156 | como está a posição do HGLG11 no ranking da SIRIOS? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 333.8 |
| 157 | como evoluiu a posição do HGRU11 no ranking de usuários ao longo do tempo? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 329.0 |
| 158 | como foi a variação de posição do HGLG11 no ranking da SIRIOS neste ano? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 370.5 |
| 159 | quais fiis se destacam no ranking da SIRIOS este mês? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 377.0 |
| 160 | quais fiis têm melhor posição no ranking de dy 12 meses? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 340.1 |
| 161 | quais fiis têm o maior dividend yield em 12 meses? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 219.6 |
| 162 | quais fiis têm o maior patrimônio líquido? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 281.0 |
| 163 | quais fiis têm o maior valor de mercado? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 343.8 |
| 164 | quais fiis têm o menor drawdown histórico? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 348.4 |
| 165 | qual a posição atual do HGLG11 no ranking de usuários? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 249.5 |
| 166 | qual é hoje a posição do HGRU11 no ranking do IFIL? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 320.4 |
| 167 | ranking dos fiis com melhor sharpe ratio | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 255.2 |
| 168 | top 5 fiis por sharpe ratio | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 299.1 |
| 169 | top fiis por menor volatilidade | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 314.3 |
| 170 | Quais ativos do MXRF11 estão inadimplentes | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 351.7 |
| 171 | Quais endereços fazem parte do VISC11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 311.9 |
| 172 | Quais imóveis compõem o HGLG11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 244.1 |
| 173 | Qual o tamanho em metros quadrados dos imóveis do KNRI11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 370.4 |
| 174 | Vacância dos ativos do XPML11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 299.1 |
| 175 | o FPAB11 já fez parte do IFIX? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 374.9 |
| 176 | O HGLG11 é um fundo de gestão ativa ou passiva? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 302.3 |
| 177 | peso do MCCI11 no IFIX | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 530.4 |
| 178 | Qual foi a data do IPO do ALMI11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 387.7 |
| 179 | Qual o CNPJ do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 302.8 |
| 180 | Qual é a classificação oficial do XPLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 513.8 |
| 181 | Qual é o administrador e o CNPJ do administrador do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 818.4 |
| 182 | Qual é o código ISIN do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 410.1 |
| 183 | Qual é o nome de exibição do fundo ALMI11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 304.6 |
| 184 | Qual é o nome de pregão do HGLG11 na B3? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 314.9 |
| 185 | Qual é o peso do HGLG11 no IFIX e no IFIL? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 307.4 |
| 186 | Qual é o público-alvo do XPLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 340.2 |
| 187 | Qual é o setor e o subsetor do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 318.0 |
| 188 | Qual é o site oficial do fundo XPLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 309.9 |
| 189 | Quantas cotas emitidas e quantos cotistas o HGLG11 possui? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 420.3 |
| 190 | Como foi o dy mensal do HGLG11 nos ultimos 12 meses? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 268.9 |
| 191 | Como o dy mensal do VISC11 se comportou nos ultimos 24 meses? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 331.7 |
| 192 | DY de janeiro de 2024 do VISC11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 220.7 |
| 193 | DY por mes do HGLG11 em 2023. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 281.3 |
| 194 | Evolucao do dy do VISC11 desde 2023. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 348.4 |
| 195 | Grafico com o dy mensal do MXRF11 nos ultimos 2 anos. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 330.1 |
| 196 | Historico completo de dy do MXRF11 ao longo dos ultimos anos. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 337.4 |
| 197 | Historico de dividend yield do VISC11 nos ultimos 18 meses. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 329.2 |
| 198 | Me mostra o historico de dividend yield do MXRF11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 292.2 |
| 199 | Mostra o dy 12m mes a mes do HGLG11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 313.4 |
| 200 | Qual foi o dividend yield do MXRF11 em outubro de 2024? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 344.6 |
| 201 | Qual foi o dy do MXRF11 nos ultimos 24 meses? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 358.1 |
| 202 | Qual o DY historico do HGLG11? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 394.6 |
| 203 | Quero ver o dy por mes do VISC11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 276.2 |
| 204 | Serie historica de dy do HGLG11 por mes. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 344.9 |
| 205 | Como o IFIX se comportou nos últimos 10 pregões? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 433.1 |
| 206 | Fechamento de ontem do Ibovespa em pontos e porcentagem | history_b3_indexes | history_b3_indexes | ticker_query | fiis_quota_prices | ERROR | 199.2 |
| 207 | Histórico do IBOV nos últimos 5 dias úteis | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 222.1 |
| 208 | Histórico recente do IFIX (D-1) | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 270.2 |
| 209 | Ibovespa hoje (D-1) | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 300.6 |
| 210 | Pontos do IBOV em D-1 | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 298.5 |
| 211 | Pontos do IFIX de ontem | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 638.6 |
| 212 | Qual foi a variação diária do IFIX em março de 2025? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 538.1 |
| 213 | Qual foi a variação do IFIX ontem? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 345.4 |
| 214 | Quanto o IFIL subiu ou caiu ontem? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 240.8 |
| 215 | Quanto variou o IFIL no dia? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 283.4 |
| 216 | Resumo das últimas variações do IFIX e do IFIL | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 377.4 |
| 217 | Série histórica do IFIL nos últimos 30 dias | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 348.5 |
| 218 | Variação diária do IBOV | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 331.0 |
| 219 | Variação do IFIX no fechamento de hoje (D-1) | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 244.7 |
| 220 | Cotação do dólar hoje | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 355.6 |
| 221 | Cotação do euro D-1 | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 304.9 |
| 222 | Qual foi a última cotação do euro | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 312.3 |
| 223 | Quanto está o dólar para compra e venda | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 668.4 |
| 224 | Variação percentual do dólar ontem | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 399.3 |
| 225 | CDI d-1 | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 371.4 |
| 226 | IPCA do dia | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 763.9 |
| 227 | Qual a SELIC hoje | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 296.8 |
| 228 | Qual o IGPM atual | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 306.1 |
| 229 | Taxa do INCC hoje | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 308.9 |
| 230 | última atualização do ipca | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 301.4 |
| 231 | Qual foi o fechamento do IBOV ontem? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 300.1 |
| 232 | Quanto está o IFIX hoje? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 270.6 |
| 233 | Como está o dólar hoje? | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 271.7 |
| 234 | Variação do CDI este mês | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 367.3 |
| 235 | Mostre um overview do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 293.0 |
| 236 | Qual é o DY do HGLG11? | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 290.2 |

## Details (failures/errors)

### Case 206 (ERROR)

- Question: Fechamento de ontem do Ibovespa em pontos e porcentagem
- Expected intent: history_b3_indexes
- Expected entity: history_b3_indexes
- Chosen intent: ticker_query
- Chosen entity: fiis_quota_prices
- Match intent: False
- Match entity: False
- HTTP status: 200
- Error: status_not_ok
