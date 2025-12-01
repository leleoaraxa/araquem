# 🟦 **ARAQUEM_OBSERVABILITY_CHECKLIST.md — v1.0**

## **Guia Oficial de Observabilidade — Logs, Métricas, Traces & Quality (SIRIOS Araquem)**

Local sugerido:
`docs/ARAQUEM_OBSERVABILITY_CHECKLIST.md`

---


# **0. Propósito**

Este documento consolida tudo que é necessário para garantir **observabilidade total** do Araquem:

* Métricas Prometheus
* Tracing (OpenTelemetry → Tempo)
* Logs estruturados
* Dashboards Grafana
* Qualidade (quality_gate, routing_samples, misses)
* Auditorias específicas do Narrator & Shadow
* Monitoramento de degradação e drift

É o **manual oficial** para manter o Araquem estável e seguro em produção.

---


# **1. Componentes Monitorados**

O sistema deve monitorar 8 serviços principais:

1. **Gateway / API**
2. **Orchestrator**
3. **Planner**
4. **Builder**
5. **Executor (Postgres)**
6. **Formatter**
7. **Narrator (LLM / Shadow Mode / Ativo)**
8. **Cache (Redis)**

---


# **2. Estrutura Fonte — Arquivo de Observabilidade**

Arquivo canônico:

```
data/ops/observability.yaml
```

O checklist deve ser sempre validado contra este arquivo, que define:

* thresholds
* métricas específicas por serviço
* bindings de Prometheus
* latência, erros, timeouts
* métricas do Narrator

---


# **3. Observabilidade do Pipeline /ask**

Cada requisição do `/ask` deve gerar:

### ✔ Métricas Prometheus

Exemplos:

* `sirios_api_requests_total`
* `sirios_planner_intent_score`
* `sirios_exec_pg_latency_ms`
* `sirios_narrator_latency_ms`
* `sirios_cache_hit_ratio`
* `sirios_builder_sql_length`
* `sirios_orchestrator_decision_time_ms`

### ✔ Logs estruturados

Formato JSON, contendo:

* conversation_id
* intent/entity
* latência total
* fluxos ativados (RAG, context, narrator)
* tipo de estratégia do Narrator

### ✔ Tracing OpenTelemetry

Cada etapa do pipeline deve aparecer em Tempo:

* `api.handle_request`
* `orchestrator.route`
* `planner.compute_scores`
* `builder.sql.generate`
* `executor.pg.run`
* `formatter.build`
* `narrator.llm.call`

---


# **4. Métricas Críticas (SLA / SLO)**

### **4.1 Latência**

| Serviço           | p95      | Observação       |
| ----------------- | -------- | ---------------- |
| API               | < 500 ms | sem Narrator     |
| Planner           | < 40 ms  | incl. RAG fusion |
| Builder           | < 30 ms  | SQL leve         |
| Executor          | < 120 ms | depende da view  |
| Narrator (shadow) | < 800 ms | LLM              |
| Narrator (ativo)  | < 1.5 s  | máximo tolerável |

---

### **4.2 Erros**

* taxa de erro do Narrator (`sirios_narrator_errors_total`) < **1%**
* timeout do Ollama < **1.5%**
* erro de execução SQL < **0.05%**

---

### **4.3 Cache**

* hit ratio > **85%**
* latência < **5 ms**

---

### **4.4 Context Manager**

* taxa de reutilização segura (`last_reference_used`) > **50%**
* taxa de erro de contexto < **2%**

---

### **4.5 RAG**

* rag_used_rate < **25%** (contexto só quando necessário)
* rag_fail_rate < **1%**
* chunks médios < **3**

---


# **5. Observabilidade do Narrator (Shadow + Ativo)**

O Narrator é o módulo mais sensível → precisa de métricas específicas.

### 5.1 Shadow Mode

Métricas críticas:

* `sirios_narrator_shadow_latency_ms`
* `sirios_narrator_shadow_token_input`
* `sirios_narrator_shadow_token_output`
* `sirios_narrator_shadow_errors_total`
* `sirios_narrator_shadow_strategy_distribution`

### 5.2 Ativo

Métricas críticas:

* `sirios_narrator_active_latency_ms`
* `sirios_narrator_active_fallback_rate`
* `sirios_narrator_strategy_selected`
* `sirios_narrator_incoherence_flag`
* `sirios_narrator_recommendation_violation`

---


# **6. Dashboards Grafana (Checklist)**

O Grafana deve conter pelo menos **5 dashboards**:

---

## ✔ 6.1 Dashboard 1 — “/ask Overview”

* Throughput
* Latência por camada
* Taxa de erro total
* Distribuição de intents
* Modos de execução (DB / RAG / Narrator)

---

## ✔ 6.2 Dashboard 2 — “Planner & Routing”

* Intent score histogram
* Top2 gap
* % queries com contexto
* RAG fusion rate
* Drift de distribuição das intents
* Misses rate

---

## ✔ 6.3 Dashboard 3 — “Executor (Postgres)”

* Tempo por view
* QPS
* Erros SQL
* Tempo por tabela raiz
* Cache Redis hit/miss

---

## ✔ 6.4 Dashboard 4 — “Narrator (LLM)”

* Latência p50/p95/p99
* Tamanho médio do prompt
* Tokens de entrada/saída
* Timeout rate
* Violação de estratégia de prompting
* Estratégias selecionadas (%)

---

## ✔ 6.5 Dashboard 5 — “Shadow Mode Safety”

* divergências entre baseline e Narrator
* incoerência semântica
* risco de recomendação
* comportamento por entidade
* erros por estratégia

---


# **7. Alertas**

Alertas devem ser configurados no Prometheus Alertmanager.

### 📢 Críticos

| Alerta              | Regra                                       |
| ------------------- | ------------------------------------------- |
| Narrator timeout    | p95 > 1500 ms por 5 min                     |
| Narrator alucinação | incoherence_flag > 0.5%                     |
| Executor lento      | p95 > 200 ms                                |
| Planner drift       | distribuição de intents varia > 20% num dia |

### 🟧 Moderados

* cache hit ratio < 70%
* shadow_failure_rate > 5%
* queries sem entidade aumentam > 15%

### 🟨 Informativos

* aumentos de volume
* queries por segundo

---


# **8. Quality — Relação com Observabilidade**

A pasta:

```
data/ops/quality/
```

contém:

* routing_samples.json
* routing_golden.json
* quality_list_misses output
* experimental datasets

Esses arquivos são **parte da observabilidade**, e devem ser:

* versionados
* auditados
* usados como oráculo de regressão

Quality não é só “teste”; é **telemetria semântica do sistema**.

---


# **9. Checklists Operacionais**

### **9.1 Daily Checklist**

* rodar shadow batch
* validar erros críticos
* verificar latência p95
* revisar tempo do Narrator
* rodar quality_list_misses
* atualizar rotinas de drift

---

### **9.2 Weekly Checklist**

* analisar top perguntas por tipo
* validar novos drifts de intent
* revisar token usage médio
* gerar relatório de estabilidade

---

### **9.3 Monthly Checklist**

* health check completo
* avaliação de tuning do Narrator
* limpeza de logs antigos
* rotacionar caching keys
* análise de regressão semântica

---


# **10. Conclusão**

Este checklist de Observabilidade:

* garante visibilidade total do /ask, ponta a ponta
* identifica riscos antes que afetem usuários
* dá segurança para ativar o Narrator
* prepara o terreno para finetune e expansão futura
* reforça o Guardrails Araquem v2.2.0

