# 1. Arquitetura Geral do Araquem

* **Pipeline**: o endpoint `/ask` aciona o **Orchestrator** para extrair identificadores e construir SQL; o **Planner** avalia intents e entidades com normalização/tokenização, aplica fusão com RAG e thresholds; o **Builder** gera SELECT determinístico a partir dos contratos YAML; o **Executor** (Postgres) executa a query com tracing/metrics; o **Formatter** aplica formatação declarativa e templates; o **Presenter** consolida facts, baseline determinístico e Narrator; o **Narrator** (opcional) decide uso de LLM ou modo determinístico; o retorno inclui meta e answer para o cliente.【F:app/api/ask.py†L38-L178】【F:app/orchestrator/routing.py†L90-L225】【F:app/builder/sql_builder.py†L1-L197】【F:app/executor/pg.py†L10-L52】【F:app/formatter/rows.py†L1-L118】【F:app/presenter/presenter.py†L19-L285】
* **Explain-mode**: o Planner sempre monta `decision_path` (tokenize→rank→route) com `signals` (token/phrase/anti_hits, weights), `fusion` e `rag` (hints, re-rank, context). `thresholds_applied` registra min_score/min_gap/gap/source/accepted. Quando `/ask?explain=true` ativa, as métricas de explain são emitidas e o payload é persistido em `explain_events` com `request_id`.【F:app/planner/planner.py†L98-L358】【F:app/api/ask.py†L48-L114】【F:app/orchestrator/routing.py†L400-L475】
* **RAG/decision signals**: fusão linear/re-rank combina score base e hints de entidades (`fusion.weight`, `rag_signal`, `combined`). `rag_context` guarda snippets filtrados por tokens do intent vencedor e é anexado ao explain e ao Presenter/Narrator. Thresholds podem operar em score base ou final (`apply_on`).【F:app/planner/planner.py†L187-L358】【F:app/presenter/presenter.py†L185-L285】
* **Contexto conversacional (M12)**: o `context_manager.py` mantém histórico curto de turns e o Presenter injeta `history` no meta do Narrator. As policies em `data/policies/context.yaml` deixam o contexto **habilitado** (planner/narrator ON, max_turns e limites de tamanho) e controlam entidades permitidas, mantendo proteção para domínios privados/macros enquanto os quality gates não forem consolidados.
* **Observabilidade**: runtime inicializa OTEL (OTLP gRPC), Prometheus exporters e schemas canônicos. Métricas cobrem HTTP, Planner, cache, SQL, RAG, Narrator e quality. Traces incluem atributos de rota/SQL/request_id; explain usa `trace_id` como `request_id`. Grafana/Prometheus/Tempo são previstos via configs em `data/ops/observability.yaml` e docker-compose stack (Prometheus, Grafana, Tempo, OTEL collector).【F:app/observability/runtime.py†L15-L118】【F:app/observability/metrics.py†L1-L112】【F:docker-compose.yml†L1-L90】

# 2. Estado Atual dos Módulos

## 2.1 Planner

* **Intent scoring**: normaliza (lower/strip_accents/strip_punct), tokeniza por `\b`, soma pesos para tokens/phrases include e penaliza excludes/anti_tokens. Mantém `details` por intent e `weights_summary`.【F:app/planner/planner.py†L65-L186】
* **Thresholds reais**: `_load_thresholds` lê `data/ops/planner_thresholds.yaml` (defaults min_score=0.8, min_gap=0.1, apply_on=fused; overrides por família): compostas `dividendos_yield` / `carteira_enriquecida` / `macro_consolidada` usam **min_score 0.9 / min_gap 0.2**; risco `fiis_financials_risk` usa **0.85 / 0.2**; históricas numéricas `fiis_precos` / `fiis_dividendos` e `fiis_yield_history` usam **0.9 / 0.15**; snapshots numéricos `fiis_imoveis` / `fiis_processos` usam **0.85 / 0.1**. Gate avalia `score_for_gate` e `gap` (base ou final se re-rank). `chosen.accepted` expõe resultado.【F:app/planner/planner.py†L20-L58】【F:app/planner/planner.py†L320-L358】
* **RAG fusion**: controla via YAML (`planner.rag`). Se habilitado, busca embeddings, gera `entity_hints` e funde scores (blend/additive) com peso `rag_weight` ou `re_rank.weight`. Blocos `fusion`, `scoring.final_combined`, `rag_signal` e `rag_hint` expõem números.【F:app/planner/planner.py†L187-L318】
* **Explain data model**: `explain` inclui `signals`, `decision_path`, `scoring` (intent/entity, gaps base/final, combined/final_combined, rag_signal, rag_hint, thresholds_applied), `rag` (config/used/error), `fusion`, `rag_context` (doc/snippets/reason). `/ask?explain=true` também registra analytics com `planner_output` e métricas de latência/cache.【F:app/planner/planner.py†L187-L358】【F:app/api/ask.py†L48-L114】

