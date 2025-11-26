# 1. Arquitetura Geral do Araquem

* **Pipeline**: o endpoint `/ask` aciona o **Orchestrator** para extrair identificadores e construir SQL; o **Planner** avalia intents e entidades com normalização/tokenização, aplica fusão com RAG e thresholds; o **Builder** gera SELECT determinístico a partir dos contratos YAML; o **Executor** (Postgres) executa a query com tracing/metrics; o **Formatter** aplica formatação declarativa e templates; o **Presenter** consolida facts, baseline determinístico e Narrator; o **Narrator** (opcional) decide uso de LLM ou modo determinístico; o retorno inclui meta e answer para o cliente.【F:app/api/ask.py†L38-L178】【F:app/orchestrator/routing.py†L90-L225】【F:app/builder/sql_builder.py†L1-L197】【F:app/executor/pg.py†L10-L52】【F:app/formatter/rows.py†L1-L118】【F:app/presenter/presenter.py†L19-L285】
* **Explain-mode**: o Planner sempre monta `decision_path` (tokenize→rank→route) com `signals` (token/phrase/anti_hits, weights), `fusion` e `rag` (hints, re-rank, context). `thresholds_applied` registra min_score/min_gap/gap/source/accepted. Quando `/ask?explain=true` ativa, as métricas de explain são emitidas e o payload é persistido em `explain_events` com `request_id`.【F:app/planner/planner.py†L98-L358】【F:app/api/ask.py†L48-L114】【F:app/orchestrator/routing.py†L400-L475】
* **RAG/decision signals**: fusão linear/re-rank combina score base e hints de entidades (`fusion.weight`, `rag_signal`, `combined`). `rag_context` guarda snippets filtrados por tokens do intent vencedor e é anexado ao explain e ao Presenter/Narrator. Thresholds podem operar em score base ou final (`apply_on`).【F:app/planner/planner.py†L187-L358】【F:app/presenter/presenter.py†L185-L285】
* **Contexto conversacional (M12)**: o `context_manager.py` mantém histórico curto de turns e o Presenter injeta `history` no meta do Narrator. As policies em `data/policies/context.yaml` controlam se o contexto está ativo; por padrão está **desligado** para não interferir no baseline enquanto os quality gates não forem consolidados.
* **Observabilidade**: runtime inicializa OTEL (OTLP gRPC), Prometheus exporters e schemas canônicos. Métricas cobrem HTTP, Planner, cache, SQL, RAG, Narrator e quality. Traces incluem atributos de rota/SQL/request_id; explain usa `trace_id` como `request_id`. Grafana/Prometheus/Tempo são previstos via configs em `data/ops/observability.yaml` e docker-compose stack (Prometheus, Grafana, Tempo, OTEL collector).【F:app/observability/runtime.py†L15-L118】【F:app/observability/metrics.py†L1-L112】【F:docker-compose.yml†L1-L90】

# 2. Estado Atual dos Módulos

## 2.1 Planner

* **Intent scoring**: normaliza (lower/strip_accents/strip_punct), tokeniza por `\b`, soma pesos para tokens/phrases include e penaliza excludes/anti_tokens. Mantém `details` por intent e `weights_summary`.【F:app/planner/planner.py†L65-L186】
* **Thresholds reais**: `_load_thresholds` lê `data/ops/planner_thresholds.yaml` (defaults min_score=1.0, min_gap=0.5, apply_on base; per-intent/entity overrides). Gate avalia `score_for_gate` e `gap` (base ou final se re-rank). `chosen.accepted` expõe resultado.【F:app/planner/planner.py†L20-L58】【F:app/planner/planner.py†L320-L358】
* **RAG fusion**: controla via YAML (`planner.rag`). Se habilitado, busca embeddings, gera `entity_hints` e funde scores (blend/additive) com peso `rag_weight` ou `re_rank.weight`. Blocos `fusion`, `scoring.final_combined`, `rag_signal` e `rag_hint` expõem números.【F:app/planner/planner.py†L187-L318】
* **Explain data model**: `explain` inclui `signals`, `decision_path`, `scoring` (intent/entity, gaps base/final, combined, thresholds_applied, rag_signal/hint), `rag` (config/used/error), `rag_context` (doc/snippets/reason), `fusion` (enabled/used/weight/mode/affected/error). `/ask?explain=true` também registra analytics com `planner_output` e métricas de latência/cache.【F:app/planner/planner.py†L187-L358】【F:app/api/ask.py†L48-L114】

