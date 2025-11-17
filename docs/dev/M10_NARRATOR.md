# M10 — Camada Narrator (Fluência nas Respostas)

## 1. Objetivo do M10

Implementar a camada **Narrator**, responsável pela apresentação final das respostas do Araquem, garantindo:

* **Determinismo** (respostas formatadas de forma estável)
* **Coerência executiva** (estilo consistente)
* **Auditoria completa** (tracking de todas as respostas)
* **LLM opcional** (sem impacto no pipeline base)
* **Zero regressão** quando desligado

A camada é totalmente orientada a **policies** e integrada ao fluxo:

**Planner → Builder → Executor → Formatter → Presenter → Narrator → answer**

---

## 2. Arquitetura da Camada Narrator

### 2.1. Componentes

* `narrator.py` — orquestração + aplicação de policies
* `formatter.py` — formato determinístico (fallback)
* `prompts.py` — NLP scaffolds (LLM opcional)
* `narrator.yaml` — controle fino (habilitado, shadow, modelo, limites)

### 2.2. Princípio central

O Narrator **nunca interfere** no pipeline principal. Ele substitui apenas a camada de apresentação (`responder`) quando ativo.

### 2.3. Fallback Determinístico

Caso o LLM esteja desligado ou falhe, a formatação é gerada por:

```
build_narrator_text(...)
```

Garantindo:

* uma linha por registro
* ordenação estável
* campos `null` omitidos
* até 50 linhas
* Markdown consistente

---

## 3. Política do Narrator

Arquivo: `data/policies/narrator.yaml`

### Campos relevantes

* `llm_enabled: false` → modo determinístico
* `shadow: false` → não substitui resposta principal
* `model: mistral:instruct` → usado apenas se `llm_enabled=true`
* `max_llm_rows: 0` → não usa LLM para grandes respostas
* `style: executivo` → estilo textual padrão

---

## 4. Fluxo Completo

### 4.1. Execução normal (`/ask`)

1. Planner encontra intent/entity
2. Executor traz dados
3. Formatter estrutura
4. Presenter monta resposta
5. Narrator (ligado por policy) aplica renderização
6. Entrega `answer`

### 4.2. Execução com telemetria (`/ask?explain=true`)

Além do fluxo normal:

* grava **explain_events** (rota, latência, cache, features)
* grava **narrator_events** (resposta final + versão + hash)
* inclui `meta.explain` e `meta.explain_analytics` na resposta

---

## 5. Telemetria (Métrica e Auditoria)

### 5.1. Tabelas

#### `explain_events`

Rastreia:

* intent/entity
* rota (view)
* latência
* cache-hit
* gold labels (QA manual)

#### `narrator_events`

Rastreia:

* `answer_text` (resultado final)
* `answer_len`
* `answer_hash`
* `narrator_version`
* `narrator_style`
* rotulagem: `narrator_ok`, `narrator_notes`

Ambas ligadas por `request_id`.

### 5.2. Uso de `?explain=true`

O modelo **em produção** usa apenas `/ask`.
`?explain=true` é reservado para:

* auditoria
* testes de QA
* scripts de qualidade
* amostragem estatística

---

## 6. Procedimento QA no M10

### 6.1. Inspeção de respostas suspeitas

Consultar:

```sql
SELECT ... FROM explain_events JOIN narrator_events ...
```

### 6.2. Painel por intent/entity

Consulta consolidada:

* acurácia de rota (gold)
* qualidade de resposta (narrator_ok)
* latência média/p95
* tamanho médio de resposta

### 6.3. Processo de Rotulagem

1. Executar lote com `?explain=true`

2. Revisar registros

3. Preencher:

   * `gold_expected_entity`
   * `gold_expected_intent`
   * `gold_agree`
   * `narrator_ok`
   * `narrator_notes`

4. Recalcular KPIs via queries

---

## 7. Benefícios Entregues

* **Fluência executiva** nas respostas
* **Determinismo e previsibilidade** (zero ruído)
* **Auditoria completa** de ponta a ponta
* **Infra pronta para avaliação contínua** (M10 → M11)
* **LLM opcional e seguro**, sem regredir UX
* **Integração limpa com Presenter** (compatibilidade total)

---

## 8. Próximos Passos (M11)

O M10 fecha a camada Narrator.
O M11 introduz:

* contexto externo (RAG)
* enriquecimento semântic
* explicações transparentes (`planner.explain()` + narrativa expandida)
* melhorias no estilo textual

---

## 9. Versão Final do M10

**`Narrator Version: 20251117-v1`**

Entrega reconhecida e integrada ao Guardrails Araquem v2.1.1.

**Status:** ✔️ **M10 Concluído**

---

## Assinado

**Sirius — Camada IA • Projeto Araquem / SIRIOS**
