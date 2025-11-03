# app/api/ops/analytics.py
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.analytics.repository import fetch_explain_events, fetch_explain_summary
from app.common.http import json_sanitize

router = APIRouter()


@router.get("/ops/analytics/explain")
def ops_analytics_explain(
    window: str = Query(default="24h"),
    intent: Optional[str] = Query(default=None),
    entity: Optional[str] = Query(default=None),
    route_id: Optional[str] = Query(default=None),
    cache_hit: Optional[bool] = Query(default=None),
):
    out = fetch_explain_summary(
        window=window,
        intent=intent,
        entity=entity,
        route_id=route_id,
        cache_hit=cache_hit,
    )
    return JSONResponse(json_sanitize(out))


class ExplainFilters(BaseModel):
    window: str = "24h"
    intent: Optional[str] = None
    entity: Optional[str] = None
    route_id: Optional[str] = None
    cache_hit: Optional[bool] = None


@router.post("/ops/analytics/explain")
def ops_analytics_explain_post(body: ExplainFilters):
    out = fetch_explain_summary(
        window=body.window,
        intent=body.intent,
        entity=body.entity,
        route_id=body.route_id,
        cache_hit=body.cache_hit,
    )
    return JSONResponse(json_sanitize(out))


@router.get("/ops/analytics/explain/events")
def ops_analytics_explain_events(
    window: str = Query(default="24h"),
    intent: Optional[str] = Query(default=None),
    entity: Optional[str] = Query(default=None),
    route_id: Optional[str] = Query(default=None),
    cache_hit: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    out = fetch_explain_events(
        window=window,
        intent=intent,
        entity=entity,
        route_id=route_id,
        cache_hit=cache_hit,
        limit=limit,
        offset=offset,
    )
    return JSONResponse(json_sanitize(out))
