# 📘 RAG Context Builder — Documentação Técnica (Araquem M12)

**Módulo:** `app/rag/context_builder.py`
**Papel:** Construir, de forma determinística, o contexto textual utilizado pelo Narrator e pelas camadas de explicabilidade.
**Fonte de verdade:** `data/policies/rag.yaml` (política de RAG).

---

# 1. Visão Geral

O **Context Builder** é responsável por:

1. **Verificar se o RAG deve ser habilitado** para uma pergunta, usando as políticas definidas em `rag.yaml`.
2. **Gerar embeddings da pergunta** usando o `OllamaClient`.
3. **Consultar o EmbeddingStore** para recuperar os chunks relevantes.
4. **Normalizar** os chunks (texto + metadados).
5. Entregar um dicionário determinístico para o Narrator, contendo:

   * pergunta, intent, entity
   * coleções utilizadas
   * chunks retornados
   * snapshot da policy aplicada
   * status habilitado/desabilitado

O módulo **nunca chama LLM**. É 100% determinístico e testável.

---

# 2. Pipeline Interno

Fluxo simplificado:

```
Planner → Orchestrator → Context Builder → Narrator/Explain
```

O Context Builder atua exatamente no ponto onde o sistema decide:

* **usar RAG** (para intenções textuais, como notícias); ou
* **não usar RAG** e seguir com dados SQL estruturados (cadastro, preços, dividendos, métricas…).

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
  allow_intents: [fiis_noticias]
```

### ✔ Verdades importantes

1. **Somente intents declaradas em `allow_intents` podem usar RAG.**
2. Se `deny_intents` contiver a intent → RAG é desativado *ainda que* esteja em `allow_intents`.
3. Intents não listadas em `allow_intents` → RAG **off**.

### Exemplo do projeto:

* Apenas `fiis_noticias` é permitido.
* Tudo que é tabular (preços, cadastro, dividendos, rankings, processos, financials…) entra em `deny_intents`.

Resultado:

| Intent                  | RAG habilitado? |
| ----------------------- | --------------- |
| `fiis_noticias`         | ✅ Sim           |
| `fiis_cadastro`         | ❌ Não (deny)    |
| `fiis_rankings`         | ❌ Não (deny)    |
| `fiis_dividendos`       | ❌ Não (deny)    |
| `client_fiis_positions` | ❌ Não (deny)    |

---

# 5. Regras de Profile / Entities (Gate 2)

Se a intent passou pelo routing, o Context Builder aplica as regras:

1. `rag.entities` (se entity estiver mapeada)
2. `rag.default` (não usado no projeto atual)
3. `rag.profiles` (fallback principal)

No projeto Araquem, usamos:

```yaml
profiles:
  default:
    k: 5
    min_score: 0.20
    max_context_chars: 12000
```

Como não há `entities` nem `default`, **todo RAG permitido usa `profiles.default`**.

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
  }
}
```

### Se RAG estiver desativado:

```json
{
  "enabled": false,
  "chunks": [],
  "total_chunks": 0
}
```

---

# 8. Segurança e determinismo

O módulo foi projetado segundo o **Guardrails Araquem v2.1.1**:

* Nenhum fallback heurístico.
* Nenhum hardcode.
* Política externa (YAML) é **única fonte de verdade**.
* Embedding vazio ou erro na store → retorna RAG disabled com warning, nunca explode.
* Narrator só recebe chunks se houver política explícita.

---

# 9. Testes (M12)

Os testes oficiais do M12 cobrem:

* `is_rag_enabled` com e sem `entities`
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

1. Suporte a entidades específicas no RAG (`rag.entities`).
2. Suporte a perfis múltiplos (`profile: default | ambiguous`).
3. Suporte real a `collections` para filtrar o store.
4. Truncamento de chunks usando `max_context_chars`.
5. Métricas de explain baseadas no peso BM25 x Semantics.

Essas evoluções seguem o Guardrails Araquem e serão abordadas em milestones seguintes.

---

# 11. Contato do módulo

Para integração:

```python
from app.rag.context_builder import build_context, is_rag_enabled
```

Chamado internamente pelo Orchestrator:

```python
ctx = build_context(
    question=question,
    intent=meta.intent,
    entity=meta.entity,
)
```

---