## 2.2 RAG

* **context_builder**: `build_context` aplica política `data/policies/rag.yaml` (routing.allow_intents/deny_intents, entities/default/profiles). Resolve collections, max_chunks/min_score/max_tokens, usa embeddings search determinístico e normaliza chunks (texto, score, doc_id, collection). Desabilita quando não permitido ou erro, retornando `enabled=False` e motivo.【F:app/rag/context_builder.py†L1-L179】【F:data/policies/rag.yaml†L1-L80】
* **entity_hints**: Planner lê store via `cached_embedding_store`, gera vetor com `OllamaClient.embed` e converte resultados em hints por entidade (`entity_hints_from_rag`).【F:app/planner/planner.py†L187-L230】
* **RAG fusion & re-ranking**: peso definido em policy (`rag.weight` ou `re_rank.weight`); modos blend/additive ajustam score final; `fusion` bloco aponta `affected_entities` e erro. Re-rank flag controla se thresholds usam score final.【F:app/planner/planner.py†L240-L320】
* **Políticas**: `data/policies/rag.yaml` define profiles (default/macro/risk), roteamento por intent, collections por entidade e default seguro (concepts-fiis). Intents **negados** para RAG: domínios puramente numéricos/privados (FIIs SQL, posição de cliente). Intents **permitidos**: domínios textuais/explicativos (`fiis_noticias`, `fiis_financials_risk`, `history_market_indicators`, `history_b3_indexes`, `history_currency_rates`).

## 2.3 Formatter

* **Responsabilidade**: `render_rows_template` carrega `entity.yaml`→presentation.kind→template Jinja em `responses/{kind}.md.j2`, com campos key/value e empty_message. Protege path e falhas retornam string vazia.【F:app/formatter/rows.py†L1-L89】
* **Rows/Aggregates/Meta**: `format_rows` mantém colunas declaradas, aplica formatação decimal/data/percent/currency e métricas (`metric_key` em meta). Meta agregada fica em `aggregates` do orchestrator/presenter; requested_metrics lidas via ontology ask config.【F:app/formatter/rows.py†L90-L118】【F:app/orchestrator/routing.py†L280-L332】

## 2.4 Presenter

* **FactsPayload**: estrutura canônica com question/intent/entity/score/result_key/rows/primary/aggregates/identifiers/requested_metrics/ticker/fund e planner_score.【F:app/presenter/presenter.py†L19-L157】
* **PresentResult**: inclui answer, legacy_answer, rendered_template, narrator_meta, facts.【F:app/presenter/presenter.py†L59-L80】
* **Workflow determinístico**: sempre constrói facts, renderiza baseline determinístico via `render_answer` e `render_rows_template`, monta narrator_info (enabled/shadow/model/latency/error/used/strategy) e final_answer inicia como baseline.【F:app/presenter/presenter.py†L162-L226】
* **narrator_shadow/fallback/baseline/template**: quando Narrator retorna strategy `llm_shadow`, mantém baseline; erros retornam baseline com strategy `fallback_error`; template renderizado é retornado em PresentResult junto ao baseline.【F:app/presenter/presenter.py†L240-L285】
* **render_rows_template integração**: chamada após legacy_answer para gerar Markdown tabular conforme entity presentation; resultado exposto em `rendered_template`.【F:app/presenter/presenter.py†L204-L212】
* **render_answer integração**: baseline textual determinístico sempre computado e usado em fallback/shadow.【F:app/presenter/presenter.py†L204-L266】
* **Contexto conversacional**: Presenter injeta o `history` produzido pelo `context_manager` em `meta.narrator_context`, mas com `enabled: false` nas policies, evitando qualquer impacto enquanto baseline/quality não forem fechados.

