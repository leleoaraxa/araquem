# Inventário do Domínio de FIIs da SIRIOS (V1)

## 1. Visão Geral do Domínio de FIIs na SIRIOS
A SIRIOS organiza dados de Fundos de Investimento Imobiliário para cobrir desde informações cadastrais e séries diárias de preços até proventos, métricas financeiras e de risco, com extensões para macroindicadores e posições individuais de clientes. As intents da ontologia alinham consultas de usuários a entidades como cadastro, preços, dividendos, riscos, imóveis, processos, notícias e rankings, enquanto dados históricos de índices, moedas e indicadores permitem contextualizar o mercado.

Blocos de domínio identificados:
- Cadastro e classificação de FIIs.
- Preços e histórico de cota.
- Dividendos e proventos.
- Indicadores financeiros e de risco.
- Cronograma de recebíveis e indexadores.
- Imóveis e portfólio físico.
- Processos judiciais.
- Notícias.
- Rankings e movimentos em IFIX/IFIL e rankings de usuários/SIRIOS.
- Mercado macro (índices, moedas, indicadores econômicos).
- Posições do cliente (carteira de FIIs).

## 2. Mapa de Entidades x Intents x Perguntas de Usuário
| intent | entity | descrição_negócio | principais_campos | exemplos_de_perguntas_do_usuário | telas_relacionadas |
| --- | --- | --- | --- | --- | --- |
| client_fiis_positions | client_fiis_positions | Posições do cliente em FIIs, com quantidades e valores por data. | documento do cliente, data da posição, ticker, nome do FII, participante, quantidade, preço de fechamento, variação em valor, quantidade disponível | “quais são minhas posições em FIIs?”, “quantas cotas tenho do MXRF11?”, “carteira de fundos imobiliários por corretora” | não identificado |
| fiis_cadastro | fiis_cadastro | Dados cadastrais 1×1 de cada FII: identificação, administração, classificação e participação em índices. | ticker, CNPJ, nome de exibição, nome B3, classificação/setor, tipo de gestão, público-alvo, ISIN, datas e pesos IFIX/IFIL, número de cotas/cotistas | “qual o CNPJ do KNRI11?”, “quem é o administrador do HGLG11?”, “peso do VISC11 no IFIX” | não identificado |
| fiis_dividendos | fiis_dividendos | Histórico de proventos pagos por FII com datas e valores por cota. | ticker, data de pagamento, valor do dividendo por cota, data-com | “quando foi pago o último dividendo do MXRF11?”, “qual o valor por cota dos proventos de agosto?” | não identificado |
| fiis_precos | fiis_precos | Série diária de preços de cotas de FIIs, com OHLC e variação. | ticker, data de negociação, preço de fechamento (ajustado), abertura, máxima, mínima, variação diária | “qual o preço de fechamento do KNRI11 ontem?”, “quanto o HGLG11 variou hoje?” | não identificado |
| fiis_financials_snapshot | fiis_financials_snapshot | Snapshot D-1 de indicadores financeiros e operacionais do FII. | DY mensal/anual, último dividendo e data, market cap, enterprise value, P/VP, patrimônio e receita por cota, payout, cap rate, alavancagem, caixa, passivos, variação mês/ano | “qual o dividend yield do VISC11?”, “qual a alavancagem do HGRU11?”, “quanto é o market cap do HGLG11?” | não identificado |
| fiis_financials_risk | fiis_financials_risk | Indicadores de risco (volatilidade e índices de risco-retorno) em D-1. | volatilidade, Sharpe, Treynor, Alfa de Jensen, beta, Sortino, drawdown, R² | “qual o Sharpe do KNRI11?”, “quão volátil está o MXRF11?” | não identificado |
| fiis_financials_revenue_schedule | fiis_financials_revenue_schedule | Estrutura de vencimento de recebíveis e indexadores de receita. | percentuais de receita por buckets de vencimento (0–3m … >36m/indeterminado), percentuais indexados a IGPM/IPCA/INPC/INCC | “quanto das receitas vence em até 6 meses do HGLG11?”, “qual percentual indexado ao IPCA?” | não identificado |
| fiis_imoveis | fiis_imoveis | Imóveis e ativos operacionais do portfólio do FII. | nome do ativo, classe do ativo, endereço/localização, área total, número de unidades, vacância, inadimplência, status | “quais imóveis compõem o portfólio do VISC11?”, “qual a vacância dos ativos do KNRI11?” | não identificado |
| fiis_processos | fiis_processos | Processos judiciais associados ao FII, com risco e andamento. | número do processo, fase de julgamento, instância, data de início, valor da causa, partes, risco de perda, análise de impacto | “o MXRF11 tem processos judiciais em andamento?”, “qual o risco de perda do processo X?” | não identificado |
| fiis_noticias | fiis_noticias | Notícias D-1 ligadas a FIIs, com fonte e links. | fonte, título, tags, descrição, URL e imagem, data de publicação | “quais as últimas notícias do HGLG11?”, “tem matéria recente sobre o IFIX?” | não identificado |
| fiis_rankings | fiis_rankings | Aparições e movimentos em rankings (usuários, SIRIOS, IFIX, IFIL). | contagem de aparições e movimentos líquidos para usuários, SIRIOS, IFIX, IFIL | “em que posição o VISC11 aparece nos rankings da SIRIOS?”, “quais FIIs mais subiram no IFIX?” | não identificado |
| history_b3_indexes | history_b3_indexes | Pontos e variação diária de índices B3 (IBOV, IFIX, IFIL) D-1. | data, pontos e variação de IBOV, IFIX e IFIL | “quanto fechou o IFIX ontem?”, “qual a variação do IBOV no dia?” | não identificado |
| history_currency_rates | history_currency_rates | Cotações D-1 de USD/EUR em BRL, compra/venda e variação. | data, dólar compra/venda e variação, euro compra/venda e variação | “qual a cotação do dólar ontem?”, “como fechou o euro (venda)?” | não identificado |
| history_market_indicators | history_market_indicators | Indicadores macroeconômicos (IPCA, CDI, SELIC, IGPM etc.) D-1. | data, nome do indicador, valor observado | “qual foi o CDI de ontem?”, “quanto está a SELIC meta?” | não identificado |

