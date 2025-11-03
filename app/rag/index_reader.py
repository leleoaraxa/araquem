# app/rag/index_reader.py
from __future__ import annotations
import os, json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional


def _has_vec(row: Dict[str, Any]) -> bool:
    v = row.get("embedding")
    return (
        isinstance(v, list)
        and len(v) > 0
        and all(isinstance(x, (int, float)) for x in v)
    )


def _cos(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return (dot / (na * nb)) if (na > 0 and nb > 0) else 0.0


class EmbeddingStore:
    def __init__(self, jsonl_path: str):
        self.path = Path(jsonl_path)
        self._rows: List[Dict[str, Any]] = []
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    self._rows.append(json.loads(line))
        else:
            raise FileNotFoundError(jsonl_path)

    def rows_with_vectors(self) -> List[Dict[str, Any]]:
        """Retorna somente linhas com vetor não-vazio (sanity)."""
        return [r for r in self._rows if _has_vec(r)]

    def search_by_vector(self, qvec: List[float], k: int = 5) -> List[Dict[str, Any]]:
        rows = self.rows_with_vectors()  # <-- filtra vazios
        scored = [(_cos(qvec, r["embedding"]), r) for r in rows]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [dict(score=s, **r) for s, r in scored[:k]]

    def search_by_text(self, text: str, embedder, k: int = 5) -> List[Dict[str, Any]]:
        """
        Usa um cliente de embeddings compatível (ex.: OllamaClient) que expõe .embed([text]) -> [[float]].
        """
        try:
            vecs = embedder.embed([text]) or []
            qvec = vecs[0] if vecs and isinstance(vecs[0], list) else []
        except Exception:
            qvec = []
        if not qvec:
            return []
        return self.search_by_vector(qvec, k=k)
