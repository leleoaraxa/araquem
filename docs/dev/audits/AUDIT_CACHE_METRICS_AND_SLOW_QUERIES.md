# Auditoria: Cache de Métricas e Consultas Lentas (/ask)

## 1) Resumo executivo
- O runner de diagnostics mede `cache_hit_metrics` lendo `meta.compute.metrics_cache_hit`, mas o pipeline só popula esse flag quando há cache de métricas do planner (ticker + metric + janela); as perguntas de carteira x benchmark não atendem a esses requisitos, resultando em 0% de hits.
- O cache de resposta é cache-first e faz short-circuit: hits retornam direto do Redis (`meta.cache.hit`), pulando rota do orchestrator e qualquer tentativa de cache de métricas ou execução SQL.
- As chaves de resposta são baseadas no `plan_hash` (entity, intent, bucket, scope, identifiers, agg_params, flags, requested_metrics) e não incorporam `conversation_id`; métricas usam chave separada com `make_cache_key` + metric/window.
- As 5 perguntas mais lentas (carteira vs benchmark/última leitura) roteiam para `client_fiis_performance_vs_benchmark_summary` (SQL view homônima, privada, TTL 900s); custo visível só via `meta.elapsed_ms` e métricas do executor (`sirios_sql_query_duration_seconds`).
- Para comprovar gargalos, rode o suite com `--explain` e compare `meta.elapsed_ms` versus o histogram do executor; depois execute `EXPLAIN ANALYZE` no view `client_fiis_performance_vs_benchmark_summary` com os parâmetros do plano.

## 2) Cache de metrics (hipótese → evidência → como provar → ação mínima)
- **Hipótese:** O runner marca 0% porque procura `meta.compute.metrics_cache_hit`, mas o planner só ativa o cache de métricas quando a entidade tem `ticker`, `agg_params.metric` e janela normalizada; as rotas de carteira vs benchmark não fornecem `metric`/`window`.
- **Evidência:** O runner lê `meta.compute.metrics_cache_hit` para somar hits.【F:scripts/diagnostics/run_ask_suite.py†L428-L438】 O orchestrator só monta contexto de métricas se houver `ticker`, `agg_params.metric` e `window_norm`; caso contrário retorna `None` e não tenta ler/gravar cache.【F:app/orchestrator/routing.py†L277-L325】【F:app/orchestrator/routing.py†L720-L750】
- **Como provar:** Executar uma pergunta que tenha `agg_params.metric` (ex.: entidades com compute-on-read) com `explain=true` e verificar `meta.compute.metrics_cache_hit` mudar para `true` na segunda chamada; contrastar com uma pergunta de carteira vs benchmark (permanece `false`).
- **Ação mínima:** Documentar no runner que `cache_hit_metrics` só faz sentido para entidades com `metric`+`window`; opcionalmente logar um aviso quando `meta.compute` estiver ausente.

## 3) Cache de response e short-circuit (hipótese → evidência → como provar → ação mínima)
- **Hipótese:** Quando `meta.cache.hit` é `true`, o /ask retorna o payload normalizado do Redis e não chama o orchestrator, logo nada de métricas SQL nem cache de métricas é avaliado.
- **Evidência:** O fluxo é cache-first; se `cache_hit` ficar `true`, `_fetch` (orchestrator.route_question) não é chamado.【F:app/api/ask.py†L335-L436】 O payload final só substitui `meta.cache` e segue direto para presenter.【F:app/api/ask.py†L677-L714】
- **Como provar:** Popular manualmente uma chave de resposta com `make_plan_cache_key` e repetir a pergunta com `--explain`; observar que `meta.cache.hit=true`, `meta.compute.metrics_cache_hit` mantém o valor gravado anteriormente e nenhuma query SQL aparece nos logs do executor.
- **Ação mínima:** Incluir no diagnóstico a distinção “cache de resposta curto-circuitou o planner”, para evitar interpretar `metrics_cache_hit=false` como ausência de cache quando a rota nem foi executada.

## 4) Chaves / Key building
- **Onde é construída:** `plan_hash = build_plan_hash(...)` em `routing.prepare_plan`, compondo fingerprint com entity, intent, bucket, scope, identifiers normalizados, `agg_params`, flags (`multi_ticker*`, `compute_mode`) e `requested_metrics`; o cache de resposta usa `make_plan_cache_key(build_id, scope, entity, plan_hash)` no /ask.【F:app/orchestrator/routing.py†L428-L459】【F:app/api/ask.py†L333-L407】【F:app/cache/rt_cache.py†L268-L315】【F:app/cache/rt_cache.py†L383-L387】
- **Campos que entram:** todos os identifiers resolvidos/inferidos (ex.: `document_number`, `benchmark_code`, `date_reference`), `agg_params`, flags e métricas solicitadas; **não** inclui `conversation_id` ou `client_id` exceto se eles forem copiados para identifiers via bindings de `param_inference.yaml` (para carteiras, `document_number <- context.client_id`).【F:data/ops/param_inference.yaml†L268-L279】【F:data/policies/cache.yaml†L30-L46】
- **Cache de métricas:** usa `make_cache_key(build_id, scope, entity, cache_identifiers)` com `metric_key` e `window_norm` incorporados à hash, respeitando o mesmo `cfg-<hash>` do conjunto de configs.【F:app/orchestrator/routing.py†L312-L324】【F:app/cache/rt_cache.py†L376-L381】 TTL e scope vêm da policy da entidade (ex.: 900s, `prv` para carteira vs benchmark summary).【F:data/policies/cache.yaml†L38-L46】