## 3. Descrição Detalhada por Entidade
### 3.1 client_fiis_positions
- **Intent associada:** client_fiis_positions.
- **Tipo de dado:** posições de cliente (privado) com data e ticker.
- **Objetivo de negócio:** responder à carteira do usuário em FIIs, quantidades e variação de valor por participante.
- **Principais campos:** documento do cliente (CPF/CNPJ), data da posição, ticker, nome do FII, participante/corretora, quantidade em custódia e disponível, preço de fechamento, variação em valor.
- **Relações:** ticker conecta com entidades públicas (cadastro, preços, dividendos) para enriquecer visão de carteira.
- **Telas/funcionalidades:** não identificado.

### 3.2 fiis_cadastro
- **Intent associada:** fiis_cadastro.
- **Tipo de dado:** cadastro 1×1 de FII.
- **Objetivo de negócio:** identificar o fundo, administrador, classificações, público-alvo e participação em índices.
- **Principais campos:** ticker, CNPJ do FII e do administrador, nomes de exibição/pregão, classificação/setor/subsetor, tipo de gestão, público-alvo, ISIN, data de IPO, site, pesos IFIX/IFIL, número de cotas e cotistas.
- **Relações:** ticker é chave para preços, dividendos, indicadores, imóveis, rankings e processos.
- **Telas/funcionalidades:** não identificado.

### 3.3 fiis_dividendos
- **Intent associada:** fiis_dividendos.
- **Tipo de dado:** série de proventos por FII.
- **Objetivo de negócio:** mostrar valores por cota, datas de pagamento e datas-com para analisar renda.
- **Principais campos:** ticker, data de pagamento, valor do dividendo por cota, data-com.
- **Relações:** complementa preços e snapshots financeiros (DY, payout) para análises de retorno.
- **Telas/funcionalidades:** não identificado.

### 3.4 fiis_precos
- **Intent associada:** fiis_precos.
- **Tipo de dado:** série diária OHLC e variação.
- **Objetivo de negócio:** acompanhar cotação e volatilidade diária dos FIIs.
- **Principais campos:** ticker, data de negociação, preços de fechamento (ajustado), abertura, máxima, mínima, variação diária.
- **Relações:** base para métricas de risco (volatilidade) e comparação com índices B3.
- **Telas/funcionalidades:** não identificado.