## 2.5 Narrator

* **narrator.yaml**: carregado via `data/policies/narrator.yaml` (default/entidades, llm_enabled/shadow/model/max_llm_rows/use_rag_in_prompt etc.). Effective policy combina default + overrides, ignorando env para habilitação/shadow.【F:app/narrator/narrator.py†L85-L160】
* **Política de LLM**: `_should_use_llm` checa policy enabled e limites de linhas; render retorna baseline se desabilitado ou max_llm_rows <=0 ou rows>limite ou client indisponível. Tokens/latency/strategy registrados.【F:app/narrator/narrator.py†L121-L212】【F:app/narrator/narrator.py†L360-L460】
* **Shadow mode**: se `shadow=True`, estratégia final `llm_shadow` devolve baseline mas registra uso; Narrator_meta marca enabled/shadow/model/strategy e rag_ctx. LLM errors caem em `llm_failed` com baseline.【F:app/narrator/narrator.py†L360-L520】
* **Estado atual**: **LLM globalmente desligado** (`llm_enabled: false`, `shadow: false`, `max_llm_rows: 0`) para todas as entidades (incluindo risco, macro, índices e notícias). O sistema opera 100% determinístico.

## 2.6 Executor

* **SQL executor real**: `PgExecutor.query` usa psycopg, sanitiza SQL para tracing, abre trace span `executor.sql.execute`, seta atributos db.system/name/table/statement, executa com params e retorna dict rows. Emite métricas de duração e rows retornados; erros incrementam `sirios_sql_errors_total`. Usa DATABASE_URL.【F:app/executor/pg.py†L10-L52】
* **Views/Materialized views**: builder lê `entity.yaml` (`sql_view`, `result_key`, `columns`) e gera SELECT. Suporta métricas (UNION de SQLs), agregações (avg/sum/list/latest), filtros de período/default_date_field, multi-ticker e window months/count. Materialized views seguem `sql_view` declarado nos contratos (não há geração dinâmica).【F:app/builder/sql_builder.py†L1-L332】【F:app/builder/sql_builder.py†L332-L520】
* **Parâmetros inferidos**: `infer_params` fornece `agg_params` (agg/order/window/metric/limit/period); builder injeta em SQL (placeholders, window filters, metrics). Orchestrator normaliza janela e usa para cache key.【F:app/orchestrator/routing.py†L250-L332】【F:app/builder/sql_builder.py†L180-L332】

## 2.7 Observability

* **Métricas existentes**: catálogo inclui HTTP, planner (routed, explain, gaps, thresholds), cache, SQL, RAG (search/hits/context/re-rank), Narrator, explain persistence, quality. Facade valida labels e exporta via Prometheus client.【F:app/observability/metrics.py†L1-L112】【F:app/observability/runtime.py†L70-L152】
* **Counters/Histograms**: `emit_counter/emit_histogram/emit_gauge` normalizam labels; buckets padrão ms; exemplos: `sirios_planner_route_decisions_total`, `planner_rag_context_latency_ms`, `sirios_narrator_latency_ms`.【F:app/observability/metrics.py†L1-L112】【F:app/observability/runtime.py†L70-L152】
* **request_id/tracing**: `/ask` gera `request_id`; explain analytics usa `trace_id` do span. Tracing OTEL inicializado com OTLP exporter; spans para planner.route e executor.sql.execute incluem atributos de rota/cache/SQL.【F:app/api/ask.py†L38-L178】【F:app/orchestrator/routing.py†L330-L420】【F:app/executor/pg.py†L18-L52】【F:app/observability/runtime.py†L31-L90】
* **Integração OTEL**: `init_tracing` configura TracerProvider e BatchSpanProcessor para OTLP; docker-compose traz Tempo e otel-collector para backend de traces; Grafana dashboards previstos para quality e observability.【F:app/observability/runtime.py†L15-L90】【F:docker-compose.yml†L1-L90】【F:grafana/provisioning/dashboards/quality_dashboard.json†L1-L80】

