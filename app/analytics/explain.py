# app/analytics/explain.py
"""
Explainability core for Araquem — Guardrails v2.0 compliant

This module generates a human-readable explanation for a routed request
without introducing heuristics or hardcodes about the data layer.
It consumes *inputs* (request_id, planner_output, metrics) and returns a
structured payload ready to be serialized and attached to responses or logs.

Design notes (Guardrails alignment):
- Source of truth remains YAML/ontology/SQL. We *do not* infer or fetch data here.
- This module only formats/aggregates already-decided information.
- No direct imports from planner/executor internals beyond standard types.
- Tracing is added via OpenTelemetry; metrics are *inputs*, not scraped here.

Usage:
    from app.analytics.explain import explain
    payload = explain(request_id, planner_output, metrics)
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from app.observability.instrumentation import (
    set_trace_attribute,
    trace as start_trace,
)


@dataclass
class ExplainDetails:
    intent: Optional[str] = None
    entity: Optional[str] = None
    view: Optional[str] = None
    route_id: Optional[str] = None
    cache_hit: Optional[bool] = None
    latency_ms: Optional[float] = None
    route_source: Optional[str] = None  # e.g., "planner", "cache", "fallback"
    notes: Optional[str] = None  # free-form, but caller-controlled


def _pick(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely pick the first present key from a dict; avoids schema coupling."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _coerce_latency_ms(value: Any) -> Optional[float]:
    """Coerce provided latency to milliseconds if possible; avoid guessing."""
    if value is None:
        return None
    try:
        # Accept numeric already-in-ms
        if isinstance(value, (int, float)):
            return float(value)
        # Accept dict forms like {"ms": 12.3} or {"seconds": 0.0123}
        if isinstance(value, dict):
            if "ms" in value and isinstance(value["ms"], (int, float)):
                return float(value["ms"])
            if "seconds" in value and isinstance(value["seconds"], (int, float)):
                return float(value["seconds"]) * 1000.0
        # Accept strings like "42" or "42ms" or "0.042s"
        if isinstance(value, str):
            v = value.strip().lower()
            if v.endswith("ms"):
                return float(v[:-2].strip())
            if v.endswith("s"):
                return float(v[:-1].strip()) * 1000.0
            return float(v)
    except Exception:
        return None
    return None


def _build_summary(d: ExplainDetails) -> str:
    """Compose a concise, human-readable summary from details."""
    parts = []
    # Core target
    if d.entity and d.intent:
        parts.append(f"Consulta '{d.intent}' em '{d.entity}'")
    elif d.entity:
        parts.append(f"Consulta em '{d.entity}'")
    elif d.intent:
        parts.append(f"Consulta '{d.intent}'")
    else:
        parts.append("Consulta executada")

    # View
    if d.view:
        parts.append(f"via view {d.view}")

    # Latency and cache
    perf_bits = []
    if d.latency_ms is not None:
        perf_bits.append(f"latência {d.latency_ms:.0f}ms")
    if d.cache_hit is True:
        perf_bits.append("cache hit")
    elif d.cache_hit is False:
        perf_bits.append("cache miss")
    if perf_bits:
        parts.append(f"({', '.join(perf_bits)})")

    return " ".join(parts) + "."


def explain(
    request_id: str,
    planner_output: Dict[str, Any],
    metrics: Dict[str, Any],
    *,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate an explainability payload for a single handled request.

    Parameters
    ----------
    request_id : str
        Correlation id (must be provided by the caller/orchestrator).
    planner_output : Dict[str, Any]
        Decision context produced upstream (planner/router). This function will
        *not* assume a rigid schema; it will attempt to read common keys like
        "intent", "entity", "view", or nested "route" forms.
    metrics : Dict[str, Any]
        Caller-provided metrics snapshot for this request (e.g., latency_ms,
        cache_hit). We do not scrape Prometheus here.
    notes : Optional[str]
        Free-form field for caller-controlled annotations (kept in details.notes).

    Returns
    -------
    Dict[str, Any]
        {
          "request_id": str,
          "timestamp": ISO8601,
          "summary": str,
          "details": { ...ExplainDetails... }
        }
    """
    with start_trace(
        "analytics.explain", component="analytics", operation="explain"
    ) as span:
        # Extract fields without coupling to a specific schema.
        # Direct keys
        intent = _pick(planner_output, "intent", "matched_intent", default=None)
        entity = _pick(planner_output, "entity", "matched_entity", default=None)
        view = _pick(planner_output, "view", "selected_view", default=None)
        route_id: Optional[str] = None

        # Nested route forms commonly used by planners
        route = (
            planner_output.get("route") if isinstance(planner_output, dict) else None
        )
        if isinstance(route, dict):
            intent = intent or _pick(route, "intent")
            entity = entity or _pick(route, "entity")
            view = view or _pick(route, "view")
            route_id = _pick(route, "route_id") or route_id

        if route_id is None:
            route_id = _pick(planner_output, "route_id", default=None)

        # Final fallback policy (retrocompatível):
        # route_id <- view <- entity <- ""
        if not route_id:
            route_id = view or entity or ""

        # Metrics inputs (caller-supplied)
        cache_hit = _pick(metrics, "cache_hit", default=None)
        latency_ms = _coerce_latency_ms(
            _pick(metrics, "latency_ms", "latency", default=None)
        )
        route_source = _pick(metrics, "route_source", default=None)

        details = ExplainDetails(
            intent=intent,
            entity=entity,
            view=view,
            route_id=route_id,
            cache_hit=cache_hit if isinstance(cache_hit, bool) else None,
            latency_ms=latency_ms,
            route_source=route_source,
            notes=notes,
        )

        summary = _build_summary(details)

        # Tracing attributes for correlation
        if span is not None:
            if intent:
                set_trace_attribute(span, "explain.intent", intent)
            if entity:
                set_trace_attribute(span, "explain.entity", entity)
            if view:
                set_trace_attribute(span, "explain.view", view)
            if route_id:
                set_trace_attribute(span, "explain.route_id", route_id)
            if latency_ms is not None:
                set_trace_attribute(span, "explain.latency_ms", latency_ms)
            if cache_hit is not None:
                set_trace_attribute(span, "explain.cache_hit", bool(cache_hit))
            if route_source:
                set_trace_attribute(span, "explain.route_source", route_source)

        payload = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "details": asdict(details),
        }
        return payload


__all__ = ["explain", "ExplainDetails"]
