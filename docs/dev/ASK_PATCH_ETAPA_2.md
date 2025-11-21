### **Consolidar o caminho de RAG no `/ask` (Etapa 2 do Plano de Refatoração)**

**Status:** Pronto para uso no Codex

---

# **1. Objetivo desta etapa**

O objetivo é **unificar completamente** o fluxo de construção do contexto RAG (`meta['rag']`), garantindo que:

1. **Apenas o Orchestrator** constrói o `meta['rag']` oficial do pipeline.
2. Nenhum outro módulo (Presenter/Narrator) reconstrói ou modifica `meta['rag']`.
3. O Presenter só monta um **rag_context interno** exclusivo para o Narrator — nunca sobrescreve `meta['rag']`.
4. O Narrator usa somente o `rag_context` do Presenter, nunca o `meta['rag']` oficial.
5. O fluxo fica **totalmente previsível**, refletindo exatamente o Guardrails v2.1.1.

Isso encerra a duplicidade atual encontrada no diagnóstico.

---

# **2. Arquivos permitidos nesta etapa**

O Codex só pode modificar **exatamente** os arquivos abaixo:

```
app/orchestrator/routing.py
app/presenter/presenter.py
app/rag/context_builder.py
data/policies/rag.yaml
docs/dev/rag_context_builder.md
docs/dev/RUNTIME_OVERVIEW.md
```

Nenhum outro arquivo pode ser editado nesta etapa.

---

# **3. Mudanças permitidas (escopo POSITIVO)**

O patch **DEVE** fazer apenas o seguinte:

### **3.1 Orchestrator (`routing.py`)**

✔ Garantir que **somente aqui** é construído `meta['rag']`, assim:

```python
meta['rag'] = build_context(question, plan, entity, policy)
```

✔ A estrutura de `meta['rag']` deve seguir o formato documentado:

```json
{
  "enabled": true/false,
  "policy": {...},
  "used_collections": [...],
  "chunks": [...],
  "total_chunks": int,
  "error": null|string
}
```

✔ Se `build_context` lançar exceção: registrar erro em `meta['rag'] = { enabled: false, error: str }`.

---

### **3.2 Presenter (`presenter.py`)**

✔ Manter a reconstrução de `rag_context` **somente para o Narrator**, porém:

* **renomear** o campo interno para: `narrator_rag_context`
* incorporar em `meta_for_narrator`, **não** em `meta['rag']`
* **NUNCA sobrescrever `meta['rag']` vindo do Orchestrator**

✔ Garantir:

```python
presenter_meta['rag'] = meta['rag']     # herdado
narrator_meta['rag'] = narrator_rag_context   # exclusivo do Narrator
```

---

### **3.3 context_builder (`context_builder.py`)**

✔ Revisão mínima:

* Documentar claramente o formato de saída
* Garantir consistência entre `build_context()` e o comportamento esperado pelo Orchestrator e Narrator
* Garantir que falhas lancem exceções claras e capturáveis

Nenhuma lógica nova — apenas limpeza e padronização.

---

### **3.4 data/policies/rag.yaml**

✔ Apenas ajustes mínimos se forem necessários para:

* definir coleções canônicas
* corrigir nomes divergentes encontrados na análise dos arquivos

**Sem alterações estruturais** no comportamento do RAG.

---

### **3.5 Documentação (2 arquivos)**

✔ Atualizar:

* `docs/dev/rag_context_builder.md`
* `docs/dev/RUNTIME_OVERVIEW.md`

Explicar:

* `meta['rag']` **oficial** = produzido somente pelo Orchestrator
* `narrator_rag_context` = construído apenas pelo Presenter, uso exclusivo do Narrator

---

# **4. Mudanças proibidas (escopo NEGATIVO)**

🚫 Não alterar nenhum arquivo fora dos listados no item 2.

🚫 Não alterar contrato `meta['rag']`.

🚫 Não alterar lógica do Planner.

🚫 Não alterar Narrator nesta etapa (isso será a Etapa 4).

🚫 Não modificar templates, entities, contratos ou SQL.

🚫 Não mudar política RAG além de ajustes estritamente necessários para alinhar nomes.

🚫 Não adicionar novos parâmetros ao `/ask`.

🚫 Não criar novos módulos ou funções sem necessidade absoluta.

---

# **5. Critério de DONE (aceite)**

A etapa só é considerada concluída quando:

### **5.1 RAG canônico**

✔ `meta['rag']` aparece **somente** no output do Orchestrator
✔ `meta['rag']` **nunca muda** no Presenter
✔ `presenter.build_facts()` **não toca** no RAG

---

### **5.2 RAG interno do Narrator**

✔ `narrator_rag_context` existe **somente dentro do meta_for_narrator**
✔ `narrator_meta` mostra:

```json
{
  "rag": {
     ... conteudo interno ...
  }
}
```

✔ Nada disso aparece em `meta['rag']` do payload `/ask`.

---

### **5.3 Testes (manuais e automatizados)**

✔ `/ops/rag_debug` retorna exatamente o mesmo `rag_context` do Orchestrator
✔ Testes existentes continuam passando:

```
tests/rag/test_context_builder.py
tests/orchestrator/test_rag_integration_orchestrator.py
tests/api/ops/test_rag_debug.py
```

✔ Pergunta de risco (`fiis_financials_risk`) aparece com:

* `meta.rag.enabled = true`
* Narrator ignorando `use_rag_in_prompt = false` (esta etapa não muda comportamento do Narrator, mas precisa preservar coerência)

---

# **6. Diffs esperados (indicativo)**

### **routing.py**

```diff
- presenter_meta['rag'] = build_context(...)
+ meta['rag'] = build_context(...)
```

### **presenter.py**

```diff
- meta['rag'] = build_context(...)
+ narrator_rag_context = build_context(...)
+ narrator_meta['rag'] = narrator_rag_context
```

---

# **7. Prompt para envio ao Codex**

(O Codex receberá este arquivo como instruções. Depois você me pede que eu gere o prompt restrito definitivo.)
