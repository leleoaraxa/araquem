# Test Migration Report — contratos atuais

## tests/test_bootstrap.py::test_metrics_exposes_prometheus_format
- **Suposição antiga:** a rota `/metrics` expunha a métrica `sirios_requests_total`.
- **Contrato atual observado:** a resposta expõe os nomes atualizados `sirios_http_requests_total`, `sirios_http_request_duration_seconds` e `sirios_planner_top2_gap_histogram` (além de métricas padrão do client Prometheus).
- **Mudança mínima proposta:** validar que pelo menos uma das métricas `sirios_http_requests_total`, `sirios_http_request_duration_seconds` ou `sirios_planner_top2_gap_histogram` está presente no payload bruto.

## tests/test_ontology_tokens.py::test_anti_tokens_apply_penalty_on_price_queries
- **Suposição antiga:** a penalização por anti-tokens aparecia diretamente como `anti_penalty > 0` dentro de `details['cadastro']`.
- **Contrato atual observado:** a intenção vencedora é `precos`, com pesos negativos aplicados em `explain.signals.weights_summary` (`phrase_sum < 0` e `token_sum <= 0`), enquanto `anti_penalty` permanece `0.0`.
- **Mudança mínima proposta:** confirmar que a intenção vencedora é `precos` e que existe penalidade negativa via `phrase_sum` ou `token_sum` no resumo de pesos de sinais, sem depender de `anti_penalty`.
