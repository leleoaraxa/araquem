# 📘 RAG Context Builder — Documentação Técnica (Araquem M12)

**Módulo:** `app/rag/context_builder.py`
**Papel:** Construir, de forma determinística, o contexto textual utilizado pelo Narrator e pelas camadas de explicabilidade.
**Fonte de verdade:** `data/policies/rag.yaml` (política de RAG).

> **Estado atual (2025):** RAG está **desligado por policy**. O Context Builder ainda é chamado pelo Orchestrator para gerar o `meta.rag` canônico (indicando `enabled=False` e a razão), mas **não calcula embeddings nem consulta índices**.

---

# 1. Visão Geral

O **Context Builder** é responsável por:

1. **Aplicar a policy de RAG** para decidir se o recurso pode ser habilitado.
2. **Gerar o `meta.rag` determinístico** com intent/entity, snapshot da policy e o estado (`enabled`/`reason`).
3. **Somente quando a policy libera**: gerar embeddings da pergunta e consultar o `EmbeddingStore`.

Com a policy atual (`allow_intents=[]` e `rerank.enabled=false`), o fluxo encerra no passo 1 e retorna `meta.rag` com `enabled=False` sem chamar `OllamaClient` ou carregar índices. O módulo **nunca chama LLM**.

---

# 2. Pipeline Interno

Fluxo simplificado:

```
Planner → Orchestrator → Context Builder → Narrator/Explain
```

O Context Builder atua exatamente no ponto onde o sistema decide:

* **não usar RAG** (estado atual, negado por policy) e seguir com dados SQL estruturados; ou
* **usar RAG** (apenas se a policy for flexibilizada para intents textuais) antes de enviar contexto ao Narrator.

---

# 3. Carregamento da Política (`rag.yaml`)

A política é carregada em:

```python
load_rag_policy()  # lê data/policies/rag.yaml
```

Se houver erro no YAML → retorna `{}` e desativa RAG para garantir segurança.

Estrutura mínima esperada:

```yaml
version: 1

profiles:
  default: {...}
  ambiguous: {...}

routing:
  deny_intents: [...]
  allow_intents: [...]
```

> **Observação:** A chave `terms:` é ignorada pelo Context Builder (usada apenas por validadores externos).

---

# 4. Regras de Routing (Gate 1)

O primeiro gate sempre é o **routing**, localizado em `rag.yaml`:

```yaml
routing:
  deny_intents: [...]
  allow_intents: []
```

### ✔ Verdades importantes

1. **Com `allow_intents=[]`, todas as intents atuais resultam em RAG negado.**
2. Se no futuro `allow_intents` receber intents textuais, a negação continua valendo para intents presentes em `deny_intents`.
3. Enquanto a policy seguir vazia, o Context Builder apenas registra `enabled=False` no `meta.rag` e encerra.

---

# 5. Regras de Profile / Entities (Gate 2)

Se a intent passar pelo routing (não ocorre no estado atual), o Context Builder aplica as regras:

1. `rag.entities` (se entity estiver mapeada)
2. `rag.default` (fallback seguro)
3. `rag.profiles` (para herdar parâmetros por perfil)

Com o gate fechado, a seleção de perfis não é utilizada e os parâmetros retornados no `meta.rag` refletem apenas a policy aplicada (incluindo `enabled=False` e `reason`).

---

# 6. Normalização dos chunks

Os chunks recuperados do `EmbeddingStore` passam por:

```python
_normalize_chunk(item)
```

Que garante:

* `text` sempre presente (usa chaves: `text`, `content`, `body`, `snippet`)
* `score` convertido para float
* preservação dos metadados:

  * `doc_id`
  * `chunk_id`
  * `collection`
  * `entity`
  * `source_id`
  * `tags`

Isso garante consistência no Narrator e no explain.

---

# 7. Estrutura do Resultado (`build_context`)

Formato retornado:

```json
{
  "enabled": true | false,
  "question": "...",
  "intent": "...",
  "entity": "...",
  "used_collections": ["..."],
  "chunks": [ {text, score, doc_id, ...} ],
  "total_chunks": N,
  "policy": {
    "max_chunks": 5,
    "min_score": 0.20,
    "max_tokens": 12000,
    "collections": [...]
  },
  "error": null
}
```

### Se RAG estiver desativado:

```json
{
  "enabled": false,
  "chunks": [],
  "total_chunks": 0,
  "error": null
}
```

---

# 8. Segurança e determinismo

O módulo foi projetado segundo o **Guardrails Araquem v2.1.1**:

* Nenhum fallback heurístico.
* Nenhum hardcode.
* Política externa (YAML) é **única fonte de verdade**.
* Embedding vazio ou erro na store → retorna RAG disabled com warning, nunca explode.
* Narrator só recebe chunks se houver política explícita. O contexto canônico (`meta['rag']`) é gerado pelo Orchestrator; o Presenter pode gerar um `narrator_rag_context` separado apenas para uso interno do Narrator.

---

# 9. Testes (M12)

Os testes oficiais do M12 cobrem:

* `get_rag_policy` com e sem `entities`
* `routing.allow_intents` e `deny_intents`
* `build_context` com RAG off (não chama embeddings)
* `build_context` com RAG on usando mocks de:

  * `cached_embedding_store`
  * `OllamaClient`

Isso garante que:

* O gating está correto.
* O módulo é determinístico.
* A resposta sempre segue o mesmo formato.
* Políticas externas realmente comandam o comportamento.

---

# 10. Evoluções previstas (M12 → M13)

1. Truncamento de chunks usando `max_context_chars` / `max_tokens`.
2. Métricas de explain baseadas no peso BM25 x Semantics.
3. Telemetria detalhada para latência de embedding e cache.
4. Ferramentas de observabilidade para `/ops/rag_debug` compartilharem o mesmo snapshot do Orchestrator.

Essas evoluções seguem o Guardrails Araquem e serão abordadas em milestones seguintes.

---

# 11. Contato do módulo

Para integração:

```python
from app.rag.context_builder import build_context, get_rag_policy
```

Chamado internamente pelo Orchestrator:

```python
ctx = build_context(
    question=question,
    intent=meta.intent,
    entity=meta.entity,
)
```

O Orchestrator publica esse contexto em `meta['rag']` e o Presenter apenas o reusa; quando necessário para o Narrator, o Presenter monta um `narrator_rag_context` separado sem modificar o payload canônico.

---
