import json
import math
import time
from decimal import Decimal
from typing import Any
from uuid import uuid4

from fastapi import Request

from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.observability.instrumentation import get_trace_id


def _make_request_id() -> str:
    """Replica da implementação original de geração de request_id."""
    trace_id = get_trace_id()
    if trace_id:
        return trace_id
    return uuid4().hex


def make_request_id() -> str:
    return _make_request_id()


def _json_sanitize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    if isinstance(obj, Decimal):
        try:
            f = float(obj)
            if math.isnan(f) or math.isinf(f):
                return 0.0
            return f
        except Exception:
            return 0.0
    if isinstance(obj, dict):
        return {str(k): _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_sanitize(v) for v in obj]
    try:
        return json.loads(json.dumps(obj))
    except Exception:
        return str(obj)


def json_sanitize(obj: Any) -> Any:
    return _json_sanitize(obj)


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dt = time.perf_counter() - start

    route = request.url.path
    method = request.method
    status = str(response.status_code)

    histogram("sirios_http_request_duration_seconds", dt, route=route, method=method)
    counter("sirios_http_requests_total", route=route, method=method, code=status)
    return response


__all__ = ["json_sanitize", "make_request_id", "metrics_middleware"]
