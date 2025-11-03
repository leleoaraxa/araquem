from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.context import planner
from app.observability.instrumentation import trace as start_trace

router = APIRouter()


@router.get("/debug/planner")
def debug_planner(q: str):
    try:
        return planner.explain(q)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/_debug/trace")
def debug_trace():
    with start_trace("api.debug.manual", component="api", operation="debug"):
        return {"ok": True}
