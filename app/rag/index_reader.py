# app/rag/index_reader.py
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List

from app.core.hotreload import get_manifest_hash


_EMB_CACHE = {"key": None, "rows": None, "mtime": None}


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
        if not self.path.exists():
            raise FileNotFoundError(jsonl_path)

        resolved_path = str(self.path.resolve())
        manifest_path = self.path.parent / "manifest.json"
        manifest_hash = get_manifest_hash(str(manifest_path))
        cache_key = (resolved_path, manifest_hash)

        try:
            current_mtime = self.path.stat().st_mtime
        except OSError:
            current_mtime = None

        cached_rows = _EMB_CACHE.get("rows")
        cached_key = _EMB_CACHE.get("key")
        cached_mtime = _EMB_CACHE.get("mtime")

        if (
            cached_rows is not None
            and cached_key == cache_key
            and (
                current_mtime is None
                or cached_mtime is None
                or math.isclose(cached_mtime, current_mtime)
            )
        ):
            self._rows = cached_rows
        else:
            rows: List[Dict[str, Any]] = []
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    rows.append(json.loads(line))
            _EMB_CACHE["key"] = cache_key
            _EMB_CACHE["rows"] = rows
            _EMB_CACHE["mtime"] = current_mtime
            self._rows = rows

    def rows_with_vectors(self) -> List[Dict[str, Any]]:
        """Retorna somente linhas com vetor não-vazio (sanity)."""
        return [r for r in self._rows if _has_vec(r)]

    def search_by_vector(
        self, qvec: List[float], k: int = 5, min_score: float | None = None
    ) -> List[Dict[str, Any]]:
        rows = self.rows_with_vectors()  # <-- filtra vazios
        scored = [(_cos(qvec, r["embedding"]), r) for r in rows]
        scored.sort(key=lambda t: t[0], reverse=True)
        ranked = [dict(score=s, **r) for s, r in scored]
        if min_score is not None:
            ranked = [r for r in ranked if float(r.get("score", 0.0)) >= min_score]
        return ranked[:k]

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
