# Ask Suite Report

_Generated at: 2026-01-28 15:16:54 UTC_

## Summary

- Total: **237**
- Pass: **233**
- Fail: **3**
- Skip: **0**
- Error: **1**

## Metrics

- Accuracy (intent): **98.7%** (236 checked)
- Accuracy (entity): **98.7%** (236 checked)

### Latency (ms)

- p50: 344.1
- p95: 566.2
- avg: 380.9
- max: 1652.4

## Cases

| # | Question | Expected Intent | Expected Entity | Chosen Intent | Chosen Entity | Status | Latency (ms) |
|---:|---|---|---|---|---|---|---:|
| 1 | Evolução dos dividendos da minha carteira de FIIs | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 723.4 |
| 2 | Histórico de dividendos da minha carteira | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 316.2 |
| 3 | Minha renda mensal com FIIs está crescendo | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 465.8 |
| 4 | Quanto minha carteira de FIIs recebeu de dividendos em cada mês | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 297.7 |
| 5 | Renda mensal dos meus FIIs | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | client_fiis_dividends_evolution | PASS | 362.6 |
| 6 | Me mostra a visão consolidada da minha carteira de FIIs. | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 529.8 |
| 7 | Quais FIIs da minha carteira aparecem no IFIX e qual a posição de cada um no índice? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 250.4 |
| 8 | Quais setores mais pesam na minha carteira de FIIs? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 348.1 |
| 9 | Quais são os FIIs da minha carteira e o valor investido em cada um? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 344.0 |
| 10 | Qual FII da minha carteira tem o melhor índice de Sharpe? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 268.6 |
| 11 | Qual FII da minha carteira tem o pior max drawdown? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 370.9 |
| 12 | Qual FII tem o maior peso na minha carteira hoje? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 298.7 |
| 13 | Qual é o DY de 12 meses da minha carteira de FIIs? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 274.6 |
| 14 | Qual é o DY mensal dos meus FIIs? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 300.8 |
| 15 | Qual é o peso de cada FII na minha carteira hoje? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 384.7 |
| 16 | Qual é o total de dividendos dos meus FIIs acumulado em 12 meses? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 275.2 |
| 17 | Quanto valem meus FIIs hoje no total? | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 467.1 |
| 18 | Ranking dos meus FIIs por DY de 12 meses. | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 622.3 |
| 19 | Ranking dos meus FIIs por Sharpe. | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | client_fiis_enriched_portfolio | PASS | 267.9 |
| 20 | Como foi a performance da minha carteira de FIIs versus o IFIX nos últimos 12 meses | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 1652.4 |
| 21 | Comparar o retorno da minha carteira de FIIs com o IFIL | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 292.6 |
| 22 | Minha carteira de FIIs está melhor ou pior que o CDI | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 317.9 |
| 23 | Performance da minha carteira frente ao IBOV no último mês | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 277.1 |
| 24 | Qual foi a rentabilidade da minha carteira de FIIs versus o IFIX em 2024 | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | client_fiis_performance_vs_benchmark | PASS | 279.0 |
| 25 | Resumo da performance da minha carteira de FIIs versus o IFIX | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 497.5 |
| 26 | Última leitura da carteira vs CDI | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 284.9 |
| 27 | Performance acumulada da carteira contra o IBOV (resumo) | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 270.9 |
| 28 | Visão resumida carteira de FIIs vs IFIL até hoje | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 256.5 |
| 29 | Excesso de retorno da carteira frente ao benchmark na última data | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 343.6 |
| 30 | Carteira vs IFIX no fechamento do período mais recente | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 319.8 |
| 31 | Resumo carteira vs CDI D-1 | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 359.7 |
| 32 | Performance da minha carteira contra IBOV até agora (visão resumida) | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | client_fiis_performance_vs_benchmark_summary | PASS | 373.8 |
| 33 | distribuição da minha carteira de fiis por fundo | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 411.5 |
| 34 | Em qual corretora estão minhas cotas do XPML11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 352.3 |
| 35 | Minhas posições de FIIs | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 287.4 |
| 36 | Peso do HGLG11 na minha carteira de FIIs | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 415.2 |
| 37 | Qual meu preço médio do CPTS11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 387.6 |
| 38 | Quanto tenho de quantidade em custódia de MXRF11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 379.0 |
| 39 | Rentabilidade da minha posição em VISC11 | client_fiis_positions | client_fiis_positions | client_fiis_positions | client_fiis_positions | PASS | 520.9 |
| 40 | Cenário macro atual: juros, inflação e câmbio estão favoráveis ou desfavoráveis para FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 385.2 |
| 41 | Como a alta do dólar influencia o cenário para FIIs de recebíveis e fundos em geral? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 312.1 |
| 42 | Como a combinação de Selic em queda e dólar volátil costuma impactar os fundos imobiliários? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 724.7 |
| 43 | Como a curva de juros projetada pode afetar o preço dos FIIs nos próximos anos? | consolidated_macroeconomic | consolidated_macroeconomic | fiis_quota_prices | fiis_quota_prices | FAIL | 327.7 |
| 44 | Como a queda da Selic tende a impactar FIIs de tijolo? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 267.0 |
| 45 | Como está o cenário macro hoje para FIIs, considerando Selic, IPCA e câmbio? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 333.1 |
| 46 | Como juros altos costumam afetar fundos imobiliários? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 315.6 |
| 47 | Como um ambiente de juros altos e inflação controlada afeta fundos imobiliários? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 319.4 |
| 48 | Me dá um panorama macro consolidado (IPCA, Selic, CDI, IFIX e dólar) pensando em FIIs hoje. | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 394.6 |
| 49 | Me explica o cenário de juros e inflação no Brasil em 2025 e o impacto para FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 329.7 |
| 50 | O ambiente de juros e inflação em 2025 está mais favorável para FIIs de tijolo ou de papel? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 293.6 |
| 51 | O que significa IPCA alto para FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 341.8 |
| 52 | Qual é a importância do IPCA e da Selic para quem vive de renda com FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 439.4 |
| 53 | Qual é a relação entre Selic, CDI e o desempenho médio dos FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 263.9 |
| 54 | Qual é o impacto de um IPCA acelerando e Selic estável nos FIIs? | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | consolidated_macroeconomic | PASS | 284.5 |
| 55 | Dividendos do HGLG11 em cada mês do último ano | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 324.4 |
| 56 | Dividendos pagos pelo HGLG11 nos últimos 12 meses | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 343.2 |
| 57 | Dividendos que o KNRI11 pagou em janeiro de 2025 | fiis_dividends | fiis_dividends | fiis_dividends_yields | fiis_dividends_yields | FAIL | 344.1 |
| 58 | Lista de pagamentos de proventos do VINO11 | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 569.3 |
| 59 | Me mostra a distribuição de rendimentos do KNRI11 mês a mês | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 463.5 |
| 60 | Me mostra o histórico de dividendos do KNRI11 | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 224.5 |
| 61 | Proventos já anunciados do MXRF11 para os próximos meses | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 334.2 |
| 62 | Quais foram os dividendos do HGLG11 com data com em outubro de 2025? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 387.9 |
| 63 | Quais os dividendos do HGLG11 esse mês? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 299.1 |
| 64 | Quais os proventos mensais do HGLG11 em 2025? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 226.7 |
| 65 | Quais proventos o MXRF11 pagou em 2024? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 289.9 |
| 66 | Qual foi o último dividendo pago pelo HGLG11? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 444.9 |
| 67 | Qual é o próximo pagamento de dividendos do MXRF11? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 242.3 |
| 68 | Quanto o MXRF11 distribuiu de dividendos em março de 2025? | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 312.3 |
| 69 | Total de dividendos do VISC11 nos últimos 6 meses | fiis_dividends | fiis_dividends | fiis_dividends | fiis_dividends | PASS | 300.6 |
| 70 | Histórico de dividendos e dy do MXRF11 | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 448.5 |
| 71 | O que é dividend yield em FIIs | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 650.1 |
| 72 | Qual o DY de 12 meses do HGLG11 | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 326.6 |
| 73 | Quanto o CPTS11 pagou de dividendos e dy em 08/2023 | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 701.7 |
| 74 | Último dividendo pago pelo VISC11 e o dy correspondente | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 426.6 |
| 75 | As receitas do HGLG11 estão mais concentradas no curto prazo ou no longo prazo? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 475.9 |
| 76 | Como está distribuída a receita futura do HGLG11 por faixa de vencimento? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 341.4 |
| 77 | Compare o cronograma de receitas de HGLG11 e XPLG11. | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 407.9 |
| 78 | cronograma de receitas do LRDI11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 368.3 |
| 79 | percentual de receitas do BCFF11 indexadas ao INPC | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 350.5 |
| 80 | percentual de receitas do RBRF11 indexadas ao IGPM | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 321.5 |
| 81 | Qual a estrutura de recebíveis do HGLG11? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 318.3 |
| 82 | Qual percentual das receitas do HGLG11 tem vencimento acima de 36 meses? | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 342.4 |
| 83 | receitas com vencimento acima de 36 meses do VISC11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 403.1 |
| 84 | receitas com vencimento em 6-9 meses do KNRI11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 497.8 |
| 85 | receitas com vencimento indeterminado do MXRF11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 415.3 |
| 86 | receitas indexadas ao IPCA do HGLG11 | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | PASS | 277.1 |
| 87 | Beta do XPLG11 em relação ao IFIX | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 494.3 |
| 88 | Coeficiente de determinação do CPTS11 | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 320.5 |
| 89 | Max drawdown do MXRF11 | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 391.0 |
| 90 | Qual FII está mais volátil hoje | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 356.0 |
| 91 | Qual o Sharpe do HGLG11 | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | fiis_financials_risk | PASS | 370.1 |
| 92 | Comparando ALMI11 e HGLG11, qual deles tem maior patrimônio líquido hoje? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 495.1 |
| 93 | Me traga um resumo financeiro do HGLG11: patrimônio, P/VP e alavancagem. | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 385.1 |
| 94 | O XPLG11 está alavancado? Qual o nível de alavancagem dele? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 434.8 |
| 95 | Quais são os principais indicadores financeiros do XPLG11 hoje (PL, VP/cota, vacância)? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 610.8 |
| 96 | Qual a ABL total do HGLG11 e qual a vacância física? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 303.7 |
| 97 | Qual a dívida líquida do ALMI11 no último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 452.5 |
| 98 | Qual a receita por cota do XPLG11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 353.8 |
| 99 | Qual a receita total do HGLG11 no último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 346.2 |
| 100 | Qual a vacância financeira do XPLG11 hoje? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 299.0 |
| 101 | Qual o P/VP atual do ALMI11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 440.5 |
| 102 | Qual o patrimônio líquido do HGLG11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 354.8 |
| 103 | Qual o payout e a reserva de dividendos do HGLG11 no último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 302.5 |
| 104 | Qual o valor patrimonial por cota do XPLG11? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 256.8 |
| 105 | Quanto de caixa e dívida o HGLG11 tem hoje? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 318.2 |
| 106 | Quantos imóveis o ALMI11 tem no portfólio, segundo o último relatório gerencial? | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | fiis_financials_snapshot | PASS | 277.0 |
| 107 | Desde quando existem processos contra o ALMI11 e como está o andamento deles? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 519.7 |
| 108 | Existe algum processo relevante contra o ALMI11 que possa afetar o fundo? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_news | fiis_news | FAIL | 386.3 |
| 109 | Me dá um resumo das ações judiciais envolvendo o ALMI11. | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 369.8 |
| 110 | O ALMI11 tem processos judiciais em aberto? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 274.6 |
| 111 | Quais processos existem contra o ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 496.1 |
| 112 | Quais são os principais fatos dos processos do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 330.6 |
| 113 | Quais são os processos do ALMI11 em 1ª instância? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 386.3 |
| 114 | Qual o risco de perda dos processos judiciais do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 299.9 |
| 115 | Qual o status das ações judiciais do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 309.9 |
| 116 | Qual o valor total das causas dos processos do ALMI11? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 313.4 |
| 117 | Quanto o ALMI11 pode perder se perder todas as ações judiciais? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 339.5 |
| 118 | Quantos processos judiciais o ALMI11 possui hoje? | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | fiis_legal_proceedings | PASS | 339.8 |
| 119 | Houve algum fato relevante envolvendo contratos ou locatários do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 512.1 |
| 120 | Me atualize com as notícias mais recentes sobre o setor logístico de FIIs. | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 376.0 |
| 121 | Mostre as últimas manchetes sobre FIIs em geral. | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 346.6 |
| 122 | O que saiu na mídia sobre o HGLG11 no último mês? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 630.5 |
| 123 | Quais foram as três últimas notícias publicadas sobre o HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 376.8 |
| 124 | Quais foram as últimas notícias do XPLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 426.6 |
| 125 | Quais matérias recentes destacaram o desempenho do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 316.0 |
| 126 | Quais notícias recentes existem sobre fundos imobiliários logísticos como HGLG11 e XPLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 521.1 |
| 127 | Quais são as últimas notícias do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 326.0 |
| 128 | Resuma as principais notícias do HGLG11 desta semana. | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 321.7 |
| 129 | Tem alguma notícia negativa recente sobre o HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 310.0 |
| 130 | Teve algum fato relevante recente do HGLG11? | fiis_news | fiis_news | fiis_news | fiis_news | PASS | 270.5 |
| 131 | Apresenta um overview detalhado do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 293.0 |
| 132 | Comparativo de overview entre HGLG11, MXRF11 e VISC11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 547.2 |
| 133 | Ficha resumo do fundo MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 386.7 |
| 134 | Ficha tecnica resumida do VISC11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 413.0 |
| 135 | Me mostre um panorama geral do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 370.3 |
| 136 | Panorama do fundo MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 296.5 |
| 137 | Principais pontos do fundo MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 288.7 |
| 138 | Quais os destaques do VISC11 hoje? | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 306.7 |
| 139 | Quero um resumo completo do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 310.9 |
| 140 | Resumo dos principais indicadores de HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 292.8 |
| 141 | Resumo geral do MXRF11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 263.1 |
| 142 | Visao geral do VISC11 como investimento. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 263.7 |
| 143 | Como está o KNRI11 e o XPLG11 hoje? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 411.4 |
| 144 | Como está o preço do VINO agora? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 341.4 |
| 145 | Me mostra o preço do VINO11 agora | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 236.9 |
| 146 | Máxima e mínima do MXRF11 em 27/10/2025 | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 315.0 |
| 147 | Mínima do HGLG11 no dia 27/10/2025 | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 435.1 |
| 148 | O HGLG11 subiu ou caiu hoje? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 370.2 |
| 149 | Preço de fechamento de ontem do KNRI11 | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 397.4 |
| 150 | Qual a cotação atual do KNRI11? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 684.7 |
| 151 | Qual foi a cotação de ontem do VISC11? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 405.2 |
| 152 | Qual foi a máxima do HGLG11 em 27/10/2025? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 447.2 |
| 153 | Qual foi o último preço negociado de XPLG11? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 413.6 |
| 154 | Quanto está o HGLG11 hoje? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 294.6 |
| 155 | Quanto fechou o HGLG11 ontem? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 401.8 |
| 156 | Quanto o KNRI11 variou hoje em porcentagem? | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | fiis_quota_prices | PASS | 370.2 |
| 157 | como está a posição do HGLG11 no ranking da SIRIOS? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 438.0 |
| 158 | como evoluiu a posição do HGRU11 no ranking de usuários ao longo do tempo? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 459.0 |
| 159 | como foi a variação de posição do HGLG11 no ranking da SIRIOS neste ano? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 330.4 |
| 160 | quais fiis se destacam no ranking da SIRIOS este mês? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 302.8 |
| 161 | quais fiis têm melhor posição no ranking de dy 12 meses? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 427.5 |
| 162 | quais fiis têm o maior dividend yield em 12 meses? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 315.6 |
| 163 | quais fiis têm o maior patrimônio líquido? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 296.6 |
| 164 | quais fiis têm o maior valor de mercado? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 478.5 |
| 165 | quais fiis têm o menor drawdown histórico? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 304.0 |
| 166 | qual a posição atual do HGLG11 no ranking de usuários? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 439.5 |
| 167 | qual é hoje a posição do HGRU11 no ranking do IFIL? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 398.7 |
| 168 | ranking dos fiis com melhor sharpe ratio | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 434.4 |
| 169 | top 5 fiis por sharpe ratio | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 292.2 |
| 170 | top fiis por menor volatilidade | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 289.7 |
| 171 | Quais ativos do MXRF11 estão inadimplentes | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 479.0 |
| 172 | Quais endereços fazem parte do VISC11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 430.0 |
| 173 | Quais imóveis compõem o HGLG11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 387.6 |
| 174 | Qual o tamanho em metros quadrados dos imóveis do KNRI11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 443.4 |
| 175 | Vacância dos ativos do XPML11 | fiis_real_estate | fiis_real_estate | fiis_real_estate | fiis_real_estate | PASS | 691.2 |
| 176 | o FPAB11 já fez parte do IFIX? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 440.3 |
| 177 | O HGLG11 é um fundo de gestão ativa ou passiva? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 421.9 |
| 178 | peso do MCCI11 no IFIX | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 431.7 |
| 179 | Qual foi a data do IPO do ALMI11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 387.0 |
| 180 | Qual o CNPJ do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 320.4 |
| 181 | Qual é a classificação oficial do XPLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 412.5 |
| 182 | Qual é o administrador e o CNPJ do administrador do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 325.7 |
| 183 | Qual é o código ISIN do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 294.7 |
| 184 | Qual é o nome de exibição do fundo ALMI11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 283.1 |
| 185 | Qual é o nome de pregão do HGLG11 na B3? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 344.4 |
| 186 | Qual é o peso do HGLG11 no IFIX e no IFIL? | fiis_rankings | fiis_rankings | fiis_rankings | fiis_rankings | PASS | 428.4 |
| 187 | Qual é o público-alvo do XPLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 319.9 |
| 188 | Qual é o setor e o subsetor do HGLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 305.3 |
| 189 | Qual é o site oficial do fundo XPLG11? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 307.2 |
| 190 | Quantas cotas emitidas e quantos cotistas o HGLG11 possui? | fiis_registrations | fiis_registrations | fiis_registrations | fiis_registrations | PASS | 350.6 |
| 191 | Como foi o dy mensal do HGLG11 nos ultimos 12 meses? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 433.9 |
| 192 | Como o dy mensal do VISC11 se comportou nos ultimos 24 meses? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 549.4 |
| 193 | DY de janeiro de 2024 do VISC11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 437.9 |
| 194 | DY por mes do HGLG11 em 2023. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 325.6 |
| 195 | Evolucao do dy do VISC11 desde 2023. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 317.1 |
| 196 | Grafico com o dy mensal do MXRF11 nos ultimos 2 anos. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 512.7 |
| 197 | Historico completo de dy do MXRF11 ao longo dos ultimos anos. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 523.5 |
| 198 | Historico de dividend yield do VISC11 nos ultimos 18 meses. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 404.5 |
| 199 | Me mostra o historico de dividend yield do MXRF11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 297.4 |
| 200 | Mostra o dy 12m mes a mes do HGLG11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 338.7 |
| 201 | Qual foi o dividend yield do MXRF11 em outubro de 2024? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 542.3 |
| 202 | Qual foi o dy do MXRF11 nos ultimos 24 meses? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 275.1 |
| 203 | Qual o DY historico do HGLG11? | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 307.0 |
| 204 | Quero ver o dy por mes do VISC11. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 297.8 |
| 205 | Serie historica de dy do HGLG11 por mes. | fiis_yield_history | fiis_yield_history | fiis_yield_history | fiis_yield_history | PASS | 327.9 |
| 206 | Como o IFIX se comportou nos últimos 10 pregões? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 558.5 |
| 207 | Fechamento de ontem do Ibovespa em pontos e porcentagem | history_b3_indexes | history_b3_indexes | ticker_query | fiis_quota_prices | ERROR | 237.6 |
| 208 | Histórico do IBOV nos últimos 5 dias úteis | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 565.4 |
| 209 | Histórico recente do IFIX (D-1) | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 307.8 |
| 210 | Ibovespa hoje (D-1) | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 437.9 |
| 211 | Pontos do IBOV em D-1 | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 268.6 |
| 212 | Pontos do IFIX de ontem | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 487.7 |
| 213 | Qual foi a variação diária do IFIX em março de 2025? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 314.7 |
| 214 | Qual foi a variação do IFIX ontem? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 300.4 |
| 215 | Quanto o IFIL subiu ou caiu ontem? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 305.6 |
| 216 | Quanto variou o IFIL no dia? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 280.3 |
| 217 | Resumo das últimas variações do IFIX e do IFIL | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 324.7 |
| 218 | Série histórica do IFIL nos últimos 30 dias | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 306.2 |
| 219 | Variação diária do IBOV | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 272.9 |
| 220 | Variação do IFIX no fechamento de hoje (D-1) | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 382.9 |
| 221 | Cotação do dólar hoje | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 519.3 |
| 222 | Cotação do euro D-1 | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 549.1 |
| 223 | Qual foi a última cotação do euro | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 319.5 |
| 224 | Quanto está o dólar para compra e venda | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 532.8 |
| 225 | Variação percentual do dólar ontem | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 492.8 |
| 226 | CDI d-1 | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 683.7 |
| 227 | IPCA do dia | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 359.1 |
| 228 | Qual a SELIC hoje | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 485.7 |
| 229 | Qual o IGPM atual | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 347.1 |
| 230 | Taxa do INCC hoje | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 319.0 |
| 231 | última atualização do ipca | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 302.3 |
| 232 | Qual foi o fechamento do IBOV ontem? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 313.6 |
| 233 | Quanto está o IFIX hoje? | history_b3_indexes | history_b3_indexes | history_b3_indexes | history_b3_indexes | PASS | 350.0 |
| 234 | Como está o dólar hoje? | history_currency_rates | history_currency_rates | history_currency_rates | history_currency_rates | PASS | 326.0 |
| 235 | Variação do CDI este mês | history_market_indicators | history_market_indicators | history_market_indicators | history_market_indicators | PASS | 301.4 |
| 236 | Mostre um overview do HGLG11. | fiis_overview | fiis_overview | fiis_overview | fiis_overview | PASS | 310.9 |
| 237 | Qual é o DY do HGLG11? | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | fiis_dividends_yields | PASS | 325.3 |

