# app/observability/instrumentation.py
# Facade de Observability — sem dependência de prometheus_client aqui.
# Implementação/registro ficam em app/observability/runtime.py, via set_backend().

from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable
import time

# ---------------- Backend plugável (injetado por runtime.bootstrap) ---------


_CACHE_ENTITY_COUNTERS = {
    "cache_hits_total",
    "cache_misses_total",
    "metrics_cache_hits_total",
    "metrics_cache_misses_total",
}


class _Backend:
    def inc(self, name: str, labels: Dict[str, str], value: float = 1.0) -> None: ...

    def observe(self, name: str, value: float, labels: Dict[str, str]) -> None: ...

    def set_gauge(self, name: str, value: float, labels: Dict[str, str]) -> None: ...

    def start_span(self, name: str, attributes: Dict[str, Any]): ...

    def end_span(
        self,
        span,
        exc_type: Optional[type] = None,
        exc_value: Optional[BaseException] = None,
        exc_tb: Any = None,
    ) -> None: ...

    def set_span_attr(self, span, key: str, value: Any) -> None: ...

    def span_trace_id(self, span) -> Optional[str]:
        return None

    def current_trace_id(self) -> Optional[str]:
        return None


_backend: Optional[_Backend] = None


def set_backend(backend: _Backend) -> None:
    global _backend
    _backend = backend


def _ensure():
    if _backend is None:
        raise RuntimeError(
            "Observability backend not initialized. Call runtime.bootstrap()."
        )


# ----------------- API genérica --------------------------------------------


def counter(name: str, **labels) -> None:
    _ensure()
    # Suporte a incremento arbitrário sem virar label
    value = float(labels.pop("_value", 1.0))
    if name in _CACHE_ENTITY_COUNTERS:
        entity = labels.pop("entity", "")
        if labels:
            raise ValueError(
                f"Cache metric '{name}' only accepts the 'entity' label."
            )
        labels = {"entity": "" if entity is None else str(entity)}
    _backend.inc(name, labels, value=value)


def histogram(name: str, value: float, **labels) -> None:
    _ensure()
    _backend.observe(name, value, labels)


def gauge(name: str, value: float, **labels) -> None:
    _ensure()
    _backend.set_gauge(name, float(value), labels)


@contextmanager
def trace(op: str, **attributes):
    _ensure()
    span = _backend.start_span(op, attributes)
    t0 = time.perf_counter()
    exc: Optional[BaseException] = None
    try:
        yield span
    except Exception as e:
        exc = e
        _backend.set_span_attr(span, "error", True)
        _backend.set_span_attr(span, "exception", repr(e))
        raise
    finally:
        _backend.set_span_attr(span, "latency_ms", (time.perf_counter() - t0) * 1000.0)
        if exc is not None:
            _backend.end_span(span, type(exc), exc, exc.__traceback__)
        else:
            _backend.end_span(span, None, None, None)


def set_trace_attribute(span, key: str, value: Any) -> None:
    _ensure()
    _backend.set_span_attr(span, key, value)


def get_trace_id(span=None) -> Optional[str]:
    if _backend is None:
        return None
    if span is not None:
        return _backend.span_trace_id(span)
    return _backend.current_trace_id()


def instrument(component: str, operation: str) -> Callable:
    """
    Decorator p/ latência + contador ok/erro padronizados (app_op_total).
    """

    def _wrap(fn: Callable) -> Callable:
        def _inner(*args, **kwargs):
            with trace(
                f"{component}.{operation}", component=component, operation=operation
            ):
                try:
                    res = fn(*args, **kwargs)
                    counter(
                        "app_op_total",
                        component=component,
                        operation=operation,
                        status="ok",
                    )
                    return res
                except Exception:
                    counter(
                        "app_op_total",
                        component=component,
                        operation=operation,
                        status="error",
                    )
                    raise

        return _inner

    return _wrap


# ----------------- Atalhos canônicos de M6.6 (Explain) ---------------------


def record_explain_start() -> None:
    # Mantido como no contrato (no-op por ora, útil se formos separar timers)
    return None


def record_explain_success(explain: Dict[str, Any], latency_ms: float) -> None:
    intent = str(explain.get("intent", "")) or ""
    entity = str(explain.get("entity", "")) or ""
    route_id = str(explain.get("route_id", "")) or ""
    counter("planner_explain_total", intent=intent, entity=entity, route_id=route_id)
    histogram(
        "planner_explain_latency_ms_bucket",
        float(latency_ms),
        intent=intent,
        entity=entity,
        route_id=route_id,
    )


def record_explain_error(stage: str) -> None:
    counter("planner_explain_errors_total", stage=str(stage or ""))


def compare_with_gold(
    explain: Dict[str, Any], gold_intent: Optional[str], gold_entity: Optional[str]
) -> None:
    if gold_intent is None and gold_entity is None:
        return
    intent = str(explain.get("intent", "")) or ""
    entity = str(explain.get("entity", "")) or ""
    route_id = str(explain.get("route_id", "")) or ""
    counter("planner_explain_gold_total", intent=intent, entity=entity)
    is_ok = (gold_intent == intent) and (gold_entity == entity)
    counter(
        "planner_explain_match_total",
        intent=intent,
        entity=entity,
        route_id=route_id,
        match=("correct" if is_ok else "wrong"),
    )
    if is_ok:
        counter("planner_explain_gold_agree_total", intent=intent, entity=entity)
