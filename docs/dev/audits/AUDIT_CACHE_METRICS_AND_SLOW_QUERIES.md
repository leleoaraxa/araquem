# Auditoria: Cache de Métricas e Consultas Lentas (/ask)

## 1) Resumo executivo
- O runner de diagnostics mede `cache_hit_response` e `cache_hit_metrics` lendo `meta.cache.hit` e `meta.compute.metrics_cache_hit` do payload do /ask.【F:scripts/diagnostics/run_ask_suite.py†L428-L438】
- O /ask é cache-first: um hit em Redis faz short-circuit, devolvendo o payload normalizado do cache e pulando `_fetch` (orchestrator + SQL + cache de métricas).【F:app/api/ask.py†L361-L437】
- As chaves de resposta usam `make_plan_cache_key(build_id, scope, entity, plan_hash)`, onde o `plan_hash` é uma fingerprint do plano gerada pela função de cache e usada na chave de resposta; os componentes considerados são definidos pela própria função de fingerprint, e `conversation_id` não participa.【F:app/cache/rt_cache.py†L268-L315】【F:app/cache/rt_cache.py†L376-L387】
- As perguntas mais lentas listadas no `routing_samples.json` roteiam para `client_fiis_performance_vs_benchmark_summary` (TTL 900s, scope prv); o único timer no payload é `meta.elapsed_ms`, e o executor exporta `sirios_sql_query_duration_seconds`.【F:data/ops/quality/routing_samples.json†L125-L162】【F:data/policies/cache.yaml†L38-L46】【F:app/executor/pg.py†L25-L63】
- O runner sempre chama `/ask?explain=true` (URL fixa), então não há flag `--explain` no CLI; usar suites válidas (`*_suite.json`) ou perguntas extraídas do `routing_samples.json` para medir `meta.elapsed_ms` e, se necessário, cruzar com as métricas do executor.【F:scripts/diagnostics/run_ask_suite.py†L51-L69】【F:scripts/diagnostics/run_ask_suite.py†L600-L665】

## 2) Cache de metrics (hipótese → evidência → como provar → ação mínima)
- **Hipótese:** O runner registra 0% porque lê `meta.compute.metrics_cache_hit`, mas o orchestrator só calcula chave de métricas quando existem `ticker`, `agg_params.metric` e janela normalizada; as perguntas de carteira vs benchmark não preenchem `metric`/`window`.
- **Evidência:** O runner extrai `cache_hit_metrics = _safe_get(resp, "meta.compute.metrics_cache_hit")`.【F:scripts/diagnostics/run_ask_suite.py†L428-L438】 O orchestrator só monta contexto de cache de métricas se achar `ticker`, `metric_key` e `window_norm`; sem isso retorna `None` e não tenta cachear.【F:app/orchestrator/routing.py†L277-L325】
- **Como provar:** Rodar perguntas que populam `agg_params.metric` (ex.: suites compute-on-read) com o runner (que já usa `/ask?explain=true`) e comparar primeira vs segunda execução: `meta.compute.metrics_cache_hit` deve virar `true` quando a chave for elegível; repetir com uma pergunta de carteira vs benchmark e observar que permanece `false`.
- **Ação mínima:** Anotar no diagnóstico que `cache_hit_metrics` só é interpretável para entidades com `metric` + `window_norm`; se `meta.compute` vier ausente, tratar como “não aplicável” em vez de erro.

## 3) Cache de response e short-circuit (hipótese → evidência → como provar → ação mínima)
- **Hipótese:** Quando `meta.cache.hit` é `true`, o /ask responde o valor normalizado do Redis e não chama `_fetch`, logo nem o orchestrator nem o executor rodam.
- **Evidência:** O /ask tenta ler `make_plan_cache_key(...)`; se `cache_hit` ficar `true`, usa `cached_value` normalizado e pula `_fetch`, só partindo para `_fetch` quando `cache_hit` é falso.【F:app/api/ask.py†L361-L437】
- **Como provar:** Executar a mesma pergunta duas vezes com os mesmos parâmetros pelo runner; na segunda execução, `meta.cache.hit` deve vir `true`, `cache_get_outcome=hit` no log e não aparece latência do executor (`sirios_sql_query_duration_seconds`) no intervalo observado.
- **Ação mínima:** Documentar no relatório que `metrics_cache_hit=false` em resposta cacheada não significa ausência de cache de métricas; significa apenas que a rota não foi executada.

