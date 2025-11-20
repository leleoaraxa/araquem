# **NARRATOR_REDESIGN_PLAN.md**

### *Redesign completo do fluxo do Narrator — Arquitetura final (pós-auditoria M12/M13)*

---

# **1. Objetivo do redesign**

Este documento define **a nova arquitetura do Narrator**, corrigindo os problemas encontrados no fluxo atual, sem alterar o comportamento externo do Araquem (mesma API/contratos), mas eliminando:

* caminhos duplicados de RAG
* prompt excessivamente grande
* contradições entre SYSTEM_PROMPT e snippets
* vazamento de textos conceituais do RAG
* uso indevido do LLM quando o renderer determinístico já é suficiente
* duplicidade entre baseline, rendered_text e RAG
* decisões espalhadas no código (orchestrator + presenter + narrator)

O resultado é um **Narrator preditivo, minimalista, sem marretas, 100% policy-driven**.

---

# **2. Redesign: Nova Arquitetura Global**

A partir desta fase, todo o fluxo será reorganizado em **três grandes camadas com responsabilidades claras**:

---

## **2.1. CAMADA 1 — Data Layer (Orchestrator + Presenter)**

### **Responsabilidade única: entregar dados estruturados (FACTS)**

Sem RAG.
Sem texto conceitual.
Sem narrativa.
Sem prompt.

### Novo contrato:

```json
facts = {
  "result_key": "...",
  "primary": {...},
  "rows": [...],
  "requested_metrics": [...],
  "identifiers": {...},
  "aggregates": {...}
}
```

### O que sai desta camada:

✔ SQL executado
✔ rows
✔ primary
✔ agregados
✔ ticker(s)

### O que NÃO sai mais:

❌ RAG
❌ rendered_text
❌ texto explicativo
❌ narrativa pré-montada

---

## **2.2. CAMADA 2 — RAG Layer (Builder Único)**

### **NOVO padrão: somente o Narrator pode pedir contexto RAG.**

Elimina totalmente:

* build_rag_context no Orchestrator
* hints carregados duas vezes
* rag_context criado no presenter

### Novo fluxo:

```
Narrator.render → RAG.builder(context)
```

### RAG.builder fará:

* carregar rag.yaml
* verificar se intent/entity tem coleção permitida
* gerar embedding da pergunta
* recuperar *snippets*
* truncar textos
* retornar **RAG_CONTEXT minimalista**

Formato final:

```json
rag_context = {
  "enabled": true|false,
  "snippets": [
      {"score": 0.68, "text": "...truncado..."},
      {"score": 0.52, "text": "...truncado..."}
  ]
}
```

### Limites rígidos:

* Máximo 3 snippets
* Cada snippet máx 300 chars
* Nunca incluir YAML dos goldens, config ou samples
* Nunca incluir código

---

## **2.3. CAMADA 3 — Narrator (Unique Brain)**

### Narrator agora decide TUDO:

* se usa conceito puro
* se usa dados
* se combina conceito + dados
* se aciona o LLM
* se usa texto determinístico
* como montar o prompt
* COMO e QUANDO usar RAG

#### Regras finais:

### **3.3.1. Ordem de decisão**

1. **Caso 1 — Modo Conceitual**

   * Pergunta sem ticker
   * Política da entidade define prefer_concept_when_no_ticker
   * Resultado: usa apenas conceitos (do renderer ou RAG)
   * Sem rows
   * Sem baseline “linhas formatadas”

2. **Caso 2 — Renderer Determinístico**

   * Sempre executado
   * Se produzido, vira baseline

3. **Caso 3 — RAG Fallback**

   * Apenas se `rows` estiver vazio
   * E se entidade permitir: `rag_fallback_when_no_rows: true`

4. **Caso 4 — LLM**

   * Somente se:

     * LLM habilitado
     * número de linhas <= max_llm_rows
     * nunca em modo conceitual puro
   * LLM funciona como “polidor”
   * Não pode introduzir novos conceitos
   * Só pode reescrever baseline + contexto estruturado

