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
* **Explain data model**: `explain` inclui `signals`, `decision_path`, `scoring` (intent/entity, gaps base/final, combined/final_combined, rag_signal, rag_hint, thresholds_applied), `rag` (config/used/error), `fusion`, `rag_context` (doc/snippets/reason). `/ask?explain=true` também registra analytics com `planner_output` e métricas de latência/cache.【F:app/planner/planner.py†L187-L358】【F:app/api/ask.py†L48-L114】

## 2.2 RAG

* **context_builder**: `build_context` aplica política `data/policies/rag.yaml` (routing.allow_intents/deny_intents, entities/default/profiles). Resolve collections, max_chunks/min_score/max_tokens, usa embeddings search determinístico e normaliza chunks (texto, score, doc_id, collection). Desabilita quando não permitido ou erro, retornando `enabled=False` e motivo.【F:app/rag/context_builder.py†L1-L179】【F:data/policies/rag.yaml†L1-L80】
* **entity_hints**: Planner lê store via `cached_embedding_store`, gera vetor com `OllamaClient.embed` e converte resultados em hints por entidade (`entity_hints_from_rag`).【F:app/planner/planner.py†L187-L230】
* **RAG fusion & re-ranking**: peso definido em policy (`rag.weight` ou `re_rank.weight`); modos blend/additive ajustam score final; `fusion` bloco aponta `affected_entities` e erro. Re-rank flag controla se thresholds usam score final.【F:app/planner/planner.py†L240-L320】
* **Políticas**: `data/policies/rag.yaml` define profiles (default/macro/risk), roteamento por intent, collections por entidade e default seguro (concepts-fiis). Intents **negados** para RAG: domínios puramente numéricos/privados (FIIs SQL, posição de cliente). Intents **permitidos**: domínios textuais/explicativos (`fiis_noticias`, `fiis_financials_risk`, `history_market_indicators`, `history_b3_indexes`, `history_currency_rates`). Comentários explicam o racional de cada deny/allow.

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
* **Contexto conversacional**: Presenter injeta o `history` produzido pelo `context_manager` em `meta.narrator_context`, mas com `enabled: false` nas policies, evitando qualquer impacto enquanto baseline/quality não forem fechados.

## 2.5 Narrator

* **narrator.yaml**: carregado via `data/policies/narrator.yaml` (default/entidades, llm_enabled/shadow/model/max_llm_rows/use_rag_in_prompt etc.). Effective policy combina default + overrides, ignorando env para habilitação/shadow.【F:app/narrator/narrator.py†L85-L160】
* **Política de LLM**: `_should_use_llm` checa policy enabled e limites de linhas; render retorna baseline se desabilitado ou max_llm_rows <=0 ou rows>limite ou client indisponível. Tokens/latency/strategy registrados.【F:app/narrator/narrator.py†L121-L212】【F:app/narrator/narrator.py†L360-L460】
* **Shadow mode**: se `shadow=True`, estratégia final `llm_shadow` devolve baseline mas registra uso; Narrator_meta marca enabled/shadow/model/strategy e rag_ctx. LLM errors caem em `llm_failed` com baseline.【F:app/narrator/narrator.py†L360-L520】
* **Estado atual**: **LLM globalmente desligado** (`llm_enabled: false`, `shadow: false`, `max_llm_rows: 0`) para todas as entidades (incluindo risco, macro, índices e notícias). Overrides por entidade existem, mas todos com LLM OFF; o sistema opera 100% determinístico.

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

*(mantive a mesma estrutura, ajustando apenas comentários para refletir o estado atual; não vou repetir tudo aqui para não alongar demais, mas a ideia é exatamente o texto que você já tinha, com as correções abaixo)*

Principais atualizações conceituais:

* **fiis_dividendos (histórica)**
  * Entidade continua focada em `dividend_amt` e datas.
  * Ontologia ajustada para **remover DY/yield** dos tokens dessa intent (DY agora é função de snapshot/rankings).
  * `param_inference` cobre janelas de meses/eventos para perguntas de “últimos X meses/pagamentos”.

* **fiis_financials_snapshot (snapshot D-1)**
  * Fonte principal de **valores de DY** (mensal/12m) por FII.
  * Tokens de DY/yield na ontologia agora apontam para esta entidade (valor) ou `fiis_rankings` (posições).

* **fiis_financials_revenue_schedule (snapshot D-1)**
  * Buckets de receita ajustados em `quality.yaml` com `accepted_range` para todos os campos percentuais, incluindo indexadores.
  * Narrator e RAG explicitamente desativados (apenas resposta tabular/determinística).

