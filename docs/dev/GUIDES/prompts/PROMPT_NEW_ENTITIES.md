# ✅ **VERSÃO FINAL — `PROMPT_NEW_ENTITIES.md` (Araquem M8.x, Guardrails v2.2.0)**

> **Use este prompt dentro do repositório** sempre que uma nova entidade precisar nascer ou sofrer ajustes estruturais.
> O Codex deve produzir **arquivos completos** ou **patches prontos para commit**, cobrindo 100% das peças declarativas do ecossistema Araquem.

---

# ───────────────────────────────────────────────

# **REGRAS ABSOLUTAS**

# ───────────────────────────────────────────────

* **Sem pastas novas.** Sempre usar a topologia já existente.
* **Payload do `/ask` é IMUTÁVEL**. (`question`, `conversation_id`, `nickname`, `client_id`).
  Nenhum parâmetro novo pode ser criado.
* **Zero heurística/hardcode em código.**
  Toda lógica deve vir de YAML, ontologia ou SQL. Nenhum desvio em Python.
* **Compute-on-read e composições** seguem padrões existentes.
  Não criar lógicas nem funções Python para isso.
* **Privacidade (LGPD):** entidades `client_*` sempre usam
  `document_number: context.client_id`, nunca texto da pergunta.
* **RAG/Narrator/Context** só podem ser configurados via YAML, seguindo precedentes.
* **A saída do Codex deve conter APENAS arquivos/diffs.**
  Nada de explicações.

---

# ───────────────────────────────────────────────

# **ESCOPO A SER ANALISADO (SEMPRE)**

# ───────────────────────────────────────────────

### 1) Entidade base

* `data/entities/<entity>/<entity>.yaml`
* `data/contracts/entities/<entity>.schema.yaml`
* `data/entities/<entity>/template.md`
* `data/entities/<entity>/responses/*.md.j2`
* `data/entities/<entity>/hints.md`

### 2) Catálogo, ontologia e políticas

* `data/entities/catalog.yaml`
* `data/ontology/entity.yaml`
* `data/policies/*.yaml` (quality, rag, narrator, context, cache)
* `data/ops/entities_consistency_report.yaml`

### 3) Quality, planner e parâmetros

* `data/ops/quality/routing_samples.json`
* `data/ops/quality/projection_*.json`
* `data/ops/param_inference.yaml`
* `data/ops/planner_thresholds.yaml`

### 4) RAG e conceitos

* `data/rag/golden/rag_golden_set.json`
* `data/rag/concepts/concepts-*.yaml`

### 5) Amostras e documentação

* `docs/database/samples/<entity>.csv`
* `docs/dev/ENTITIES_INVENTORY_2025.md`
* `docs/ARAQUEM_STATUS_2025.md`
* `docs/CHECKLIST-2025.0-prod.md`
* `docs/GUARDRAILS_ARAQUEM_v2.2.0.md`

---

# ───────────────────────────────────────────────

# **PASSO A PASSO PARA CRIAR/ATUALIZAR ENTIDADE**

# ───────────────────────────────────────────────

## **1) Reconhecer o tipo**

Snapshot D-1, histórico (metrics), compute-on-read, composite, overview, macro/index/currency, risco, privada (`client_*`), single-row, lista/tabela, agrega, multi-ticker, janelas temporais.

## **2) Buscar padrão equivalente**

Basear-se sempre em: `fiis_*`, `history_*`, `fiis_overview`, `client_*`.

---

## **3) Criar `<entity>.yaml`**

### **3.1. Campos obrigatórios**

* `id: <entity>`
* `description:` texto em PT-BR
* `private: true` (SOMENTE se for client_*)
* `sql_view:` ou bloco `sql:` (compute-on-read usando parâmetros nomeados já existentes)
* `result_key:` (REGRA FORMAL, abaixo)
* `default_date_field:` (quando temporal → regra formal)
* `options:` (multi-ticker, overview, etc.)
* `identifiers:` (ticker, document_number, outros)
* `columns:` lista de colunas reais (nome, alias, desc)

### **3.2. **REGRAS FORMAIS — `result_key`**

O Codex **deve** aplicar:

```
- Se entidade é FII (pública):      result_key: ticker
- Se entidade é privada:            result_key: document_number
- Se entidade é overview single-row: result_key: id
- Se a granularidade é multi-data:  result_key: <campo natural>
```

Nunca inventar valores.
Sempre replicar padrão das entidades equivalentes.

### **3.3. **REGRAS FORMAIS — `default_date_field`**

Obrigatório quando:

* entidade é histórica, OU
* possui janelas temporais, OU
* aparece em param_inference

Exemplos:

```
default_date_field: ref_date
default_date_field: ref_month
default_date_field: payment_date
```

