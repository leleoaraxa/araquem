# app/api/ops/metrics.py
from fastapi import APIRouter

from app.observability.metrics import (
    compute_rag_index_metrics,
    list_metrics_catalog,
    register_rag_index_metrics,
)

router = APIRouter(prefix="/ops/metrics", tags=["ops-metrics"])


@router.get("/catalog")
def ops_metrics_catalog():
    return list_metrics_catalog()


@router.post("/rag/register")
def ops_rag_register_metrics():
    metrics = compute_rag_index_metrics()
    register_rag_index_metrics(metrics)
    return {"status": "ok", "metrics": metrics}
