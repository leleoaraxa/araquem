## 1. Escopo e objetivo

**Objetivo geral**

Estabilizar e simplificar o fluxo completo do endpoint **`/ask`** no Araquem, garantindo que:

* Todo o caminho **pergunta → resposta** esteja:

  * 100% alinhado ao **Guardrails Araquem v2.1.1** e ao runtime descrito em `RUNTIME_OVERVIEW.md`;
  * livre de heurísticas ocultas e hardcodes (fora de YAML/ontologia/políticas reais);
  * orientado por **YAML + ontologia + contratos + views reais**.
* O comportamento do sistema seja:

  * previsível e auditável (telemetria coerente em `meta` e explain analytics);
  * observável (Prometheus/Tempo) com spans e métricas consistentes;
  * fácil de depurar e evoluir em etapas pequenas (patches Codex sequenciais).

**Escopo deste plano**

Cobrir **somente** o fluxo **online** do `/ask` (sem alterar comportamento fora do pipeline canônico descrito em `docs/dev/RUNTIME_OVERVIEW.md`):

* `app/api/ask.py`
* `app/core/context.py`, `app/core/hotreload.py`
* `app/cache/rt_cache.py`
* `app/planner/*` (`planner.py`, `param_inference.py`, `ontology_loader.py`)
* `app/orchestrator/routing.py`
* `app/builder/sql_builder.py`
* `app/executor/pg.py`
* `app/formatter/rows.py`
* `app/presenter/presenter.py`
* `app/narrator/*` (`narrator.py`, `prompts.py`, `formatter.py`)
* `app/rag/*` (`context_builder.py`, `index_reader.py`, `hints.py`, `ollama_client.py`)
* `app/observability/*` (instrumentation + metrics + runtime)
* `data/ontology/entity.yaml`
* `data/entities/<entity>/<entity>.yaml` + `responses/*.md.j2`
* `data/contracts/entities/*.schema.yaml`
* `data/policies/*.yaml` (cache, formatting, narrator, rag, quality)
* `data/ops/quality/*` (especialmente `routing_samples.json` e projeções)
* `docs/dev/RUNTIME_OVERVIEW.md` e docs auxiliares já existentes (NARRATOR_*, rag_* etc.)

**Fora de escopo (por enquanto)**

* Scripts de cron (`scripts/quality`, `scripts/embeddings`, k8s/quality).
* Infra de Docker/K8s, Prometheus, Tempo, Grafana (apenas ler configuração para entender métricas).
* Features futuras (ex.: novas entidades, novos indicadores de risco etc.).

> **Importante:** Este documento é **apenas plano de refatoração**.
> Especificações de patch para Codex serão produzidas em arquivos separados (`*_PATCH_SPEC.md`) por etapa.

---

## 2. Visão geral do pipeline atual (`/ask`)

### 2.1. Linha do tempo conceitual

Fluxo lógico atual (2025-11-20, baseado nos lotes analisados e na documentação congelada em `RUNTIME_OVERVIEW.md`):

1. **HTTP → `/ask`**

   * `app/api/ask.py`
   * Recebe `AskPayload` (`question`, `conversation_id`, `nickname`, `client_id`).
   * Aplica contexto global (via `core/context`), registra métricas (`sirios_planner_*`, `sirios_cache_ops_total`).
   * Chama `planner.explain(...)` e, em caso de `entity` ausente, responde `unroutable` com `meta.planner`.

2. **Planner**

   * `app/planner/planner.py`
   * Normaliza pergunta, tokeniza, pontua intents, aplica thresholds (`data/ops/planner_thresholds.yaml`).
   * Integra sinais de RAG/hints quando habilitado (`plan['rag']`).
   * Define `plan.chosen.intent`, `plan.chosen.entity`, `plan.chosen.score` e `plan.explain` (decision_path, thresholds_applied).

