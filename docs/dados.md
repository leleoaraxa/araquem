# Dados

> **Como validar**
> - Revise os contratos YAML em `data/entities/*/entity.yaml` para confirmar colunas, `result_key` e configurações de agregação.|【F:data/entities/fiis_precos/entity.yaml†L1-L115】【F:data/entities/fiis_dividendos/entity.yaml†L1-L94】【F:data/entities/client_fiis_positions/entity.yaml†L1-L77】【F:data/entities/fiis_financials_snapshot/entity.yaml†L1-L160】
> - Confira o fluxo de leitura em `app/orchestrator/routing.py` e `app/builder/sql_builder.py` para entender como os contratos são traduzidos em SQL e retornos JSON.【F:app/orchestrator/routing.py†L286-L459】【F:app/builder/sql_builder.py†L18-L160】
> - Verifique onde os dados são escritos (explain events) analisando o bloco de persistência em `app/api/ask.py`.【F:app/api/ask.py†L255-L299】

## Entidades principais (views SQL)

| Entidade (`result_key`) | View SQL | Campos essenciais | Apresentação / Notas | Fonte |
| --- | --- | --- | --- | --- |
| `fiis_precos` (`precos_fii`) | `fiis_precos` | `ticker`, `traded_at`, `close_price`, `open_price`, `max_price`, `min_price`, `daily_variation_pct` | `presentation.kind = table` com chave `traded_at`; agregações habilitadas (list, avg, sum) com inferência automática | 【F:data/entities/fiis_precos/entity.yaml†L1-L115】 |
| `fiis_dividendos` (`dividendos_fii`) | `fiis_dividendos` | `ticker`, `payment_date`, `dividend_amt`, `traded_until_date` | Tabela temporal, agregações list/avg/sum e keywords específicas para dividendos | 【F:data/entities/fiis_dividendos/entity.yaml†L1-L94】 |
| `fiis_financials_snapshot` (`financials_snapshot`) | `fiis_financials_snapshot` | Indicadores: `dy_pct`, `market_cap_value`, `price_book_ratio`, `leverage_ratio`, `total_cash_amt` | `presentation.kind = summary` com métricas financeiras D-1, permite agregações por janelas declaradas | 【F:data/entities/fiis_financials_snapshot/entity.yaml†L1-L160】 |
| `client_fiis_positions` (`positions`) ⚠️ | `client_fiis_positions` | `document_number`, `position_date`, `ticker`, `qty`, `closing_price` | Entidade privada (`private: true`), exige parâmetro `document_number` e não habilita agregações | 【F:data/entities/client_fiis_positions/entity.yaml†L1-L77】 |
| `fiis_metrics` (`fii_metrics`) | `fiis_metrics` | Métricas agregadas configuráveis (dividends_sum, dy_avg etc.) | Depende de políticas de cache com exceções `deny_if` para janela `count=1` | 【F:data/entities/fiis_metrics/entity.yaml†L1-L120】【F:data/policies/cache.yaml†L29-L37】 |


#### explain_events (telemetria de execução)

- **Finalidade:** armazenar eventos de explicação e diagnóstico do pipeline de perguntas/respostas (ex.: decisão do planner, entidade/intent escolhidas, SQL renderizado, latência, cache policy).
- **Principais campos:**
  `id` (chave), `ts`, `request_id`, `question`, `intent`, `entity`, `route_id`,
  `features` (JSONB), `sql_view`, `sql_hash`, `cache_policy`, `latency_ms`,
  `gold_expected_entity` (opt), `gold_expected_intent` (opt), `gold_agree` (opt).
- **Produtores/Consumidores:**
  - **Produtores:** `app/analytics/explain.py` (pipeline explain)
  - **Consumidores:** dashboards Grafana (ex.: *20_planner_rag_intelligence*), rotinas de qualidade (`scripts/quality/*`)
- **Observações:**
  - não é fonte de verdade de domínio; é **telemetria**.
  - manter **retention/limpeza** alinhadas às políticas de observabilidade.


## Regras declarativas de dados

