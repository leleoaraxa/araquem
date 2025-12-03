### GUARDRAILS ARAQUEM — v2.2.0 (Draft Sirius)

> **Escopo:** consolida a v2.1.1 + decisões de 2025-11 (Narrator, Contexto, RAG, Planner, Heurísticas).
> **Princípio-mãe:** Tudo que é comportamento de negócio nasce em **YAML/ontologia/SQL real**. Código só executa.

---

## 1. Contrato do `/ask` (imutabilidade)

1. Payload do endpoint `/ask` é **imutável**:

   ```json
   {
     "question": "string",
     "conversation_id": "string",
     "nickname": "string | null",
     "client_id": "string | null"
   }
   ```

2. **É proibido**:

   * adicionar campos arbitrários (ex.: `disable_rag`, `debug`, etc.);
   * usar querystrings para controlar janela, agregação ou limite (ex.: `?agg=sum&window=12m`).

3. Toda parametrização de janela / agregação / filtros:

   * é inferida internamente pelo **Planner → Builder → Formatter**;
   * é exposta no retorno apenas em `meta.aggregates`, nunca via mudança do shape de `results`.

---

## 2. Fonte de verdade: YAML + Ontologia + SQL

1. **Fonte de verdade de entidades**:

   * `data/entities/*/entity.yaml`
   * `data/contracts/entities/*.schema.yaml`
   * `data/ontology/*.yaml`
   * views/tabelas reais no Postgres (`sql_view`, `result_key` etc.).

2. É **terminantemente proibido**:

   * criar colunas, métricas ou entidades “no grito” em `.py`;
   * colocar regra de negócio só em código sem registro na ontologia / entity.yaml.

3. Padrão para dados D-1 com atualização diária:

   * **compute-on-read**
   * **uma única entidade de métricas** por domínio
   * SQL parametrizado no builder;
   * janelas (3, 6, 12, 24 meses, últimas N ocorrências) e métricas (média, soma, lista) definidas via YAML/ontologia.

---

## 3. Arquitetura de pipeline (/ask)

1. Pipeline canônico:

   * **Orchestrator** (entrada → planner → executor)
   * **Planner** (intents/entities, thresholds, RAG hints, context)
   * **Builder** (SQL determinístico, a partir de contracts/metadados)
   * **Executor** (Postgres; sempre com tracing/metrics)
   * **Formatter** (rows → shape canônico)
   * **Presenter** (FactsPayload, templates, Narrator)
   * **Narrator** (determinístico + opcional LLM)
   * **RAG** (context_builder + policies)
   * **Context Manager** (histórico conversacional).

2. Cada módulo deve ser configurado por:

   * `data/policies/*.yaml`
   * `data/entities/*`
   * `data/ontology/*`

   **Nunca** por constantes internas mágicas.

---

## 4. RAG (Retriever + Policies)

1. Políticas de RAG são definidas em:

   * `data/policies/rag.yaml`:

     * collections por entidade,
     * `k`, `min_score_explain`, `weight`, `re_rank`, etc.

2. O **context_builder**:

   * lê as policies de RAG;
   * monta contexto textual estruturado para o Narrator;
   * nunca inventa coleção ou intent; tudo vem do YAML.

3. O fluxo de debug:

   * `/ops/rag_debug`
   * script `scripts/rag/rag_debug.sh`
   * JSON salvo em `/tmp/araquem/rag_debug_last_with_rag.json`.

4. **Desligar RAG em quality / rotinas pesadas**:

   * Nunca alterando payload `/ask`.
   * Semântica canônica: usar variáveis de ambiente / policies internas (por ex. `QUALITY_DISABLE_RAG`) e tratar isso no código de **qualidade**, não na API pública.

---

## 5. Planner (thresholds, scoring, RAG fusion, contexto)

1. Configuração de intents/entities:

   * `data/policies/planner_thresholds.yaml`
   * `data/ops/quality/routing_samples.json` (samples).

2. O Planner sempre:

   * normaliza (lower, strip_accents, strip_punct);
   * tokeniza (`split: \b`);
   * aplica pesos `token` / `phrase` definidos em policies;
   * aplica anti-tokens (`exclude`, `anti_tokens`);

   … e toma decisão com base em:

   * `min_score` e `min_gap`;
   * top2 gap (`intent_top2_gap_base / final`).