3. **Orchestrator + Builder + Executor + Formatter**

   * `app/orchestrator/routing.py`
   * `app/builder/sql_builder.py`
   * `app/executor/pg.py`
   * `app/formatter/rows.py`
   * Reaplica planner e gate (score, gap, thresholds YAML), extrai identificadores (`ticker`, `tickers`).
* Chama `infer_params` (compute-on-read) e resolve `requested_metrics` via `ask.metrics_synonyms` do `<entity>.yaml`.
   * Prepara cache de métricas (`_prepare_metrics_cache_context`), tenta Redis, ou monta SQL (`build_select_for_entity`), executa (`PgExecutor.query`) e formata (`format_rows`).
   * Monta `results` e `meta` (planner, gate, aggregates, requested_metrics, rows_total, elapsed_ms, explain/explain_analytics quando `explain=True`).
   * Constrói **o contexto de RAG canônico** via `rag.context_builder.build_context` e preenche `meta['rag']` (com fallback seguro em caso de erro).

4. **Presenter / Facts**

   * `app/presenter/presenter.py`
   * Constrói `facts` (`build_facts`) a partir de `plan.chosen`, `results`, `identifiers`, `aggregates` e `requested_metrics`.
   * Define `result_key`, `primary`, `rows`, `ticker`/`fund`, `planner_score` e baseline determinístico (Responder + template).

5. **Narrator**

   * `app/narrator/narrator.py`
   * `app/narrator/prompts.py`
   * Aplica política global + por entidade (`data/policies/narrator.yaml`):
     * `llm_enabled` e `shadow` **sempre** vêm do YAML (sem override por env);
     * `model` (e opcionalmente `style`) podem ser sobrescritos por env (`NARRATOR_MODEL`) quando não definidos na policy.
   * Decide baseline vs LLM, com shadow opcional, sempre com baseline calculado.
   * Usa `facts`, `meta_for_narrator` (intent, entity, explain, result_key, rag_context) para gerar texto determinístico ou LLM (`Narrator.render`).

6. **Resposta final**

   * `app/api/ask.py` monta o JSON final com `status`, `results`, `meta` (planner, gate, aggregates, requested_metrics, rag, narrator, cache, analytics) e `answer` (Narrator ou baseline).

### 2.2. Camadas principais (resumo)

| Camada          | Responsável principal                                | Fontes de verdade                                |
| --------------- | ---------------------------------------------------- | ------------------------------------------------ |
| HTTP / API      | `app/api/ask.py`                                     | Payload `/ask`, `RUNTIME_OVERVIEW.md`            |
| Contexto global | `app/core/context.py`, `app/core/hotreload.py`       | `.env`, configs, ontologia, policies             |
| Cache online    | `app/cache/rt_cache.py`                              | `data/policies/cache.yaml`                       |
| Planejamento    | `app/planner/*`                                      | `data/ontology/entity.yaml`, thresholds, hints   |
| Execução SQL    | `app/orchestrator/routing.py`, `builder`, `executor` | `docs/database/ddls/*.sql`, contratos, entities  |
| Formatação rows | `app/formatter/rows.py`                              | `data/contracts/entities/*.schema.yaml`          |
| Presenter/Facts | `app/presenter/presenter.py`                         | ontologia + entities + templates                 |
| Narrator        | `app/narrator/*`                                     | `data/policies/narrator.yaml`, `data/entities/*` |
| RAG             | `app/rag/*`, `data/embeddings/*`, `data/concepts/*`  | `data/policies/rag.yaml`, `index.yaml`, hints    |
| Quality / Ops   | `app/api/ops/*.py`, `data/ops/quality/*`, Prometheus | `data/policies/quality.yaml`, `QUALITY.md`       |

---

## 3. Achados e riscos (cruzando os 6 lotes)

### 3.1. Arquitetura e fluxo `/ask`

1. **RAG com duplo caminho lógico**

   * Orchestrator já monta `meta['rag']` com base em `rag.context_builder`.
   * Presenter também possui lógica relacionada a RAG (para debug/execução local).
   * Risco:

     * dois pontos de construção de contexto com potencial divergência de política;
     * aumento de complexidade para debugar shadow/disable.