## Details (failures/errors)

### Case 43 (FAIL)

- Question: Como a curva de juros projetada pode afetar o preço dos FIIs nos próximos anos?
- Expected intent: consolidated_macroeconomic
- Expected entity: consolidated_macroeconomic
- Chosen intent: fiis_quota_prices
- Chosen entity: fiis_quota_prices
- Match intent: False
- Match entity: False
- HTTP status: 200
- Error: -

### Case 57 (FAIL)

- Question: Dividendos que o KNRI11 pagou em janeiro de 2025
- Expected intent: fiis_dividends
- Expected entity: fiis_dividends
- Chosen intent: fiis_dividends_yields
- Chosen entity: fiis_dividends_yields
- Match intent: False
- Match entity: False
- HTTP status: 200
- Error: -

### Case 108 (FAIL)

- Question: Existe algum processo relevante contra o ALMI11 que possa afetar o fundo?
- Expected intent: fiis_legal_proceedings
- Expected entity: fiis_legal_proceedings
- Chosen intent: fiis_news
- Chosen entity: fiis_news
- Match intent: False
- Match entity: False
- HTTP status: 200
- Error: -

### Case 207 (ERROR)

- Question: Fechamento de ontem do Ibovespa em pontos e porcentagem
- Expected intent: history_b3_indexes
- Expected entity: history_b3_indexes
- Chosen intent: ticker_query
- Chosen entity: fiis_quota_prices
- Match intent: False
- Match entity: False
- HTTP status: 200
- Error: status_not_ok