## 5) Top 5 queries lentas (hipótese → evidência → como provar → ação mínima)
- **Perguntas mapeadas → entidade:** As cinco formuladas (“Resumo carteira vs CDI D-1”, “Excesso de retorno… última data”, “Performance … IBOV (resumo)”, “Performance carteira vs IBOV até agora (resumo)”, “Visão resumida carteira vs FIIs vs IFIL”) têm `expected_entity = client_fiis_performance_vs_benchmark_summary` no suite.【F:data/ops/quality/routing_samples.json†L125-L162】 O entity YAML aponta para o view `client_fiis_performance_vs_benchmark_summary` (privado, TTL 900s).【F:data/entities/client_fiis_performance_vs_benchmark_summary/client_fiis_performance_vs_benchmark_summary.yaml†L1-L33】【F:data/policies/cache.yaml†L38-L46】
- **Custo visível:** O único timer no payload é `meta.elapsed_ms`, que mede o pipeline do orchestrator (inclui query + format).【F:app/orchestrator/routing.py†L922-L945】 O executor expõe métricas Prometheus `sirios_sql_query_duration_seconds` e `sirios_sql_rows_returned_total`, permitindo isolar tempo de SQL.【F:app/executor/pg.py†L25-L63】
- **Como provar:** Rodar `python scripts/diagnostics/run_ask_suite.py --suite-path data/ops/quality/routing_samples.json --base-url <api> --conversation-id X --client-id <doc> --explain` e capturar `meta.elapsed_ms` para essas perguntas, em paralelo coletar o histogram `sirios_sql_query_duration_seconds{entity="client_fiis_performance_vs_benchmark_summary"}` no Prometheus para o mesmo período. Se o histogram ≈ elapsed_ms, o custo é SQL; se muito menor, o overhead está em formatação/presenter.
- **Ação mínima:** Executar `EXPLAIN ANALYZE SELECT * FROM client_fiis_performance_vs_benchmark_summary WHERE document_number = '<doc>' AND benchmark_code = '<bm>' ORDER BY date_reference DESC LIMIT 1;` (ajustando parâmetros do plano) para verificar índices em `document_number`, `benchmark_code`, `date_reference` e confirmar se o custo vem do view ou pós-processamento.

## 6) Apêndice: trechos e comandos
- `scripts/diagnostics/run_ask_suite.py` (contadores de cache).【F:scripts/diagnostics/run_ask_suite.py†L236-L264】【F:scripts/diagnostics/run_ask_suite.py†L428-L438】
- `app/orchestrator/routing.py` (cache de métricas: requisitos, leitura, escrita, meta.compute).【F:app/orchestrator/routing.py†L277-L325】【F:app/orchestrator/routing.py†L720-L912】【F:app/orchestrator/routing.py†L922-L945】
- `app/api/ask.py` (short-circuit de cache de resposta e escrita).【F:app/api/ask.py†L335-L436】【F:app/api/ask.py†L550-L715】
- `app/cache/rt_cache.py` (plan hash e chaves).【F:app/cache/rt_cache.py†L268-L315】【F:app/cache/rt_cache.py†L376-L387】
- `data/policies/cache.yaml` (TTL/escopo/key_fields das entidades afetadas).【F:data/policies/cache.yaml†L30-L46】
- `data/ops/param_inference.yaml` (bindings de identifiers).【F:data/ops/param_inference.yaml†L268-L279】
- `data/ops/quality/routing_samples.json` (mapeamento das perguntas lentas para a entidade).【F:data/ops/quality/routing_samples.json†L125-L162】
- `app/executor/pg.py` (métricas de tempo de SQL).【F:app/executor/pg.py†L25-L63】
- Comandos executados (saídas resumidas):
  - `grep -nE "Cache hit|cache_hit|metrics|aggregate|analytics" scripts/diagnostics/run_ask_suite.py`
  - `grep -Rni "metrics_cache" app orchestrator` (filtros em `app/orchestrator/routing.py`)
  - `grep -Rni "plan_hash" app` + `nl` em `routing.py`, `rt_cache.py`, `ask.py`
  - `grep -Rni "carteira vs" data` e `nl data/ops/quality/routing_samples.json | sed -n '110,170p'`
