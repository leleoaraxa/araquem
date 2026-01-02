# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 21 entidades auditadas, RAG limitado, Narrator em shadow, quality “✅ Sem misses”, contexto ligado com buckets/TTL, Shadow ligado em dev, experimento v0 configurado, ParamInference compute-on-read multi-ticker, Narrator bucket D global pós-SQL)*

---

## 0. Contexto Conversacional (M12–M13)

> 🟩 Base técnica pronta. Próxima etapa: *refinar e observar em produção controlada*.

**✔️ Feito**

* [✔] `context_manager.py` criado e integrado ao `/ask` (`append_turn` user/assistant).

* [✔] Presenter injeta `history` no meta do Narrator conforme `data/policies/context.yaml`.

* [✔] Policies de contexto definidas (planner, narrator, `last_reference`) com `context.enabled: true` e escopo controlado.

* [✔] `last_reference` implementado com política dedicada, TTL em número de turnos e gate único `last_reference_allows_entity(entity)`.

* [✔] Política M12 de last_reference alinhada ao Guardrails: `/ask` imutável; last_reference só nasce de resposta aceita; prioridade texto → identifiers → contexto.

* [✔] `param_inference.yaml` enriquecido com `params.ticker` (source: `[text, context]`) para as intents de FII.

* [✔] `infer_params(...)` recebendo `identifiers`, `client_id`, `conversation_id`, validando janelas (`windows_allowed`) e usando contexto apenas como fallback.

* [✔] `Orchestrator.route_question(...)` passando `client_id` e `conversation_id` para `infer_params`.

* [✔] `/ask` registrando `last_reference` best-effort após resposta bem-sucedida.

* [✔] `routing_samples.json` com cenários multi-turno (CNPJ → Sharpe → overview; notícias → processos → risco).

* [✔] Sanity checks de contexto verdes:

  * [✔] `context_sanity_check.py` (CNPJ → Sharpe → overview).
  * [✔] `context_sanity_check_news_processos_risk.py` (notícias → processos → risco).

* [✔] `context.last_reference.allowed_entities` alinhado com o uso real.

* [✔] `ContextManager` estendido para last_reference **multi-ticker por bucket**, com:

  * [✔] Armazenamento de `tickers: [...]` (lista deduplicada) em vez de um único `ticker`.
  * [✔] Mapa interno por bucket (`_last_reference_by_bucket`), permitindo herança isolada por bucket (A/B/C/D).
  * [✔] Política `bucket_ttl` em `data/policies/context.yaml` (`last_reference.bucket_ttl.{A,B,C,D}`) controlando TTL por bucket.

* [✔] `/ask` agora extrai o `bucket` do `planner.explain.bucket.selected` e:

  * [✔] injeta `bucket` no `meta` de todos os `append_turn` (user/assistant),
  * [✔] envia `bucket` para `context_manager.resolve_last_reference(...)`,
  * [✔] envia `bucket` para `context_manager.update_last_reference(...)` (alinhado ao multi-ticker).

**🟦 Falta (M13 — refinamento)**

* [ ] Testar **LLM OFF** comparando respostas antes/depois de `context.enabled: true`.
* [ ] Criar `M13_CONTEXT_README.md` (prioridades de ticker, escopo, evolução segura).
* [ ] Monitorar em ambiente controlado:

  * [ ] `planner_rag_context_*`
  * [ ] Logs de padrão real de “esse fundo / ele”.

---

## 1. Entidades & Realidade dos Dados (D-1 vs Histórico)

> 🟩 21 entidades auditadas e documentadas em `docs/dev/ARAQUEM_STATUS_2025.md`.

**✔️ Feito**

* [✔] Auditoria profunda das 21 entidades.
* [✔] Classificação D-1 / histórica / quase-estática.
* [✔] Impactos sobre RAG, Narrator, Quality e cache mapeados.
* [✔] Documentado em `ARAQUEM_STATUS_2025.md`.
* [✔] `entities_consistency_report.yaml` garantindo integridade (schema, policies, quality).
* [✔] Novos projections:

  * [✔] `client_fiis_dividends_evolution`
  * [✔] `client_fiis_performance_vs_benchmark`
  * [✔] `fiis_overview`
  * [✔] `fiis_yield_history`
  * [✔] Compostas: `fiis_dividends_yields`, `client_fiis_enriched_portfolio`, `consolidated_macroeconomic`