# 3. Entidades

## 3.1 Visão geral

* **FIIs (domínio público)**
  `fiis_cadastro`, `fiis_precos`, `fiis_dividendos`, `fiis_imoveis`, `fiis_rankings`, `fiis_processos`, `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`, `fiis_noticias`.
* **Macro/Índices/Moedas (domínio público)**
  `history_b3_indexes`, `history_currency_rates`, `history_market_indicators`.
* **Cliente (domínio privado)**
  `client_fiis_positions`.

## 3.2 FIIs – resumo por entidade

* **fiis_cadastro (snapshot D-1)**
  Cadastro 1×1 de FIIs com identificadores (ticker, CNPJ, ISIN), nomes (display_name, b3_name), classificação/segmento, gestão, público-alvo, administrador/custodiante, pesos IFIX/IFIL e contagens de cotas/cotistas.

  * **Realidade dos dados**: snapshot D-1, sem histórico; ~416 FIIs.
  * **Chave**: `ticker`.
  * **RAG/Narrator**: RAG negado; Narrator off → respostas puramente SQL.

* **fiis_precos (histórica)**
  Série diária multi-ticker (open/close/adj_close/max/min/daily_variation_pct) com `default_date_field: traded_at`.

  * **Realidade dos dados**: histórica diária, multi-anos.
  * **Janelas**: configuradas em `param_inference` (3/6/12/24 meses e últimas N cotações).
  * **RAG/Narrator**: RAG negado; Narrator off.

* **fiis_dividendos (histórica)**
  Série histórica de proventos (`dividend_amt`, `payment_date`, `traded_until_date`; `default_date_field: payment_date`).

  * **Realidade dos dados**: histórico de eventos de proventos por FII.
  * **Janelas**: janela padrão 12 meses (`months:12`) com palavras-chave para últimos X meses/eventos.
  * **Importante**: entidade expõe **valores de dividendos**, não DY/yield (DY vem de snapshot/rankings).
  * **RAG/Narrator**: RAG negado; Narrator off.

* **fiis_financials_snapshot (snapshot D-1)**
  Foto diária por FII de métricas financeiras: DY mensal/12m, payout, P/VP, market cap, cap rate, alavancagem, caixa/passivos, patrimônio etc.; `default_date_field: updated_at`.

  * **Realidade dos dados**: snapshot D-1, ~415 FIIs, 1 linha por ticker.
  * **DY/yield**: principal fonte de **indicadores de yield** (DY corrente e 12m).
  * **RAG/Narrator**: RAG negado; Narrator off.

* **fiis_financials_revenue_schedule (snapshot D-1)**
  Cronograma de receitas por FII em buckets de prazo (0–3m, 3–6m, …, >36m).

  * **Realidade dos dados**: D-1, sem histórico; 1 linha por FII com percentuais em [0,1].
  * **Janelas**: **sem janelas temporais** (não é série histórica).
  * **RAG/Narrator**: RAG negado; Narrator off.

* **fiis_financials_risk (snapshot D-1)**
  Métricas de risco quantitativo (volatilidade, Sharpe, Treynor, Sortino, alfa de Jensen, beta, R², max drawdown), todas calculadas sobre janelas históricas pré-definidas, mas expostas como **foto D-1**.

  * **Realidade dos dados**: D-1, 1 linha por FII, sem histórico por FII na entidade.
  * **RAG**: permitido **apenas conceitual** (explicar o que é Sharpe, beta, etc.), nunca para números.
  * **Narrator**: overrides presentes, mas LLM off.

* **fiis_imoveis (snapshot D-1)**
  Lista de imóveis/unidades dos FIIs (tijolo/híbridos), com classe, endereço, área, unidades, vacância, inadimplência, status e timestamps.

  * **Realidade dos dados**: D-1; relação 1:N entre ticker e imóveis; múltiplos `updated_at`, mas sem histórico longitudinal.
  * **Chave natural**: `ticker + asset_name`.
  * **Aggregations**: habilitadas no YAML, mas **sem param_inference** (não há janelas históricas; usar apenas como lista/ordenado).
  * **RAG/Narrator**: RAG negado; Narrator off.

