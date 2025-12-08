### 4.x – Baseline de roteamento (ontologia) – **0 misses**

- Data: 2025-12-08
- Commit: `<preencher_commit_hash>`
- Arquivo central: `data/ontology/entity.yaml`
- Código do Planner: `app/planner/planner.py` (com suporte a `<ticker>` e `(sem ticker)` via `resolve_ticker_from_text`)

**Suítes de qualidade consideradas neste baseline (quality_push):**

```bash
python scripts/quality/quality_push.py \
  data/ops/quality/payloads/fiis_precos_suite.json \
  data/ops/quality/payloads/fiis_dividendos_suite.json \
  data/ops/quality/payloads/fiis_yield_history_suite.json \
  data/ops/quality/payloads/fii_overview_suite.json \
  data/ops/quality/payloads/fiis_processos_suite.json \
  data/ops/quality/payloads/fiis_financials_revenue_schedule_suite.json \
  data/ops/quality/payloads/fiis_rankings_suite.json \
  data/ops/quality/payloads/fiis_financials_snapshot_suite.json \
  data/ops/quality/payloads/fiis_noticias_suite.json \
  data/ops/quality/payloads/fiis_cadastro_suite.json \
  data/ops/quality/payloads/history_b3_indexes_suite.json \
  data/ops/quality/payloads/macro_consolidada_suite.json \
  data/ops/quality/payloads/carteira_enriquecida_suite.json \
  data/ops/quality/payloads/client_fiis_positions_suite.json \
  data/ops/quality/payloads/history_currency_rates_suite.json \
  data/ops/quality/payloads/client_fiis_performance_vs_benchmark_suite.json \
  data/ops/quality/payloads/dividendos_yield_suite.json \
  data/ops/quality/payloads/fiis_financials_risk_suite.json \
  data/ops/quality/payloads/fiis_imoveis_suite.json \
  data/ops/quality/payloads/history_market_indicators_suite.json \
  data/ops/quality/payloads/negativos_indices.json
```

**Resultado consolidado:**

* Total de casos aceitos: **218**
* Misses de roteamento: **0**
* Comando de verificação:

  ```bash
  python scripts/quality/quality_list_misses.py
  # ✅ Sem misses.
  ```

**Entidades cobertas diretamente pelas suítes:**

* FIIs públicos:
  `fiis_precos`, `fiis_dividendos`, `fiis_yield_history`, `fii_overview`,
  `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`,
  `fiis_financials_risk`, `fiis_rankings`, `fiis_imoveis`,
  `fiis_noticias`, `fiis_processos`, `fiis_cadastro`
* Macro / índices:
  `macro_consolidada`, `history_market_indicators`, `history_b3_indexes`,
  `history_currency_rates`
* Carteira / cliente:
  `carteira_enriquecida`, `client_fiis_positions`, `client_fiis_performance_vs_benchmark`
* Conceito misto de dividendos/yield:
  `dividendos_yield`
* Cenários negativos/edge:
  `negativos_indices`

**Observações de arquitetura:**

* Placeholders `\<ticker>` e `(sem ticker)` agora são **funcionais** no Planner:

  * Interpretação centralizada em `Planner.explain()` com auxílio de `resolve_ticker_from_text`.
  * Matching de `tokens` e `phrases` respeita presença/ausência de ticker na pergunta.
* Nenhuma alteração foi feita em **thresholds**, `planner/routing` fora da lógica de scoring por ontologia.
* Esse estado é o **baseline canônico de roteamento 2025.0** – qualquer mudança futura em ontologia deve:

  * Passar por nova rodada de `quality_push` com as mesmas suítes, e
  * Atualizar este registro em caso de alteração nos resultados.