3. Integração com RAG:

   * RAG fornece `rag_signal` e `rag_hint` com scores por entidade;
   * `fusion` combina base + rag usando `weight` configurado no YAML;
   * nunca “pula” para uma entidade sem que ela exista na ontologia.

4. Contexto no Planner:

   * O Planner recebe da `Context Policy` apenas:

     * se contexto está `enabled`
     * se a `entity` está `allowed` ou `denied`.
   * Ele **não altera tokens, nem pergunta**; apenas registra `context_allowed` no explain.

---

## 6. Context Manager (Histórico conversacional)

1. Configuração:

   * `data/policies/context.yaml` (fonte canônica).

   Exemplo (linha mestra que estamos usando):

   ```yaml
   terms:
     - name: "context"
       kind: "policy"
       scope: "context"
       version: 1

   context:
     enabled: true        # pode ser desligado em produção se necessário
     max_turns: 4
     ttl_seconds: 3600
     max_chars: 4000

     planner:
       enabled: true
       max_turns: 2
       allowed_entities:
         - fiis_precos
         - fiis_dividendos
         - fiis_financials_risk
         - fiis_financials_snapshot
         - fiis_imoveis
         - fiis_rankings
         - fiis_processos
         - fiis_noticias
       denied_entities:
         - client_fiis_positions
         - history_b3_indexes
         - history_currency_rates
         - history_market_indicators

     narrator:
       enabled: true
       inject_history: true
       max_turns: 3
       max_chars: 2000
       allowed_entities:
         - fiis_precos
         - fiis_dividendos
         - fiis_financials_risk
         - fiis_financials_snapshot
         - fiis_imoveis
         - fiis_rankings
         - fiis_processos
         - fiis_noticias
       denied_entities:
         - client_fiis_positions
         - history_b3_indexes
         - history_currency_rates
         - history_market_indicators
   ```

2. API interna do `ContextManager`:

   * `append_turn(client_id, conversation_id, intent, entity, question, answer, meta)`
   * `load_recent(client_id, conversation_id)`
   * `to_wire(turns)` → formato compacto para Narrator.

3. Endpoints de debug/ops:

   * `/ops/context_debug` → snapshot de estado atual;
   * `/ops/context_clear` → limpa histórico (para testes / qualidade).

4. Regra de ouro:

   * Contexto **nunca pode quebrar** o fluxo.
   * Qualquer erro no context manager resulta em “fail open”: segue sem histórico.

---

## 7. Narrator (Determinístico + LLM opcional)

1. **Policy canônica**:

   * `data/policies/narrator.yaml` (global + overrides por entidade).

   Linha de base atual (com LLM desativado globalmente):

   ```yaml
   terms:
     - name: "narrator"
       kind: "policy"
       scope: "narrator"
       version: 1

   default:
     llm_enabled: false
     shadow: false
     model: sirios-narrator:latest
     style: executivo
     max_llm_rows: 0
     max_prompt_tokens: 4000
     max_output_tokens: 700
     use_rag_in_prompt: true
     use_conversation_context: true
     prefer_concept_when_no_ticker: true
     rag_fallback_when_no_rows: true
     concept_with_data_when_rag: false

   llm_enabled: false
   shadow: false
   max_llm_rows: 0

   entities: {}
   ```

   > **Quando for religar LLM**: fazê-lo primeiro ajustando apenas o YAML (sem mudar código).

2. Regras de arquitetura do Narrator:

   * `app/narrator/narrator.py`:

     * lê policies de `narrator.yaml`;
     * calcula `compute.mode = "data" | "concept"` com base na policy (`prefer_concept_when_no_ticker`) + `identifiers`;
     * injeta `history` no meta **apenas** se o contexto estiver habilitado e entidade permitida;
     * trata LLM como **camada opcional**, sempre com fallback determinístico (`legacy_answer`).

3. **Heurísticas no Narrator (NOVA REGRA v2.2.0)**

   * É **proibido** adicionar novas regras de negócio em `.py` (ex.: “Sharpe < 0 então o fundo é ruim”, “vacância > 30% é elevada”).

   * Qualquer interpretação de:

     * “bom/ruim”
     * “alto/baixo”
     * “elevado/reduzido”
     * “eficiente/ineficiente”

     deve nascer em:

     * `data/policies/narrator.yaml`, ou
     * `data/concepts/*` / `data/policies/*` apropriado.

   * **Heurísticas existentes em `app/narrator/prompts.py`** são consideradas **legado a ser pago**, e devem ser migradas gradualmente com o processo:

     1. Configurar as regras em YAML (thresholds, textos, labels);
     2. Código passa a ler essas configs;
     3. Somente depois remover a lógica “mágica” embutida.

