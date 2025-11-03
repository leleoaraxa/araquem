from fastapi import APIRouter

from app.observability.metrics import list_metrics_catalog

router = APIRouter()


@router.get("/ops/metrics/catalog")
def ops_metrics_catalog():
    return list_metrics_catalog()