* **fiis_rankings (snapshot D-1)**
  Posições em múltiplos rankings (usuários, Sírios, IFIX, IFIL) e rankings quantitativos (DY 12m/mensal, dividendos 12m, market cap, patrimônio, Sharpe, Sortino, menor volatilidade, menor drawdown), com movimentos.

  * **Realidade dos dados**: D-1, 1 linha por FII; depende de materialized `fiis_rankings_quant`.
  * **DY/yield**: aqui o DY entra como **posição no ranking**, não como valor.
  * **RAG/Narrator**: RAG negado; Narrator off.

* **fiis_processos (snapshot D-1)**
  Lista de processos judiciais por FII, com número do processo, instância, julgamento, valores, partes, risco de perda (`loss_risk_pct`), fatos e análise de impacto.

  * **Realidade dos dados**: foto D-1 de `view_fiis_history_judicial`; 1 linha por processo.
  * **Chave natural**: `ticker + process_number`.
  * **RAG/Narrator**: RAG negado; Narrator off.

* **fiis_noticias (histórica textual)**
  Histórico de notícias/matérias por FII, com título, tags, descrição, URLs, imagens e timestamps.

  * **Realidade dos dados**: histórico textual por ticker (`ticker + published_at`).
  * **RAG**: permitido com collections `fiis_noticias`, `concepts-fiis`, `concepts-risk`, uso estritamente contextual.
  * **Quality**: freshness 30h + not_null para campos críticos; cache TTL 24h (D-1).

## 3.3 Macro / Índices / Moedas

* **history_currency_rates (histórica)**
  Série diária de câmbio USD/EUR em BRL (compra/venda) com variação percentual, `default_date_field: rate_date`.

  * **Realidade dos dados**: histórico multi-ano; 1 linha por data D-1 (USD+EUR).
  * **Quality/Cache**: ainda **sem bloco específico** em `quality.yaml` e `cache.yaml` (ponto de melhoria).
  * **RAG**: permitido no perfil `macro` (collection `concepts-macro`), apenas conceitual (o número continua 100% SQL).

* **history_b3_indexes (histórica)**
  Série diária de IBOV, IFIX e IFIL (pontos e variação diária), `default_date_field: index_date`.

  * **Realidade dos dados**: histórico 2021–2025; 1 linha por data.
  * **Observação de dados**: muitos zeros em variações e pontos de IFIL indicam necessidade de regra de qualidade/range.
  * **Quality/Cache**: ainda sem política específica; depende da materialized view e do refresh externo.
  * **RAG**: permitido (perfil `macro`), apenas para explicar conceitos de índices.

* **history_market_indicators (histórica)**
  Indicadores macroeconômicos (CDI, SELIC, poupança, IGP-M, etc.) por data (`indicator_date`, `indicator_name`, `indicator_amt`).

  * **Realidade dos dados**: série diária D-1 (amostra ~março–novembro/2025).
  * **Chave natural**: `indicator_date + indicator_name`.
  * **Quality/Cache**: sem bloco dedicado em `quality.yaml` e `cache.yaml`.
  * **RAG**: permitido (perfil `macro`) para explicação de conceitos; números continuam vindo do SQL.

## 3.4 Cliente (privado)

* **client_fiis_positions (snapshot D-1, PRIVADO)**
  Materialized view com a carteira de FIIs do cliente por data (`position_date`), por ticker/participante, derivada de `fc_fiis_portfolio(document_number)` sobre `equities_positions`.

  * **Realidade dos dados**: snapshot D-1; 1 linha por (`document_number`, `ticker`, `participant_name`, `position_date`).
  * **LGPD**: `document_number` **nunca aparece** na apresentação padrão (somente em nível de dados/SQL).
  * **Param inference**: `inference: false` + binding explícito `document_number: context.client_id`.
  * **Quality/Cache**: freshness 30 min; cache privado (`scope: prv`) com TTL 900s por (`document_number`, `position_date`, `ticker`).
  * **RAG/Narrator**: intent negada em RAG, Narrator off.