* [✔] `routing_samples.json` atualizado com compostas e multi-turno.

**🟦 Falta**

* [ ] Backlog de modelagem fina — seguir `ARAQUEM_STATUS_2025.md`.

---

## 2. RAG – Conteúdo e Políticas

> 🟩 RAG limitado, seguro e alinhado às políticas v2.

**✔️ Feito**

* [✔] `rag.yaml` revisto (versão 2): perfis `default`, `macro`, `risk`.
* [✔] RAG permitido apenas para intents textuais:

  * `fiis_news`
  * `fiis_financials_risk`
  * `history_market_indicators` / `history_b3_indexes` / `history_currency_rates` (macro/índices/moedas)
* [✔] RAG **negado** para tudo numérico e privado.
* [✔] Collections alinhadas (`concepts-*`).
* [✔] Fallback seguro (`default`).
* [✔] Estado de RAG documentado em `ARAQUEM_STATUS_2025.md`.

**🟦 Falta**

* [ ] Monitorar latência, uso, recall real.
* [ ] Ajustar min_score/pesos com dados reais (usando `data/ops/quality*` + `data/golden`).

---

## 3. Planner – Thresholds e Calibração Final

> 🟩 Planner calibrado com baseline de roteamento **“Sem misses”**.

**✔️ Feito**

* [✔] Ontologia consolidada (`data/ontology/entity.yaml`).

* [✔] Conflitos resolvidos (macro, dy x dividendos, risk x snapshot).

* [✔] `param_inference.yaml` calibrado.

* [✔] Compute-on-read solidificado (D-1, janelas 3/6/12m, etc.).

* [✔] Thresholds finalizados por família (min_score, min_gap, por entidade).

* [✔] `quality_list_misses.py` → **0 misses**.

* [✔] `quality_diff_routing.py` limpo, sem regressões.

* [✔] `data/ops/param_inference.yaml` enriquecido com bloco `compute_on_read` para:

  * [✔] `fiis_dividends`
  * [✔] `fiis_quota_prices`
  * [✔] `fiis_yield_history`

  definindo, via YAML, `window.allowed/default` (ex.: `months:3/6/12/24`) e `agg.allowed/default` (`list`, `avg`, `sum`, `latest`), reforçando o padrão **compute-on-read declarativo**.

* [✔] `infer_params(...)` agora:

  * [✔] lê `compute_on_read.window/agg` por intent (quando presente),
  * [✔] detecta phrases (“médio/média”, “acumulado/soma”, “últimos 12 meses” etc.) e só aceita `agg/window` se estiverem em `allowed` do YAML, caindo em `default` se não,
  * [✔] continua respeitando `windows_allowed` da intent + entidade, com fallback seguro.

* [✔] Suporte a **N tickers** no ParamInference, sem “achatar” a lista:

  * [✔] Novo helper `_tickers_from_identifiers(...)` para consolidar `ticker` + `tickers: [...]` em lista deduplicada.
  * [✔] `params.ticker.allow_multi_ticker` em `param_inference.yaml` para intents multi-ticker (`fiis_dividends`, `fiis_quota_prices`, `fiis_yield_history`).
  * [✔] Quando `identifiers["tickers"]` tem múltiplos tickers e `allow_multi_ticker=true`, `infer_params` **não** preenche `out["ticker"]` e deixa a lista intacta em `identifiers` — o fan-out continua responsabilidade do Orchestrator.
  * [✔] Quando há somente 1 ticker (texto/contexto), `infer_params` mantém o comportamento mono-ticker (preenche `ticker` normalmente).

* [✔] Novos testes em `tests/planner/test_param_inference_regression.py` cobrindo:

  * [✔] Casos multi-ticker compute-on-read para `fiis_yield_history` (ex.: DY médio HGLG11 x MXRF11 nos últimos 12 meses → `agg=avg`, `window=months:12`, sem `ticker`).
  * [✔] Casos mono-ticker compute-on-read (DY acumulado HGLG11 em 24 meses → `agg=sum`, `window=months:24`, `ticker="HGLG11"`).
  * [✔] Casos sem ticker, garantindo que ParamInference apenas escolhe `agg/window` sem inventar ticker.

**🟦 Falta**

