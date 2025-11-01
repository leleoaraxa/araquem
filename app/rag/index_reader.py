# app/rag/index_reader.py
from __future__ import annotations
import os, json
from pathlib import Path
from typing import Dict, Any, List
import math


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

    def search_by_vector(self, qvec: List[float], k: int = 5) -> List[Dict[str, Any]]:
        scored = [(_cos(qvec, r["embedding"]), r) for r in self._rows]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [dict(score=s, **r) for s, r in scored[:k]]