2. **`meta` parcialmente documentado**

   * `docs/dev/RUNTIME_OVERVIEW.md` descreve boa parte do `meta`, mas:

     * campos adicionados recentemente (ex.: `meta['narrator']['strategy']`, campos de RAG refinados) podem não estar documentados;
     * algumas estruturas (ex.: `meta['aggregates']`, `meta['requested_metrics']`) aparecem em código e JSON de runtime, mas sem documentação única.

3. **Dependência forte de conhecimento implícito**

   * Vários comportamentos (principalmente no Orchestrator e Presenter) dependem de:

    * nomes de `result_key` alinhados manualmente com `<entity>.yaml` e templates;
     * convenções sobre colunas (ex.: ordering vs contratos).
   * Isso ainda não está 100% amarrado em contratos + ontologia.

### 3.2. Planner, ontologia e param inference

1. **Planner bem alinhado, mas complexo de depurar**

   * Integra sinais de:

     * tokens/phrases;
     * anti-tokens;
     * RAG hints (`rag_hint`, `rag_signal`, `fusion`).
   * Estrutura de `meta.planner.explain` é rica, porém:

     * poucas ferramentas de consumo/visualização além do `/ops/analytics` e logs.

2. **Param inference com acoplamento implícito**

   * `param_inference` faz inferências por entidade usando heurísticas baseadas na ontologia, mas também em regras implícitas no código:

     * janela temporal;
     * agregações padrão;
     * ordenação.
   * Guardrails já dizem que tudo isso deveria ser YAML/ontologia-driven; hoje o código ainda carrega parte da lógica.

### 3.3. RAG

1. **Política RAG vs uso efetivo**

   * `data/policies/rag.yaml` define:

     * coleções por intent/entity;
     * limites de chunks;
     * modo de re-rank.
   * `context_builder` implementa isso corretamente para `meta['rag']`.
   * Contudo:

     * a forma como o Narrator usa esse `rag_ctx` ainda é parcialmente acoplada ao SYSTEM_PROMPT e à política do Narrator (ex.: `use_rag_in_prompt`).

2. **Conteúdos conceituais ricos mas sensíveis**

   * Hints (`data/entities/*/hints.md`) e concepts (`data/concepts/*.yaml`) trazem conteúdo conceitual forte.
   * Para risco (`fiis_financials_risk`), o chunk de hints pode ser literalmente recitado pelo LLM se não houver barreiras mais fortes.

### 3.4. Narrator

1. **Override por entidade recentemente introduzido**

   * `narrator.yaml` agora permite:

     * `llm_enabled`, `max_llm_rows`, `use_rag_in_prompt` específicos por entidade.
   * Código de `Narrator` já usa `_get_effective_policy(entity, policy)`.
   * Porém:

     * existem campos de meta (`enabled`, `shadow`, `strategy`) que ainda podem refletir estado global e não o effective policy.
     * o fluxo de baseline/LLM ainda é complexo para auditar de fora.

2. **Modo conceitual vs por fundo**

   * Para algumas entidades (ex.: `fiis_financials_risk`), temos flags:

     * `prefer_concept_when_no_ticker`
     * `rag_fallback_when_no_rows`
     * `concept_with_data_when_rag`
   * O comportamento está implementado, mas:

     * depende de extração de ticker em vários pontos (pergunta, filtros, meta), o que aumenta o espaço de erro;
     * exige boa documentação para não gerar surpresas ao time de produto.

3. **Templates Jinja vs renderizadores Python**

   * Entidades possuem:

     * templates `responses/*.md.j2` (Jinja);
     * renderers específicos no `render_narrative`.
   * Para risco, o fluxo determinístico é bom, mas a combinação com RAG/LLM ainda não está 100% disciplinada.

### 3.5. Contratos, entities e views

