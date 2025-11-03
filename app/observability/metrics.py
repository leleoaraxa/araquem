# app/observability/metrics.py

from __future__ import annotations
import os
from typing import Dict, Iterable, Mapping, Any

from app.observability.instrumentation import counter as _counter
from app.observability.instrumentation import histogram as _histogram

STRICT = os.getenv("SIRIOS_METRICS_STRICT", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Catálogo canônico: nome -> {type, labels}
_METRICS_SCHEMA: Dict[str, Dict[str, Any]] = {
    # HTTP
    "sirios_http_request_duration_seconds": {
        "type": "histogram",
        "labels": {"route", "method"},
    },
    "sirios_http_requests_total": {
        "type": "counter",
        "labels": {"route", "method", "code"},
    },
    # Planner / routing
    "sirios_planner_duration_seconds": {
        "type": "histogram",
        "labels": {"stage"},
    },  # e.g., stage=plan
    "sirios_planner_routed_total": {
        "type": "counter",
        "labels": {"outcome"},
    },  # ok | unroutable
    "sirios_planner_explain_enabled_total": {"type": "counter", "labels": set()},
    "sirios_planner_explain_latency_seconds": {"type": "histogram", "labels": set()},
    "sirios_planner_top2_gap_histogram": {"type": "histogram", "labels": set()},
    "sirios_planner_blocked_by_threshold_total": {
        "type": "counter",
        "labels": {"reason", "intent", "entity"},
    },
    "sirios_planner_route_decisions_total": {
        "type": "counter",
        "labels": {"intent", "entity", "outcome"},
    },
    "sirios_planner_explain_nodes_total": {"type": "counter", "labels": {"node_kind"}},
    "sirios_planner_intent_score": {"type": "histogram", "labels": {"intent"}},
    "sirios_planner_entity_score": {"type": "histogram", "labels": {"entity"}},
    "sirios_planner_projection_total": {
        "type": "counter",
        "labels": {"outcome", "entity"},
    },
    # Quality / routing checks (usadas no /ops/quality/push e no quality_report)
    "sirios_planner_top1_match_total": {
        "type": "counter",
        "labels": {"result"},  # result=hit|miss
    },
    "sirios_planner_confusion_total": {
        "type": "counter",
        "labels": {"expected_intent", "predicted_intent"},
    },
    # (mantém-se o restante do catálogo)
    # Cache
    "sirios_cache_ops_total": {
        "type": "counter",
        "labels": {"op", "outcome"},
    },  # op=get|set, outcome=hit|miss|ok|fail
    # Explain persistence
    "sirios_explain_events_failed_total": {"type": "counter", "labels": set()},
}


def _validate_and_normalize(name: str, labels: Mapping[str, Any]) -> Mapping[str, str]:
    spec = _METRICS_SCHEMA.get(name)
    if spec is None:
        if STRICT:
            raise ValueError(f"[metrics] Métrica não cadastrada: {name}")
        # Em modo não-estrito, permite qualquer label (retrocompat), mas ainda normaliza
        return {k: str(v) for k, v in labels.items() if v is not None}

    allowed = spec.get("labels", set())
    unknown = set(labels.keys()) - set(allowed)
    if unknown and STRICT:
        raise ValueError(
            f"[metrics] Labels não permitidos para {name}: {sorted(unknown)}; permitidos={sorted(allowed)}"
        )

    # filtra desconhecidos em modo brando
    return {k: str(v) for k, v in labels.items() if (k in allowed and v is not None)}


def emit_counter(name: str, **labels: Any) -> None:
    value = float(labels.pop("_value", 1.0))
    labs = _validate_and_normalize(name, labels)
    _counter(name, _value=value, **labs)


def emit_histogram(name: str, value: float, **labels: Any) -> None:
    labs = _validate_and_normalize(name, labels)
    _histogram(name, float(value), **labs)


# Opcional: utilidade para consultar o catálogo (debug/admin)
def list_metrics_catalog() -> Dict[str, Dict[str, Any]]:
    return {
        k: {"type": v["type"], "labels": sorted(list(v["labels"]))}
        for k, v in _METRICS_SCHEMA.items()
    }