* **fiis_financials_risk (snapshot D-1)**
  * RAG permitido **apenas conceitual** (coleções `concepts-risk`, `concepts-fiis`), nunca para números.
  * Ontologia enriquecida com tokens/phrases para perguntas de Sharpe, beta, MDD, etc.
  * Templates em `responses/summary.md.j2` sendo humanizados para explicar as métricas de forma amigável.

Demais entidades (cadastro, preços, imóveis, rankings, processos, notícias) seguem exatamente como descrito na sua versão anterior, com a ressalva de que:

* Notícias negativas/recentes agora roteiam corretamente para `fiis_noticias` graças a ajustes de tokens/phrases.
* Perguntas de histórico de preços **não** concorrem mais com macro/índices/moedas por conta de excludes em `fiis_precos` (usd/dólar/ipca/câmbio etc.).

## 3.3 Macro / Índices / Moedas

* **history_currency_rates (histórica)**
  * Histórico multi-ano de USD/EUR em BRL (compra/venda).
  * Ontologia ajustada para capturar “histórico do dólar”, “variação do dólar nos últimos 12 meses” etc., reduzindo colisão com `fiis_precos`.
  * `quality.yaml` agora inclui freshness (30h) e ranges mínimos (>0 para taxa de câmbio).
  * Roteamento de perguntas tipo “histórico do dólar nos últimos 30 dias” passou a ir corretamente para esta entidade (misses corrigidos).

* **history_b3_indexes (histórica)**
  * Igual descrição anterior, agora com bloco de quality (freshness + ranges para variações) consolidado.

* **history_market_indicators (histórica)**
  * Mesma estrutura anterior; ontologia agora captura “histórico do IPCA”, “histórico da inflação”, “série histórica do IPCA” etc.
  * `quality.yaml` cobre faixa de `indicator_amt` com limites realistas.
  * Perguntas do tipo “histórico do IPCA nos últimos 24 meses” deixaram de cair em `fiis_precos` após refinamento dos tokens.

## 3.4 Cliente (privado)

*(igual ao texto que você já tinha; só relembrando o ponto chave)*

* **client_fiis_positions (snapshot D-1, PRIVADO)**
  * Materialized view com carteira de FIIs por data / ticker / participante.
  * `document_number` nunca aparece na apresentação; binding via `context.client_id`.
  * RAG negado; Narrator off; quality com freshness 30min.

## 3.5 Mapa D-1 vs histórico (resumo mental)

* **Históricas (linha do tempo explícita)**
  `fiis_precos`, `fiis_dividendos`, `fiis_noticias`, `history_b3_indexes`, `history_currency_rates`, `history_market_indicators`.

* **Snapshots D-1 (foto do dia anterior, sem histórico na entidade)**
  `fiis_cadastro`, `fiis_imoveis`, `fiis_rankings`, `fiis_processos`, `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`, `client_fiis_positions`.

## 3.6 Notas sobre DY / yield e dividendos

* DY/yield **não** sai de `fiis_dividendos` (apenas `dividend_amt` + datas).
* Valores de yield atuais vêm de:
  * `fiis_financials_snapshot` → DY corrente / DY 12m por fundo (snapshot).
  * `fiis_rankings` → posições em rankings de DY.
* Implicações de routing:
  * “quanto é o DY do HGLG11?” → `fiis_financials_snapshot`.
  * “top 10 FIIs com maior DY” → `fiis_rankings`.
  * “histórico de pagamentos do MXRF11” → `fiis_dividendos`.

**Backlog conceitual**:

* Possível entidade futura `fiis_yield_history` para registrar yield histórico (evitando recomputar a cada pergunta).

## 3.7 Novos compostos possíveis (joins SQL)

*(mantém o mesmo texto que você já tinha, apenas reforçando que ainda é backlog e não contrato atual)*

* **Ficha completa do FII** – join cadastro + snapshot + risk + rankings.
* **Painel de risco/retorno** – join snapshot + risk + rankings.
* **Visão consolidada da carteira do cliente** – join positions + snapshot + rankings, respeitando LGPD.

## 3.8 Relatório de consistência de entidades

* **Arquivo**: `data/ops/entities_consistency_report.yaml`.
* **Função**: mapear, para cada entidade canônica (pasta em `data/entities/*`), se ela:
  * tem schema em `data/contracts/entities/*.schema.yaml`,
  * tem projection de quality,
  * aparece em `quality.yaml.datasets`,
  * está (ou é explicitamente excluída) em `cache.yaml`, `rag.yaml`, `narrator.yaml`,
  * tem intents associadas na ontologia,
  * possui (ou não precisa de) regras em `param_inference.yaml`.
