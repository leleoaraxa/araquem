### **Etapa 4 — Harmonização Completa do Narrator + Policies**

## **1. Objetivo da Etapa**

Garantir que o comportamento do **Narrator** (determinístico vs LLM) seja:

### ✔ 100% policy-driven

(somente `data/policies/narrator.yaml` decide o fluxo)

### ✔ Previsível

(principalmente em entidades críticas como `fiis_financials_risk`)

### ✔ Sem heurísticas ocultas

(tudo explícito, auditável e documentado)

### ✔ Com telemetria clara

(`meta['narrator']` consistente e padronizado)

### ✔ Integrado ao fluxo RAG unificado da Etapa 2

(o Presenter usa narrator_rag_context sem sobrescrever meta['rag'])

---

## **2. Escopo de Arquivos Permitidos nesta Etapa**

### **Código**

* `app/narrator/narrator.py`
* `app/narrator/prompts.py`
* `app/narrator/formatter.py` *(se necessário, ajustes mínimos)*
* `app/presenter/presenter.py` *(apenas se necessário adicionar campos de strategy)*

### **Policies**

* `data/policies/narrator.yaml`

### **Documentação**

* `docs/dev/NARRATOR_REDESIGN_PLAN.md`
* `docs/dev/RUNTIME_OVERVIEW.md` (seção narrador)

### **❌ Proibido alterar**

* Orchestrator (`routing.py`)
* RAG (`context_builder.py`, etc.)
* Planner
* Builder / Executor / Formatter
* Entities, contratos, views, ontologia

---

## **3. Problemas Observados (baseados no lote 1–6 + patches anteriores)**

### **3.1. Effective policy não é fonte única da verdade**

O Narrator mistura:

* flags globais (`llm_enabled`, `shadow`)
* flags por entidade
* fallback implícito

❌ Isso gera condições onde o LLM responde mesmo quando a policy por entidade deveria impedir.

---

### **3.2. `meta['narrator']` ainda não é padronizado**

Exposição inconsistente:

* `used`
* `strategy`
* `enabled`
* `shadow`
* `error`
* `rag`
* `model`

Faltam motivos explícitos de fallback:

* `llm_disabled_by_policy`
* `llm_skipped_rows_limit`
* `client_unavailable`
* `rag_suppressed_by_policy`
* etc.

---

### **3.3. Uso de RAG no Narrator ainda é ambíguo**

Mesmo com Etapa 2 implementada:

* RAG do Presenter e RAG do Orchestrator podem divergir nos formatos e políticas
* O Narrator ainda pode acidentalmente incluir chunks em prompts quando não deveria

Entidade `fiis_financials_risk` deve **NUNCA** usar RAG no prompt.

---

### **3.4. Estratégia do Narrator não está explícita**

Hoje existe:

* determinístico (baseline)
* shadow
* llm

Mas falta padronização e semântica formal.

---

## **4. Objetivos da Etapa 4**

### **4.1. Single source of truth: effective policy**

Implementar, revisar e travar:

```python
effective = _get_effective_policy(entity, global_policy)
```

E tudo (tudo!) no Narrator deve honrar:

* `effective['llm_enabled']`
* `effective['shadow']`
* `effective['max_llm_rows']`
* `effective['use_rag_in_prompt']`
* `effective['model']`

---

### **4.2. Estratégia explicitamente definida e documentada**

Adicionar padrões formais:

```
deterministic
llm
llm_shadow
llm_disabled_by_policy
llm_skipped_max_rows
llm_failed
rag_forbidden_by_policy
```

E **tudo** deve aparecer em `meta['narrator']['strategy']`.

---

### **4.3. Campos padronizados no meta do Narrator**

Formato final desejado:

```json
"narrator": {
    "enabled": bool,
    "shadow": bool,
    "model": "llama3.1:latest",
    "latency_ms": 12.5,
    "error": null,
    "used": false,
    "strategy": "deterministic",
    "effective_policy": {
        "llm_enabled": false,
        "shadow": false,
        "max_llm_rows": 0,
        "use_rag_in_prompt": false
    },
    "rag": { ... narrator_rag_context ... }
}
```

---

### **4.4. Revisão rigorosa de `data/policies/narrator.yaml`**

Padrão desejado:

```yaml
version: 1

default:
  llm_enabled: false
  shadow: false
  model: llama3.1:latest
  max_llm_rows: 0
  use_rag_in_prompt: false

entities:
  fiis_financials_risk:
    llm_enabled: false
    shadow: false
    max_llm_rows: 0
    use_rag_in_prompt: false
  fiis_noticias:
    llm_enabled: true
    shadow: false
    max_llm_rows: 5
    use_rag_in_prompt: true
```

---

### **4.5. Revisão do `prompts.py` para respeitar `use_rag_in_prompt`**

Regra:

**Se `effective_policy['use_rag_in_prompt'] == False`, RAG não entra no prompt em hipótese alguma.**

---

### **4.6. Assegurar que baseline é sempre calculado**

O Presenter já faz isso corretamente — apenas garantir que o Narrator nunca possa sobrepor sem permissão.

---

## **5. Lista Completa de Modificações Permitidas**

### **5.1. Em `narrator.py`**

* Implementar effective policy unificada
* Padronizar decision tree:

  ```
  1. Nunca usar LLM se llm_enabled == False
  2. Nunca usar LLM se rows > max_llm_rows
  3. Nunca usar RAG em prompt se use_rag_in_prompt == False
  4. Shadow não altera answer
  ```
* Sempre registrar estratégia explícita
* Sempre retornar `effective_policy` no meta

### **5.2. Em `prompts.py`**

* Inserir `if not effective_policy.use_rag_in_prompt: rag = None`
* Documentar claramente a regra
* Tirar qualquer heurística escondida

### **5.3. Em `narrator.yaml`**

* Reescrever seguindo o padrão acima
* Garantir defaults seguros
* Garantir política rígida para `fiis_financials_risk`

### **5.4. (Opcional) Ajustes mínimos no Presenter**

Apenas se necessário passar `effective_policy` ao Narrator.

### **5.5. Documentação**

* Atualizar RUNTIME_OVERVIEW (seção Narrator)
* Atualizar NARRATOR_REDESIGN_PLAN
* Criar tabela de estratégias do Narrator

---

## **6. Testes Necessários (obrigatórios)**

### **6.1. Testes unitários (Novos)**

* `test_narrator_effective_policy.py`
* `test_narrator_strategy_matrix.py`
* `test_narrator_rag_suppression.py`

### **6.2. Testes end-to-end (Manuais ou Automação)**

* Pergunta de risco → deve ser sempre determinístico
* Notícias → deve usar LLM com RAG
* Pergunta tabular (ex.: dividendos) → determinístico

---

## **7. Resultado Esperado da Etapa 4**

Ao final desta etapa, o Narrator deve:

### ✔ Ser completamente governado por policy

sem exceções, sem heurísticas, sem marretas

### ✔ Ter saída padronizada, auditável, previsível

### ✔ Ser totalmente compatível com o fluxo unificado do RAG

### ✔ Estar pronto para Etapa 5 (sweep de contratos/entities/views)