## 3.5 Mapa D-1 vs histórico (resumo mental)

* **Históricas (linha do tempo explícita)**
  `fiis_precos`, `fiis_dividendos`, `fiis_noticias`, `history_b3_indexes`, `history_currency_rates`, `history_market_indicators`.

* **Snapshots D-1 (foto do dia anterior, sem histórico na entidade)**
  `fiis_cadastro`, `fiis_imoveis`, `fiis_rankings`, `fiis_processos`, `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`, `client_fiis_positions`.

## 3.6 Notas sobre DY / yield e dividendos

* DY/yield **não** sai de `fiis_dividendos` (que traz apenas `dividend_amt` + datas).
* Os **valores de yield** atuais vêm de:

  * `fiis_financials_snapshot` → DY corrente / DY 12m por fundo (snapshot).
  * `fiis_rankings` → posições em rankings de DY (quem paga mais/menos, etc.).
* Implicação:

  * Perguntas de “**quanto é o DY**” devem ir para `fiis_financials_snapshot`.
  * Perguntas de “**quem são os top/bottom em DY**” devem ir para `fiis_rankings`.
  * `fiis_dividendos` serve para **histórico de pagamentos**, não para yield.

**Backlog conceitual** (não implementado ainda):

* Avaliar uma entidade futura de **yield histórico** (ex.: `fiis_yield_history`) para evitar recalcular DY em tempo real a partir de preços+dividendos em cada pergunta.

## 3.7 Novos compostos possíveis (joins SQL)

Sem alterar contratos atuais, o desenho das entidades permite construir respostas mais ricas via joins:

* **Ficha completa do FII**

  * Join: `fiis_cadastro` + `fiis_financials_snapshot` + `fiis_rankings`.
  * Entrega: CNPJ, setor, gestão, público-alvo, P/VP, DY, alavancagem, ranking relativo (DY, market cap, risco).

* **Painel de risco/retorno do FII**

  * Join: `fiis_financials_snapshot` + `fiis_financials_risk` + `fiis_rankings`.
  * Entrega: DY, volatilidade, Sharpe, Sortino, beta, max drawdown e posição em rankings de risco.

* **Visão consolidada da carteira do cliente**

  * Join: `client_fiis_positions` + `fiis_financials_snapshot` + `fiis_rankings`.
  * Entrega: quantidades, pesos na carteira, DY da carteira, top/bottom por risco/rentabilidade — tudo respeitando LGPD (sem vazar document_number).

Esses compostos podem ser atendidos:

* ou via **SQL parametrizado** direto pelo Builder (nova entidade no futuro),
* ou via **templates** que combinam múltiplas queries coordenadas pelo Orchestrator/Presenter.

# 4. Ontologia

* **Estrutura**: `data/ontology/entity.yaml` define normalize (lower/strip_accents/strip_punct), token_split `\b`, weights token/phrase e intents com tokens/phrases include/exclude, anti_tokens e entities associadas.【F:data/ontology/entity.yaml†L1-L120】
* **Synonyms/metrics_synonyms**: routing extrai métricas solicitadas comparando `ask.metrics_synonyms` de cada `entity.yaml` com pergunta normalizada; identifica métricas para formatter/presenter. (Mapa dentro de cada entidade via chave ask.metrics_synonyms).【F:app/orchestrator/routing.py†L30-L70】【F:app/orchestrator/routing.py†L470-L520】
* **Influência no routing**: planner usa intents do ontology para scoring e associação de entidades; normalização e tokenização controlam sensibilidade; anti_tokens penalizam. `extract_requested_metrics` usa synonyms para meta.requested_metrics, influenciando Narrator e formatação.【F:app/planner/planner.py†L98-L186】【F:app/orchestrator/routing.py†L30-L90】【F:app/presenter/presenter.py†L19-L157】
* **Interação RAG**: intents vencedores orientam filtros de snippets (tokens include) em `rag_context`, garantindo relevância semântica ao contextualizar Presenter/Narrator.【F:app/planner/planner.py†L300-L358】
* **Notas de intents para FIIs**: tokens de indicadores financeiros (payout, alavancagem, market cap, price book/PVP, DY/dy12m quando não forem ranking) resolvem via `fiis_financials_snapshot`; histórico de dividendos (`dividend_amt`) permanece em `fiis_dividendos`; rankings/comparações globais usam entidades como `fiis_rankings`.
* **Notas de dividendos / DY**: tokens de DY/yield foram removidos da intent `fiis_dividendos` (entidade só expõe dividend_amt); roteamento de yield permanece nos intents apropriados (`fiis_financials_snapshot` para valores, `fiis_rankings` para posições).