* **Uso**: evitar “entidades órfãs” em policies e servir de checklist automático para novos domínios.

# 4. Ontologia

* **Estrutura**: `data/ontology/entity.yaml` define normalize (lower/strip_accents/strip_punct), token_split `\b`, weights token/phrase e intents com tokens/phrases include/exclude, anti_tokens e entities associadas.【F:data/ontology/entity.yaml†L1-L120】
* **Synonyms/metrics_synonyms**: routing extrai métricas solicitadas comparando `ask.metrics_synonyms` de cada `entity.yaml` com pergunta normalizada; identifica métricas para formatter/presenter. (Mapa dentro de cada entidade via chave ask.metrics_synonyms).【F:app/orchestrator/routing.py†L30-L70】【F:app/orchestrator/routing.py†L470-L520】
* **Influência no routing**: planner usa intents do ontology para scoring e associação de entidades; normalização e tokenização controlam sensibilidade; anti_tokens penalizam. `extract_requested_metrics` usa synonyms para meta.requested_metrics, influenciando Narrator e formatação.【F:app/planner/planner.py†L98-L186】【F:app/orchestrator/routing.py†L30-L90】【F:app/presenter/presenter.py†L19-L157】
* **Interação RAG**: intents vencedores orientam filtros de snippets (tokens include) em `rag_context`, garantindo relevância semântica ao contextualizar Presenter/Narrator.【F:app/planner/planner.py†L300-L358】
* **Ajustes recentes**:
  * DY/yield removidos de `fiis_dividendos` e reforçados em `fiis_financials_snapshot`/`fiis_rankings`.
  * Tokens/phrases para “histórico do dólar”, “variação do dólar…”, “histórico do IPCA…” direcionando corretamente para `history_currency_rates` e `history_market_indicators`.
  * Ampliação de tokens para notícias negativas de FIIs, reduzindo colisão com `fiis_precos`.
* **Estado dos testes**: após ajustes, `quality_list_misses.py` passa a retornar **0 misses** no dataset atual.

# 5. Explain Mode

*(mesmo texto base, com ênfase que explain é a principal ferramenta para calibrar ontologia/thresholds; não alterei estrutura)*

# 6. Quality

* **quality_list_misses.py**: wrapper que chama `quality_diff_routing.py` para listar perguntas que falham nos quality gates comparando samples routing; usa arquivo `data/ops/quality/routing_samples.json` e grava misses em `data/ops/quality_experimental/routing_misses_via_ask.json`. Estado atual: **0 misses**.
* **quality_push**: endpoint `/ops/quality/push` recebe payloads de amostras de roteamento, valida policy e registra métricas; scripts `quality_push.py` e `quality_push_cron.py` automatizam envio e verificações com tokens e quality gates. Dashboards Grafana gerados por `gen_quality_dashboard.py`.【F:app/api/ops/quality.py†L148-L420】【F:scripts/quality/quality_push.py†L1-L90】【F:scripts/quality/gen_quality_dashboard.py†L1-L160】
* **Baseline**: `quality_report` utiliza policy `data/policies/quality.yaml` ou fallback e expõe métricas de top1/gap/routed; scripts shell `quality_gate_check.sh` consultam API/Prometheus. Baseline determinístico do Presenter/Narrator garante comparação consistente em shadow/LLM. Prometheus coleta métricas `sirios_planner_top1_match_total`, `planner_quality_*`.【F:app/api/ops/quality.py†L480-L563】【F:app/observability/runtime.py†L70-L152】【F:app/presenter/presenter.py†L204-L285】
* **Cobertura atual de datasets**:
  * Com qualidade declarada: FIIs (`fiis_precos`, `fiis_dividendos`, `fiis_imoveis`, `fiis_processos`, `fiis_rankings`, `fiis_financials_snapshot`, `fiis_financials_revenue_schedule`, `fiis_financials_risk`, `fiis_noticias`, `fiis_cadastro`, `client_fiis_positions`) e macro (`history_currency_rates`, `history_b3_indexes`, `history_market_indicators`).

# 7. Caminho para Produção

*(mantém a mesma lógica da sua versão, agora sincronizada com o checklist: entidades auditadas, RAG/Narrator/quality alinhados, contexto conversacional pronto porém desligado, e próximos passos em cima disso).*
