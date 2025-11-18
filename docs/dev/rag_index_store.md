# 📘 RAG Index Store — EmbeddingStore (Araquem M12)

**Módulo:** `app/rag/index_reader.py`
**Classe principal:** `EmbeddingStore`
**Papel:** Ler o índice de embeddings (`embeddings.jsonl`) em disco e expor buscas por similaridade (vetor ou texto), de forma **determinística**, **cacheada** e independente de LLM.

---

## 1. Visão Geral

O **Index Store** é a camada responsável por:

1. Ler o arquivo de embeddings em formato **JSONL** (um JSON por linha).
2. Manter um cache em memória respeitando:

   * caminho físico do arquivo,
   * hash do manifest,
   * `mtime` do arquivo (modificação em disco).
3. Expor duas operações principais:

   * `search_by_vector(qvec, k, min_score)`
   * `search_by_text(text, embedder, k)`
4. Calcular similaridade via **cosseno** entre o vetor da pergunta e o vetor do chunk.

Ele é consumido diretamente pelo `Context Builder` (`app/rag/context_builder.py`), que monta o contexto final enviado para o Narrator.

---

## 2. Formato do índice de embeddings (`embeddings.jsonl`)

Cada linha do arquivo `embeddings.jsonl` é um JSON com, no mínimo:

* `embedding`: lista de números (`List[float]`) representando o vetor do chunk.

Campos típicos usados em outras camadas:

* `text` / `content` / `body` / `snippet`: conteúdo textual do chunk.
* `collection`: coleção à qual o chunk pertence (ex.: `fiis_noticias`).
* `id`, `doc_id`, `chunk_id`, `entity`, `tags`, etc.: metadados adicionais.

Exemplo ilustrativo de uma linha:

```json
{
  "id": "row-1",
  "embedding": [0.12, -0.03, 0.44, ...],
  "text": "Notícia relevante sobre HGLG11...",
  "collection": "fiis_noticias",
  "entity": "fiis_noticias",
  "doc_id": "doc-123",
  "chunk_id": "chunk-001"
}
```

> **Importante:**
>
> * O `EmbeddingStore` exige apenas que `embedding` exista e seja um vetor válido.
> * A normalização de texto e metadados é feita pelo `Context Builder` via `_normalize_chunk`.

---

## 3. Cache e Manifest

A classe usa um cache global `_EMB_CACHE`:

```python
_EMB_CACHE = {"key": None, "rows": None, "mtime": None}
```

Na inicialização:

1. Resolve o caminho absoluto para `embeddings.jsonl`.

2. Lê o `manifest.json` no mesmo diretório e calcula um **hash** via:

   ```python
   manifest_hash = get_manifest_hash(str(manifest_path))
   ```

3. Monta uma chave de cache:

   ```python
   cache_key = (resolved_path, manifest_hash)
   ```

4. Lê `mtime` do arquivo (`stat().st_mtime`).

Se:

* o cache já tem linhas (`rows`),
* o `cache_key` atual é igual ao do cache,
* e o `mtime` não mudou (ou é compatível via `math.isclose`),

então o `EmbeddingStore` **reusa** as linhas já carregadas em memória.

Caso contrário:

* reabre o arquivo,
* lê todas as linhas,
* faz `json.loads(line)` uma a uma,
* atualiza `_EMB_CACHE`.

> Resultado:
>
> * alterações em `embeddings.jsonl` ou `manifest.json` invalidam o cache,
> * operações subsequentes reutilizam o conteúdo em memória, evitando rereads custosos.

---

## 4. Filtros básicos: `rows_with_vectors()`

Método:

```python
def rows_with_vectors(self) -> List[Dict[str, Any]]:
    """Retorna somente linhas com vetor não-vazio (sanity)."""
    return [r for r in self._rows if _has_vec(r)]
```

* `_has_vec(row)` verifica:

  * `embedding` é uma lista,
  * comprimento > 0,
  * todos os elementos são `int` ou `float`.

Esse método é usado internamente pela busca.
Linhas sem vetor válido **nunca** entram no ranking.

---

## 5. Similaridade: `_cos(a, b)`

A similaridade é calculada pelo **cosseno** entre dois vetores:

```python
dot = sum(x * y for x, y in zip(a, b))
na = sqrt(sum(x * x for x in a))
nb = sqrt(sum(x * x for x in b))
score = (dot / (na * nb)) if (na > 0 and nb > 0) else 0.0
```

Propriedades:

* vetores paralelos → score ≈ 1.0
* vetores ortogonais → score ≈ 0.0
* vetores opostos → score ≈ -1.0 (na prática, valores negativos podem ser filtrados via `min_score`).