## 4) Chaves / Key building
- **Padrão observado vs código:** As chaves vistas no Redis seguem `araquem:dev-20251030:cfg-<hash>:<pub|prv>:<entity>:plan:<hash>`. O código gera um `plan_hash` que funciona como fingerprint do plano e monta a chave com `make_plan_cache_key(build_id, scope, entity, plan_hash)`, o que explica o segmento `cfg-<hash>:<scope>:<entity>:plan:<hash>` observado.【F:app/cache/rt_cache.py†L268-L315】【F:app/cache/rt_cache.py†L376-L387】
- **Campos que entram:** identifiers (ex.: `document_number`, `benchmark_code`, `date_reference`), `agg_params`, flags e métricas solicitadas entram no `plan_hash`; `conversation_id` não entra, e `client_id` só entra se tiver sido copiado para identifiers (não há uso direto fora do plano).【F:app/cache/rt_cache.py†L268-L315】
- **Cache de métricas:** quando elegível, a chave usa `make_cache_key(build_id, scope, entity, cache_identifiers)` com `metric_key` e `window_norm`; TTL e scope vêm da policy (`client_fiis_performance_vs_benchmark_summary`: ttl 900s, scope prv).【F:app/orchestrator/routing.py†L277-L325】【F:app/cache/rt_cache.py†L376-L381】【F:data/policies/cache.yaml†L38-L46】

## 5) Top 5 queries lentas (hipótese → evidência → como provar → ação mínima)
- **Perguntas mapeadas → entidade:** As cinco listadas (“Carteira vs IFIX no fechamento…”, “Excesso de retorno… última data”, “Performance … IBOV (resumo)”, “Performance carteira vs IBOV até agora (visão resumida)”, “Resumo carteira vs CDI D-1”) têm `expected_entity = client_fiis_performance_vs_benchmark_summary` no `routing_samples.json`.【F:data/ops/quality/routing_samples.json†L125-L162】 A policy da entidade define TTL 900s e scope `prv`.【F:data/policies/cache.yaml†L38-L46】
- **Custo visível:** O payload só expõe `meta.elapsed_ms` (pipeline completo do orchestrator).【F:app/orchestrator/routing.py†L922-L945】 O executor exporta `sirios_sql_query_duration_seconds` e `sirios_sql_rows_returned_total`, permitindo medir o tempo de SQL separadamente.【F:app/executor/pg.py†L25-L63】
- **Como provar:** Extrair as perguntas do `routing_samples.json` (ver Apêndice) e rodá-las com o runner usando uma suite válida (`*_suite.json`) que as contenha ou convertendo as perguntas para um arquivo `--questions-file`; o runner já envia `/ask?explain=true`, então basta coletar `meta.elapsed_ms` e, no mesmo intervalo, ler o histogram `sirios_sql_query_duration_seconds{entity="client_fiis_performance_vs_benchmark_summary"}`. Se necessário, rodar `EXPLAIN ANALYZE` com os parâmetros do plano (benchmark, document_number, date_reference) extraídos do explain.
- **Ação mínima:** Registrar `meta.elapsed_ms` dessas perguntas e comparar com `sirios_sql_query_duration_seconds` para saber se o gargalo é SQL ou formatação; em seguida, executar `EXPLAIN ANALYZE` com os parâmetros reais antes de otimizar.

## 6) Apêndice: trechos e comandos
- `scripts/diagnostics/run_ask_suite.py` — URL fixa com `explain=true` e leitura de `cache_hit_response`/`cache_hit_metrics`.【F:scripts/diagnostics/run_ask_suite.py†L40-L69】【F:scripts/diagnostics/run_ask_suite.py†L428-L438】
- `app/api/ask.py` — leitura da chave de resposta e short-circuit quando `cache_hit` é verdadeiro.【F:app/api/ask.py†L361-L437】
- `app/cache/rt_cache.py` — fingerprint do plano (`plan_hash`) e construção da chave com `cfg-<hash>:<scope>:<entity>:plan:<hash>`.【F:app/cache/rt_cache.py†L268-L315】【F:app/cache/rt_cache.py†L376-L387】
- `data/ops/quality/routing_samples.json` — bloco das perguntas lentas mapeadas para `client_fiis_performance_vs_benchmark_summary`.【F:data/ops/quality/routing_samples.json†L125-L162】
- Comandos executados (saídas resumidas):
  - `grep -nE 'cache_hit_response|cache_hit_metrics|meta\\.cache\\.hit|meta\\.compute\\.metrics_cache_hit' scripts/diagnostics/run_ask_suite.py`
  - `sed -n '420,455p' scripts/diagnostics/run_ask_suite.py` e `nl -ba` correspondente
  - `grep -Rni ':plan:' app | head` e `grep -Rni 'cfg-' app | head`
  - `nl -ba app/api/ask.py | sed -n '360,430p'`
  - `nl -ba app/cache/rt_cache.py | sed -n '260,340p'` e `sed -n '350,410p'`
  - `nl -ba data/ops/quality/routing_samples.json | sed -n '120,170p'`
