# app/api/ops/rag.py
import os
from pathlib import Path

from fastapi import APIRouter

from app.observability.metrics import compute_rag_index_metrics, register_rag_index_metrics

router = APIRouter(prefix="/ops/rag", tags=["ops"])


def _resolve_store_path() -> Path:
    idx_path = os.getenv("RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl")
    return Path(idx_path)


@router.post("/refresh")
def rag_refresh():
    store_path = _resolve_store_path()
    base_dir = store_path.parent
    filename = store_path.name
    metrics = compute_rag_index_metrics(base_dir=base_dir, filename=filename)
    register_rag_index_metrics(metrics)

    if not store_path.exists():
        return {
            "ok": False,
            "reason": "missing_index",
            "path": str(store_path),
            "metrics": metrics,
        }

    return {"ok": True, "metrics": metrics}