1. **Align geral bom, mas precisa de sweep**

   * Os arquivos:

     * `data/contracts/entities/*.schema.yaml`
    * `data/entities/<entity>/<entity>.yaml`
     * `docs/database/ddls/views.sql`
   * em geral batem, mas:

     * é necessário um check sistemático para garantir que:

       * toda coluna usada no `rows.py`/templates está nos contratos;
       * tipos e nomes são coerentes;
       * nenhuma entidade está com campos “órfãos”.

2. **Campos de risco**

   * Para `fiis_financials_risk`, há colunas como:

     * `volatility_ratio`, `sharpe_ratio`, `treynor_ratio`, `jensen_alpha`, `beta_index`, `sortino_ratio`, `max_drawdown`, `r_squared`.
   * Esses campos aparecem:

     * em `views.sql`;
     * em `fiis_financials_risk.schema.yaml`;
    * em `<entity>.yaml` e templates Jinja.
   * É importante garantir que **todos** são usados de forma consistente pelo Narrator e pelas telas.

### 3.6. Quality e `/ops/quality/report`

1. **`/ops/quality/report` com violação crônica de `top2_gap_p50`**

   * Resposta atual indica:

     * `top1_accuracy`, `routed_rate`, `misses` ok;
     * `top2_gap_p50` = 0.0, abaixo do `min_top2_gap` configurado.
   * Metadados mostram:

     * expressão Prometheus usando `sirios_planner_top2_gap_histogram_bucket`;
     * agregação em múltiplas janelas (10m, 1h, 6h, 24h).
   * Hipóteses:

     * métrica não está sendo emitida corretamente (`emit_histogram` vs labels/`le`);
     * buckets/labels mudaram com o tempo e o `gap_expr` ficou desatualizado;
     * falta de amostragem suficiente em janelas pequenas.

2. **Projeções de qualidade**

   * `data/ops/quality/projection_*.json` descrevem projeções esperadas por entidade.
   * O código de `quality_push.py` e `quality_gate_check.sh` depende desse formato.
   * É preciso revisar se a projeção de `fiis_financials_risk` está coerente com as queries reais.

---

## 4. Objetivos de refatoração do `/ask`

Ao final deste plano, a rota `/ask` deve:

1. **Ter um único caminho de RAG canônico**

   * `meta['rag']` construído em um ponto bem definido (Orchestrator) e consumido por Presenter/Narrator sem duplicação.

2. **Ser 100% policy/ontologia-driven**

   * Planner, RAG, Narrator, cache, formatting:

     * sempre lendo de `data/policies/*.yaml` + `data/ontology/entity.yaml`;
     * sem parâmetros mágicos no código.

3. **Garantir determinismo quando desejado**

   * Para entidades como `fiis_financials_risk`, quando a policy diz “sem LLM / sem RAG no prompt”:

     * resultado deve ser **puramente determinístico**, mesmo que o cliente LLM esteja disponível.

4. **Aumentar previsibilidade de `meta`**

   * Estrutura de `meta` estável e documentada (RUNTIME_OVERVIEW atualizado).
   * `meta['narrator']` expõe claramente:

     * estratégia usada (`deterministic` vs `llm`);
     * `enabled`, `shadow` efetivos por entidade;
     * erros/razões de fallback.

5. **Qualidade operacional alinhada**

   * `/ops/quality/report` volta a ficar **green** para o conjunto atual de amostras:

     * sem violação constante de `top2_gap_p50`;
     * métricas de rota e thresholds coerentes com a realidade de uso.

---

## 5. Plano de refatoração em etapas

Cada etapa abaixo é pensada para virar **um patch Codex separado**, com escopo pequeno e arquivos explicitamente listados.

### Etapa 0 — Sanidade e baseline de testes

**Objetivo**

* Garantir que o estado atual do repositório (código do zip) está com:

  * testes unitários/integração passando (`pytest`);
  * rota `/ask` funcional para cenários de base (ex.: perguntas simples de cadastro, risco, notícias).