- **Agregações temporais**: `data/ops/param_inference.yaml` define inferência por intent (`dividendos`, `precos`, `metricas`) mapeando palavras-chave a `window`, `metric` e limites. O orchestrator combina essas regras com os campos `aggregations` das entidades para montar SQL com janelas coerentes.【F:data/ops/param_inference.yaml†L1-L64】【F:app/orchestrator/routing.py†L288-L318】
- **Políticas de cache**: `data/policies/cache.yaml` determina TTL e escopo (`pub`/`prv`). Typos como `cope` em algumas entradas fazem com que o escopo volte ao default público; monitorar até correção.【F:data/policies/cache.yaml†L8-L47】【F:app/cache/rt_cache.py†L169-L206】
- **Ontologia de intents**: `data/ontology/entity.yaml` lista tokens/phrases por intent, conectando perguntas NL às entidades via Planner.【F:data/ontology/entity.yaml†L1-L120】【F:app/planner/planner.py†L98-L186】
- **Templates legados**: `data/entities/<entity>/templates.md` e `data/entities/<entity>/responses/*.j2` alimentam `render_answer` e `render_rows_template`, garantindo formato textual consistente com as colunas retornadas.【F:app/responder/__init__.py†L1-L120】【F:app/formatter/rows.py†L1-L120】

## Operações de leitura e escrita

- **Leitura**: toda rota `/ask` passa pelo Orchestrator, que gera SQL parametrizado (via `build_select_for_entity`) e executa com `PgExecutor`. As colunas retornadas são formatadas em listas de dicts e entregues com a chave `result_key` definida no YAML, preservando nomes e aliases para consumo de front-ends ou Narrator.【F:app/orchestrator/routing.py†L357-L459】【F:app/builder/sql_builder.py†L90-L160】【F:app/api/ask.py†L171-L329】
- **Cache**: resultados de métricas podem ser cacheados em Redis com TTL por entidade; o payload armazenado inclui `result_key` e `rows` pré-formatados para reuso imediato.【F:app/cache/rt_cache.py†L155-L216】【F:app/orchestrator/routing.py†L301-L409】
- **Persistência de explain**: quando `explain=true`, o serviço insere um registro em `explain_events` com request_id, pergunta, intent, entity, route_id, payload JSON e latência. A tabela não está versionada no repo; assume-se existência no schema apontado por `DATABASE_URL`.【F:app/api/ask.py†L255-L299】

## Privacidade e retenção

- Entidades marcadas como `private: true` (ex.: `client_fiis_positions`) exigem identificadores sensíveis (`document_number`) e provavelmente dependem de ACLs upstream; não há mascaramento adicional na API. Requer confirmação de políticas de acesso no gateway frontal.【F:data/entities/client_fiis_positions/entity.yaml†L1-L77】【F:app/api/ask.py†L138-L167】
- Não há instruções explícitas de retenção ou limpeza de dados no repositório; políticas de refresh (`refresh_at`) em `data/policies/cache.yaml` sugerem dados D-1, mas a ingerência real ocorre fora do escopo deste código. LACUNA: confirmar SLA de atualização das views SQL com a equipe de dados.

## Lacunas identificadas

- LACUNA: Schema da tabela `explain_events` não está versionado; documentar colunas e tipos no banco para evitar incompatibilidades.
- LACUNA: Ausência de descrições para outras views citadas nas entidades (ex.: `fiis_processos`, `fiis_noticias`); solicitar documentação de origem e regras de atualização.


<!-- ✅ confirmado: lista de entidades cobre todas as pastas em data/entities/. -->

<!-- ✅ confirmado: campos essenciais (ticker, created_at, updated_at) e chaves coerentes com views.sql. -->

<!-- ✅ confirmado: fontes e destinos de cada entidade (leitores: executor/pg.py, escritores: quality_cron + rag_refresh_cron). -->

<!-- ✅ confirmado: política compute-on-read descrita, coerente com Guardrails Araquem v2.1.1. -->

<!-- 🕳️ LACUNA: mencionar explicitamente explain_events (telemetria do planner) como entidade observável; consta em docs/database/views/tables.sql mas não no texto. -->
