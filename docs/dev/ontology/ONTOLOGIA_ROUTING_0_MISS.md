# Ontologia – Baseline de Roteamento 0-miss (2025-12-08)

## 1. Contexto

Este documento registra o baseline de roteamento da ontologia do Araquem com **0 misses** na suíte de qualidade de intents, após:

- Ajustes na ontologia (`data/ontology/entity.yaml`) com uso consistente de:
  - Placeholders `\<ticker>` e `(sem ticker)`
  - Tokens e phrases por entidade
  - Anti-tokens setoriais (`macro_consolidada`, `client_*`, `client_fiis_enriched_portfolio`, etc.)
- Atualização do Planner (`app/planner/planner.py`) para:
  - Resolver ticker uma vez por pergunta (`resolve_ticker_from_text`)
  - Aplicar matching placeholder-aware em tokens e phrases
  - Manter telemetria e decision_path intactos.

## 2. Escopo do baseline

Suítes executadas:

```bash
python scripts/quality/quality_push.py \
  data/ops/quality/payloads/fiis_quota_prices_suite.json \
  data/ops/quality/payloads/fiis_dividends_suite.json \
  data/ops/quality/payloads/fiis_yield_history_suite.json \
  data/ops/quality/payloads/fiis_overview_suite.json \
  data/ops/quality/payloads/fiis_legal_proceedings_suite.json \
  data/ops/quality/payloads/fiis_financials_revenue_schedule_suite.json \
  data/ops/quality/payloads/fiis_rankings_suite.json \
  data/ops/quality/payloads/fiis_financials_snapshot_suite.json \
  data/ops/quality/payloads/fiis_news_suite.json \
  data/ops/quality/payloads/fiis_registrations_suite.json \
  data/ops/quality/payloads/history_b3_indexes_suite.json \
  data/ops/quality/payloads/macro_consolidada_suite.json \
  data/ops/quality/payloads/client_fiis_enriched_portfolio_suite.json \
  data/ops/quality/payloads/client_fiis_positions_suite.json \
  data/ops/quality/payloads/history_currency_rates_suite.json \
  data/ops/quality/payloads/client_fiis_performance_vs_benchmark_suite.json \
  data/ops/quality/payloads/fiis_dividends_yields_suite.json \
  data/ops/quality/payloads/fiis_financials_risk_suite.json \
  data/ops/quality/payloads/fiis_real_estate_suite.json \
  data/ops/quality/payloads/history_market_indicators_suite.json \
  data/ops/quality/payloads/negativos_indices_suite.json
````

Resultado:

* **218** amostras aceitas
* **0 misses** (`quality_list_misses.py` → “✅ Sem misses.”)

## 3. Regras de governança deste baseline

1. **Imutabilidade relativa**

   * `data/ontology/entity.yaml` passa a ser tratado como baseline de produção para roteamento.
   * Qualquer mudança em intents/phrases/anti_tokens deve:

     * Ser motivada por caso de uso concreto (nova entidade, novo tipo de pergunta, etc.).
     * Gerar novo run de `quality_push` com a mesma lista de suítes.
     * Ser registrada neste documento ou no `ARAQUEM_STATUS_2025`.

2. **Código permitido / não permitido neste contexto**

   * Permitido:

     * Evoluir ontologia (`entity.yaml`) e suites de qualidade.
     * Evoluir `ticker_index` e `resolve_ticker_from_text` respeitando contrato atual.
   * Não permitido (neste baseline):

     * Alterar thresholds de planner/routing “por fora” da ontologia para “forçar” match.
     * Introduzir heurísticas ad-hoc no planner/orchestrator que burlem o scoring da ontologia.

3. **Relação com buckets e contexto**

   * O baseline foi medido em cima do scorer do Planner, respeitando:

     * Regras de bucket vigentes (`data/ontology/bucket_rules.yaml`).
     * Anti-tokens entre entidades públicas, privadas e macro.
   * O comportamento em `/ask` deve ser periodicamente auditado com experimentos dedicados (shadow mode).