**Ações**

* Rodar suíte de testes existente (sem alteração de código).
* Coletar alguns exemplos reais de `/ask` (incluindo risco, processos, cadastro, indicadores) para servir de baseline manual.

**Arquivos envolvidos**

* Nenhum arquivo modificado; apenas execução de testes e coleta de amostras (JSON em `tmp/`).

---

### Etapa 1 — Documentar e congelar contrato do `/ask`

**Objetivo**

* Consolidar a **documentação canônica** do pipeline `/ask` (entrada → resposta), alinhada ao código atual.

**Ações**

* Atualizar/expandir `docs/dev/RUNTIME_OVERVIEW.md` para:

  * incluir diagrama sequencial do `/ask`;
  * descrever `meta` completo (planner, orchestrator, rag, narrator, cache, analytics).
* Criar (ou atualizar) `docs/dev/ASK_PIPELINE_REFACTOR_PLAN.md` (este arquivo) como plano de trabalho oficial.

**Arquivos permitidos**

* `docs/dev/RUNTIME_OVERVIEW.md`
* `docs/dev/ASK_PIPELINE_REFACTOR_PLAN.md` (novo)

**Garantias**

* Nenhum código de produção alterado.
* Somente documentação.

---

### Etapa 2 — Consolidar caminho de RAG no `/ask`

**Objetivo**

* Definir **um único ponto oficial** de construção de `meta['rag']` e eliminar caminhos paralelos.

**Ações (conceituais)**

1. Escolher:

   * **Padrão recomendado:** Orchestrator é o **único** responsável por montar `meta['rag']` usando `rag.context_builder`.
2. Ajustar:

   * Presenter e Narrator passam a **apenas consumir** `meta['rag']`, sem reconstruir contexto.
3. Garantir:

   * `meta['rag']` tem formato único documentado em `RUNTIME_OVERVIEW.md` e `rag_context_builder.md`.

**Arquivos previstos para patch futuro**

* `app/orchestrator/routing.py`
* `app/presenter/presenter.py`
* `app/rag/context_builder.py`
* `data/policies/rag.yaml` (se necessário ajustar nomes de coleções ou flags)
* `docs/dev/rag_context_builder.md`
* `docs/dev/RUNTIME_OVERVIEW.md`

**Testes alvo**

* `tests/rag/test_context_builder.py`
* `tests/orchestrator/test_rag_integration_orchestrator.py`
* `tests/api/ops/test_rag_debug.py`

---

### Etapa 3 — Alinhar Presenter e Facts com ontologia/entidades

**Objetivo**

* Garantir que `facts` é sempre construído de forma:

  * coerente com a ontologia (`data/ontology/entity.yaml`);
  * alinhado às configurações por entidade (`data/entities/<entity>/<entity>.yaml`);
  * adequado para consumo pelo Narrator e pelas telas.

**Ações (conceituais)**

1. Revisar `build_facts`:

   * confirmar uso correto de `result_key`, `primary`, `rows`, `requested_metrics`, `ticker`, `fund`.
2. Alinhar chaves de `facts` com:

   * templates Jinja `responses/*.md.j2`;
   * campos esperados em `narrator.render_narrative` e `prompts.build_prompt`.
3. Atualizar documentação:

   * seção “FACTS” em `RUNTIME_OVERVIEW.md`;
   * se necessário, mini-doc `FACTS_CONTRACT.md`.

**Arquivos previstos para patch futuro**

* `app/presenter/presenter.py`
* `data/entities/<entity>/<entity>.yaml` (apenas se for necessário correção de chaves)
* `data/entities/*/responses/*.md.j2` (ajustes pontuais)
* `docs/dev/RUNTIME_OVERVIEW.md` (seção FACTS)

**Testes alvo**

* Adicionar testes de presenter (novo arquivo `tests/presenter/test_presenter_facts.py`).
* Reusar amostras de `tmp/sample_*.json` como fixtures.

---

