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
5. Entregar um dicionário determinístico para o Orchestrator (`meta['rag']`) e para o Narrator (via `narrator_rag_context` no Presenter), contendo:

   * pergunta, intent, entity
   * coleções utilizadas
   * chunks retornados
   * snapshot da policy aplicada
   * status habilitado/desabilitado e erro (quando existir)

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
  allow_intents: [fiis_noticias, fiis_financials_risk, history_market_indicators, history_b3_indexes, history_currency_rates]
```

### ✔ Verdades importantes

1. **Somente intents declaradas em `allow_intents` podem usar RAG.**
2. Se `deny_intents` contiver a intent → RAG é desativado *ainda que* esteja em `allow_intents`.
3. Intents não listadas em `allow_intents` → RAG **off**.

### Exemplo do projeto:

* Intents textuais habilitadas: `fiis_noticias`, `fiis_financials_risk`, `history_market_indicators`, `history_b3_indexes`, `history_currency_rates`.
* Intents tabulares (preços, cadastro, dividendos, rankings, processos, snapshots) entram em `deny_intents` e não usam RAG.

Resultado (recorte):

| Intent                      | RAG habilitado? |
| --------------------------- | --------------- |
| `fiis_noticias`             | ✅ Sim           |
| `fiis_financials_risk`      | ✅ Sim           |
| `history_market_indicators` | ✅ Sim           |
| `fiis_cadastro`             | ❌ Não (deny)    |
| `fiis_rankings`             | ❌ Não (deny)    |
| `client_fiis_positions`     | ❌ Não (deny)    |

---

# 5. Regras de Profile / Entities (Gate 2)

Se a intent passou pelo routing, o Context Builder aplica as regras:

1. `rag.entities` (se entity estiver mapeada)
2. `rag.default` (fallback seguro)
3. `rag.profiles` (para herdar parâmetros por perfil)

No projeto Araquem, usamos perfis e entidades explícitas:

```yaml
profiles:
  default: { k: 6, min_score: 0.20, max_context_chars: 12000 }
  macro:   { k: 4, min_score: 0.10 }
  risk:    { k: 6, min_score: 0.15 }

rag:
  entities:
    fiis_noticias:         { profile: default, collections: [fiis_noticias, concepts-fiis, concepts-risk], max_chunks: 6 }
    fiis_financials_risk:  { profile: risk,    collections: [concepts-risk, concepts-fiis], max_chunks: 5 }
    history_market_indicators: { profile: macro, collections: [concepts-macro], max_chunks: 4 }
    history_b3_indexes:    { profile: macro, collections: [concepts-macro], max_chunks: 4 }
    history_currency_rates:{ profile: macro, collections: [concepts-macro], max_chunks: 4 }
  default:
    profile: default
    max_chunks: 3
    collections: [concepts-fiis]
    min_score: 0.25
```

Se a entidade não estiver mapeada em `rag.entities`, o builder usa `rag.default` como fallback seguro.

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

1. Truncamento de chunks usando `max_context_chars` / `max_tokens`.
2. Métricas de explain baseadas no peso BM25 x Semantics.
3. Telemetria detalhada para latência de embedding e cache.
4. Ferramentas de observabilidade para `/ops/rag_debug` compartilharem o mesmo snapshot do Orchestrator.

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

O Orchestrator publica esse contexto em `meta['rag']` e o Presenter apenas o reusa; quando necessário para o Narrator, o Presenter monta um `narrator_rag_context` separado sem modificar o payload canônico.

---
