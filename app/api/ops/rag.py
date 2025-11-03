# app/api/ops/rag.py
from fastapi import APIRouter
from pathlib import Path
import os, time, json

from app.utils.filecache import load_jsonl_cached
from app.observability.metrics import emit_gauge

router = APIRouter(prefix="/ops/rag", tags=["ops"])


def _has_vec(r):
    v = r.get("embedding")
    return isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v)


@router.post("/refresh")
def rag_refresh():
    idx_path = os.getenv("RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl")
    p = Path(idx_path)
    if not p.exists():
        emit_gauge("rag_index_size_total", 0)
        emit_gauge("rag_index_docs_total", 0)
        emit_gauge("rag_index_last_refresh_timestamp", 0)
        emit_gauge("rag_index_density_score", 0.0)
        return {"ok": False, "reason": "missing_index", "path": idx_path}

    rows = load_jsonl_cached(idx_path) or []
    docs_total = len(rows)
    with_vec = sum(1 for r in rows if _has_vec(r))
    density = (with_vec / docs_total) if docs_total > 0 else 0.0
    size_bytes = p.stat().st_size if p.exists() else 0
    now_epoch = int(time.time())

    emit_gauge("rag_index_size_total", float(size_bytes))
    emit_gauge("rag_index_docs_total", float(docs_total))
    emit_gauge("rag_index_last_refresh_timestamp", float(now_epoch))
    emit_gauge("rag_index_density_score", float(density))

    return {
        "ok": True,
        "size": size_bytes,
        "docs": docs_total,
        "density": density,
        "ts": now_epoch,
    }