Snapshots sem data → não incluir.

### **3.4. Seções Opcionais**

* `presentation.kind: table|summary`
* `empty_message:`
* `order_by_whitelist:`
* `aggregations.enabled:` true/false
* `aggregations.defaults.list.limit/order`
* `responses:` (template)
* `ask:` (próxima seção)

---

## **4) Configurar `ask` e identificadores**

### **REGRAS FORMAIS — `requires_identifiers`**

O Codex deve aplicar:

```
- Se entidade exige ticker:        requires_identifiers: [ticker]
- Se entidade exige documento:     requires_identifiers: [document_number]
- Se é overview multi-ticker:      requires_identifiers: []
- Se é privada:                    requires_identifiers: [document_number]
```

### **REGRAS FORMAIS — `options.supports_multi_ticker`**

O Codex deve aplicar TRUE quando:

* entidade aceita listagem de vários tickers
* exemplo: preços, dividendos, yield, risco, rankings, overview multi

---

## **5) Criar schema**

Espelhar as colunas do entity, com:

* `string`, `number`, `integer`, `boolean`,
* ou `string + format: date|date-time`
* `required:` = chaves naturais + campos essenciais

---

## **6) Templates**

* `template.md` → sem Jinja, documento humano.
* `.md.j2` → tabela/list/summary com filtros BR.
* Rows vazios → sempre mostrar empty_message.
* Multi-data → usar namespace se necessário.

---

## **7) Catálogo**

Adicionar registro:

```
title:
kind:
paths:
coverage:
  cache_policy:
  rag_policy:
  narrator_policy:
  param_inference:
identifiers.natural_keys:
notes:
```

Privacidade, denies, comportamentos devem ser explicitados.

---

## **8) Ontologia**

Adicionar intent:

* tokens/phrases include/exclude
* entidades associadas
* pesos existentes
* nunca citar PII em entidades públicas

---

## **9) Políticas**

### Quality

* not_null
* accepted_range
* referência ao CSV
* criação de `projection_<entity>.json`

### Routing Samples

* adicionar perguntas para validar o intent

### Planner Thresholds

Seguir famílias:

* **Objetivas** → 1.0 / 0.20
* **Moderadas** → 0.8 / 0.10
* **Risco** → 0.8 / 0.00
* **Históricas/Macro** → 0.8 / 0.10
* **Privadas** → 0.8 / 0.10

### Param Inference

* default_agg
* default_window
* windows_allowed
* keywords
* privados → inference: false + bindings.document_number

### Context / Cache

* Atualizar allowed/denied conforme padrão da categoria.

### RAG

* Nunca criar collection nova.
* Apenas ponto para coleções existentes.
* Se deny, adicionar a deny_intents.

### Narrator

* `llm_enabled: false` como padrão.
* Privadas/números → desativado.

---

## **10) Consistency Report**

Atualizar:

* has_schema
* has_hints
* in_quality_policy
* in_cache_policy
* in_rag_policy
* in_narrator_policy
* has_ontology_intent
* has_param_inference
* notas (privada, deny RAG, etc.)

---

## **11) Amostras e Documentação**

* Criar `<entity>.csv` se necessário
* Atualizar `golden_set.json`
* Atualizar conceitos se for textual
* Atualizar inventário e status
* Atualizar checklist de produção

---

# ───────────────────────────────────────────────

# **VALIDAÇÃO FINAL (OBRIGATÓRIA)**

# ───────────────────────────────────────────────

Antes de responder, o Codex deve garantir:

* `<entity>.yaml` ↔ schema ↔ catalog ↔ consistency estão alinhados
* planner_thresholds e param_inference contemplam a intent
* quality_projection criado
* testes de roteamento adicionados
* templates corretos (.md e .j2)
* privacidade respeitada
* nenhum arquivo faltando

---

# ───────────────────────────────────────────────

# **SAÍDA OBRIGATÓRIA DO CODEX**

# ───────────────────────────────────────────────

Entregar somente **arquivos/diffs completos**, incluindo:

* `<entity>.yaml`
* `template.md`
* `responses/*.md.j2`
* `hints.md`
* `schema.yaml`
* `catalog.yaml`
* `entity.yaml` (ontologia)
* `quality.yaml`
* `routing_samples.json`
* `projection_<entity>.json`
* `param_inference.yaml`
* `planner_thresholds.yaml`
* `entities_consistency_report.yaml`
* `rag.yaml`
* `narrator.yaml`
* `context.yaml`
* `cache.yaml`
* `golden_set.json`
* `concepts-*.yaml`
* CSV de amostra (se fornecida)
* docs de inventário / status atualizados

Nenhuma explicação.
Nenhum texto solto.
Apenas arquivos prontos para commit.