### 3.5 fiis_financials_snapshot
- **Intent associada:** fiis_financials_snapshot.
- **Tipo de dado:** snapshot D-1 com indicadores financeiros, caixa e endividamento.
- **Objetivo de negócio:** avaliar saúde financeira, distribuição de dividendos, valuation e alavancagem.
- **Principais campos:** DY mensal/anual, soma anual de proventos, último dividendo e data, market cap, enterprise value, P/VP, patrimônio e receita por cota, payout, taxa de crescimento, cap rate, alavancagem, patrimônio total, variações mês/ano, reserva de dividendos, taxas de administração/performance devidas, caixa total, receita esperada, passivos totais.
- **Relações:** usa dados de dividendos e preços para derivar DY e valuation; complementa riscos e rankings.
- **Telas/funcionalidades:** não identificado.

### 3.6 fiis_financials_risk
- **Intent associada:** fiis_financials_risk.
- **Tipo de dado:** indicadores quantitativos de risco D-1.
- **Objetivo de negócio:** medir risco e performance ajustada de risco por FII.
- **Principais campos:** volatilidade, índices de Sharpe, Treynor, Alfa de Jensen, beta, Sortino, drawdown máximo, R².
- **Relações:** depende de preços e benchmarks (ex.: índices de mercado) para cálculo; relaciona-se a rankings e comparações.
- **Telas/funcionalidades:** não identificado.

### 3.7 fiis_financials_revenue_schedule
- **Intent associada:** fiis_financials_revenue_schedule.
- **Tipo de dado:** distribuição temporal de receitas e indexadores.
- **Objetivo de negócio:** analisar concentração de recebíveis por prazo e exposição a indexadores.
- **Principais campos:** percentuais de receita em buckets de vencimento (0–3m até >36m/indeterminado) e percentuais indexados a IGPM, INPC, IPCA, INCC.
- **Relações:** complementa snapshots financeiros para avaliar previsibilidade de receitas e risco de duration.
- **Telas/funcionalidades:** não identificado.

### 3.8 fiis_imoveis
- **Intent associada:** fiis_imoveis.
- **Tipo de dado:** detalhes dos imóveis/ativos do portfólio (1×N).
- **Objetivo de negócio:** mapear ativos físicos, ocupação e riscos operacionais.
- **Principais campos:** nome do ativo, classe, endereço/localização, área total, número de unidades, vacância, inadimplência, status operacional.
- **Relações:** usa ticker de cadastro; conecta com snapshots (vacância/receita) e notícias/processos relacionados a ativos.
- **Telas/funcionalidades:** não identificado.

### 3.9 fiis_processos
- **Intent associada:** fiis_processos.
- **Tipo de dado:** processos judiciais relacionados ao FII.
- **Objetivo de negócio:** avaliar riscos legais e potenciais impactos financeiros.
- **Principais campos:** número do processo, julgamento/andamento, instância, data de início, valor da causa, partes, risco de perda, fatos principais, análise de impacto.
- **Relações:** ticker vincula a cadastro e snapshots para impacto em valuation; notícias podem referenciar processos.
- **Telas/funcionalidades:** não identificado.

### 3.10 fiis_noticias
- **Intent associada:** fiis_noticias.
- **Tipo de dado:** notícias e matérias D-1 sobre FIIs.
- **Objetivo de negócio:** informar eventos recentes e contexto qualitativo.
- **Principais campos:** fonte, título, tags, descrição, URL, imagem, data de publicação.
- **Relações:** ticker vincula a outros dados; complementa preços/dividendos para narrativas de mercado.
- **Telas/funcionalidades:** não identificado.

### 3.11 fiis_rankings
- **Intent associada:** fiis_rankings.
- **Tipo de dado:** contagem de aparições e movimentos em rankings diversos.
- **Objetivo de negócio:** indicar popularidade e momentum em rankings de usuários, SIRIOS e índices IFIX/IFIL.
- **Principais campos:** contagem e movimentos líquidos em rankings de usuários, SIRIOS, IFIX e IFIL.
- **Relações:** ticker liga a indicadores de desempenho/risco; pode alimentar telas de “top FIIs”.
- **Telas/funcionalidades:** não identificado.

### 3.12 history_b3_indexes
- **Intent associada:** history_b3_indexes.
- **Tipo de dado:** série D-1 de pontos e variações de IBOV, IFIX, IFIL.
- **Objetivo de negócio:** fornecer benchmarks de mercado para comparação com FIIs e carteiras.
- **Principais campos:** data, pontos e variação de IBOV, IFIX, IFIL.
- **Relações:** usados em cálculo de betas/risco e na contextualização de preços e rankings.
- **Telas/funcionalidades:** não identificado.