### Etapa 4 — Narrator + policies: harmonização completa

> Esta etapa deve respeitar e complementar o que já foi definido em `NARRATOR_REDESIGN_PLAN.md` e `NARRATOR_PATCH_SPEC.md`, sem reabrir decisões já consolidadas.

**Objetivo**

* Tornar o comportamento do Narrator:

  * inteiramente governado por `data/policies/narrator.yaml`;
  * previsível por entidade (ex.: `fiis_financials_risk` determinístico, sem RAG em prompt);
  * observável via `meta['narrator']`.

**Ações (conceituais)**

1. Finalizar modelo de **effective policy**:

   * `_get_effective_policy(entity, self.policy)` como caminho oficial.
   * `enabled`, `shadow`, `max_llm_rows`, `use_rag_in_prompt` sempre vindos da effective policy.
2. Ajustar meta do Narrator:

   * `meta['narrator']` deve expor:

     * `enabled`/`shadow` efetivos;
     * `strategy`: `"deterministic"` ou `"llm"`;
     * `error` (motivo de fallback, ex.: `llm_disabled_by_policy`, `client_unavailable`, `llm_skipped: rows_count...`).
3. Firmar política por entidade:

   * `fiis_financials_risk`:

     * `llm_enabled: false`;
     * `max_llm_rows: 0`;
     * `use_rag_in_prompt: false`;
     * garantindo que o texto final seja sempre construído a partir do renderer determinístico + templates.
   * Outras entidades: avaliar necessidades específicas (ex.: notícias, processos, rankings).

**Arquivos previstos para patch futuro**

* `app/narrator/narrator.py`
* `app/narrator/prompts.py`
* `data/policies/narrator.yaml`
* `docs/dev/NARRATOR_REDESIGN_PLAN.md`
* `docs/dev/NARRATOR_FLOW_*` (ajustes de documentação, se necessário)

**Testes alvo**

* `tests/narrator/test_concept_mode.py`
* `tests/narrator/test_rag_integration.py`
* (eventualmente) novos testes para:

  * effective policy por entidade;
  * `use_rag_in_prompt = False`.

---

### Etapa 5 — Sweep de contratos, entities e views

**Objetivo**

* Garantir que a tríade:

  * `docs/database/ddls/views.sql`
  * `data/contracts/entities/*.schema.yaml`
  * `data/entities/<entity>/<entity>.yaml`
* está 100% consistente para todas as entidades do DOMÍNIO FIIs.

**Ações (conceituais)**

1. Para cada entidade (client_fiis_positions, fiis_cadastro, ..., history_market_indicators):

   * checar se:

     * todas as colunas da view aparecem no contrato `.schema.yaml`;
    * o `result_key` do `<entity>.yaml` está alinhado ao que o Orchestrator/presenter usam;
     * templates `responses/*.md.j2` referenciam somente campos existentes.
2. Corrigir discrepâncias pontuais:

   * nomes de campos;
   * tipos/formatos;
   * chaves primárias e ordenação padrão.

**Arquivos previstos para patch futuro**

* `docs/database/ddls/views.sql`
* `data/contracts/entities/*.schema.yaml`
* `data/entities/<entity>/<entity>.yaml`
* `data/entities/*/responses/*.md.j2`

**Testes alvo**

* `scripts/core/validate_data_contracts.py` (rodar e garantir 0 erros).
* Adicionar testes de smoke de `formatter/rows.py` se necessário.

---

### Etapa 6 — Qualidade e `/ops/quality/report`

**Objetivo**

* Fazer `/ops/quality/report` voltar a ficar **green**, com métricas coerentes com o comportamento atual do planner.

**Ações (conceituais)**

1. Confirmar métrica `top2_gap_p50`:

   * revisar `app/observability/metrics.py` para ver como `sirios_planner_top2_gap_histogram_bucket` é emitida;
   * revisar expressão em `app/api/ops/quality.py` e nos arquivos de Prometheus (`prometheus/recording_rules.yml`, `templates/*.j2`).
