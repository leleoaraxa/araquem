# tests/rag/test_index_reader.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import math
import pytest

from app.rag import index_reader


@pytest.fixture
def reset_emb_cache() -> None:
    """Reseta o cache global entre os testes para evitar interferência."""
    index_reader._EMB_CACHE["key"] = None
    index_reader._EMB_CACHE["rows"] = None
    index_reader._EMB_CACHE["mtime"] = None


@pytest.fixture
def embeddings_jsonl(
    embeddings_path: Path, monkeypatch: pytest.MonkeyPatch, reset_emb_cache: None
) -> Path:
    """Cria um arquivo JSONL de embeddings simples para testes."""

    # Força o manifest hash para um valor estável
    monkeypatch.setattr(
        index_reader, "get_manifest_hash", lambda manifest_path: "dummy-hash"
    )

    path = embeddings_path / "embeddings.jsonl"

    rows: List[Dict[str, Any]] = [
        {
            "id": "row-1",
            "embedding": [1.0, 0.0],
            "text": "primeiro chunk",
            "collection": "fiis_noticias",
        },
        {
            "id": "row-2",
            "embedding": [0.0, 1.0],
            "text": "segundo chunk",
            "collection": "fiis_noticias",
        },
        {
            "id": "row-3",
            # embedding vazio -> deve ser ignorado por rows_with_vectors()
            "embedding": [],
            "text": "sem vetor",
            "collection": "outra_colecao",
        },
    ]

    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Também cria um manifest.json vazio só para existir no path esperado
    manifest_path = path.parent / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    return path


def test_embedding_store_raises_if_file_not_found(
    embeddings_path: Path, reset_emb_cache: None
) -> None:
    """Se o arquivo JSONL não existir, a classe deve levantar FileNotFoundError."""
    missing = embeddings_path / "nao_existe.jsonl"
    with pytest.raises(FileNotFoundError):
        index_reader.EmbeddingStore(str(missing))


def test_rows_with_vectors_filters_empty_embeddings(embeddings_jsonl: Path) -> None:
    """rows_with_vectors deve descartar linhas sem vetor válido."""
    store = index_reader.EmbeddingStore(str(embeddings_jsonl))
    rows = store.rows_with_vectors()

    # Apenas as duas primeiras linhas têm embedding não-vazio
    ids = {r["id"] for r in rows}
    assert ids == {"row-1", "row-2"}
    # Garante que nenhuma linha com embedding vazio entrou
    assert all(len(r["embedding"]) > 0 for r in rows)


def test_search_by_vector_orders_by_cosine_similarity(embeddings_jsonl: Path) -> None:
    """search_by_vector deve ordenar pelos scores de similaridade em ordem decrescente."""
    store = index_reader.EmbeddingStore(str(embeddings_jsonl))

    # Vetor de consulta paralelo ao embedding de row-1
    qvec = [1.0, 0.0]
    results = store.search_by_vector(qvec, k=2)

    assert len(results) == 2
    # A primeira posição deve ser a mais similar (row-1)
    assert results[0]["id"] == "row-1"
    assert results[1]["id"] == "row-2"

    # Score de row-1 deve ser 1.0 (mesma direção e norma)
    assert math.isclose(results[0]["score"], 1.0, rel_tol=1e-6)
    # Score de row-2 deve ser 0.0 (ortogonal ao vetor [1, 0])
    assert math.isclose(results[1]["score"], 0.0, rel_tol=1e-6)


def test_search_by_vector_respects_min_score(embeddings_jsonl: Path) -> None:
    """min_score deve filtrar resultados abaixo do threshold."""
    store = index_reader.EmbeddingStore(str(embeddings_jsonl))

    # Vetor 45° entre [1,0] e [0,1] -> ambos com cos ~ 0.707
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    qvec = [inv_sqrt2, inv_sqrt2]

    results_all = store.search_by_vector(qvec, k=5, min_score=0.60)
    assert len(results_all) == 2  # ambos acima de 0.6

    results_high_threshold = store.search_by_vector(qvec, k=5, min_score=0.8)
    # Nenhum deve passar de 0.8
    assert results_high_threshold == []


class _DummyEmbedder:
    """Cliente de embeddings fake para testar search_by_text."""

    def __init__(self) -> None:
        self.last_texts: List[str] = []
        self.should_raise: bool = False
        self.return_empty: bool = False

    def embed(self, texts: List[str]) -> List[List[float]]:
        self.last_texts = texts
        if self.should_raise:
            raise RuntimeError("erro fake no embedder")
        if self.return_empty:
            return []
        # Retorna vetor paralelo a row-2 ([0, 1])
        return [[0.0, 1.0]]


def test_search_by_text_uses_embedder_and_delegates_to_search_by_vector(
    embeddings_jsonl: Path,
) -> None:
    """search_by_text deve usar embedder.embed e delegar para search_by_vector."""
    store = index_reader.EmbeddingStore(str(embeddings_jsonl))
    embedder = _DummyEmbedder()

    results = store.search_by_text("algum texto de consulta", embedder, k=1)

    # Garante que o embedder foi chamado com o texto correto
    assert embedder.last_texts == ["algum texto de consulta"]

    # Como o embedder retorna vetor paralelo a row-2, ela deve ser a primeira
    assert len(results) == 1
    assert results[0]["id"] == "row-2"


def test_search_by_text_returns_empty_when_embedder_fails(
    embeddings_jsonl: Path,
) -> None:
    """Se o embedder falhar ou retornar vetor vazio, search_by_text deve devolver []."""
    store = index_reader.EmbeddingStore(str(embeddings_jsonl))
    embedder = _DummyEmbedder()

    # Caso 1: embedder lança exceção
    embedder.should_raise = True
    results_err = store.search_by_text("texto", embedder, k=5)
    assert results_err == []

    # Caso 2: embedder retorna lista vazia
    embedder.should_raise = False
    embedder.return_empty = True
    results_empty = store.search_by_text("texto", embedder, k=5)
    assert results_empty == []