### 3.13 history_currency_rates
- **Intent associada:** history_currency_rates.
- **Tipo de dado:** cotações D-1 de moedas USD/EUR em BRL.
- **Objetivo de negócio:** contextualizar impactos cambiais em fundos expostos a moedas ou ativos dolarizados.
- **Principais campos:** data, dólar compra/venda e variação, euro compra/venda e variação.
- **Relações:** macro complementar às análises de risco/retorno; pode afetar notícias e narrativas.
- **Telas/funcionalidades:** não identificado.

### 3.14 history_market_indicators
- **Intent associada:** history_market_indicators.
- **Tipo de dado:** indicadores macroeconômicos D-1.
- **Objetivo de negócio:** prover taxas/índices (IPCA, CDI, SELIC, IGPM etc.) para comparar yields, indexadores e custo de capital.
- **Principais campos:** data, nome do indicador, valor numérico.
- **Relações:** úteis para análises de indexação de receitas, custo de oportunidade e riscos de mercado.
- **Telas/funcionalidades:** não identificado.

## 4. Comparação com o Documento Atual data/concepts/fiis.md
**Cobertura atual:** o fiis.md aborda conceitos gerais de FIIs, tipos de fundos (tijolo, papel, híbrido, desenvolvimento), governança (administrador, gestor, custodiante), métricas clássicas (DY, VPA, P/VP, vacância, cap rate, alavancagem, liquidez), riscos (mercado, vacância, crédito, gestão) e glossário essencial.

**Lacunas identificadas em relação às entidades/ontologia:**
- Não aborda posições de clientes (client_fiis_positions) e aspectos de privacidade.
- Não menciona cronograma de recebíveis e indexadores de receita (fiis_financials_revenue_schedule).
- Cobertura superficial ou ausente de métricas quantitativas de risco avançado (Sharpe, Treynor, Jensen, Sortino, drawdown, R²) já modeladas em fiis_financials_risk.
- Não trata de processos judiciais (fiis_processos) nem de potenciais impactos legais.
- Não inclui notícias como fonte de contexto (fiis_noticias).
- Rankings (IFIX/IFIL, rankings de usuários/SIRIOS) não aparecem.
- Macrocontexto e benchmarks (history_b3_indexes, history_market_indicators, history_currency_rates) não são mencionados.
- Integração de dados financeiros de snapshot (market cap, EV, payout, alavancagem, caixa, passivos) e reservas de dividendos não está presente.

## 5. Mapa de Domínios para o Futuro fiis.md V1
- **Capítulo 1 – Introdução a Fundos Imobiliários:** contextualizar FIIs e objetivos do guia.
- **Capítulo 2 – Universo de FIIs na SIRIOS:** explicar como a SIRIOS organiza intents e entidades (cadastro, preços, dividendos, indicadores, risco).
- **Capítulo 3 – Cadastro e Classificação dos Fundos (fiis_cadastro):** identificação, classificação, governança e participação em índices.
- **Capítulo 4 – Preço e Rendimentos (fiis_precos, fiis_dividendos):** histórico de cotação, proventos e datas-com.
- **Capítulo 5 – Indicadores Financeiros e Valuation (fiis_financials_snapshot):** DY, payout, market cap, P/VP, caixa, passivos e crescimento.
- **Capítulo 6 – Risco e Performance Ajustada (fiis_financials_risk):** volatilidade, Sharpe, Treynor, Sortino, drawdown, beta, R².
- **Capítulo 7 – Recebíveis e Indexadores (fiis_financials_revenue_schedule):** prazos de receitas e exposição a indexadores.
- **Capítulo 8 – Imóveis e Portfólio Físico (fiis_imoveis):** ativos, localização, vacância, inadimplência e status.
- **Capítulo 9 – Notícias e Eventos (fiis_noticias, fiis_processos):** notícias recentes e processos judiciais com riscos e impactos.
- **Capítulo 10 – Rankings e Popularidade (fiis_rankings):** aparições e movimentos em rankings de usuários, SIRIOS, IFIX e IFIL.
- **Capítulo 11 – Contexto de Mercado e Macroeconomia (history_b3_indexes, history_market_indicators, history_currency_rates):** índices de mercado, taxas macro e câmbio como benchmarks.
- **Capítulo 12 – Minha Carteira de FIIs (client_fiis_positions):** visão do investidor sobre posições, quantidades e valores (com controles de privacidade).