* [ ] Acompanhar `planner.explain()` em produção controlada (mapear dúvidas reais de usuário).
* [ ] Tratar explicitamente o caso “IPCA alto para FIIs?”:

  * [ ] Ajustar para preferir `history_market_indicators` (conceito) em vez de executar `fiis_financials_revenue_schedule` com 0 linhas.

---

## 4. Narrator – Modelo & Policies (shadow mode)

> 🟩 Narrator ativado em shadow, 100% seguro (zero impacto no answer).

**✔️ Feito**

* [✔] `data/policies/narrator.yaml` estruturado com:

  * [✔] `default` determinístico (LLM desligado para entidades não textuais).

  * [✔] Entidades com LLM+shadow:

    * `fiis_financials_risk`
    * `fiis_news`
    * `history_market_indicators`
    * `history_b3_indexes`
    * `history_currency_rates`

  * [✔] Seção `buckets` adicionada:

    * [✔] Buckets `A`, `B`, `C` com `llm_enabled: false` (SQL-only).
    * [✔] Bucket `D` com `llm_enabled: true`, `mode: global_post_sql`, `max_tokens` e `temperature` declarados, e `entities: [consolidated_macroeconomic]` como alvo inicial.

* [✔] `sirios-narrator:latest` integrado ao `app/narrator/narrator.py`.

* [✔] Presenter integrando Narrator, mas mantendo baseline determinístico como **fonte da resposta final** (shadow puro).

* [✔] `llm_enabled` / `shadow` por entidade controlados só por YAML.

* [✔] `max_llm_rows` ajustado (3–5) por entidade textual.

* [✔] Estilo executivo curto configurado via policy.

* [✔] Narrator respeita `prefer_concept_when_no_ticker` para entidades macro/risk (design pronto, ligado à policy).

* [✔] Instrumentação-base:

  * [✔] Latência por chamada (`sirios_narrator_latency_ms`).
  * [✔] Contador de render (`sirios_narrator_render_total`, outcome `ok|skip|error`).

* [✔] Implementado `Narrator.render_global_post_sql(...)` para bucket D:

  * [✔] Usa `bucket_policy` derivada de `narrator.buckets` para decidir se o bucket/entidade podem usar LLM em modo global pós-SQL.
  * [✔] Compacta `results/meta` em um `facts_payload` seguro (máx. N linhas e M colunas, sem blobs gigantes nem `meta` inútil).
  * [✔] Chama o LLM apenas quando `bucket="D"`, `mode="global_post_sql"` e a entidade está na lista permitida do bucket (ex.: `consolidated_macroeconomic`).
  * [✔] Escreve a narrativa em `meta["narrative"]`, **sem alterar `results`**.

* [✔] Novo prompt `build_bucket_d_global_prompt(...)` em `app/narrator/prompts.py`:

  * [✔] Monta instruções em PT-BR, tom executivo e claro, focado em contexto macro.
  * [✔] Reforça: não inventar números; usar apenas `[DADOS_FACTUAIS]`; não fazer call de compra/venda.
  * [✔] Inclui `question`, `entity`, `bucket`, `facts_payload` e bloco `[META_CONTEXTO]` no prompt.

* [✔] `OllamaClient.generate(...)` agora aceita `temperature` e `max_tokens` via kwargs, traduzindo para `options.temperature` e `options.num_predict` no payload da API do Ollama, alinhado às policies do Narrator.

* [✔] Novos testes em `tests/narrator/test_narrator_bucket_d_llm.py` garantindo:

  * [✔] Bucket `D` com `entity="consolidated_macroeconomic"` dispara o LLM, enriquece `meta["narrative"]` e preserva `results` intacto.
  * [✔] Buckets não-D (ex.: A) **não** disparam LLM, mesmo com a mesma entidade.
  * [✔] Métricas `services_narrator_llm_requests_total` e `services_narrator_llm_latency_seconds` são emitidas corretamente.

**🟦 Falta**

* [ ] Rodar uma bateria de perguntas (usando `data/ops/quality*` + `data/golden`) para comparar textos do Narrator vs baseline.

* [ ] Ajustar estilo/nível de detalhe por entidade (risk vs notícias vs macro).

* [ ] Consolidar um `NARRATOR_README.md` explicando:

  * quando o Narrator entra,
  * o que ele pode ou não alterar,
  * como interpretar métricas.

