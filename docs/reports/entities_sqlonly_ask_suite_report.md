# Relatório — /ask suites SQL-only

Execução das suites geradas a partir de perguntas existentes, rodadas contra o endpoint local `/ask` com `CACHE_BYPASS=1`. Todas as requisições falharam por conexão recusada no `http://localhost:8000/ask`.

## Resumo por entidade

| Entidade | Total | Pass | Fail | Top-3 falhas |
| --- | --- | --- | --- | --- |
| client_fiis_enriched_portfolio | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| client_fiis_dividends_evolution | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| client_fiis_performance_vs_benchmark | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| client_fiis_performance_vs_benchmark_summary | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| client_fiis_positions | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_dividends_yields | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_overview | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_registrations | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_dividends | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_financials_revenue_schedule | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_financials_risk | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_financials_snapshot | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_real_estate | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_news | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_quota_prices | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_legal_proceedings | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_rankings | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| fiis_yield_history | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| history_b3_indexes | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| history_currency_rates | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| history_market_indicators | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |
| consolidated_macroeconomic | 3 | 0 | 3 | http_not_ok (3), request_error (3), status_not_ok (3) |

## Falhas amostradas (1–2 por entidade)

### client_fiis_enriched_portfolio
- client_fiis_enriched_portfolio-q1: "Peso do {{ticker}} na minha carteira" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- client_fiis_enriched_portfolio-q2: "Valor investido em {{ticker}} na carteira" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### client_fiis_dividends_evolution
- client_fiis_dividends_evolution-q1: "evolução dos dividendos da minha carteira" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- client_fiis_dividends_evolution-q2: "como evoluiu a renda dos meus fiis mês a mês" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### client_fiis_performance_vs_benchmark
- client_fiis_performance_vs_benchmark-q1: "rentabilidade da minha carteira de fiis versus o IFIX" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- client_fiis_performance_vs_benchmark-q2: "como minha carteira está em relação ao CDI" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### client_fiis_performance_vs_benchmark_summary
- client_fiis_performance_vs_benchmark_summary-q1: "resumo da performance da minha carteira de fiis versus o IFIX" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- client_fiis_performance_vs_benchmark_summary-q2: "última leitura da carteira vs CDI" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### client_fiis_positions
- client_fiis_positions-q1: "Como está distribuída a carteira de FIIs por setor ou classe de ativo?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- client_fiis_positions-q2: "Quais posições aumentaram ou reduziram desde o último período de referência?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_dividends_yields
- fiis_dividends_yields-q1: "Qual foi o DY mensal do {{ticker}} em {{mês/ano}}?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_dividends_yields-q2: "Mostre dividendos e dividend yield do {{ticker}} nos últimos 12 meses." — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_overview
- fiis_overview-q1: "resumo do HGLG11" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_overview-q2: "como está o KNRI11 hoje?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_registrations
- fiis_registrations-q1: "qual o CNPJ do HGLG11?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_registrations-q2: "quem administra o VISC11?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_dividends
- fiis_dividends-q1: "quais dividendos o MXRF11 pagou neste mês?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_dividends-q2: "quando foi o último pagamento do HGLG11?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_financials_revenue_schedule
- fiis_financials_revenue_schedule-q1: "receita com vencimento em 0–3 meses do HGLG11" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_financials_revenue_schedule-q2: "quanto vence em 12 meses do XPML11" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_financials_risk
- fiis_financials_risk-q1: "qual o Sharpe do HGRU11?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_financials_risk-q2: "beta e R² do KNRI11 em relação ao IFIX" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_financials_snapshot
- fiis_financials_snapshot-q1: "Qual o lucro ou resultado distribuível mais recente do FII?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_financials_snapshot-q2: "Como evoluíram receitas, despesas e margens entre períodos?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_real_estate
- fiis_real_estate-q1: "Quais imóveis compõem a carteira do FII e onde estão localizados?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_real_estate-q2: "Qual a tipologia (ex.: lajes, galpões, shoppings) dos imóveis listados?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_news
- fiis_news-q1: "Quais foram as últimas notícias publicadas sobre determinado FII?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_news-q2: "Houve fatos relevantes ou comunicados de mercado recentes?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_quota_prices
- fiis_quota_prices-q1: "como fechou o HGLG11 hoje?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_quota_prices-q2: "qual foi a variação do MXRF11 ontem?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_legal_proceedings
- fiis_legal_proceedings-q1: "Existem processos judiciais ou administrativos envolvendo o FII?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_legal_proceedings-q2: "Qual o estágio atual (ex.: em andamento, decisão, acordo) de cada processo?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_rankings
- fiis_rankings-q1: "Quais FIIs lideram o ranking por rendimento ou dividend yield?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_rankings-q2: "Como os fundos se posicionam por liquidez ou volume negociado?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### fiis_yield_history
- fiis_yield_history-q1: "Qual foi o DY mensal do {{ticker}} em {{mês/ano}}?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- fiis_yield_history-q2: "Como tem sido a evolução do DY do {{ticker}} nos últimos 12 meses?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### history_b3_indexes
- history_b3_indexes-q1: "quanto fechou o IFIX ontem?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- history_b3_indexes-q2: "qual foi a variação do IBOV na data X?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### history_currency_rates
- history_currency_rates-q1: "como fechou o dólar ontem?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- history_currency_rates-q2: "qual a variação do euro na última cotação?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### history_market_indicators
- history_market_indicators-q1: "qual foi o CDI ontem?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- history_market_indicators-q2: "quanto está o IPCA acumulado no último dado?" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus

### consolidated_macroeconomic
- consolidated_macroeconomic-q1: "IPCA e SELIC no dia {{data}}" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
- consolidated_macroeconomic-q2: "IFIX e IBOV na semana passada" — falhas: http_not_ok, request_error, status_not_ok, entity_mismatch; erro: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /ask?explain=true (Caused by NewConnectionError("HTTPConnection(host='localhost', port=8000): Failed to establish a new connection: [Errno 111] Connection refus