---

## 6. Busca por vetor: `search_by_vector`

Assinatura:

```python
def search_by_vector(
    self,
    qvec: List[float],
    k: int = 5,
    min_score: float | None = None,
) -> List[Dict[str, Any]]:
```

Passos:

1. Obtém apenas linhas válidas:

   ```python
   rows = self.rows_with_vectors()
   ```

2. Calcula `(score, row)` para cada linha:

   ```python
   scored = [(_cos(qvec, r["embedding"]), r) for r in rows]
   ```

3. Ordena por `score` decrescente:

   ```python
   scored.sort(key=lambda t: t[0], reverse=True)
   ```

4. Constrói uma lista de dicts:

   ```python
   ranked = [dict(score=s, **r) for s, r in scored]
   ```

5. Se `min_score` foi definido, filtra:

   ```python
   if min_score is not None:
       ranked = [r for r in ranked if float(r.get("score", 0.0)) >= min_score]
   ```

6. Retorna apenas os `k` primeiros:

   ```python
   return ranked[:k]
   ```

> O `score` é sempre incluído no resultado (campo numérico).
> Esse campo é aproveitado pelo `Context Builder` para filtrar e pelo Narrator/Explain para transparência.

---

## 7. Busca por texto: `search_by_text`

Assinatura:

```python
def search_by_text(self, text: str, embedder, k: int = 5) -> List[Dict[str, Any]]:
    """
    Usa um cliente de embeddings compatível (ex.: OllamaClient)
    que expõe .embed([text]) -> [[float]].
    """
```

Passos:

1. Chama o cliente de embeddings:

   ```python
   vecs = embedder.embed([text]) or []
   qvec = vecs[0] if vecs and isinstance(vecs[0], list) else []
   ```

2. Em caso de exceção ou vetor vazio → retorna `[]`.

3. Caso contrário, delega para `search_by_vector(qvec, k=k)`.

> **Importante:**
>
> * Essa função não sabe nada sobre intents/entities.
> * Ela apenas converte texto em vetor e delega a busca vetorial.

---

## 8. Integração com Context Builder

O `Context Builder` usa o `EmbeddingStore` assim:

```python
from app.rag.index_reader import EmbeddingStore
from app.utils.filecache import cached_embedding_store

store: EmbeddingStore = cached_embedding_store(_RAG_INDEX_PATH)
embedder = OllamaClient()
vectors = embedder.embed([question])
qvec = vectors[0] ...
results = store.search_by_vector(qvec, k=max_chunks_val, min_score=min_score_val) or []
```

E depois normaliza os resultados via `_normalize_chunk`, montando o contexto final.

O campo `collection` de cada linha é utilizado como metadado (`used_collections` e `policy.collections`), e é configurado indiretamente via:

* `data/policies/rag.yaml` → `entities.fiis_noticias.collections = ["fiis_noticias"]`
* pipeline de indexação → coloca `collection="fiis_noticias"` em cada chunk de notícias.

---

## 9. Garantias de Testes (M12)

Os testes em `tests/rag/test_index_reader.py` exercitam:

1. **Inicialização:**

   * arquivo inexistente → `FileNotFoundError`.
2. **Filtragem:**

   * `rows_with_vectors()` descarta linhas com embedding vazio.
3. **Ranking:**

   * `search_by_vector()` ordena corretamente por similaridade.
   * `min_score` filtra resultados abaixo do threshold.
4. **Integração com embedder:**

   * `search_by_text()`:

     * usa `embedder.embed([text])`,
     * delega para `search_by_vector()`,
     * em caso de erro ou vetor vazio → retorna `[]`.

Esses testes garantem que o `EmbeddingStore` é:

* determinístico,
* seguro contra dados ruins,
* isolado de detalhes de LLM (o embedder é só uma dependência explícita).

---

## 10. Evoluções Futuras (M12+)

Possíveis incrementos, sem quebrar o contrato atual:

1. **Filtro por `collection` diretamente na busca**, usando informações da policy (`rag.entities.*.collections`).
2. Exposição de métricas internas (ex.: contagem de rows, distribuição de scores) para a camada de observabilidade.
3. Sanitização adicional de embeddings (ex.: norma zero, normalização explícita).

Qualquer evolução deve manter:

* o formato do `embeddings.jsonl` compatível,
* a API pública de `EmbeddingStore` (`rows_with_vectors`, `search_by_vector`, `search_by_text`),
* o acoplamento mínimo com o restante do RAG (Context Builder continua sendo o orquestrador de intents/entities).

---
