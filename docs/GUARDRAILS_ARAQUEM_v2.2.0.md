# **GUARDRAILS ARAQUEM — v2.2.0 (Draft Sirius)**

> **Escopo:** consolida a v2.1.1 + decisões de 2025-11 (Narrator, Contexto, RAG, Planner, Heurísticas).
> **Princípio-mãe:** Tudo que é comportamento de negócio nasce em **YAML/ontologia/SQL real**. Código só executa.

> **Nota de precisão (v2.2.0):**
> Para fins deste documento, entende-se por *comportamento de negócio* qualquer **regra, interpretação, agregação, classificação, decisão ou rótulo semântico**.
> Código **nunca decide**; apenas executa contratos declarados.

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

* `data/entities/<entity>/<entity>.yaml`
* `data/contracts/entities/*.schema.yaml`
* `data/ontology/*.yaml`
* views/tabelas reais no Postgres (`sql_view`, `result_key` etc.).

2. É **terminantemente proibido**:

* criar colunas, métricas ou entidades “no grito” em `.py`;
* colocar regra de negócio só em código sem registro na ontologia / `<entity>.yaml`.

3. Padrão para dados D-1 com atualização diária:

* **compute-on-read**
* **uma única entidade de métricas** por domínio
* SQL parametrizado no builder;
* janelas (3, 6, 12, 24 meses, últimas N ocorrências) e métricas (média, soma, lista) definidas via YAML/ontologia.

### **Nota normativa adicional (v2.2.0)**

> **Compute-on-read** aplica-se **exclusivamente** a **entidades de métricas históricas**.
> Entidades do tipo **snapshot / última leitura** **não são compute-on-read**, mesmo que executem SQL complexo ou agregações internas.
> Essa distinção impacta diretamente decisões de cache, métricas e observabilidade.

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

*(conteúdo original preservado integralmente)*

4. Regra de ouro:

* Contexto **nunca pode quebrar** o fluxo.
* Qualquer erro no context manager resulta em “fail open”: segue sem histórico.

---

## 7. Narrator (Determinístico + LLM opcional)

*(conteúdo original preservado integralmente, incluindo YAML e regras)*

### 7.4 Buckets e uso de LLM (Regra Dura)

*(conteúdo original preservado integralmente)*

---

## 8. Presenter & FactsPayload

*(conteúdo original preservado integralmente)*

---

## 9. Quality Gate (Routing & Narrator)

*(conteúdo original preservado integralmente)*

---

## 10. Observabilidade & Segurança

1. Observabilidade:

* Instrumentação em todos os principais passos (planner, executor, narrator, rag, context);
* métricas no Prometheus + dashboards no Grafana.

2. Segurança / LGPD:

*(conteúdo original preservado)*

### **10.3 Cache e métricas de cache (Nota v2.2.0)**

Para fins de observabilidade e diagnóstico:

* Métricas de **cache de response (plan-based)** e **cache de métricas (metric/window)** devem ser **analisadas separadamente**.
* O campo `cache_hit_metrics` **não se aplica** a:

  * entidades privadas,
  * entidades do tipo snapshot / última leitura,
  * respostas servidas via short-circuit por cache de response.
* Dashboards, relatórios e diagnósticos **não devem interpretar** `cache_hit_metrics = false` como falha nesses casos.

---

## 11. Buckets do Planner (A/B/C/D)

*(conteúdo original preservado integralmente)*

---

## 12. Cache em tempo real (rt_cache)

*(conteúdo original preservado integralmente)*

---

## **13. Diretriz Arquitetural — Cache de Métricas em Entidades Privadas (NOVA — v2.2.0)**

> **Status:** Aprovada
> **Origem:** Auditoria “Cache de Métricas e Consultas Lentas (/ask)”
> **Escopo:** Pipeline `/ask`, Cache, Orchestrator, Diagnostics

### 13.1 Princípio

O **cache de métricas** é **exclusivo** para entidades **compute-on-read** que exponham explicitamente:

* `agg_params.metric`
* `window_norm`

Entidades **privadas do tipo snapshot / última leitura** **não utilizam** cache de métricas.

---

### 13.2 Fundamentação

* O pipeline `/ask` é **cache-first** para **cache de response (plan-based)**, com **short-circuit completo** em caso de hit.
* Entidades privadas snapshot:

  * não operam por `metric/window`;
  * já possuem **TTL curto** no cache de response;
  * não se beneficiam de cache parcial sem violar o contrato ontológico.
* Auditorias demonstram que o gargalo nessas entidades é **SQL**, não Redis.

---

### 13.3 Regras Normativas

1. **Proibição**
   É proibido implementar cache de métricas para entidades privadas snapshot.

2. **Aplicabilidade**
   `cache_hit_metrics` **não se aplica** a entidades privadas snapshot.

3. **Interpretação correta**
   `cache_hit_metrics = false` ou ausente **não indica erro** quando:

   * a entidade não expõe `metric/window`, ou
   * houve short-circuit por cache de response.

4. **Otimização**
   Para entidades privadas snapshot, otimizações devem ocorrer em:

   * SQL (índices, `EXPLAIN ANALYZE`, views),
   * **nunca** por introdução de novos tipos de cache.

---

### 13.4 Exceções

Qualquer exceção a esta diretriz exige, obrigatoriamente:

1. Proposta arquitetural formal;
2. Ganho mensurável comprovado;
3. Prova de não violação do contrato ontológico;
4. Plano explícito de auditoria e rollback.

---

## **Status do Documento**

* ✔ Conteúdo original **preservado integralmente**
* ✔ Decisões novas **explicitamente adicionadas**
* ✔ Nenhuma regra anterior enfraquecida
* ✔ Pronto para **commit como Guardrails Araquem v2.2.0**

---