# 5. Explain Mode

* **Logs/payload**: `plan['explain']` contém `signals` (token_scores, phrase_scores, anti_hits, normalizations, weights_summary), `decision_path`, `scoring` (intent/entity, gaps base/final, combined/final_combined, rag_signal, rag_hint, thresholds_applied), `rag` (config/used/error), `fusion`, `rag_context` (doc/snippets/reason). `/ask?explain=true` adiciona `explain_analytics` com route_id/view/cache info e persiste em `explain_events` (intent/entity/route_id/sql_view/sql_hash/cache_policy/latency).【F:app/planner/planner.py†L187-L358】【F:app/api/ask.py†L48-L114】
* **Exemplo (reduzido)**: `decision_path`=[{stage:tokenize,value:<norm>,result:[...]},{stage:rank,type:intent_scoring,intent:<name>,score:<x>},{stage:route,type:entity_select,entity:<ent>,score_after:<x>}]; `thresholds_applied`={min_score:1.0,min_gap:0.5,gap:top2_gap,accepted:true,source:base}; `rag_context`={top_doc:<id>,snippets:[...],reason:"Contexto cita tokens..."}.【F:app/planner/planner.py†L98-L358】

# 6. Quality

* **quality_list_misses.py**: wrapper que chama `quality_diff_routing.py` para listar perguntas que falham nos quality gates comparando samples routing; usa arquivo `data/ops/quality/routing_samples.json` e grava misses em `data/ops/quality_experimental/routing_misses_via_ask.json`.【F:scripts/quality/quality_list_misses.py†L1-L40】
* **quality_push**: endpoint `/ops/quality/push` recebe payloads de amostras de roteamento, valida policy e registra métricas; scripts `quality_push.py` e `quality_push_cron.py` automatizam envio e verificações com tokens e quality gates. Dashboards Grafana gerados por `gen_quality_dashboard.py`.【F:app/api/ops/quality.py†L148-L420】【F:scripts/quality/quality_push.py†L1-L90】【F:scripts/quality/gen_quality_dashboard.py†L1-L160】
* **Baseline**: `quality_report` utiliza policy `data/policies/quality.yaml` ou fallback e expõe métricas de top1/gap/routed; scripts shell `quality_gate_check.sh` consultam API/Prometheus. Baseline determinístico do Presenter/Narrator garante comparação consistente em shadow/LLM. Prometheus coleta métricas `sirios_planner_top1_match_total`, `planner_quality_*`.【F:app/api/ops/quality.py†L480-L563】【F:app/observability/runtime.py†L70-L152】【F:app/presenter/presenter.py†L204-L285】
* **Cobertura atual de datasets**:

  * Com qualidade declarada: FIIs (`fiis_precos`, `fiis_dividendos`, `fiis_imoveis`, `fiis_processos`, `fiis_rankings`, `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`, `fiis_noticias`, `fiis_cadastro`, `client_fiis_positions`).
  * **Sem qualidade declarada ainda**: `history_currency_rates`, `history_b3_indexes`, `history_market_indicators` → precisam de freshness/ranges/TTLs para consolidar o domínio macro.

# 7. Caminho para Produção

## 7.1 O que já está pronto (estado 2025.0-prod – core)