---

## 8. Presenter & FactsPayload

1. `app/presenter/presenter.py`:

   * constrói `FactsPayload` canônico:

     * `question`, `intent`, `entity`, `score`, `planner_score`
     * `rows`, `primary`, `aggregates`, `identifiers`
     * `requested_metrics`, `ticker`, `fund`
   * chama:

     * `render_answer` (determinístico)
     * `render_rows_template` (tabela)
     * Narrator (quando habilitado).

2. O `PresentResult` sempre inclui:

   * `answer` (texto final para o cliente)
   * `legacy_answer` (baseline determinístico)
   * `rendered_template` (markdown tabular)
   * `narrator_meta` (meta de uso do Narrator)
   * `facts` (payload usado para geração).

3. O Presenter:

   * Nunca mexe em SQL, nem faz transformação sem ontologia;
   * Apenas agrega o que já veio do Orchestrator/Formatter.

---

## 9. Quality Gate (Routing & Narrator)

1. Quality de roteamento:

   * samples em `data/ops/quality/routing_samples.json`;
   * scripts:

     * `scripts/quality/quality_list_misses.py`
     * `scripts/quality/quality_diff_routing.py`
     * `scripts/quality/quality_push.py`.

2. Métricas mínimas (exemplo atual):

   * `top1_accuracy >= 0.93`
   * `routed_rate >= 0.98`
   * `misses_abs <= 30`
   * `misses_ratio <= 0.10`.

3. RAG pode ser desabilitado nos testes de quality:

   * via variável de ambiente (ex.: `QUALITY_DISABLE_RAG=1`)
   * sem alterar payload `/ask`.

4. Explicabilidade (`planner.explain` / `explain=true`) deve sempre:

   * mostrar tokens, weights, thresholds, rag_signal, fusion, context;
   * nunca esconder regras de scoring.

---

## 10. Observabilidade & Segurança

1. Observabilidade:

   * Instrumentação em todos os principais passos (planner, executor, narrator, rag, context);
   * métricas no Prometheus + dashboards no Grafana.

2. Segurança / LGPD:

   * PII deve ser mascarado/omitido no Presenter/Formatter para:

     * logs, traces, explain, debug endpoints;
   * roles de banco (`sirios_api`, `edge_user`) configuradas para:

     * SELECT em views necessárias;
     * REFRESH de matviews apenas por roles autorizados;
     * nunca expor dados de cliente indevidamente em rotas públicas.

---

## 11. Buckets do Planner (A/B/C/D)

> **Objetivo:** separar claramente *tipo de pergunta* (bucket) de *entidade específica*, evitando competição indesejada entre domínios diferentes.

**Bucket A — SQL com ticker (FIIs)**
Sinais: ticker explícito (AAAA11) ou herdado via contexto.
Entidades: todas `fiis_*`, `fii_overview`, `dividendos_yield`.

**Bucket B — SQL cliente (privadas)**
Sinais: “minha carteira”, “meus FIIs”, “quanto EU recebi de dividendos” etc.
`client_id` é obrigatório para acesso, MAS NÃO define o bucket.
Entidades: `carteira_enriquecida`, `client_fiis_*`.

**Bucket C — SQL macro/índices/moedas**
Sinais: IPCA, CDI, SELIC, IFIX, IFIL, IBOV, dólar, USD/BRL, “quanto foi X”, “como evoluiu X”, etc.
Entidades: `history_market_indicators`, `history_b3_indexes`, `history_currency_rates`, `macro_consolidada`.

**Bucket D — Conceitual / LLM / chitchat**
Quando nenhuma das regras acima define A/B/C.

### Regras:

1. **Fase 1 — Bucketização**
   O Planner decide primeiro o bucket com base no texto e no contexto permitidos.

2. **Fase 2 — Seleção de entidade**
   A escolha da entidade só pode ocorrer ENTRE entidades do bucket escolhido.

3. **Proibições:**

   * Entidades de buckets diferentes **não competem entre si**.
   * Buckets A/B/C **não podem pular para LLM** sem tentar SQL.
   * `client_id` não define bucket.

4. **Integridade com Narrator:**
   Flags como `prefer_concept_when_no_ticker` **não podem sobrescrever a bucketização**.
   Buckets A/B/C priorizam sempre dados SQL.