* [ ] **Ajuste dirigido de prompt para casos de Sharpe negativo em `fiis_financials_risk`**, garantindo:

  * interpretação correta (“retorno pior que ativo livre de risco”, sem falar “positivo e alto” com valor negativo),
  * nenhuma mudança em dados/pipeline — **apenas prompt/policy YAML**.

* [ ] Validar exemplos concretos (como o caso `VINO11`, Sharpe -27,45%) usando apenas shadow / logs.

---

## 5. RAG + Narrator – Integração Profissional

> 🟦 Seção atual de foco (UX + conceito + dados).

**✔️ Feito (setup inicial)**

* [✔] Narrator recebendo facts estruturados (`FactsPayload`) + snippets RAG limitados por entidade.

* [✔] Shadow mode ligado apenas para entidades textuais certas (risco, notícias, macro).

* [✔] Snippet RAG limitado por entidade via `rag_snippet_max_chars` em `narrator.yaml`:

  * [✔] `fiis_financials_risk`: 280 chars
  * [✔] `fiis_news`: 320 chars
  * [✔] `history_*`: 260 chars

* [✔] Policy `prefer_concept_when_no_ticker` ativada nas entidades macro, preparando terreno para perguntas conceituais (IPCA, juros, câmbio) sem ticker.

* [✔] Presenter já monta pacote completo para o Narrator:

  * [✔] Pergunta original.
  * [✔] Facts (rows/aggregates/identifiers).
  * [✔] Snippets de RAG.
  * [✔] Histórico de conversa (quando permitido).

* [✔] Implementado `_compact_facts_payload(...)` para buckets globais:

  * [✔] Gera payload enxuto a partir de `results`/`meta`, com limite de linhas/colunas.
  * [✔] Reduz risco de prompts gigantes no bucket D (`global_post_sql`), mantendo apenas o essencial para narrativa macro.

**🟦 Falta (refino UX)**

* [ ] Fechar a regra de compute-mode (`data` vs `concept`) na prática:

  * [ ] Garantir que perguntas macro sem ticker caiam em modo conceito.
  * [ ] Garantir que perguntas “percentual da receita indexada ao IPCA do FII X” continuem em `fiis_financials_revenue_schedule` (dados).

* [ ] Validar tempo de inferência real do Narrator (p95/p99) em ambiente controlado.

* [ ] Desenhar exemplos canônicos de UX:

  * [ ] Risco de um FII (explicação simples a partir dos indicadores).
  * [ ] Interpretação de IPCA alto/baixo para FIIs.
  * [ ] Interpretação de notícia negativa/neutra/positiva.

* [ ] Ajustar prompt final para ficar sempre ≤ ~3800 tokens (contando contexto, RAG, facts).

* [ ] Criar prompts de verificação (anti-alucinação) no lado do Narrator (ex: “não inventar números; se não houver dados, dizer explicitamente”).

* [ ] **Garantir que todos os refinamentos sejam feitos apenas em YAML/prompt/policies**, sem alterar:

  * código do Planner,
  * código do Builder/Executor,
  * contrato do `/ask`,
  * ontologia ou views de dados.

---

## 6. Observabilidade do Narrator (Shadow Logs)

> 🟩 Camada de auditabilidade do Narrator implementada, sem impacto no `/ask`.

**✔️ Feito**

* [✔] `data/policies/narrator_shadow.yaml` criado com:

  * [✔] `enabled`, `environment_allowlist`, `private_entities`.

  * [✔] Bloco de `sampling`:

    * [✔] `default` (rate=1.0, `only_when_llm_used`, `only_when_answer_nonempty`, `always_on_llm_error`).
    * [✔] Overrides por entidade (`fiis_financials_risk`, `fiis_news`, `history_market_indicators`).

  * [✔] Bloco de `redaction` (mask_fields, max_rows_sample, max_chars).

  * [✔] Bloco de `storage` com sink `file` (`logs/narrator_shadow/*.jsonl`, payload limitado por KB).

  * [✔] Bloco de `metrics` (`sirios_narrator_shadow_*`).