2. Ajustar um dos lados:

   * se a métrica de runtime mudou, atualizar `gap_expr`;
   * se a expressão está correta mas os buckets/labels mudaram, alinhar emissores.
3. Revisar thresholds em `data/policies/quality.yaml`:

   * especialmente `min_top2_gap` para o cenário de uso atual.

**Arquivos previstos para patch futuro**

* `app/api/ops/quality.py`
* `app/observability/metrics.py`
* `prometheus/recording_rules.yml` + `templates/recording_rules.yml.j2`
* `data/policies/quality.yaml`
* `docs/dev/QUALITY.md`

**Testes alvo**

* Se existirem testes para quality, ajustá-los;
* Caso contrário, adicionar testes de unidade para `_fetch_top2_gap` (ou função equivalente) em `app/api/ops/quality.py`.

---

### Etapa 7 — Acabamento de observabilidade e DX

**Objetivo**

* Deixar o caminho `/ask` totalmente traçável e amigável para operação e debugging.

**Ações (conceituais)**

1. Revisar `app/observability/instrumentation.py` e `runtime.py`:

   * garantir que as principais etapas do `/ask` (planner, orchestrator, executor, presenter, narrator, rag) estão:

     * emitindo métricas claras;
     * expondo spans/traces em Tempo/Grafana.
2. Padronizar logs-chave:

   * IDs de requisição (`request_id`);
   * intenção/entidade escolhidas;
   * erros do Narrator, executor, RAG.
3. Melhorar DX de `/ops/rag_debug`:

   * garantir que o JSON salvo em `tmp/araquem/rag_debug_last*.json` reflete o fluxo canônico após refatoração.

**Arquivos previstos para patch futuro**

* `app/observability/instrumentation.py`
* `app/observability/runtime.py`
* `app/api/ops/rag_debug.py`
* `scripts/rag/rag_debug.sh`
* `docs/dev/ARCHITECTURE_RISKS.md` (atualização, se necessário)

---

## 6. Dependências e ordem recomendada

Ordem sugerida de execução das etapas:

1. **Etapa 0** — Sanidade e baseline (sem código).
2. **Etapa 1** — Documentação do contrato `/ask` (sem código).
3. **Etapa 2** — Consolidar RAG (impacta Orchestrator/Presenter).
4. **Etapa 3** — Ajustar Presenter/Facts (consumidor direto do Orchestrator).
5. **Etapa 4** — Harmonizar Narrator + policies (consome facts + meta, incluindo RAG).
6. **Etapa 5** — Sweep contratos/entities/views (garante dados coerentes para todas as camadas).
7. **Etapa 6** — Quality `/ops/quality/report` (fecha ciclo com observabilidade).
8. **Etapa 7** — Ajustes finais de observabilidade/DX.

Cada etapa deve:

* virar um **`*_PATCH_SPEC.md`** dedicado;
* resultar em um **único PR / patch Codex**;
* ser validada com:

  * testes automatizados;
  * pelo menos 1–2 requisições reais `/ask` (amostras salvas em `tmp/`).

---

## 7. Como usar este plano com o Codex (próxima fase)

* Para cada etapa (2 a 7):

  1. Criar um arquivo `docs/dev/ASK_PATCH_ETAPA_X.md` (ou similar) contendo:

     * escopo de arquivos;
     * mudanças permitidas;
     * exemplos de antes/depois, se necessário;
     * requisitos de testes.
  2. A partir desse arquivo, gerar um **prompt restrito** para o Codex:

     * listando **apenas** os arquivos que podem ser tocados;
     * proibindo criação de novos módulos sem instrução explícita;
     * exigindo diff unificado + resumo técnico.

* Este plano (`ASK_PIPELINE_REFACTOR_PLAN.md`) permanece como **fonte-mãe** para:

  * priorizar etapas;
  * garantir que não se perca o controle ao longo dos dias de trabalho.

---