## 2.2 RAG

* **context_builder**: `build_context` aplica política `data/policies/rag.yaml` (routing.allow_intents/deny_intents, entities/default/profiles). Resolve collections, max_chunks/min_score/max_tokens, usa embeddings search determinístico e normaliza chunks (texto, score, doc_id, collection). Desabilita quando não permitido ou erro, retornando `enabled=False` e motivo.【F:app/rag/context_builder.py†L1-L179】【F:data/policies/rag.yaml†L1-L120】
* **entity_hints**: Planner lê store via `cached_embedding_store`, gera vetor com `OllamaClient.embed` e converte resultados em hints por entidade (`entity_hints_from_rag`).【F:app/planner/planner.py†L187-L230】
* **RAG fusion & re-ranking**: peso definido em policy (`rag.weight` ou `re_rank.weight`); modos blend/additive ajustam score final; `fusion` bloco aponta `affected_entities` e erro. Re-rank flag controla se thresholds usam score final.【F:app/planner/planner.py†L240-L320】
* **Políticas**: `data/policies/rag.yaml` define profiles (default/macro/risk) com weights atualizados e roteamento por intent/entidade. RAG **permitido** somente para intents textuais/explicativos (`fiis_noticias`), risco conceitual (`fiis_financials_risk` com restrição estrita a explicações, sem números vindos do RAG) e domínios macro/índices/moedas (`history_market_indicators`, `history_b3_indexes`, `history_currency_rates`). RAG **negado** para todas as entidades numéricas (históricas e snapshots), entidades privadas, overview consolidado e compostas (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`). Comentários explicam o racional de cada deny/allow e o mapeamento de profiles default/macro/risk.

## 2.3 Formatter

* **Responsabilidade**: `render_rows_template` carrega `entity.yaml`→presentation.kind→template Jinja em `responses/{kind}.md.j2`, com campos key/value e empty_message. Protege path e falhas retornam string vazia.【F:app/formatter/rows.py†L1-L89】
* **Rows/Aggregates/Meta**: `format_rows` mantém colunas declaradas, aplica formatação decimal/data/percent/currency e métricas (`metric_key` em meta). Meta agregada fica em `aggregates` do orchestrator/presenter; requested_metrics lidas via ontology ask config.【F:app/formatter/rows.py†L90-L118】【F:app/orchestrator/routing.py†L280-L332】
* **Estado atual**: templates `responses/*.md.j2` estão sendo gradualmente “humanizados” (ex.: `fiis_financials_risk`) para respostas mais amigáveis, ainda 100% determinísticas.

## 2.4 Presenter

* **FactsPayload**: estrutura canônica com question/intent/entity/score/result_key/rows/primary/aggregates/identifiers/requested_metrics/ticker/fund e planner_score.【F:app/presenter/presenter.py†L19-L157】
* **PresentResult**: inclui answer, legacy_answer, rendered_template, narrator_meta, facts.【F:app/presenter/presenter.py†L59-L80】
* **Workflow determinístico**: sempre constrói facts, renderiza baseline determinístico via `render_answer` e `render_rows_template`, monta narrator_info (enabled/shadow/model/latency/error/used/strategy) e final_answer inicia como baseline.【F:app/presenter/presenter.py†L162-L226】
* **narrator_shadow/fallback/baseline/template**: quando Narrator retorna strategy `llm_shadow`, mantém baseline; erros retornam baseline com strategy `fallback_error`; template renderizado é retornado em PresentResult junto ao baseline.【F:app/presenter/presenter.py†L240-L285】
* **render_rows_template integração**: chamada após legacy_answer para gerar Markdown tabular conforme entity presentation; resultado exposto em `rendered_template`.【F:app/presenter/presenter.py†L204-L212】
* **render_answer integração**: baseline textual determinístico sempre computado e usado em fallback/shadow.【F:app/presenter/presenter.py†L204-L266】
* **Contexto conversacional**: Presenter injeta o `history` produzido pelo `context_manager` em `meta.narrator_context`, respeitando policies habilitadas (planner/narrator ON, limites de turns/charset) e a lista de entidades permitidas, mantendo proteção para domínios privados/macros enquanto baseline/quality não forem fechados.

## 2.5 Narrator

* **narrator.yaml**: carregado via `data/policies/narrator.yaml` (default/entidades, llm_enabled/shadow/model/max_llm_rows/use_rag_in_prompt etc.). Effective policy combina default + overrides, ignorando env para habilitação/shadow.【F:app/narrator/narrator.py†L85-L160】
* **Política de LLM**: `_should_use_llm` checa policy enabled e limites de linhas; render retorna baseline se desabilitado ou max_llm_rows <=0 ou rows>limite ou client indisponível. Tokens/latency/strategy registrados.【F:app/narrator/narrator.py†L121-L212】【F:app/narrator/narrator.py†L360-L460】
* **Shadow mode**: se `shadow=True`, estratégia final `llm_shadow` devolve baseline mas registra uso; Narrator_meta marca enabled/shadow/model/strategy e rag_ctx. LLM errors caem em `llm_failed` com baseline.【F:app/narrator/narrator.py†L360-L520】
* **Estado atual**: **LLM globalmente desligado** (`llm_enabled: false`, `shadow: false`, `max_llm_rows: 0`) para todas as entidades (incluindo risco, macro, índices, notícias, compostas e entidades privadas de carteira). Overrides por entidade existem, mas todos com LLM OFF; o sistema opera 100% determinístico.

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

Hoje o Araquem trabalha com **21 entidades canônicas**:

* **FIIs (domínio público)**
  `fiis_cadastro`, `fiis_precos`, `fiis_dividendos`, `fiis_yield_history`, `fii_overview`,
  `fiis_imoveis`, `fiis_rankings`, `fiis_processos`,
  `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`,
  `fiis_noticias`,
  `dividendos_yield` (composta, pública).

* **Macro/Índices/Moedas (domínio público)**
  `history_b3_indexes`, `history_currency_rates`, `history_market_indicators`,
  `macro_consolidada` (composta, pública).

* **Cliente (domínio privado)**
  `client_fiis_positions`,
  `client_fiis_dividends_evolution`,
  `client_fiis_performance_vs_benchmark`,
  `carteira_enriquecida` (composta, privada).

Todas elas aparecem no catálogo em `data/entities/catalog.yaml` com paths para `entity.yaml`, schema, projection de quality (quando existe) e flags de cobertura (cache, RAG, Narrator, param_inference, ontologia).

## 3.2 FIIs – resumo por entidade (pontos-chave)

### fiis_dividendos (histórica)

* Entidade histórica de proventos (`dividend_amt`, datas, ticker).
* **Não** responde perguntas de DY/yield – isso foi limpo da ontologia para evitar confusão.
* `param_inference` cuida de janelas (meses / últimos N pagamentos).

### fiis_yield_history (histórica)

* Entidade histórica com evolução mensal de yield:

  * `ref_month`, `dividends_sum`, `dy_monthly`, `price_ref` etc.
* Alvo natural para perguntas:

  * “histórico de dividend yield do MXRF11 nos últimos 12 meses”
  * “evolução do DY do KNRI11”
  * “comparativo de DY mensal entre HGLG11 e VISC11”
* Tem schema, projection de quality (`projection_fiis_yield_history_evolution.json`) e routing samples dedicados.

### dividendos_yield (composta, histórica, pública)

* **Nova entidade pública composta**: junta dividendos históricos + DY mensal/12m por FII.
* View: `public.dividendos_yield`.
* Colunas típicas: `ticker`, `ref_month`, `dividend_amt`, `dy_monthly`, `dy_12m_pct`.
* Alvo natural para perguntas que pedem **“dividendos e DY” juntos**, por exemplo:

  * “histórico de dividendos e DY do MXRF11 nos últimos 12 meses”
  * “quanto o HGLG11 pagou de dividendos e qual foi o DY em 2024-08”
* Políticas:

  * **cache**: público;
  * **RAG**: deny;
  * **Narrator**: off;
  * **inferência temporal**: habilitada (janelas históricas por mês / 12m).

### fiis_financials_snapshot (snapshot D-1)

* Fonte principal de **DY atual** (mensal/12m) e indicadores financeiros (market cap, cap rate, alavancagem, payout, etc.).
* Tokens de DY na ontologia apontam aqui (valor) ou para `fiis_rankings` (posição em ranking).

### fiis_financials_revenue_schedule (snapshot D-1)

* Estrutura de **receitas futuras** por bucket de prazo (0–3m, 3–6m, …, >36m) e por indexador (IPCA, IGPM, INPC, INCC).
* Quality com `accepted_range` para todos os percentuais (incluindo indexadores).
* RAG e Narrator **negados** – resposta sempre tabular/determinística.
* Tem projection própria (`projection_fiis_financials_revenue_schedule.json`) e routing samples, incluindo perguntas como
  “como está distribuída a receita futura do MXRF11 por índice”.

### fiis_financials_risk (snapshot D-1)

* Métricas de risco: volatilidade, Sharpe, Sortino, Treynor, Jensen alpha, beta, MDD, R².
* RAG permitido apenas para **explicação conceitual** (collections `concepts-risk`, `concepts-fiis`); números vêm sempre do SQL.
* Ontologia bem enriquecida para perguntas de Sharpe/beta/MDD etc.
* Templates em `responses/summary.md.j2` humanizados para explicar as métricas.

### fiis_cadastro, fiis_imoveis, fiis_rankings, fiis_processos, fiis_noticias, fiis_precos

* Mesma visão da versão anterior, com ajustes na ontologia para reduzir colisões:

  * Notícias negativas/recentes vão para `fiis_noticias` e não para preços.
  * Perguntas de “histórico do dólar” e “histórico do IPCA” não caem em `fiis_precos`.

### fii_overview (snapshot D-1)

* Visão consolidada D-1 por FII:

  * Combina cadastro, snapshot financeiro, indicadores de risco e rankings em uma “ficha executiva”.
* Indicadores-chave:

  * DY mensal/12m, dividendos 12m, último dividendo, datas de pagamento,
  * market cap, EV, P/BV, PL por cota, receita por cota, payout, cap rate, alavancagem,
  * métricas de risco (volatilidade, Sharpe, Sortino, MDD, beta, R²),
  * rankings (popularidade, IFIX/IFIL, DY, risco).
* Alvo natural para:

  * “resumo do HGLG11”
  * “overview do KNRI11”
  * “como está o MXRF11 hoje?”
* RAG negado; Narrator off; resposta 100% SQL + templates.

## 3.3 Macro / Índices / Moedas

* **history_currency_rates (histórica)**

  * Histórico multi-ano de USD/EUR em BRL (compra/venda).
  * Ontologia cobre “histórico do dólar”, “variação do dólar nos últimos 12 meses” etc.
  * Quality: freshness 30h, taxas >0, faixas realistas.

* **history_b3_indexes (histórica)**

  * Índices da B3 (IBOV, IFIX, IFIL) com pontos e variação.
  * Quality consolidado com faixas para variações diárias.

* **history_market_indicators (histórica)**

  * IPCA, CDI, Selic, IGP-M, INCC, INPC etc.
  * Ontologia captura “histórico do IPCA”, “série histórica da inflação”.
  * Quality controla faixa de `indicator_amt`.

* **macro_consolidada (composta, histórica, pública)**

  * **Nova entidade macro consolidada** que une IPCA/SELIC/CDI, IFIX/IBOV e câmbio em uma mesma visão canônica.
  * View: `public.macro_consolidada`.
  * Uso típico:

    * “IPCA e Selic em 2025-11-12”;
    * “IFIX e IBOV do dia 2025-11-14”;
    * consultas macro consolidadas por data/período.
  * Políticas:

    * **cache**: público;
    * **RAG**: deny (somente números SQL);
    * **Narrator**: off;
    * **janelas históricas**: habilitadas (inferência temporal ligada no builder/param_inference).

## 3.4 Cliente (privado)

* **client_fiis_positions (snapshot D-1, PRIVADO)**

  * Materialized view com carteira de FIIs do cliente (document_number, data, ticker, qty, PM, % carteira etc.).
  * `document_number` nunca aparece na apresentação; binding via `context.client_id`.
  * RAG negado; Narrator off; quality com freshness 30min.

* **client_fiis_dividends_evolution (histórica agregada, PRIVADO)**

  * Evolução mensal dos dividendos da carteira (`year_reference`, `month_number`/`month_name`, `total_dividends`).
  * Perguntas típicas:

    * “evolução dos dividendos da minha carteira de FIIs”
    * “renda mensal dos meus FIIs”
    * “minha renda mensal com FIIs está crescendo?”
  * `document_number` vem **exclusivamente** de contexto seguro (`context.client_id` via `param_inference`); nunca do texto.
  * RAG e Narrator negados; resposta determinística.
  * Tem schema, projection (`projection_client_fiis_dividends_evolution.json`), quality dataset e routing samples.

* **client_fiis_performance_vs_benchmark (histórica, PRIVADO)**

  * Série temporal de valor/retorno da carteira de FIIs vs. benchmark (IFIX, IFIL, IBOV, CDI).
  * Campos: `portfolio_amount`, `portfolio_return_pct`, `benchmark_value`, `benchmark_return_pct`, `benchmark_code`.
  * Perguntas típicas:

    * “minha carteira de FIIs está melhor ou pior que o CDI?”
    * “performance da minha carteira de FIIs versus o IFIX nos últimos 12 meses”
  * Mesmo modelo de segurança:

    * `document_number` bindado via `context.client_id`;
    * RAG/Narrator negados; SQL puro; LGPD respeitada.
  * Tem schema, projection (`projection_client_fiis_performance_vs_benchmark.json`), quality dataset e routing samples.

* **carteira_enriquecida (composta, snapshot D-1, PRIVADO)**

  * **Nova entidade privada composta** com posição enriquecida do cliente: junta posições, cadastro, risco, DY e rankings por FII da carteira.
  * View: `public.carteira_enriquecida`.
  * Binding: `document_number: context.client_id` (nunca vem do texto).
  * Perguntas alvo:

    * “valor investido em MXRF11 na carteira”;
    * “DY mensal dos meus FIIs”;
    * “ranking de Sharpe dos meus FIIs na carteira”.
  * Políticas:

    * **cache**: privado;
    * **RAG**: deny;
    * **Narrator**: off;
    * **inferência temporal**: desabilitada (foto D-1 da carteira).

## 3.5 Mapa D-1 vs histórico (resumo mental)

* **Históricas (linha do tempo explícita)**
  `fiis_precos`, `fiis_dividendos`, `fiis_yield_history`, `fiis_noticias`,
  `history_b3_indexes`, `history_currency_rates`, `history_market_indicators`,
  `client_fiis_dividends_evolution`, `client_fiis_performance_vs_benchmark`,
  `dividendos_yield`, `macro_consolidada`.

* **Snapshots D-1 (foto do dia anterior, sem histórico na entidade)**
  `fiis_cadastro`, `fiis_imoveis`, `fiis_rankings`, `fiis_processos`,
  `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`,
  `fii_overview`, `client_fiis_positions`, `carteira_enriquecida`.

## 3.6 Notas sobre perguntas conceituais “sem ticker”

* Perguntas conceituais gerais (ex.: “o que significa Sharpe negativo?”, “o que é Max Drawdown?”) **não possuem dados associados** e retornam zero rows no baseline determinístico 100% SQL.
* Esse comportamento é **correto**: não gera miss em `quality_list_misses.py` e respeita o baseline sem Narrator.
* A resposta conceitual deverá vir futuramente do Narrator quando habilitado; por ora, o baseline retorna zero rows de forma intencional.

## 3.7 Notas sobre DY / yield e dividendos

* DY/yield **não** sai de `fiis_dividendos` (somente `dividend_amt` + datas).

* Valores de yield atuais e históricos vêm de:

  * `fiis_financials_snapshot` → DY corrente / DY 12m (foto D-1);
  * `fiis_yield_history` → histórico mensal de DY e dividendos por mês;
  * `fiis_rankings` → posições relativas em rankings de DY;
  * `dividendos_yield` → visão composta de **dividendos + DY mensal/12m** por FII (entidade pública).

* Implicações de routing:

  * “quanto é o DY do HGLG11?” → `fiis_financials_snapshot`.
  * “top 10 FIIs com maior DY” → `fiis_rankings`.
  * “histórico de dividend yield do MXRF11 nos últimos 12 meses” → `fiis_yield_history`.
  * “histórico de pagamentos do MXRF11” → `fiis_dividendos`.
  * “histórico de dividendos **e DY** do MXRF11 nos últimos 12 meses” → `dividendos_yield`.

**Estado atual (DY, carteira e macro compostas)**:

* As views compostas que estavam em backlog agora estão implementadas, com contratos claros:

  * ✅ `dividendos_yield` — entidade pública composta de dividendos + DY mensal/12m por FII; view `public.dividendos_yield`; políticas: cache pub, RAG deny, Narrator off, inferência temporal habilitada.
  * ✅ `carteira_enriquecida` — entidade privada com posição enriquecida do cliente (cadastro, risco, DY, rankings); view `public.carteira_enriquecida`; binding `document_number: context.client_id`; cache prv; RAG/Narrator negados; inferência desabilitada.
  * ✅ `macro_consolidada` — entidade macro histórica consolidada (IPCA, SELIC/CDI, IFIX/IBOV, câmbio); view `public.macro_consolidada`; cache pub; RAG deny; Narrator off; janelas históricas habilitadas.

* Próximos compostos (backlog futuro) seguem o padrão compute-on-read/D-1 definido no Guardrails, mas **sem novos contratos quebrando as 21 entidades atuais**.

## 3.8 Novos compostos possíveis (joins SQL)

*(Segue a mesma ideia anterior, agora tendo `fii_overview`, `fiis_yield_history`, `dividendos_yield`, `carteira_enriquecida` e `macro_consolidada` já implementados)*

* **Ficha completa do FII** – hoje coberta em grande parte por `fii_overview`. Possível extensão futura com históricos adicionais (preço, risco detalhado).
* **Painel de risco/retorno** – join snapshot + risk + rankings (backlog para entidade dedicada).
* **Visão consolidada da carteira do cliente** – hoje coberta por `carteira_enriquecida`, com possibilidade de versões temporais futuras seguindo compute-on-read e LGPD.

## 3.9 Relatório de consistência de entidades

* **Arquivo**: `data/ops/entities_consistency_report.yaml`.
* **Função**: mapear, para cada entidade canônica (pasta em `data/entities/*`), se ela:

  * tem schema em `data/contracts/entities/*.schema.yaml`,
  * tem projection de quality,
  * aparece em `quality.yaml.datasets`,
  * está (ou é explicitamente excluída) em `cache.yaml`, `rag.yaml`, `narrator.yaml`,
  * tem intents associadas na ontologia,
  * possui (ou não precisa de) regras em `param_inference.yaml`.
* **Uso**: evitar “entidades órfãs” em policies e servir de checklist automático para novos domínios (incluindo as entidades privadas e compostas de carteira/macro).

# 4. Ontologia

* **Estrutura**: `data/ontology/entity.yaml` define normalize (lower/strip_accents/strip_punct), token_split `\b`, weights token/phrase e intents com tokens/phrases include/exclude, anti_tokens e entities associadas.【F:data/ontology/entity.yaml†L1-L120】

* **Synonyms/metrics_synonyms**: routing extrai métricas solicitadas comparando `ask.metrics_synonyms` de cada `entity.yaml` com pergunta normalizada; identifica métricas para formatter/presenter. (Mapa dentro de cada entidade via chave ask.metrics_synonyms).【F:app/orchestrator/routing.py†L30-L70】【F:app/orchestrator/routing.py†L470-L520】

* **Influência no routing**: planner usa intents do ontology para scoring e associação de entidades; normalização e tokenização controlam sensibilidade; anti_tokens penalizam. `extract_requested_metrics` usa synonyms para meta.requested_metrics, influenciando Narrator e formatação.【F:app/planner/planner.py†L98-L186】【F:app/orchestrator/routing.py†L30-L90】【F:app/presenter/presenter.py†L19-L157】

* **Interação RAG**: intents vencedores orientam filtros de snippets (tokens include) em `rag_context`, garantindo relevância semântica ao contextualizar Presenter/Narrator.【F:app/planner/planner.py†L300-L358】

* **Ajustes recentes**:

  * DY/yield removidos de `fiis_dividendos` e reforçados em `fiis_financials_snapshot` / `fiis_yield_history` / `fiis_rankings` / `dividendos_yield`.
  * Tokens/phrases para “histórico do dólar”, “variação do dólar…”, “histórico do IPCA…” direcionando corretamente para `history_currency_rates` e `history_market_indicators`/`macro_consolidada`.
  * Ampliação de tokens para notícias negativas de FIIs, reduzindo colisão com `fiis_precos`.
  * Inclusão de intents privadas:

    * `client_fiis_dividends_evolution` (renda mensal de FIIs);
    * `client_fiis_performance_vs_benchmark` (carteira vs IFIX/IFIL/CDI/IBOV);
    * intent pública `fii_overview` (resumo consolidado do FII);
    * intents compostas para `dividendos_yield`, `carteira_enriquecida` e `macro_consolidada` com tokens/phrases bem delimitados.

* **Estado dos testes**: após ajustes em ontologia + routing_samples, o baseline consolidado retorna **“✅ Sem misses”** no dataset atual via `quality_list_misses.py`.

# 5. Explain Mode

*(Mesmo texto base – explain é a ferramenta oficial para calibrar ontologia/thresholds e entender decisões do Planner.)*

# 6. Quality

* **quality_list_misses.py**: wrapper que chama `quality_diff_routing.py` para listar perguntas que falham nos quality gates comparando samples routing; usa arquivo `data/ops/quality/routing_samples.json` e grava misses em `data/ops/quality_experimental/routing_misses_via_ask.json`. **Estado atual**: baseline fechado com **0 misses** após afinamento de thresholds, ajuste da ontologia para compostas, redirecionamento correto de `dividendos_yield` e correção do conflito `macro_consolidada` vs `history_market_indicators`. `python scripts/quality/quality_list_misses.py` → **“✅ Sem misses.”**.
* **quality_push**: endpoint `/ops/quality/push` recebe payloads de amostras de roteamento, valida policy e registra métricas; scripts `quality_push.py` e `quality_push_cron.py` automatizam envio e verificações com tokens e quality gates. Dashboards Grafana gerados por `gen_quality_dashboard.py`.【F:app/api/ops/quality.py†L148-L420】【F:scripts/quality/quality_push.py†L1-L90】【F:scripts/quality/gen_quality_dashboard.py†L1-L160】
* **Baseline**: `quality_report` utiliza policy `data/policies/quality.yaml` ou fallback e expõe métricas de top1/gap/routed; scripts shell `quality_gate_check.sh` consultam API/Prometheus. Baseline determinístico do Presenter/Narrator garante comparação consistente em shadow/LLM. Prometheus coleta métricas `sirios_planner_top1_match_total`, `planner_quality_*`.【F:app/api/ops/quality.py†L480-L563】【F:app/observability/runtime.py†L70-L152】【F:app/presenter/presenter.py†L204-L285】
* **Cobertura atual de datasets**:

  * FIIs:

    * preços (`fiis_precos`),
    * dividendos (`fiis_dividendos`),
    * histórico de DY (`fiis_yield_history`),
    * cadastro (`fiis_cadastro`),
    * imóveis (`fiis_imoveis`),
    * processos (`fiis_processos`),
    * rankings (`fiis_rankings`),
    * snapshot financeiro (`fiis_financials_snapshot`),
    * cronograma de receitas (`fiis_financials_revenue_schedule`),
    * risco (`fiis_financials_risk`),
    * overview consolidado (`fii_overview`),
    * notícias (`fiis_noticias`),
    * **composto de dividendos + DY** (`dividendos_yield`).
  * Cliente (privado):

    * posições de carteira (`client_fiis_positions`),
    * evolução de dividendos da carteira (`client_fiis_dividends_evolution`),
    * performance vs benchmark (`client_fiis_performance_vs_benchmark`),
    * **carteira enriquecida (posições + risco + DY + rankings)** (`carteira_enriquecida`).
  * Macro:

    * `history_currency_rates`, `history_b3_indexes`, `history_market_indicators`,
    * **macro consolidada** (`macro_consolidada`).

# 7. Caminho para Produção

*(Mantém a mesma lógica da versão anterior: travas de qualidade, RAG limitado, Narrator off, contexto pronto porém desligado, e checklist de infra/deploy acompanhando o `CHECKLIST-2025.0-prod.md`.)*