* [✔] Novo módulo `app/observability/narrator_shadow.py`:

  * [✔] Estrutura `NarratorShadowEvent`.

  * [✔] Integração com `narrator.yaml` via `_load_narrator_policy` + `_get_effective_policy`.

  * [✔] Lógica de sampling baseada em:

    * `llm_enabled` + `shadow` por entidade,
    * `environment_allowlist`,
    * `rate`,
    * erros de LLM (força coleta).

  * [✔] Redação de PII:

    * Mascara campos (`document_number`, `cpf`, `cnpj`, `email`, `phone`, etc.).
    * Entidades privadas (`client_fiis_*`) recebem redaction agressivo.

  * [✔] Registro de tamanho e descarte se exceder `max_shadow_payload_kb`.

* [✔] Hook no Presenter:

  * [✔] Monta `NarratorShadowEvent` com:

    * request (question, client_id, conversation_id, nickname),
    * routing (intent, entity, planner_score, tokens, thresholds),
    * facts,
    * rag,
    * narrator (strategy, error, latency, effective_policy),
    * presenter (answer_final, answer_baseline, rows_used, style).

  * [✔] Chama `collect_narrator_shadow(...)` em bloco `try/except` (best-effort absoluto).

* [✔] Métrica `sirios_narrator_shadow_total` com `outcome=ok|error`.

* [✔] Experimento v0 configurado:

  * [✔] Arquivo de roteiro: `data/ops/quality_experimental/shadow_experiment_v0.yaml`.
  * [✔] Script executor: `scripts/experiments/run_shadow_experiment_v0.py` (chama `/ask` respeitando `conversation_id`/`client_id`).

* [✔] Observabilidade do bucket D global do Narrator:

  * [✔] Novas métricas adicionadas ao catálogo em `app/observability/metrics.py`:

    * `services_narrator_llm_requests_total` (counter, labels: `bucket`, `entity`, `outcome`).
    * `services_narrator_llm_latency_seconds` (histogram, labels: `bucket`, `entity`).

  * [✔] `data/ops/observability.yaml` atualizado para expor essas métricas no serviço `narrator` (bindings e labels corretos).

**🟦 Falta**

* [ ] Rodar o script do experimento v0 em `dev`:

  * [ ] `docker-compose exec api bash` + `python scripts/experiments/run_shadow_experiment_v0.py`.
  * [ ] Verificar geração de `logs/narrator_shadow/narrator_shadow_*.jsonl`.

* [ ] Ajustar sampling efetivo por ambiente:

  * [ ] `dev`: rate alto (ex: 0.5–1.0).
  * [ ] `staging`: rate moderado (ex: 0.2).
  * [ ] `prod`: rate baixo (ex: 0.01–0.05), sempre `always_on_llm_error=true`.

* [ ] Desenhar plano de análise:

  * [ ] Como ler os JSONL (DuckDB / Python / outro).
  * [ ] Quais KPIs de Narrator queremos ver (taxa de erros, entidades que mais usam LLM, média de latência, etc.).

* [ ] Criar um pequeno `NARRATOR_SHADOW_README.md` com:

  * Estrutura do JSON.
  * Campos importantes.
  * Como amostrar casos para revisão manual.

* [ ] **Definir um fluxo “humanamente possível” para revisar respostas enormes (~3 mil linhas)**:

  * [ ] Filtro de campos relevantes (esconder blobs gigantes no `explain`).

  * [ ] Scripts auxiliares para:

    * resumir o `explain`,
    * destacar só: intent/entity/aggregates/answer_final/narrator.

  * [ ] Documentar esse fluxo no `NARRATOR_SHADOW_README.md`.

---

## 7. Quality – Baseline Final

> 🟩 Quality com **0 misses** (*baseline determinístico*).

**✔️ Feito**

* [✔] Policies de quality alinhadas ao contrato atual de `/ask`.
* [✔] Datasets cobrindo FIIs, carteira do cliente, macro e compostas.
* [✔] Scripts de quality rodando sem RAG/LLM (`QUALITY_DISABLE_RAG=1`).
* [✔] Baseline **0 misses**, `quality_diff_routing.py` limpo.

**🟦 Falta**

* [ ] Expandir dataset com:

  * [ ] Perguntas reais de usuários (SIRIOS).
  * [ ] Perguntas dos arquivos em `data/ops/quality*` e `data/golden`.

* [ ] Criar dashboards de quality (futuro), ligando:

  * [ ] Acurácia de roteamento.
  * [ ] Diferença “baseline vs Narrator” por entidade.

---

## 8. Infra / Produção – Ambientes e Deploy

