# app/analytics/metrics.py
"""
Analytics KPIs summarizer — Guardrails v2.0 compliant

This module exposes pure functions to compute KPIs from *already collected*
metrics snapshots. It DOES NOT scrape Prometheus or perform I/O.
The orchestrator or a façade should pass structured snapshots.

Design Principles:
- Pure, deterministic, side-effect-free.
- No hardcodes about intents/entities beyond what snapshots provide.
- Return shapes are stable and JSON-serializable.

Snapshot contracts (examples):
- request_metrics: List[{
    "intent": str | None,
    "entity": str | None,
    "latency_ms": float | int,
    "cache_hit": bool | None,
  }]
- counters: Dict[str, float|int]  (optional, for aggregated counters)

Usage:
    from app.analytics.metrics import summarize
    kpis = summarize({"request_metrics": [...], "counters": {...}})
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple
from statistics import mean


def _safe_mean(values: Iterable[float]) -> Optional[float]:
    values = [float(v) for v in values if isinstance(v, (int, float))]
    return float(mean(values)) if values else None


def _ratio(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if not den:
        return None
    if num is None:
        return None
    return float(num) / float(den)


def summarize(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute high-level KPIs from in-memory snapshots.

    Parameters
    ----------
    snapshot: Dict[str, Any]
        {
          "request_metrics": List[{"intent", "entity", "latency_ms", "cache_hit"}],
          "counters": Dict[str, Number]  # optional
        }

    Returns
    -------
    Dict[str, Any]
        {
          "totals": {"requests": int, "cache_hits": int, "cache_ratio": float | None},
          "latency": {"avg_ms": float | None, "by_intent": {intent: float}},
        }
    """
    reqs: List[Dict[str, Any]] = snapshot.get("request_metrics") or []
    counters: Dict[str, Any] = snapshot.get("counters") or {}

    # Totals
    total_requests = len(reqs)
    cache_hits = sum(1 for r in reqs if r.get("cache_hit") is True)
    cache_ratio = _ratio(cache_hits, total_requests if total_requests else None)

    # Latency
    avg_latency = _safe_mean(r.get("latency_ms") for r in reqs)

    # Latency by intent
    intents: Dict[str, List[float]] = {}
    for r in reqs:
        i = r.get("intent")
        if not i:
            continue
        intents.setdefault(str(i), []).append(r.get("latency_ms"))
    latency_by_intent = {
        k: v for k in intents.keys() for v in [_safe_mean(intents[k])] if v is not None
    }

    return {
        "totals": {
            "requests": int(total_requests),
            "cache_hits": int(cache_hits),
            "cache_ratio": cache_ratio,
        },
        "latency": {
            "avg_ms": avg_latency,
            "by_intent": latency_by_intent,
        },
        "_meta": {
            "source": "snapshot",
            "contracts": {
                "request_metrics.intent": "str|None",
                "request_metrics.entity": "str|None",
                "request_metrics.latency_ms": "float|int",
                "request_metrics.cache_hit": "bool|None",
            },
        },
    }


__all__ = ["summarize"]
