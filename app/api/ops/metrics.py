# app/api/ops/metrics.py
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.observability.metrics import (
    compute_rag_index_metrics,
    list_metrics_catalog,
    register_rag_eval_metrics,
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


class RagEvalPayload(BaseModel):
    recall_at_5: float = Field(..., ge=0.0)
    recall_at_10: float = Field(..., ge=0.0)
    mrr: float = Field(..., ge=0.0)
    ndcg_at_10: float = Field(..., ge=0.0)
    ts: int | None = None  # epoch


@router.post("/rag/eval/register")
def ops_rag_eval_register(payload: RagEvalPayload):
    register_rag_eval_metrics(payload.dict())
    return {"status": "ok", "metrics": payload.dict()}