* Pipeline `/ask` completo: Orchestrator → Planner → (RAG opcional) → Builder → Executor → Formatter → Presenter → Narrator, com explain-mode, tracing OTEL, métricas Prometheus e políticas declarativas (RAG, Narrator, Cache, Quality, Context).
* **Narrator**: modelo `sirios-narrator:latest` integrado, porém com LLM **desligado** (baseline 100% determinístico).
* **RAG**: políticas consolidadas em `data/policies/rag.yaml`, com:

  * deny_intents (FIIs numéricos, posições de cliente),
  * allow_intents textuais (`fiis_noticias`, `fiis_financials_risk` conceitual, macro, índices, câmbio),
  * profiles `default`, `macro`, `risk` e collections por entidade.
* **Entidades auditadas (bloco “1. Entidades & Realidade dos Dados”)**:

  * FIIs: `fiis_cadastro`, `fiis_precos`, `fiis_dividendos`, `fiis_imoveis`, `fiis_rankings`, `fiis_processos`, `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`, `fiis_noticias`.
  * Macro/Índices/Moedas: `history_currency_rates`, `history_b3_indexes`, `history_market_indicators`.
  * Cliente: `client_fiis_positions`.
    Cada uma com realidade de dados (D-1 vs histórico) entendida e registrada.
* **LGPD**: entidade `client_fiis_positions` configurada como privada (`private: true`), sem exposição de `document_number` no formatter, com binding seguro de `document_number` via `context.client_id` e cache escopado (`scope: prv`).

## 7.2 Pontos em aberto / próximos passos diretos

Alinhado ao checklist `CHECKLIST-2025.0-prod.md`:

1. **Entidades & dados**

   * Fechar bloco de entidades com:

     * regras de quality/cache para `history_currency_rates`, `history_b3_indexes`, `history_market_indicators`;
     * documentação clara de DY/yield (quem fornece valor, quem fornece ranking);
     * backlog explícito para possível entidade de yield histórico.
   * Explorar/registrar os **compostos SQL** (joins) entre entidades para responder perguntas mais ricas sem violar o design atual (ex.: ficha do FII, painel de risco, visão de carteira).

2. **Param inference & janelas**

   * Completar/ajustar `param_inference.yaml` para:

     * manter apenas janelas em entidades realmente históricas,
     * explicitar defaults para índices/macro (últimos 30/90/180 dias),
     * garantir que snapshots D-1 **não** tenham janelas inferidas.

3. **Quality & macro**

   * Adicionar datasets de quality para `history_currency_rates`, `history_b3_indexes`, `history_market_indicators` com:

     * freshness ~24h/30h,
     * `accepted_range` numérico positivo (>0 para taxas, limites para variações),
     * monitoramento de zeros/valores sentinela.

4. **Narrator & RAG (produção)**

   * Definir quais entidades poderão usar Narrator com LLM habilitado (provavelmente: conceitos de risco, macro, notícias; nunca números/posição cliente).
   * Ajustar `narrator.yaml` para modo shadow em produção (max_llm_rows baixo, prompts restritos, uso opcional de RAG no prompt).

5. **Contexto conversacional**

   * Ativar contexto apenas após baseline verde, começando por intents que se beneficiam de referência ao “fundo anterior” (ex.: “esse Sharpe está bom comparado ao anterior?”).
   * Garantir que o contexto não altere SQL ou números — só narrativa.

6. **Quality gates & explain**

   * Revisar os 16 misses, rodar novamente `quality_list_misses.py` e `quality_diff_routing.py` em modo sem Ollama.
   * Fixar baseline “2025.0-prod” nos YAMLs (quality, thresholds, ontologia, entities).

7. **Infra & observabilidade**

   * Consolidar configs reais de produção (DATABASE_URL, OTEL Collector, Prometheus, Grafana, Tempo).
   * Ajustar Redis com política de TTL/namespace blue-green.
   * Fechar dashboards finais `/ask`, Planner, RAG, Narrator, quality.

8. **Documentação**

   * Manter este `ARAQUEM_STATUS_2025.md` como fonte viva do “onde estamos e para onde vamos”.
   * Sincronizar com o `CHECKLIST-2025.0-prod.md` sempre que novos marcos forem concluídos.

---