---

# **3. Redesign: Novo SYSTEM_PROMPT minimalista**

### **Antes: 460+ linhas**

Repete instruções, samples, estilos, proibições.

### **Depois: 14 linhas**

Seguro, enxuto, sem ambiguidade.

```
Você é o Narrator do Araquem.
Sua função é transformar dados estruturados (FACTS) em texto claro,
objetivo e útil para o usuário, mantendo precisão total.

Regras:
1. Nunca copie trechos literais de RAG_CONTEXT.
2. Você pode usar o RAG apenas como reforço conceitual,
   nunca como fonte de texto.
3. Nunca invente números, datas ou métricas.
4. Priorize sempre FACTS → depois conceito → por último estilo.
5. Responda sempre em português do Brasil.
6. Entregue apenas o texto final, sem explicação do processo.

Saída: texto único, compacto e direto.
```

---

# **4. Redesign: Novo build_prompt()**

### Estrutura final:

```
SYSTEM_PROMPT

[PERGUNTA]
<texto da pergunta>

[FACTS]
<JSON estruturado pequeno>

[CONCEITO]
<Texto determinístico curto gerado internamente>

[RAG_SUPPORT]
<Lista de “ideias úteis” derivadas dos snippets,
NUNCA trechos literais>

[INSTRUÇÃO FINAL]
"Reescreva tudo acima como um único texto, limpo, natural e compacto."
```

### Observações:

❌ RAG_CONTEXT literal sai
❌ Few-shots saem
❌ Templates de listas/tabelas saem
❌ apresentação/estilo replicado sai

✔ O contexto é convertido para *labels conceituais*, não texto
✔ Prompt fica com < 1.500 tokens sempre

---

# **5. Nova regra de RAG → Texto**

Cada snippet é transformado em **IDEIA**, não TEXTO.

Exemplo:

Snippet RAG:

```
"Sharpe Ratio mede retorno excedente dividido pela volatilidade"
```

Convertido para “apenas o conceito”:

```
- contextualizar que Sharpe Ratio relaciona retorno excedente e volatilidade
```

O modelo nunca vê o texto original.
Logo, nunca copia.

---

# **6. Eliminação de redundâncias**

### O que sai:

* rag_context do orchestrator
* rag_context do presenter
* rendered_text duplicado
* SYSTEM_PROMPT gigantesco
* few-shots
* templates HTML-like
* snippets literais
* duplicidade facts.primary + facts.rows
* builder de RAG duplo

### O que fica:

* facts completo, determinístico
* renderer determinístico específico da entidade
* rag_context minimalista
* narrator policy única
* prompt minimalista

---

# **7. Plano de implementação (em ordem correta)**

Este documento não contém código — apenas arquitetura.

### **Fase 1 — Cleanup**

1. Remover criação de RAG do Orchestrator
2. Remover criação paralela no Presenter
3. Criar módulo único: `app/rag/context_provider.py`

### **Fase 2 — Narrator**

4. Simplificar SYSTEM_PROMPT
5. Reescrever build_prompt
6. Criar conversor RAG → IDEA
7. Criar novo modo conceitual

### **Fase 3 — Testes**

8. Validar explain=true
9. Testar com LLM desligado e ligado
10. Testar 10 entidades diferentes
11. Validar ausência de trechos literais
12. Criar golden samples atualizados

---

# **8. Resultado final esperado**

Depois do redesign:

✔ Prompt 5–7× menor
✔ RAG nunca copiável
✔ Narrativa consistente
✔ Arquitetura limpa
✔ Fluxo sem duplicidades
✔ Comportamento 100% policy-driven
✔ Zero marreta
✔ Alta previsibilidade
✔ Fácil manutenção
✔ Fácil depuração
✔ Custo de LLM reduzido
