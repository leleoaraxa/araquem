from fastapi import APIRouter
from fastapi.responses import JSONResponse
from opentelemetry import trace

from app.core.context import planner

router = APIRouter()


@router.get("/debug/planner")
def debug_planner(q: str):
    try:
        return planner.explain(q)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/_debug/trace")
def debug_trace():
    tr = trace.get_tracer("api.debug")
    with tr.start_as_current_span("manual_debug_span"):
        return {"ok": True}