**🟦 Falta**

* [ ] Configurar DB prod (roles, schemas, migrations).
* [ ] Configurar OTEL/Tempo/Prometheus/Grafana para o stack atual.
* [ ] Dashboards finais (planner, executor, RAG, Narrator, Shadow).
* [ ] Ajustar Redis (TTL, chaves de cache, métricas).
* [ ] Alertas para:

  * [ ] timeouts,
  * [ ] cache-miss anormal,
  * [ ] latência alta de Narrator/RAG.

---

## 9. Segurança & LGPD

**🟦 Falta**

* [ ] Sanitizar PII no output onde for necessário (principalmente respostas de entidades privadas).
* [ ] Reduzir exposição do `explain` (não vazar SQL bruto/dados sensíveis).
* [ ] Policies de acesso operacional (quem pode rodar o quê).
* [ ] Garantir que logs não gravem payload completo desnecessariamente.
* [ ] Revisar roles do Postgres e privilégios de views materializadas.

---

## 10. Documentação Final

**✔️ Feito**

* [✔] `ARAQUEM_STATUS_2025.md` atualizado com estado real do projeto (pipeline `/ask`, RAG, Narrator, Quality, Context).

**🟦 Falta**

* [ ] Diagramas C4 atualizados (por serviço e pelo fluxo `/ask`).
* [ ] Documentar:

  * [ ] RAG (policies, collections, limites).
  * [ ] Narrator (policies, compute-mode, shadow).
  * [ ] Context Manager (last_reference, histórico).
  * [ ] Explain / analytics.
  * [ ] Policies de qualidade, RAG, cache, observability.

---

## 11. Testes de Carga e Estresse

**🟦 Falta**

* [ ] Testar Narrator sob carga (shadow ligado).
* [ ] Testar ingestão/consulta de embeddings em batches.
* [ ] Validar p95/p99 por endpoint.
* [ ] Simular 200–500 perguntas em janela curta.

---

## 12. Entrega Final — “2025.0-prod”

**🟦 Falta**

* [ ] Tag final do release.
* [ ] Congelar embeddings / ontologia / thresholds na versão 2025.0.
* [ ] CI/CD blue-green (rotina de deploy segura).
* [ ] Smoke test pós-deploy (checklist objetivo).
* [ ] Publicação e handover (interno SIRIOS).

---

## 13. Plano de Trabalho de Amanhã — **Modo Safe (só concluir, sem quebrar nada)**

> 🎯 Objetivo: **apenas concluir o Araquem**, refinando Narrator/prompt e auditoria, **sem alterar pipeline/core/contratos**.

**Escopo POSITIVO (pode mexer)**

* [ ] Ajustes **somente em YAML/policies/prompts**, especialmente:

  * [ ] `data/policies/narrator.yaml` – texto e regras para:

    * casos de **Sharpe negativo** em `fiis_financials_risk`,
    * linguagem mais segura (“não inventar número”).

  * [ ] `data/concepts/concepts-risk.yaml` – reforçar explicação de Sharpe negativo, Sortino etc, se necessário.

* [ ] Uso de **shadow logs e explain analytics** apenas para observar:

  * [ ] Casos como `VINO11` (Sharpe -27,45%).
  * [ ] Outras respostas suspeitas do Narrator (sem mexer em dados).

* [ ] Documentação leve:

  * [ ] Atualizar `NARRATOR_README.md` / `NARRATOR_SHADOW_README.md` com lições aprendidas (Sharpe, casos limites).
  * [ ] Pequeno guia de “como revisar respostas enormes” (scripts auxiliares, filtros).

**Escopo NEGATIVO (proibido mexer amanhã)**

* [ ] ❌ Não alterar código core:
  * `planner`, `builder/sql_builder`, `executor/pg`, `presenter`, `context_manager`, `cache`.

* [ ] ❌ Não alterar contrato do `/ask` nem payload.
* [ ] ❌ Não criar novas entidades, projections ou views SQL.
* [ ] ❌ Não mudar thresholds de planner nem políticas de roteamento.
* [ ] ❌ Não mudar políticas de RAG para incluir novas entidades numéricas.
* [ ] ❌ Não mudar ontologia estrutural (`data/ontology/entity.yaml`), apenas, no máximo, textos conceituais relacionados ao Narrator.
